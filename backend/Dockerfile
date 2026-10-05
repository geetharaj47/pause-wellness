# Base Python Image
FROM python:3.12-slim

# Set environment paths
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /backend

# Install system dependencies (e.g. build-essential for C++ extensions if needed by ML libraries)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy source directories
COPY app/ ./app/

# Expose backend port
EXPOSE 8000

# Start Uvicorn ASGI server (dynamically bound to $PORT for cloud hosting or 8000 for local)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
