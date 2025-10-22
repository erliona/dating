FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        netcat-traditional \
        nginx \
    && rm -rf /var/lib/apt/lists/*

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
COPY webapp/nginx.conf /etc/nginx/conf.d/default.conf

# Make entrypoint executable
RUN chmod +x services/admin/entrypoint.sh

# Set PYTHONPATH to find modules
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8086

# Use entrypoint script to run migrations before starting the service
ENTRYPOINT ["./services/admin/entrypoint.sh"]
