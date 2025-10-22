FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY bot/ bot/
COPY core/ core/
COPY services/auth/ services/auth/

# Set PYTHONPATH to find modules
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8081

# Run the service
CMD ["python", "-m", "services.auth.main"]
