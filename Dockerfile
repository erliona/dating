# Multi-stage build for optimal image size
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim AS runtime

# Install only runtime dependencies
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        libpq5 \
        netcat-traditional \
        libgomp1 \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set up working directory
WORKDIR /app

# Copy application code
COPY bot ./bot
COPY migrations ./migrations
COPY webapp ./webapp
COPY alembic.ini .
COPY docker/entrypoint.sh ./docker/
COPY docker/healthcheck_bot.py ./docker/

# Make entrypoint and healthcheck executable
RUN chmod +x docker/entrypoint.sh docker/healthcheck_bot.py

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/opt/venv/bin:$PATH"

# Add health check using Telegram Bot API getMe
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python ./docker/healthcheck_bot.py

ENTRYPOINT ["./docker/entrypoint.sh"]
