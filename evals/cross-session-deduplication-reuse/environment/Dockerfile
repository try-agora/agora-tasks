FROM python@sha256:e5c9fa26ffb76e11e0f054f30dc2523a2f9693f0c36c0cf1e39b27e152d899fc

RUN apt-get update && apt-get install -y --no-install-recommends git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash agent \
    && mkdir -p /app /memory /logs/verifier \
    && chown -R agent:agent /app /memory
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY workspace/ /opt/task/baseline/
COPY reset.py /opt/task/reset.py
RUN python /opt/task/reset.py
