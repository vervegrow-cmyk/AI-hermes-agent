FROM hermes-agent-base:latest

WORKDIR /app
# Build with the repository root as context:
# docker build -f Dockerfile ../..
COPY pyproject.toml README.md /app/
COPY shared /app/shared
RUN uv pip install --system -e .

COPY agents/hermes-trendforge-agent /app/agents/hermes-trendforge-agent
WORKDIR /app/agents/hermes-trendforge-agent

CMD ["python", "main.py"]
