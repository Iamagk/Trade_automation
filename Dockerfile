FROM python:3.10-slim

# Install Node.js
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Node.js dependencies for the server
COPY server/package*.json ./server/
RUN cd server && npm install

# Copy all files
COPY . .

# Build Node.js server
RUN cd server && npm run build

# Expose port (Render sets PORT env)
ENV PORT=8000

# Command to run the Node.js application
CMD ["node", "server/dist/index.js"]
