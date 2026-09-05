FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for compiling packages & PostgreSQL client libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

EXPOSE 8000

# Use entrypoint script for automated startup (DB wait → download → ingest → serve)
CMD ["./entrypoint.sh"]
