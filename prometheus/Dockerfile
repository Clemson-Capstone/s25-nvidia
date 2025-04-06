FROM prom/prometheus:latest

# Create a non-root user to run Prometheus
USER root
RUN mkdir -p /prometheus && \
    chown -R nobody:nobody /prometheus

# Copy the prometheus configuration file
COPY prometheus.yml /etc/prometheus/prometheus.yml

# Set proper permissions
RUN chown nobody:nobody /etc/prometheus/prometheus.yml

# Switch back to non-root user
USER nobody

# Expose the Prometheus web UI port
EXPOSE 9090

# Command to run Prometheus with the config file
CMD ["--config.file=/etc/prometheus/prometheus.yml", \
     "--storage.tsdb.path=/prometheus", \
     "--web.console.libraries=/usr/share/prometheus/console_libraries", \
     "--web.console.templates=/usr/share/prometheus/consoles"]