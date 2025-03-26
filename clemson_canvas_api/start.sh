#!/bin/bash
set -e

# Start Prometheus in the background
echo "Starting Prometheus..."
/prometheus/prometheus --config.file=/prometheus/prometheus.yml \
  --storage.tsdb.path=/prometheus/data \
  --web.console.libraries=/prometheus/console_libraries \
  --web.console.templates=/prometheus/consoles \
  --web.listen-address=0.0.0.0:9090 > /prometheus/prometheus.log 2>&1 &
PROMETHEUS_PID=$!

# Wait for Prometheus to start
echo "Waiting for Prometheus to start..."
sleep 3

# Check if Prometheus is running by checking if the process is still alive
if ! kill -0 $PROMETHEUS_PID 2>/dev/null; then
  echo "Prometheus failed to start. Check logs at /prometheus/prometheus.log"
  exit 1
fi
echo "Prometheus started successfully with PID $PROMETHEUS_PID"

# Start the FastAPI application
echo "Starting FastAPI application..."
exec uvicorn main:app --host 0.0.0.0 --port 8012