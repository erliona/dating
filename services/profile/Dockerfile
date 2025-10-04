FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY core/ core/
COPY adapters/ adapters/
COPY services/profile/ services/profile/

# Expose port
EXPOSE 8082

# Run the service
CMD ["python", "-m", "services.profile.main"]
