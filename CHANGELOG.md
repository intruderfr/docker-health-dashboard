# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-04-16

### Added
- Initial release of Docker Health Dashboard
- CLI tool with multiple commands:
  - `status`: Quick health summary
  - `monitor`: Real-time monitoring with auto-refresh
  - `inspect`: Detailed container analysis
  - `export`: JSON metrics export
  - `health`: System health report
- Web dashboard with interactive UI
  - Real-time metrics visualization
  - Container status monitoring
  - Resource usage graphs
  - Health indicators
- Docker Health Monitor API
  - Container health tracking
  - Resource metrics collection
  - Aggregated system metrics
  - Health status detection
- REST API endpoints for integration
- Docker Compose configuration
- Comprehensive test suite
- MIT License
- Contributing guidelines

### Features
- Lightweight monitoring with minimal overhead
- Support for 100+ containers
- Configurable alert thresholds
- Health check integration
- Excessive restart detection
- Network and block I/O metrics
- JSON export for external tools
- Docker socket authentication
- Auto-restart detection

## Future Releases

### Planned for v1.1.0
- Prometheus metrics exporter
- Alert notifications (email, Slack, webhook)
- Historical trend analysis
- Container log aggregation
- Performance comparison views

### Planned for v2.0.0
- Multi-host Docker monitoring
- Kubernetes container support
- Database backend for metrics
- Advanced analytics and reporting
- Custom alert rules engine
- API authentication and authorization

---

For more information, visit the [GitHub repository](https://github.com/intruderfr/docker-health-dashboard).
