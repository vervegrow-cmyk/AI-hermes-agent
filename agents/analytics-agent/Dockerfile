FROM hermes-agent-base:latest

WORKDIR /app
COPY . /app
RUN uv pip install --system -e .

CMD ["python", "agents/analytics-agent/main.py"]

