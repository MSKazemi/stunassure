# StunAssure API container — small, non-root, production-oriented.
# The core is dependency-free; this image adds only the optional [api] extra to serve HTTP.
FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install the package (with the API extra) from source.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install ".[api]"

# Run as an unprivileged user.
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

# Container-level liveness check hits the API's own probe.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').status==200 else 1)"

CMD ["uvicorn", "stunassure.api:app", "--host", "0.0.0.0", "--port", "8000"]
