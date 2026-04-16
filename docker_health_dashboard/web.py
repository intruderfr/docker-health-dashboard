"""Flask web dashboard for Docker Health Monitoring."""

import logging
from datetime import datetime
from typing import Dict, Any, List

from flask import Flask, render_template_string, jsonify, request
from docker.errors import DockerException

from docker_health_dashboard.monitor import DockerHealthMonitor


logger = logging.getLogger(__name__)


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Docker Health Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        header {
            background: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        header h1 {
            margin-bottom: 10px;
            color: #667eea;
        }

        .timestamp {
            color: #666;
            font-size: 14px;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .card-title {
            font-size: 14px;
            color: #666;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .card-value {
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
        }

        .card-subtitle {
            font-size: 12px;
            color: #999;
            margin-top: 5px;
        }

        .status-running { color: #10b981; }
        .status-stopped { color: #ef4444; }
        .status-healthy { color: #10b981; }
        .status-unhealthy { color: #ef4444; }
        .status-starting { color: #f59e0b; }

        .containers-section {
            background: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .containers-section h2 {
            margin-bottom: 20px;
            color: #667eea;
        }

        .container-item {
            padding: 15px;
            border-left: 4px solid #667eea;
            margin-bottom: 15px;
            background: #f9fafb;
            border-radius: 4px;
        }

        .container-item:last-child {
            margin-bottom: 0;
        }

        .container-name {
            font-weight: bold;
            font-size: 16px;
            margin-bottom: 10px;
        }

        .container-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px;
            font-size: 12px;
        }

        .stat {
            padding: 8px;
            background: white;
            border-radius: 4px;
        }

        .stat-label {
            color: #666;
            font-size: 11px;
            text-transform: uppercase;
        }

        .stat-value {
            color: #333;
            font-weight: bold;
            margin-top: 4px;
        }

        .progress-bar {
            width: 100%;
            height: 4px;
            background: #e5e7eb;
            border-radius: 2px;
            margin-top: 4px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            background: #667eea;
            border-radius: 2px;
        }

        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }

        .error {
            background: #fee2e2;
            color: #991b1b;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }

        .refresh-info {
            text-align: right;
            color: #666;
            font-size: 12px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Docker Health Dashboard</h1>
            <p class="timestamp">Last updated: <span id="timestamp">loading...</span></p>
        </header>

        <div id="error-container"></div>

        <div class="grid" id="summary-cards">
            <div class="card">
                <div class="card-title">Total Containers</div>
                <div class="card-value" id="total-containers">-</div>
            </div>
            <div class="card">
                <div class="card-title">Running</div>
                <div class="card-value" id="running-containers" style="color: #10b981;">-</div>
            </div>
            <div class="card">
                <div class="card-title">Stopped</div>
                <div class="card-value" id="stopped-containers" style="color: #ef4444;">-</div>
            </div>
            <div class="card">
                <div class="card-title">Unhealthy</div>
                <div class="card-value" id="unhealthy-containers" style="color: #f59e0b;">-</div>
            </div>
        </div>

        <div class="grid" id="resource-cards">
            <div class="card">
                <div class="card-title">Memory Usage</div>
                <div class="card-value" id="memory-usage">-</div>
                <div class="progress-bar"><div class="progress-fill" id="memory-bar" style="width: 0%"></div></div>
            </div>
            <div class="card">
                <div class="card-title">CPU Usage</div>
                <div class="card-value" id="cpu-usage">-</div>
            </div>
        </div>

        <div class="containers-section">
            <h2>Containers</h2>
            <div id="containers-list" class="loading">Loading containers...</div>
        </div>

        <div class="refresh-info">
            Auto-refreshing every 5 seconds
        </div>
    </div>

    <script>
        async function fetchMetrics() {
            try {
                const response = await fetch('/api/metrics');
                if (!response.ok) throw new Error('Failed to fetch metrics');
                const data = await response.json();
                updateDashboard(data);
            } catch (error) {
                showError(`Error fetching metrics: ${error.message}`);
            }
        }

        function updateDashboard(data) {
            const agg = data.aggregated;

            document.getElementById('timestamp').textContent =
                new Date(agg.timestamp).toLocaleString();

            document.getElementById('total-containers').textContent = agg.total_containers;
            document.getElementById('running-containers').textContent = agg.running_containers;
            document.getElementById('stopped-containers').textContent = agg.stopped_containers;
            document.getElementById('unhealthy-containers').textContent = agg.unhealthy_containers;

            const memoryGb = (agg.total_memory_usage / (1024**3)).toFixed(2);
            const limitGb = (agg.total_memory_limit / (1024**3)).toFixed(2);
            document.getElementById('memory-usage').textContent = `${memoryGb}/${limitGb} GB`;

            const memoryPercent = agg.total_memory_limit > 0
                ? (agg.total_memory_usage / agg.total_memory_limit * 100)
                : 0;
            document.getElementById('memory-bar').style.width = memoryPercent + '%';

            document.getElementById('cpu-usage').textContent = agg.total_cpu_percent.toFixed(1) + '%';

            updateContainersList(data.containers);
            document.getElementById('error-container').innerHTML = '';
        }

        function updateContainersList(containers) {
            const list = document.getElementById('containers-list');

            if (containers.length === 0) {
                list.innerHTML = '<p class="loading">No containers found</p>';
                return;
            }

            const sorted = containers.sort((a, b) =>
                a.container_name.localeCompare(b.container_name)
            );

            list.innerHTML = sorted.map(c => `
                <div class="container-item">
                    <div class="container-name">${c.container_name}</div>
                    <div class="container-stats">
                        <div class="stat">
                            <div class="stat-label">Status</div>
                            <div class="stat-value status-${c.state}">${c.state.toUpperCase()}</div>
                        </div>
                        <div class="stat">
                            <div class="stat-label">Health</div>
                            <div class="stat-value">${c.health_status || 'N/A'}</div>
                        </div>
                        <div class="stat">
                            <div class="stat-label">Restarts</div>
                            <div class="stat-value">${c.restart_count}</div>
                        </div>
                        <div class="stat">
                            <div class="stat-label">Uptime</div>
                            <div class="stat-value">${Math.floor(c.uptime_seconds / 3600)}h</div>
                        </div>
                    </div>
                </div>
            `).join('');
        }

        function showError(message) {
            document.getElementById('error-container').innerHTML =
                `<div class="error">${message}</div>`;
        }

        // Initial load
        fetchMetrics();

        // Auto-refresh every 5 seconds
        setInterval(fetchMetrics, 5000);
    </script>
</body>
</html>
"""


def create_app(socket_url: str = None) -> Flask:
    """Create and configure Flask application."""
    app = Flask(__name__)

    try:
        monitor = DockerHealthMonitor(socket_url=socket_url)
    except DockerException as e:
        logger.error(f"Failed to connect to Docker: {e}")
        monitor = None

    @app.route("/")
    def index():
        """Render main dashboard page."""
        return render_template_string(HTML_TEMPLATE)

    @app.route("/api/metrics")
    def api_metrics():
        """Get aggregated metrics."""
        if not monitor:
            return jsonify({"error": "Docker connection failed"}), 500

        try:
            aggregated = monitor.get_aggregated_metrics()
            containers = monitor.get_all_containers()

            return jsonify({
                "aggregated": aggregated.to_dict(),
                "containers": [c.to_dict() for c in containers],
            })
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/containers")
    def api_containers():
        """Get list of all containers with health status."""
        if not monitor:
            return jsonify({"error": "Docker connection failed"}), 500

        try:
            containers = monitor.get_all_containers()
            return jsonify([c.to_dict() for c in containers])
        except Exception as e:
            logger.error(f"Error getting containers: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/containers/<container_id>")
    def api_container_detail(container_id: str):
        """Get detailed metrics for a specific container."""
        if not monitor:
            return jsonify({"error": "Docker connection failed"}), 500

        try:
            health = monitor.get_container_health(container_id)
            metrics = monitor.get_container_metrics(container_id)

            if not health:
                return jsonify({"error": "Container not found"}), 404

            return jsonify({
                "health": health.to_dict(),
                "metrics": metrics.to_dict() if metrics else None,
            })
        except Exception as e:
            logger.error(f"Error getting container details: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/health")
    def api_health():
        """Health check endpoint."""
        if not monitor:
            return jsonify({"status": "error", "message": "Docker not connected"}), 500

        try:
            aggregated = monitor.get_aggregated_metrics()
            return jsonify({
                "status": "healthy" if aggregated.unhealthy_containers == 0 else "degraded",
                "timestamp": aggregated.timestamp.isoformat(),
            })
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route("/api/containers/<container_id>/restart", methods=["POST"])
    def api_restart_container(container_id: str):
        """Restart a container."""
        if not monitor:
            return jsonify({"error": "Docker connection failed"}), 500

        try:
            container = monitor.client.containers.get(container_id)
            container.restart()
            return jsonify({"status": "success", "message": "Container restarted"})
        except Exception as e:
            logger.error(f"Error restarting container: {e}")
            return jsonify({"error": str(e)}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8080, debug=True)
