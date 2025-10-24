FROM python:3.11.7-slim

# SECURITY: Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install runtime dependencies
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        netcat-traditional \
        nginx \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY bot/ bot/
COPY core/ core/
COPY services/admin/ services/admin/
COPY migrations/ migrations/
COPY alembic.ini .

# Copy webapp static files
COPY webapp/ /usr/share/nginx/html/

# Copy nginx configuration
COPY services/admin/nginx.conf /etc/nginx/nginx.conf
COPY services/admin/default.conf /etc/nginx/conf.d/default.conf

# SECURITY: Set proper permissions
RUN chmod +x services/admin/entrypoint.sh \
    && chown -R appuser:appuser /app \
    && chown -R appuser:appuser /usr/share/nginx/html

# Note: Keep as root for entrypoint to create nginx directories
# USER appuser

# Set PYTHONPATH to find modules
ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8086

# Use entrypoint script to run migrations before starting the service
ENTRYPOINT ["./services/admin/entrypoint.sh"]
