# DEVELOPMENT_GUIDE

## Core development flow

1. Copy `.env.example` to `.env`
2. Install dependencies locally with `pip install -e .`
3. Run `pytest`
4. Start infra with `docker compose up -d postgres redis qdrant`
5. Run one agent locally during active development

Example:

```powershell
python agents/trend-agent/main.py
```

## Shared Docker environment

All agents inherit from the `hermes-agent-base` image so Python, Node, browser automation, and AI SDKs remain consistent.

## Shared database guidance

- Use the shared Postgres instance from `POSTGRES_URL`
- Use separate tables or schemas when needed
- Do not provision a new database per agent

## Shared Qdrant guidance

- Use one Qdrant cluster
- Create separate collections per domain or capability
- Standardize embedding metadata keys so agents can share memory safely

## Shared Redis guidance

- Prefix keys by agent or workflow namespace
- Use Redis for cache, locks, queues, and transient task state

## Hermes Runtime integration path

Future Hermes Runtime support should plug into:

- `shared/registry` for agent discovery
- `shared/config` for environment resolution
- `shared/logger` for centralized observability
- `shared/llm` for provider abstraction

Current shared LLM providers include:

- `openai`
- `deepseek`
- `anthropic`
- `gemini`

## Testing

Run:

```powershell
pytest
```

Add:

- unit tests inside each agent's `tests/`
- integration tests in top-level `tests/`
- smoke tests for Compose services as the platform grows
