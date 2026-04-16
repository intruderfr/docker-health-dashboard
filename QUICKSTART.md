# Quick Start Guide

Get Docker Health Dashboard up and running in minutes.

## Installation

### Via pip (Recommended)

```bash
pip install docker-health-dashboard
```

### From Source

```bash
git clone https://github.com/intruderfr/docker-health-dashboard.git
cd docker-health-dashboard
pip install -e .
```

## Basic Usage

### 1. Check Container Health

```bash
# Quick status summary
docker-health-dashboard status

# Expected output:
# Docker Health Summary
# ===================================================================
# | Metric                    | Count |
# |---------------------------|-------|
# | Total Containers          |   10  |
# | Running                   |    9  |
# | Stopped                   |    1  |
# ...
```

### 2. Real-time Monitoring

```bash
# Monitor containers with 5-second refresh
docker-health-dashboard monitor

# Monitor for specific duration (60 seconds)
docker-health-dashboard monitor --duration 60

# Custom refresh interval (3 seconds)
docker-health-dashboard monitor --interval 3
```

### 3. Inspect Specific Container

```bash
# Get detailed metrics for a container
docker-health-dashboard inspect my-container-name

# Shows health status, resource usage, restart count, uptime, etc.
```

### 4. System Health Report

```bash
# Get overall system health with issues
docker-health-dashboard health

# Output includes:
# - Overall Status (HEALTHY/DEGRADED/UNHEALTHY)
# - Health Score (0-100)
# - List of detected issues
```

### 5. Export Metrics

```bash
# Export all metrics to JSON
docker-health-dashboard export

# Export to custom file
docker-health-dashboard export --output my-metrics.json
```

## Web Dashboard

### Start the Server

```bash
docker-health-dashboard serve
```

Then open your browser to: http://localhost:8080

### Features
- Real-time container status
- CPU and memory usage graphs
- Health indicators
- Restart history
- Interactive container details

## Docker Compose

Run using Docker Compose:

```bash
docker-compose up
```

Access the dashboard at: http://localhost:8080

## Python API

```python
from docker_health_dashboard import DockerHealthMonitor

# Initialize monitor
monitor = DockerHealthMonitor()

# Get all containers
containers = monitor.get_all_containers()
for container in containers:
    print(f"{container.container_name}: {container.get_health_indicator()}")

# Get container metrics
metrics = monitor.get_container_metrics("my-container")
if metrics:
    print(f"Memory: {metrics.memory_percent:.1f}%")
    print(f"CPU: {metrics.cpu_percent:.2f}%")

# Find unhealthy containers
unhealthy = monitor.get_unhealthy_containers()
if unhealthy:
    print(f"Found {len(unhealthy)} unhealthy containers")

# Get system overview
agg = monitor.get_aggregated_metrics()
print(f"Running: {agg.running_containers}/{agg.total_containers}")
```

## Configuration

Create `.dhd-config.json` to customize behavior:

```json
{
  "refresh_interval": 5,
  "retention_days": 7,
  "alert_threshold_restart": 5,
  "alert_threshold_memory_percent": 80,
  "alert_threshold_cpu_percent": 90,
  "web_port": 8080,
  "web_host": "0.0.0.0"
}
```

## Troubleshooting

### Permission Denied

```bash
# Docker requires elevated permissions
sudo docker-health-dashboard status

# Or add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### Connection Refused

```bash
# Verify Docker daemon is running
docker ps

# Try with explicit socket
docker-health-dashboard --socket unix:///var/run/docker.sock status
```

### No Containers Found

```bash
# Check if you have running containers
docker ps

# List all containers including stopped
docker ps -a
```

## Next Steps

- Read [README.md](README.md) for detailed documentation
- Check [CONTRIBUTING.md](CONTRIBUTING.md) to contribute
- Review [API documentation](README.md#api-endpoints) for REST API
- Explore [examples](examples/) folder for more use cases

## Support

- GitHub Issues: https://github.com/intruderfr/docker-health-dashboard/issues
- Discussions: https://github.com/intruderfr/docker-health-dashboard/discussions

Enjoy monitoring your Docker containers!
