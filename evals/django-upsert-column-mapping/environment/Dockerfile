FROM python@sha256:e5c9fa26ffb76e11e0f054f30dc2523a2f9693f0c36c0cf1e39b27e152d899fc

RUN apt-get update && apt-get install -y --no-install-recommends git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash agent \
    && mkdir -p /app /memory /logs/verifier
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app/src:/app/vendor
WORKDIR /app
COPY workspace/ /app/
RUN chown -R agent:agent /app /memory
