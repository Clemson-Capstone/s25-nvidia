FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for Prometheus
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    tar \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Prometheus
RUN mkdir -p /prometheus && \
    wget -qO- https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz | \
    tar xvz -C /prometheus --strip-components=1

# Copy Prometheus configuration
COPY prometheus.yml /prometheus/prometheus.yml

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create directory for course data
RUN mkdir -p /app/course_data

# Copy application code
COPY . .

# Expose ports for API and Prometheus
EXPOSE 8012 9090

# Create a startup script
COPY ./start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Command to run the application and Prometheus
CMD ["/app/start.sh"]