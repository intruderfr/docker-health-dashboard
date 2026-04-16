"""Data models for Docker Health Dashboard."""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any
import json


@dataclass
class ContainerMetrics:
    """Container resource metrics."""

    cpu_percent: float
    memory_usage: int
    memory_limit: int
    memory_percent: float
    net_input: int
    net_output: int
    block_input: int
    block_output: int
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class ContainerHealth:
    """Container health status information."""

    container_id: str
    container_name: str
    state: str
    status: str
    health_status: Optional[str]
    restart_count: int
    uptime_seconds: int
    created_at: datetime
    started_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["started_at"] = self.started_at.isoformat()
        return data

    def is_unhealthy(self) -> bool:
        """Check if container is unhealthy."""
        if self.state != "running":
            return True
        if self.health_status and self.health_status not in ("healthy", "none"):
            return True
        return False

    def has_excessive_restarts(self, threshold: int = 5) -> bool:
        """Check if container has excessive restarts."""
        return self.restart_count >= threshold

    def get_health_indicator(self) -> str:
        """Get health indicator emoji/status."""
        if self.state != "running":
            return "STOPPED"
        if self.health_status == "unhealthy":
            return "UNHEALTHY"
        if self.health_status == "starting":
            return "STARTING"
        if self.health_status == "healthy":
            return "HEALTHY"
        return "RUNNING"


@dataclass
class AggregatedMetrics:
    """System-wide aggregated metrics."""

    total_containers: int
    running_containers: int
    stopped_containers: int
    total_memory_usage: int
    total_memory_limit: int
    total_cpu_percent: float
    unhealthy_containers: int
    containers_with_excessive_restarts: int
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


class MetricsEncoder(json.JSONEncoder):
    """JSON encoder for metrics objects."""

    def default(self, obj: Any) -> Any:
        """Encode objects."""
        if isinstance(obj, (ContainerMetrics, ContainerHealth, AggregatedMetrics)):
            return obj.to_dict()
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)
