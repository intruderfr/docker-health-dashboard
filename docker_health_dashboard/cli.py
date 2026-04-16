"""Command-line interface for Docker Health Dashboard."""

import sys
import json
import time
import logging
from typing import Optional

import click
from tabulate import tabulate

from docker_health_dashboard.monitor import DockerHealthMonitor


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def get_monitor(socket_url: Optional[str] = None) -> Optional[DockerHealthMonitor]:
    """Get DockerHealthMonitor instance with error handling."""
    try:
        return DockerHealthMonitor(socket_url=socket_url)
    except Exception as e:
        click.echo(f"Error: Failed to connect to Docker daemon: {e}", err=True)
        sys.exit(1)


@click.group()
@click.option(
    "--socket",
    default=None,
    help="Docker socket URL (default: unix:///var/run/docker.sock)",
)
@click.pass_context
def cli(ctx: click.Context, socket: Optional[str]) -> None:
    """Docker Health Dashboard - Monitor container health and resource usage."""
    ctx.ensure_object(dict)
    ctx.obj["socket"] = socket


@cli.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show quick health summary of all containers."""
    monitor = get_monitor(ctx.obj.get("socket"))
    if not monitor:
        return

    containers = monitor.get_all_containers()
    aggregated = monitor.get_aggregated_metrics()

    click.echo("\n" + click.style("Docker Health Summary", bold=True, fg="cyan"))
    click.echo("=" * 60)

    stats_data = [
        ["Total Containers", aggregated.total_containers],
        ["Running", aggregated.running_containers],
        ["Stopped", aggregated.stopped_containers],
        ["Unhealthy", aggregated.unhealthy_containers],
        ["Excessive Restarts", aggregated.containers_with_excessive_restarts],
    ]
    click.echo(tabulate(stats_data, headers=["Metric", "Count"], tablefmt="grid"))

    mem_gb = aggregated.total_memory_usage / (1024 ** 3)
    limit_gb = aggregated.total_memory_limit / (1024 ** 3)
    click.echo("\n" + click.style("Resource Usage", bold=True, fg="cyan"))
    click.echo("=" * 60)
    resource_data = [
        ["Total Memory", f"{mem_gb:.2f} GB / {limit_gb:.2f} GB"],
        ["Total CPU", f"{aggregated.total_cpu_percent:.1f}%"],
    ]
    click.echo(tabulate(resource_data, headers=["Resource", "Usage"], tablefmt="grid"))

    click.echo("\n" + click.style("Container Status", bold=True, fg="cyan"))
    click.echo("=" * 60)

    container_data = []
    for c in sorted(containers, key=lambda x: x.container_name):
        status = click.style(c.get_health_indicator(), fg="green" if c.state == "running" else "red")
        container_data.append([c.container_name[:20], status, c.restart_count, f"{c.uptime_seconds // 3600}h"])

    click.echo(tabulate(container_data, headers=["Container", "Health", "Restarts", "Uptime"], tablefmt="grid"))
    click.echo()


@cli.command()
@click.option("--interval", default=5, help="Refresh interval in seconds")
@click.option("--duration", default=None, help="Duration to monitor in seconds")
@click.pass_context
def monitor(ctx: click.Context, interval: int, duration: Optional[int]) -> None:
    """Monitor container health with auto-refresh."""
    monitor_obj = get_monitor(ctx.obj.get("socket"))
    if not monitor_obj:
        return
    elapsed = 0
    try:
        while True:
            if duration and elapsed >= duration:
                break
            click.clear()
            click.echo(click.style(f"Docker Health Monitor (Refresh: {interval}s) - {time.strftime('%Y-%m-%d %H:%M:%S')}", bold=True, fg="cyan"))
            click.echo("=" * 80)
            containers = monitor_obj.get_all_containers()
            aggregated = monitor_obj.get_aggregated_metrics()
            click.echo(f"Containers: {aggregated.running_containers} running, {aggregated.stopped_containers} stopped | Memory: {aggregated.total_memory_usage / (1024**3):.2f}GB | Unhealthy: {aggregated.unhealthy_containers}")
            click.echo("-" * 80)
            for c in sorted(containers, key=lambda x: x.container_name):
                if c.state == "running":
                    try:
                        metrics = monitor_obj.get_container_metrics(c.container_id)
                        if metrics:
                            status_color = "green" if c.health_status != "unhealthy" else "red"
                            click.echo(f"{click.style(c.container_name, fg=status_color):<30} CPU: {metrics.cpu_percent:>6.2f}% | Mem: {metrics.memory_percent:>5.1f}% | Restarts: {c.restart_count:>3} | Up: {c.uptime_seconds // 3600}h")
                    except Exception as e:
                        logger.error(f"Error getting metrics for {c.container_name}: {e}")
                else:
                    click.echo(f"{click.style(c.container_name, fg='red'):<30} Status: {c.state}")
            click.echo("\n" + click.style("Press Ctrl+C to stop", dim=True))
            time.sleep(interval)
            elapsed += interval
    except KeyboardInterrupt:
        click.echo("\nMonitoring stopped.")


@cli.command()
@click.argument("container_id")
@click.pass_context
def inspect(ctx: click.Context, container_id: str) -> None:
    """View detailed health report for a specific container."""
    monitor_obj = get_monitor(ctx.obj.get("socket"))
    if not monitor_obj:
        return
    health = monitor_obj.get_container_health(container_id)
    if not health:
        click.echo(f"Error: Container '{container_id}' not found", err=True)
        sys.exit(1)
    metrics = monitor_obj.get_container_metrics(container_id)
    click.echo("\n" + click.style(f"Container: {health.container_name}", bold=True, fg="cyan"))
    click.echo("=" * 60)
    health_data = [
        ["Container ID", health.container_id[:12] + "..."],
        ["Status", health.state.upper()],
        ["Health Check", health.health_status or "N/A"],
        ["Restart Count", health.restart_count],
        ["Uptime", f"{health.uptime_seconds // 3600}h {(health.uptime_seconds % 3600) // 60}m"],
        ["Created", health.created_at.strftime("%Y-%m-%d %H:%M:%S")],
        ["Started", health.started_at.strftime("%Y-%m-%d %H:%M:%S")],
    ]
    click.echo(tabulate(health_data, tablefmt="grid"))
    if metrics:
        click.echo("\n" + click.style("Resource Metrics", bold=True, fg="cyan"))
        click.echo("=" * 60)
        metrics_data = [
            ["CPU Usage", f"{metrics.cpu_percent:.2f}%"],
            ["Memory Usage", f"{metrics.memory_usage / (1024**2):.2f} MB"],
            ["Memory Limit", f"{metrics.memory_limit / (1024**2):.2f} MB"],
            ["Memory %", f"{metrics.memory_percent:.2f}%"],
            ["Network In", f"{metrics.net_input / (1024**2):.2f} MB"],
            ["Network Out", f"{metrics.net_output / (1024**2):.2f} MB"],
            ["Block In", f"{metrics.block_input / (1024**2):.2f} MB"],
            ["Block Out", f"{metrics.block_output / (1024**2):.2f} MB"],
        ]
        click.echo(tabulate(metrics_data, tablefmt="grid"))
    click.echo()


@cli.command()
@click.option("--output", "-o", default="metrics.json", help="Output file path")
@click.pass_context
def export(ctx: click.Context, output: str) -> None:
    """Export all metrics to JSON file."""
    monitor_obj = get_monitor(ctx.obj.get("socket"))
    if not monitor_obj:
        return
    if monitor_obj.export_metrics(output):
        click.echo(click.style(f"Metrics exported to {output}", fg="green"))
    else:
        click.echo(f"Error: Failed to export metrics to {output}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def health(ctx: click.Context) -> None:
    """Check overall system health status."""
    monitor_obj = get_monitor(ctx.obj.get("socket"))
    if not monitor_obj:
        return
    aggregated = monitor_obj.get_aggregated_metrics()
    health_score = 100
    issues = []
    if aggregated.unhealthy_containers > 0:
        health_score -= 20
        issues.append(f"{aggregated.unhealthy_containers} unhealthy containers")
    if aggregated.containers_with_excessive_restarts > 0:
        health_score -= 15
        issues.append(f"{aggregated.containers_with_excessive_restarts} containers with excessive restarts")
    if aggregated.total_memory_limit > 0:
        memory_percent = aggregated.total_memory_usage / aggregated.total_memory_limit * 100
        if memory_percent > 90:
            health_score -= 10
            issues.append(f"High memory usage: {memory_percent:.1f}%")
        elif memory_percent > 80:
            health_score -= 5
            issues.append(f"Elevated memory usage: {memory_percent:.1f}%")
    if aggregated.stopped_containers > 0:
        issues.append(f"{aggregated.stopped_containers} stopped containers")
    if health_score >= 80:
        status_color = "green"
        status_text = "HEALTHY"
    elif health_score >= 60:
        status_color = "yellow"
        status_text = "DEGRADED"
    else:
        status_color = "red"
        status_text = "UNHEALTHY"
    click.echo("\n" + click.style("System Health Report", bold=True, fg="cyan"))
    click.echo("=" * 60)
    click.echo(f"Overall Status: {click.style(status_text, bold=True, fg=status_color)}")
    click.echo(f"Health Score: {health_score}/100")
    click.echo(f"Timestamp: {aggregated.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    if issues:
        click.echo("\nIssues Found:")
        for issue in issues:
            click.echo(f"  - {issue}")
    else:
        click.echo("\nNo issues detected!")
    click.echo()


def main() -> None:
    """Entry point for CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()
