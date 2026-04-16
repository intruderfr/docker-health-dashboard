FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy source code
COPY docker_health_dashboard/ ./docker_health_dashboard/

# Create non-root user
RUN useradd -m -u 1000 dashboarduser && chown -R dashboarduser:dashboarduser /app
USER dashboarduser

# Expose port for web dashboard
EXPOSE 8080

# Set entrypoint to web dashboard
ENV FLASK_APP=docker_health_dashboard.web:create_app
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=8080"]
