FROM hermes-agent-base:latest

WORKDIR /app
# Build with the repository root as context:
# docker build -f Dockerfile ../..
COPY pyproject.toml README.md /app/
COPY shared /app/shared
RUN uv pip install --system -e .

COPY agents/doba-shopify-agent /app/agents/doba-shopify-agent
WORKDIR /app/agents/doba-shopify-agent

CMD ["python", "main.py"]
