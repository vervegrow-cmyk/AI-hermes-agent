FROM mcr.microsoft.com/playwright/python:v1.53.0-noble AS hermes-agent-base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ffmpeg git ca-certificates gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g pnpm \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv /usr/local/bin/uv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md /app/
COPY shared /app/shared
RUN uv pip install --system -e .

FROM hermes-agent-base AS trend-agent
COPY . /app
RUN uv pip install --system -e .
CMD ["python", "agents/trend-agent/main.py"]

FROM hermes-agent-base AS content-agent
COPY . /app
RUN uv pip install --system -e .
CMD ["python", "agents/content-agent/main.py"]

FROM hermes-agent-base AS shopify-agent
COPY . /app
RUN uv pip install --system -e .
CMD ["python", "agents/shopify-agent/main.py"]

FROM hermes-agent-base AS analytics-agent
COPY . /app
RUN uv pip install --system -e .
CMD ["python", "agents/analytics-agent/main.py"]

FROM hermes-agent-base AS hermes-trendforge-agent
COPY . /app
RUN uv pip install --system -e .
CMD ["python", "agents/hermes-trendforge-agent/main.py"]

FROM hermes-agent-base AS shopify-inventory-agent
COPY . /app
RUN uv pip install --system -e .
CMD ["python", "agents/shopify-库存-agent/main.py"]
FROM hermes-agent-base AS shopify-category-agent
COPY . /app
RUN uv pip install --system -e .
CMD ["python", "agents/shopify-类别-agent/main.py"]
