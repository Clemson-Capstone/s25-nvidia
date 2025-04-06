FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for Prometheus
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    tar \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create directory for course data
RUN mkdir -p /app/course_data

# Copy application code
COPY . .

# Expose ports for API
EXPOSE 8012

# Command to run the fastapi application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8012"]