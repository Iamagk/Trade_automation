FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY trading_system/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY trading_system/ trading_system/

# Copy env template (will be overridden by Docker Compose / Secret Manager in prod)
COPY trading_system/.env.example .env

# Expose API port
EXPOSE 8000

# Set Python path so `trading_system` is importable
ENV PYTHONPATH=/app

# Start the application
CMD ["uvicorn", "trading_system.main:app", "--host", "0.0.0.0", "--port", "8000"]
