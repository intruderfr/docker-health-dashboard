"""Core Docker Health Monitoring."""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import json
import logging

import docker
from docker.models.containers import Container
from docker.errors import DockerException

from docker_health_dashboard.models import (
    ContainerHealth,
    ContainerMetrics,
    AggregatedMetrics,
)


logger = logging.getLogger(__name__)


class DockerHealthMonitor:
    """Monitor Docker container health and resource usage."""

    def __init__(self, socket_url: Optional[str] = None):
        """
        Initialize Docker Health Monitor.

        Args:
            socket_url: Optional Docker socket URL. Uses default if not provided.

        Raises:
            DockerException: If unable to connect to Docker daemon.
        """
        try:
            if socket_url:
                self.client = docker.DockerClient(base_url=socket_url)
            else:
                self.client = docker.from_env()
            # Verify connection
            self.client.ping()
            logger.info("Successfully connected to Docker daemon")
        except DockerException as e:
            logger.error(f"Failed to connect to Docker daemon: {e}")
            raise

        self.metrics_history: Dict[str, List[ContainerMetrics]] = {}

    def get_all_containers(
        self, include_stopped: bool = True
    ) -> List[ContainerHealth]:
        """
        Get health status of all containers.

        Args:
            include_stopped: Whether to include stopped containers.

        Returns:
            List of ContainerHealth objects.
        """
        try:
            containers = self.client.containers.list(all=include_stopped)
            health_list = []

            for container in containers:
                health = self._get_container_health(container)
                health_list.append(health)

            return health_list
        except DockerException as e:
            logger.error(f"Failed to get containers: {e}")
            return []

    def get_container_health(self, container_id: str) -> Optional[ContainerHealth]:
        """
        Get health status of a specific container.

        Args:
            container_id: Container ID or name.

        Returns:
            ContainerHealth object or None if not found.
        """
        try:
            container = self.client.containers.get(container_id)
            return self._get_container_health(container)
        except docker.errors.NotFound:
            logger.warning(f"Container not found: {container_id}")
            return None
        except DockerException as e:
            logger.error(f"Failed to get container health: {e}")
            return None

    def get_container_metrics(self, container_id: str) -> Optional[ContainerMetrics]:
        """
        Get resource metrics for a specific container.

        Args:
            container_id: Container ID or name.

        Returns:
            ContainerMetrics object or None if not found.
        """
        try:
            container = self.client.containers.get(container_id)
            return self._get_container_metrics(container)
        except docker.errors.NotFound:
            logger.warning(f"Container not found: {container_id}")
            return None
        except DockerException as e:
            logger.error(f"Failed to get container metrics: {e}")
            return None

    def get_unhealthy_containers(self) -> List[ContainerHealth]:
        """
        Get list of unhealthy containers.

        Returns:
            List of unhealthy ContainerHealth objects.
        """
        all_containers = self.get_all_containers()
        return [c for c in all_containers if c.is_unhealthy()]

    def get_containers_with_excessive_restarts(
        self, threshold: int = 5
    ) -> List[ContainerHealth]:
        """
        Get containers with excessive restart counts.

        Args:
            threshold: Restart count threshold.

        Returns:
            List of ContainerHealth objects with excessive restarts.
        """
        all_containers = self.get_all_containers()
        return [c for c in all_containers if c.has_excessive_restarts(threshold)]

    def get_aggregated_metrics(self) -> AggregatedMetrics:
        """
        Get system-wide aggregated metrics.

        Returns:
            AggregatedMetrics object.
        """
        containers = self.get_all_containers()

        running = [c for c in containers if c.state == "running"]
        stopped = [c for c in containers if c.state != "running"]

        total_memory_usage = 0
        total_memory_limit = 0
        total_cpu = 0

        for container_id in [c.container_id for c in running]:
            try:
                metrics = self.get_container_metrics(container_id)
                if metrics:
                    total_memory_usage += metrics.memory_usage
                    total_memory_limit += metrics.memory_limit
                    total_cpu += metrics.cpu_percent
            except Exception as e:
                logger.warning(f"Failed to get metrics for {container_id}: {e}")

        unhealthy = [c for c in containers if c.is_unhealthy()]
        excessive_restarts = [
            c for c in containers if c.has_excessive_restarts()
        ]

        return AggregatedMetrics(
            total_containers=len(containers),
            running_containers=len(running),
            stopped_containers=len(stopped),
            total_memory_usage=total_memory_usage,
            total_memory_limit=total_memory_limit,
            total_cpu_percent=total_cpu,
            unhealthy_containers=len(unhealthy),
            containers_with_excessive_restarts=len(excessive_restarts),
            timestamp=datetime.utcnow(),
        )

    def export_metrics(self, filepath: str) -> bool:
        """
        Export all metrics to JSON file.

        Args:
            filepath: Path to save metrics file.

        Returns:
            True if successful, False otherwise.
        """
        try:
            containers = self.get_all_containers()
            aggregated = self.get_aggregated_metrics()

            data = {
                "timestamp": datetime.utcnow().isoformat(),
                "aggregated": aggregated.to_dict(),
                "containers": [c.to_dict() for c in containers],
            }

            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Metrics exported to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
            return False

    def _get_container_health(self, container: Container) -> ContainerHealth:
        """Extract health information from container."""
        stats = container.attrs
        state = stats.get("State", {})

        created = datetime.fromisoformat(
            stats.get("Created", "").replace("Z", "+00:00")
        )
        started = datetime.fromisoformat(
            state.get("StartedAt", "").replace("Z", "+00:00")
        )

        now = datetime.utcnow()
        uptime = (
            int((now - started.replace(tzinfo=None)).total_seconds())
            if started.tzinfo is None
            else int((now - started).total_seconds())
        )

        health_status = None
        if "Health" in stats:
            health_status = stats["Health"].get("Status", "none")

        return ContainerHealth(
            container_id=container.id,
            container_name=container.name,
            state=state.get("Status", "unknown"),
            status=stats.get("State", {}).get("Status", "unknown"),
            health_status=health_status,
            restart_count=state.get("RestartCount", 0),
            uptime_seconds=uptime,
            created_at=created,
            started_at=started,
        )

    def _get_container_metrics(self, container: Container) -> ContainerMetrics:
        """Extract metrics from container."""
        stats = container.stats(stream=False)

        cpu_percent = self._calculate_cpu_percent(stats)
        memory = stats.get("memory_stats", {})
        memory_usage = memory.get("usage", 0)
        memory_limit = memory.get("limit", 0)
        memory_percent = (
            (memory_usage / memory_limit * 100) if memory_limit > 0 else 0
        )

        networks = stats.get("networks", {})
        net_input = sum(
            n.get("rx_bytes", 0) for n in networks.values()
        )
        net_output = sum(
            n.get("tx_bytes", 0) for n in networks.values()
        )

        block_io = stats.get("blkio_stats", {})
        io_service_bytes = block_io.get("io_service_bytes_recursive", [])
        block_input = sum(
            io.get("value", 0) for io in io_service_bytes if io.get("op") == "Read"
        )
        block_output = sum(
            io.get("value", 0) for io in io_service_bytes if io.get("op") == "Write"
        )

        return ContainerMetrics(
            cpu_percent=cpu_percent,
            memory_usage=memory_usage,
            memory_limit=memory_limit,
            memory_percent=memory_percent,
            net_input=net_input,
            net_output=net_output,
            block_input=block_input,
            block_output=block_output,
            timestamp=datetime.utcnow(),
        )

    @staticmethod
    def _calculate_cpu_percent(stats: Dict[str, Any]) -> float:
        """Calculate CPU percentage from stats."""
        cpu_stats = stats.get("cpu_stats", {})
        precpu_stats = stats.get("precpu_stats", {})

        cpu_delta = (
            cpu_stats.get("cpu_usage", {}).get("total_usage", 0)
            - precpu_stats.get("cpu_usage", {}).get("total_usage", 0)
        )
        system_delta = (
            cpu_stats.get("system_cpu_usage", 0)
            - precpu_stats.get("system_cpu_usage", 0)
        )
        cpu_count = len(cpu_stats.get("cpus", []))

        if system_delta == 0:
            return 0.0

        cpu_percent = (cpu_delta / system_delta) * cpu_count * 100.0
        return round(cpu_percent, 2)
