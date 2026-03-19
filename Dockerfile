FROM python:3.11.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GRAPHES_CONFIG=/app/config.yaml

WORKDIR /app

# Install dependencies first to leverage Docker caching.
COPY pyproject.toml README.md LICENSE /app/
COPY graphes /app/graphes
COPY config.example.yaml /app/config.example.yaml

# Create a safe default config so the CLI imports cleanly.
# Mount a real config at runtime: -v $(pwd)/config.yaml:/app/config.yaml:ro
RUN cp /app/config.example.yaml /app/config.yaml \
    && pip install --no-cache-dir .

ENTRYPOINT ["graphes"]
CMD ["-h"]
