"""Tests for Docker Health Monitor."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from docker_health_dashboard.monitor import DockerHealthMonitor
from docker_health_dashboard.models import ContainerHealth, ContainerMetrics


@pytest.fixture
def mock_docker_client():
    """Create a mock Docker client."""
    with patch("docker_health_dashboard.monitor.docker") as mock:
        client = MagicMock()
        mock.from_env.return_value = client
        mock.DockerClient.return_value = client
        yield mock, client


@pytest.fixture
def monitor(mock_docker_client):
    """Create a DockerHealthMonitor instance with mocked client."""
    mock_module, mock_client = mock_docker_client
    monitor = DockerHealthMonitor()
    monitor.client = mock_client
    return monitor


class TestDockerHealthMonitor:
    """Test DockerHealthMonitor class."""

    def test_initialization(self, monitor):
        """Test monitor initialization."""
        assert monitor.client is not None
        assert monitor.metrics_history == {}

    def test_get_all_containers(self, monitor):
        """Test getting all containers."""
        # Create mock containers
        mock_container = MagicMock()
        mock_container.id = "abc123"
        mock_container.name = "test-container"
        mock_container.attrs = {
            "State": {
                "Status": "running",
                "RestartCount": 0,
                "StartedAt": "2026-01-01T00:00:00Z",
            },
            "Created": "2026-01-01T00:00:00Z",
        }

        monitor.client.containers.list.return_value = [mock_container]

        containers = monitor.get_all_containers()

        assert len(containers) == 1
        assert isinstance(containers[0], ContainerHealth)
        assert containers[0].container_name == "test-container"

    def test_get_container_health_found(self, monitor):
        """Test getting health of a specific container."""
        mock_container = MagicMock()
        mock_container.id = "abc123"
        mock_container.name = "test-container"
        mock_container.attrs = {
            "State": {
                "Status": "running",
                "RestartCount": 2,
                "StartedAt": "2026-01-01T00:00:00Z",
            },
            "Created": "2026-01-01T00:00:00Z",
        }

        monitor.client.containers.get.return_value = mock_container

        health = monitor.get_container_health("abc123")

        assert health is not None
        assert health.container_id == "abc123"
        assert health.restart_count == 2

    def test_get_container_health_not_found(self, monitor):
        """Test getting health of non-existent container."""
        import docker

        monitor.client.containers.get.side_effect = docker.errors.NotFound("Not found")

        health = monitor.get_container_health("nonexistent")

        assert health is None

    def test_get_container_metrics(self, monitor):
        """Test getting container metrics."""
        mock_container = MagicMock()
        mock_container.stats.return_value = {
            "cpu_stats": {
                "cpu_usage": {"total_usage": 1000000},
                "system_cpu_usage": 10000000,
                "cpus": [0, 1],
            },
            "precpu_stats": {
                "cpu_usage": {"total_usage": 900000},
                "system_cpu_usage": 9000000,
            },
            "memory_stats": {"usage": 512 * 1024 * 1024, "limit": 1024 * 1024 * 1024},
            "networks": {"eth0": {"rx_bytes": 1024, "tx_bytes": 2048}},
            "blkio_stats": {"io_service_bytes_recursive": []},
        }

        monitor.client.containers.get.return_value = mock_container

        metrics = monitor.get_container_metrics("abc123")

        assert metrics is not None
        assert isinstance(metrics, ContainerMetrics)
        assert metrics.memory_percent == 50.0

    def test_get_unhealthy_containers(self, monitor):
        """Test getting unhealthy containers."""
        mock_container = MagicMock()
        mock_container.id = "abc123"
        mock_container.name = "unhealthy"
        mock_container.attrs = {
            "State": {
                "Status": "exited",
                "RestartCount": 0,
                "StartedAt": "2026-01-01T00:00:00Z",
            },
            "Created": "2026-01-01T00:00:00Z",
        }

        monitor.client.containers.list.return_value = [mock_container]

        unhealthy = monitor.get_unhealthy_containers()

        assert len(unhealthy) == 1

    def test_get_containers_with_excessive_restarts(self, monitor):
        """Test getting containers with excessive restarts."""
        mock_container = MagicMock()
        mock_container.id = "abc123"
        mock_container.name = "restartey"
        mock_container.attrs = {
            "State": {
                "Status": "running",
                "RestartCount": 10,
                "StartedAt": "2026-01-01T00:00:00Z",
            },
            "Created": "2026-01-01T00:00:00Z",
        }

        monitor.client.containers.list.return_value = [mock_container]

        excessive = monitor.get_containers_with_excessive_restarts(threshold=5)

        assert len(excessive) == 1

    def test_get_aggregated_metrics(self, monitor):
        """Test getting aggregated metrics."""
        mock_container = MagicMock()
        mock_container.id = "abc123"
        mock_container.name = "test"
        mock_container.attrs = {
            "State": {
                "Status": "running",
                "RestartCount": 0,
                "StartedAt": "2026-01-01T00:00:00Z",
            },
            "Created": "2026-01-01T00:00:00Z",
        }

        monitor.client.containers.list.return_value = [mock_container]

        with patch.object(monitor, "get_container_metrics") as mock_metrics:
            mock_metrics.return_value = None
            agg = monitor.get_aggregated_metrics()

            assert agg.total_containers == 1
            assert agg.running_containers == 1

    def test_export_metrics(self, monitor, tmp_path):
        """Test exporting metrics to JSON file."""
        mock_container = MagicMock()
        mock_container.id = "abc123"
        mock_container.name = "test"
        mock_container.attrs = {
            "State": {
                "Status": "running",
                "RestartCount": 0,
                "StartedAt": "2026-01-01T00:00:00Z",
            },
            "Created": "2026-01-01T00:00:00Z",
        }

        monitor.client.containers.list.return_value = [mock_container]

        with patch.object(monitor, "get_container_metrics") as mock_metrics:
            mock_metrics.return_value = None
            output_file = tmp_path / "metrics.json"
            result = monitor.export_metrics(str(output_file))

            assert result is True
            assert output_file.exists()

    def test_calculate_cpu_percent(self):
        """Test CPU percentage calculation."""
        stats = {
            "cpu_stats": {
                "cpu_usage": {"total_usage": 1000000},
                "system_cpu_usage": 10000000,
                "cpus": [0, 1],
            },
            "precpu_stats": {
                "cpu_usage": {"total_usage": 900000},
                "system_cpu_usage": 9000000,
            },
        }

        cpu_percent = DockerHealthMonitor._calculate_cpu_percent(stats)
        assert cpu_percent > 0
        assert isinstance(cpu_percent, float)

    def test_calculate_cpu_percent_zero_delta(self):
        """Test CPU calculation with zero delta."""
        stats = {
            "cpu_stats": {
                "cpu_usage": {"total_usage": 1000000},
                "system_cpu_usage": 1000000,
            },
            "precpu_stats": {
                "cpu_usage": {"total_usage": 1000000},
                "system_cpu_usage": 1000000,
            },
        }

        cpu_percent = DockerHealthMonitor._calculate_cpu_percent(stats)
        assert cpu_percent == 0.0
