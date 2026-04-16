"""Tests for data models."""

import pytest
from datetime import datetime

from docker_health_dashboard.models import (
    ContainerHealth,
    ContainerMetrics,
    AggregatedMetrics,
)


class TestContainerHealth:
    """Test ContainerHealth model."""

    def test_container_health_creation(self):
        """Test creating a ContainerHealth instance."""
        now = datetime.utcnow()
        health = ContainerHealth(
            container_id="abc123",
            container_name="test-container",
            state="running",
            status="Up 2 hours",
            health_status="healthy",
            restart_count=0,
            uptime_seconds=7200,
            created_at=now,
            started_at=now,
        )

        assert health.container_id == "abc123"
        assert health.container_name == "test-container"
        assert health.state == "running"
        assert health.is_unhealthy() is False

    def test_is_unhealthy_stopped(self):
        """Test that stopped containers are unhealthy."""
        now = datetime.utcnow()
        health = ContainerHealth(
            container_id="abc123",
            container_name="test",
            state="exited",
            status="Exited",
            health_status=None,
            restart_count=0,
            uptime_seconds=0,
            created_at=now,
            started_at=now,
        )

        assert health.is_unhealthy() is True

    def test_is_unhealthy_status(self):
        """Test unhealthy status detection."""
        now = datetime.utcnow()
        health = ContainerHealth(
            container_id="abc123",
            container_name="test",
            state="running",
            status="Up",
            health_status="unhealthy",
            restart_count=0,
            uptime_seconds=3600,
            created_at=now,
            started_at=now,
        )

        assert health.is_unhealthy() is True

    def test_has_excessive_restarts(self):
        """Test excessive restart detection."""
        now = datetime.utcnow()
        health = ContainerHealth(
            container_id="abc123",
            container_name="test",
            state="running",
            status="Up",
            health_status="healthy",
            restart_count=10,
            uptime_seconds=3600,
            created_at=now,
            started_at=now,
        )

        assert health.has_excessive_restarts(5) is True
        assert health.has_excessive_restarts(15) is False

    def test_get_health_indicator(self):
        """Test health indicator generation."""
        now = datetime.utcnow()

        # Running and healthy
        health = ContainerHealth(
            container_id="abc123",
            container_name="test",
            state="running",
            status="Up",
            health_status="healthy",
            restart_count=0,
            uptime_seconds=3600,
            created_at=now,
            started_at=now,
        )
        assert health.get_health_indicator() == "HEALTHY"

        # Running but unhealthy
        health.health_status = "unhealthy"
        assert health.get_health_indicator() == "UNHEALTHY"

        # Stopped
        health.state = "exited"
        assert health.get_health_indicator() == "STOPPED"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        now = datetime.utcnow()
        health = ContainerHealth(
            container_id="abc123",
            container_name="test",
            state="running",
            status="Up",
            health_status="healthy",
            restart_count=0,
            uptime_seconds=3600,
            created_at=now,
            started_at=now,
        )

        data = health.to_dict()
        assert isinstance(data, dict)
        assert data["container_id"] == "abc123"
        assert data["container_name"] == "test"
        assert isinstance(data["created_at"], str)


class TestContainerMetrics:
    """Test ContainerMetrics model."""

    def test_container_metrics_creation(self):
        """Test creating a ContainerMetrics instance."""
        now = datetime.utcnow()
        metrics = ContainerMetrics(
            cpu_percent=12.5,
            memory_usage=512 * 1024 * 1024,
            memory_limit=1024 * 1024 * 1024,
            memory_percent=50.0,
            net_input=1024 * 1024,
            net_output=2048 * 1024,
            block_input=512 * 1024,
            block_output=256 * 1024,
            timestamp=now,
        )

        assert metrics.cpu_percent == 12.5
        assert metrics.memory_percent == 50.0
        assert metrics.net_input == 1024 * 1024

    def test_to_dict(self):
        """Test conversion to dictionary."""
        now = datetime.utcnow()
        metrics = ContainerMetrics(
            cpu_percent=12.5,
            memory_usage=512 * 1024 * 1024,
            memory_limit=1024 * 1024 * 1024,
            memory_percent=50.0,
            net_input=1024 * 1024,
            net_output=2048 * 1024,
            block_input=512 * 1024,
            block_output=256 * 1024,
            timestamp=now,
        )

        data = metrics.to_dict()
        assert isinstance(data, dict)
        assert data["cpu_percent"] == 12.5
        assert data["memory_percent"] == 50.0
        assert isinstance(data["timestamp"], str)


class TestAggregatedMetrics:
    """Test AggregatedMetrics model."""

    def test_aggregated_metrics_creation(self):
        """Test creating an AggregatedMetrics instance."""
        now = datetime.utcnow()
        agg = AggregatedMetrics(
            total_containers=10,
            running_containers=8,
            stopped_containers=2,
            total_memory_usage=4 * 1024 * 1024 * 1024,
            total_memory_limit=8 * 1024 * 1024 * 1024,
            total_cpu_percent=45.0,
            unhealthy_containers=1,
            containers_with_excessive_restarts=1,
            timestamp=now,
        )

        assert agg.total_containers == 10
        assert agg.running_containers == 8
        assert agg.unhealthy_containers == 1

    def test_to_dict(self):
        """Test conversion to dictionary."""
        now = datetime.utcnow()
        agg = AggregatedMetrics(
            total_containers=10,
            running_containers=8,
            stopped_containers=2,
            total_memory_usage=4 * 1024 * 1024 * 1024,
            total_memory_limit=8 * 1024 * 1024 * 1024,
            total_cpu_percent=45.0,
            unhealthy_containers=1,
            containers_with_excessive_restarts=1,
            timestamp=now,
        )

        data = agg.to_dict()
        assert isinstance(data, dict)
        assert data["total_containers"] == 10
        assert isinstance(data["timestamp"], str)
