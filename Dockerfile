FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (if any needed for psycopg2 or others)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose port (Render sets PORT env)
ENV PORT=8000

# Command to run the application
CMD uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
