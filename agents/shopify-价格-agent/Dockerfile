FROM hermes-agent-base:latest

WORKDIR /app
COPY . /app
RUN uv pip install --system -e .

CMD ["python", "agents/shopify-价格-agent/main.py"]
