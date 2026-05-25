FROM python:3.12-slim

# Set environment variables
ENV POETRY_VIRTUALENVS_CREATE=false \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Copy application code (includes pyproject.toml)
COPY . .

# Install Poetry and dependencies
RUN pip install --no-cache-dir poetry && \
    poetry config installer.max-workers 10 && \
    poetry install --no-interaction --no-ansi --only main --no-root && \
    pip uninstall poetry -y

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health', timeout=5).raise_for_status()" || exit 1

CMD ["/bin/sh", "./entrypoint.sh"]

