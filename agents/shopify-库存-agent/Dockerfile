FROM hermes-agent-base:latest

WORKDIR /app
COPY . /app
RUN uv pip install --system -e .

CMD ["python", "agents/shopify-库存-agent/main.py"]
