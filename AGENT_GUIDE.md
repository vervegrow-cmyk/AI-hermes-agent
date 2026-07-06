# AGENT_GUIDE

This repository is the central workspace for all Hermes agents. Use this guide to keep every agent aligned to one architecture.

## Golden rules

- Build all new agents inside `agents/`
- Reuse shared modules from `shared/`
- Do not create agent-specific databases
- Do not modify code inside `external/` directly
- Keep every agent Dockerized using the shared base image
- Expose `GET /health` and `POST /execute` on every FastAPI agent

## Standard agent layout

```text
agent-name/
├── api/
├── service/
├── workflow/
├── models/
├── tests/
├── Dockerfile
└── main.py
```

## Shared imports

```python
from shared.config import get_settings
from shared.logger import get_logger
from shared.llm import get_llm
from shared.cache import get_redis_client
from shared.database import get_db_session
from shared.vectorstore import get_qdrant_client
```

## Required endpoints

- `GET /health`: container and runtime health check
- `POST /execute`: generic task execution endpoint

Optional endpoints can be added per agent, such as:

- `POST /discover`
- `POST /discover-insights`
- `POST /generate`
- `POST /sync`
- `POST /analyze`

## LLM usage

Use the unified entry point:

```python
from shared.llm import get_llm

llm = get_llm(provider="openai", model="gpt-4.1-mini")
result = llm.generate("Summarize these product reviews.")
```

DeepSeek is also available through the same interface:

```python
llm = get_llm(provider="deepseek", model="deepseek-chat")
result = llm.generate("Score the risk of this product listing.")
```

## Shared storage policy

- Postgres: metadata, structured records, task history
- Redis: cache, short-lived state, queue coordination
- Qdrant: embeddings, semantic search, retrieval memory

## New agent checklist

1. Copy a template from `templates/`
2. Rename the package and startup port
3. Implement business logic in `service/`
4. Add tests
5. Register the agent in `shared/registry`
6. Add its Compose service
7. Document any new external dependencies
