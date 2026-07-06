# Architecture Overview

The platform uses a monorepo layout so all agents share one development lifecycle:

- shared Python package for config, logging, LLM, storage, and registry
- agent-per-service FastAPI runtime
- shared Compose stack for infra and monitoring
- template-first scaffolding for new agents

