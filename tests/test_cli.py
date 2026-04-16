"""Tests for CLI commands."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
from datetime import datetime

from docker_health_dashboard.cli import cli
from docker_health_dashboard.models import ContainerHealth, ContainerMetrics, AggregatedMetrics


@pytest.fixture
def cli_runner():
    """Create a Click CLI runner."""
    return CliRunner()


@pytest.fixture
def mock_monitor():
    """Create a mock DockerHealthMonitor."""
    with patch("docker_health_dashboard.cli.DockerHealthMonitor") as mock:
        monitor = MagicMock()
        mock.return_value = monitor
        yield mock, monitor


class TestCliStatus(cli_runner):
    """Test CLI status command."""

    def test_status_command(self, cli_runner, mock_monitor):
        """Test status command output."""
        mock_class, mock_instance = mock_monitor

        # Create test data
        now = datetime.utcnow()
        container = ContainerHealth(
            container_id="abc123",
            container_name="test-container",
            state="running",
            status="Up",
            health_status="healthy",
            restart_count=0,
            uptime_seconds=3600,
            created_at=now,
            started_at=now,
        )

        agg = AggregatedMetrics(
            total_containers=1,
            running_containers=1,
            stopped_containers=0,
            total_memory_usage=512 * 1024 * 1024,
            total_memory_limit=1024 * 1024 * 1024,
            total_cpu_percent=10.0,
            unhealthy_containers=0,
            containers_with_excessive_restarts=0,
            timestamp=now,
        )

        mock_instance.get_all_containers.return_value = [container]
        mock_instance.get_aggregated_metrics.return_value = agg

        result = cli_runner.invoke(cli, ["status"])

        assert result.exit_code == 0
        assert "Docker Health Summary" in result.output
        assert "test-container" in result.output

    def test_status_command_with_socket(self, cli_runner, mock_monitor):
        """Test status command with custom socket."""
        mock_class, mock_instance = mock_monitor
        mock_instance.get_all_containers.return_value = []
        mock_instance.get_aggregated_metrics.return_value = MagicMock(
            total_containers=0,
            running_containers=0,
            stopped_containers=0,
            total_memory_usage=0,
            total_memory_limit=0,
            total_cpu_percent=0,
            unhealthy_containers=0,
            containers_with_excessive_restarts=0,
            timestamp=datetime.utcnow(),
        )

        result = cli_runner.invoke(cli, ["--socket", "unix:///custom.sock", "status"])

        assert result.exit_code == 0
        mock_class.assert_called_with(socket_url="unix:///custom.sock")


class TestCliInspect:
    """Test CLI inspect command."""

    def test_inspect_command(self, cli_runner, mock_monitor):
        """Test inspect command."""
        mock_class, mock_instance = mock_monitor

        now = datetime.utcnow()
        health = ContainerHealth(
            container_id="abc123def456",
            container_name="test-container",
            state="running",
            status="Up",
            health_status="healthy",
            restart_count=2,
            uptime_seconds=7200,
            created_at=now,
            started_at=now,
        )

        metrics = ContainerMetrics(
            cpu_percent=15.5,
            memory_usage=512 * 1024 * 1024,
            memory_limit=1024 * 1024 * 1024,
            memory_percent=50.0,
            net_input=1024 * 1024,
            net_output=2048 * 1024,
            block_input=512 * 1024,
            block_output=256 * 1024,
            timestamp=now,
        )

        mock_instance.get_container_health.return_value = health
        mock_instance.get_container_metrics.return_value = metrics

        result = cli_runner.invoke(cli, ["inspect", "test-container"])

        assert result.exit_code == 0
        assert "test-container" in result.output
        assert "Resource Metrics" in result.output

    def test_inspect_command_not_found(self, cli_runner, mock_monitor):
        """Test inspect command with non-existent container."""
        mock_class, mock_instance = mock_monitor
        mock_instance.get_container_health.return_value = None

        result = cli_runner.invoke(cli, ["inspect", "nonexistent"])

        assert result.exit_code != 0


class TestCliExport:
    """Test CLI export command."""

    def test_export_command(self, cli_runner, mock_monitor, tmp_path):
        """Test export command."""
        mock_class, mock_instance = mock_monitor
        mock_instance.export_metrics.return_value = True

        output_file = tmp_path / "metrics.json"
        result = cli_runner.invoke(cli, ["export", "--output", str(output_file)])

        assert result.exit_code == 0
        mock_instance.export_metrics.assert_called_once_with(str(output_file))

    def test_export_command_failure(self, cli_runner, mock_monitor):
        """Test export command failure."""
        mock_class, mock_instance = mock_monitor
        mock_instance.export_metrics.return_value = False

        result = cli_runner.invoke(cli, ["export", "--output", "metrics.json"])

        assert result.exit_code != 0


class TestCliHealth:
    """Test CLI health command."""

    def test_health_command_healthy(self, cli_runner, mock_monitor):
        """Test health command with healthy system."""
        mock_class, mock_instance = mock_monitor

        agg = AggregatedMetrics(
            total_containers=5,
            running_containers=5,
            stopped_containers=0,
            total_memory_usage=2 * 1024 * 1024 * 1024,
            total_memory_limit=8 * 1024 * 1024 * 1024,
            total_cpu_percent=30.0,
            unhealthy_containers=0,
            containers_with_excessive_restarts=0,
            timestamp=datetime.utcnow(),
        )

        mock_instance.get_aggregated_metrics.return_value = agg

        result = cli_runner.invoke(cli, ["health"])

        assert result.exit_code == 0
        assert "System Health Report" in result.output
        assert "HEALTHY" in result.output

    def test_health_command_degraded(self, cli_runner, mock_monitor):
        """Test health command with degraded system."""
        mock_class, mock_instance = mock_monitor

        agg = AggregatedMetrics(
            total_containers=5,
            running_containers=4,
            stopped_containers=1,
            total_memory_usage=7 * 1024 * 1024 * 1024,
            total_memory_limit=8 * 1024 * 1024 * 1024,
            total_cpu_percent=90.0,
            unhealthy_containers=1,
            containers_with_excessive_restarts=0,
            timestamp=datetime.utcnow(),
        )

        mock_instance.get_aggregated_metrics.return_value = agg

        result = cli_runner.invoke(cli, ["health"])

        assert result.exit_code == 0
        assert "System Health Report" in result.output
        assert "Issues Found" in result.output
