FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY bot/ bot/
COPY core/ core/
COPY services/admin/ services/admin/

# Expose port
EXPOSE 8086

# Run the service
CMD ["python", "-m", "services.admin.main"]
