FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY core/ core/
COPY adapters/ adapters/
COPY services/chat/ services/chat/

# Set PYTHONPATH to find modules
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8085

# Run the service
CMD ["python", "-m", "services.chat.main"]
