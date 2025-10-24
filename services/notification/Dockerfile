FROM python:3.11.7-slim

# SECURITY: Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY core/ core/
COPY services/notification/ services/notification/

# SECURITY: Set proper permissions
RUN chown -R appuser:appuser /app

# SECURITY: Switch to non-root user
USER appuser

# Set PYTHONPATH to find modules
ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8087

# Run the service
CMD ["python", "-m", "services.notification.main"]
