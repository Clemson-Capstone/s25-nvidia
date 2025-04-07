# Prometheus Monitoring Service

## Overview

This module provides metrics collection, storage, and alerting functionality for the S25-NVIDIA project using Prometheus. It collects performance metrics from various microservices including the Course Manager API, NextJS frontend, and Milvus vector database to enable real-time monitoring, troubleshooting, and performance optimization.

## Features

- **Centralized Metrics Collection**: Scrapes metrics from multiple services
- **Real-time Monitoring**: 5-second scrape intervals for responsive monitoring
- **Secure Deployment**: Runs as non-root user for enhanced security
- **Container-Ready**: Fully containerized for easy deployment
- **Integrated Services**: Pre-configured to monitor all project components
- **Time-Series Database**: Built-in TSDB for historical metric storage

## Architecture

Prometheus acts as the central metrics collector in this architecture, pulling metrics from instrumented services at regular intervals.

```
┌─────────────────┐     ┌────────────────────┐
│                 │     │                    │
│  Course Manager │◄────┤                    │
│  API (8012)     │     │                    │
│                 │     │                    │
└─────────────────┘     │                    │
                        │                    │
┌─────────────────┐     │    Prometheus     │
│                 │     │    Server (9090)   │
│  NextJS Frontend│◄────┤                    │
│  (3000)         │     │                    │
│                 │     │                    │
└─────────────────┘     │                    │
                        │                    │
┌─────────────────┐     │                    │
│                 │     │                    │
│  Milvus Database│◄────┤                    │
│  (9091)         │     │                    │
│                 │     │                    │
└─────────────────┘     └────────────────────┘
```

## Technical Specifications

### Dependencies

| Component                  | Version               | Purpose                                     |
|----------------------------|----------------------|----------------------------------------------|
| Prometheus Server          | latest               | Metrics collection and storage               |

### File Structure

```
prometheus/
├── Dockerfile              # Container definition
├── prometheus.yml          # Prometheus configuration
└── README.md               # This documentation file
```

### Configuration

The `prometheus.yml` file defines the scraping configuration:

```yaml
global:
  scrape_interval: 15s      # Default interval for all targets
  evaluation_interval: 15s  # How frequently to evaluate rules

scrape_configs:
  - job_name: 'course_data_manager'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['host.docker.internal:8012']
    scrape_interval: 5s     # Override for this specific target

  - job_name: 'nextjs_frontend'
    metrics_path: '/api/metrics'
    static_configs:
      - targets: ['host.docker.internal:3000']
    scrape_interval: 5s

  - job_name: 'milvus_standalone'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['host.docker.internal:9091']
    scrape_interval: 5s
```

## Monitored Services

### Course Data Manager API

- **Port**: 8012
- **Metrics Path**: `/metrics`
- **Scrape Interval**: 5s
- **Metrics**: Request counts, latency, active requests, file processing stats

### NextJS Frontend

- **Port**: 3000
- **Metrics Path**: `/api/metrics`
- **Scrape Interval**: 5s
- **Metrics**: Page load times, API requests, client-side errors

### Milvus Vector Database

- **Port**: 9091
- **Metrics Path**: `/metrics`
- **Scrape Interval**: 5s
- **Metrics**: Query performance, index stats, memory usage

## Running the Service

### Docker Environment

The Prometheus service is containerized using Docker:

```bash
# Build the image
docker build -t s25-nvidia-prometheus .

# Run the container
docker run -d -p 9090:9090 --name s25-prometheus s25-nvidia-prometheus
```

### Configuration Options

Additional configuration options can be passed as command-line arguments:

```bash
docker run -d -p 9090:9090 --name s25-prometheus s25-nvidia-prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/prometheus \
  --storage.tsdb.retention.time=15d \
  --web.enable-lifecycle
```

### Volume Mounts (Optional)

For persistent storage of metrics:

```bash
docker run -d -p 9090:9090 \
  -v $(pwd)/prometheus-data:/prometheus \
  --name s25-prometheus s25-nvidia-prometheus
```

## Security Considerations

- **Non-root Execution**: Container runs as `nobody` user
- **Minimal Attack Surface**: Contains only necessary components
- **Read-only Configuration**: Configuration files have appropriate permissions
- **Network Isolation**: Only exposes the required 9090 port

## Integration Points

This Prometheus service integrates with:

1. **Course Manager API**: Collects service metrics, request latency, and file processing stats
2. **NextJS Frontend**: Monitors client-side performance and API interactions
3. **Milvus Database**: Tracks vector database performance and resource usage
4. **Grafana (optional)**: Can be connected as a data source for advanced dashboards

## Using the Prometheus UI

The Prometheus web interface is available at:

```
http://localhost:9090/
```

Key features of the UI:

- **Expression Browser**: Query metrics using PromQL 
- **Graph View**: Visualize metric trends over time
- **Targets Page**: Monitor scraping status of all endpoints
- **Alerts Page**: View and manage alerting rules
- **Status Page**: Check Prometheus server health and configuration

## Example PromQL Queries

### Course Manager API Performance

```
rate(course_data_manager_request_processing_seconds_count[5m])
```

### Active Requests

```
course_data_manager_active_requests
```

### File Size Distribution

```
histogram_quantile(0.95, sum(rate(course_data_manager_file_sizes_bytes_bucket[5m])) by (le))
```

## Troubleshooting

- **Target Scraping Failures**: Verify network connectivity and service availability
- **Missing Metrics**: Check that services are properly instrumented
- **High Cardinality Issues**: Review metric labels for excessive values
- **Storage Issues**: Monitor disk usage with `prometheus_tsdb_size_bytes`

## Maintainers

This module is part of the S25-NVIDIA project.

## License

Refer to the main project repository for license information.
