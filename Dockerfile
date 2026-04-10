# ─────────────────────────────────────────────────────────────
# test-pyramid-analyzer GitHub Action — Docker image
# ─────────────────────────────────────────────────────────────
FROM python:3.11-slim

LABEL org.opencontainers.image.title="test-pyramid-analyzer"
LABEL org.opencontainers.image.description="Analyze test pyramid distribution and detect anti-patterns"
LABEL org.opencontainers.image.source="https://github.com/ABNclearroute/test-pyaramid-analyzer"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Install Python dependencies first (maximise layer cache re-use)
COPY pyproject.toml ./
RUN pip install --no-cache-dir \
        typer \
        "typer[all]" \
        pyyaml \
        rich \
        jinja2 \
        requests

# Copy the package source and install it
COPY src/ src/
RUN pip install --no-cache-dir --no-deps -e .

# Copy the action entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
