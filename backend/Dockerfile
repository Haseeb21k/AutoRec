# Use python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set env variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for SQLite DB if not exists (though we use Postgres on Railway)
RUN mkdir -p /app/data

# Command uses shell form to interpolate $PORT variable
# Listen on 0.0.0.0 (IPv4) - Standard for most Docker environments
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
