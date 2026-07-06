# EXTERNAL_PROJECT_GUIDE

Use this guide when bringing GitHub repositories into the Hermes platform.

## Placement rules

Place a project in `agents/` when:

- it is already an executable business workflow service
- it naturally maps to one Hermes agent

Place a project in `shared/` when:

- it provides reusable SDK logic
- it becomes common infrastructure for multiple agents

Place a project in `external/` when:

- it is a third-party upstream dependency
- you want to preserve the original repo without direct edits
- you will wrap or adapt it from Hermes code

Place a project in `infra/` when:

- it manages deployment, observability, networking, or infrastructure services

## Classification checklist

When evaluating a GitHub project, classify it as one of:

- `Agent`
- `Service`
- `Library`
- `Infrastructure`

## Decision model

- `Agent` -> prefer `agents/`
- `Service` -> `external/` plus a wrapper, unless it becomes a first-class Hermes runtime service
- `Library` -> `shared/` if you are internalizing it, otherwise `external/`
- `Infrastructure` -> `infra/`

## Integration rule

Do not directly modify third-party source in `external/`. Instead:

1. keep the upstream repo clean
2. add wrapper code in `agents/` or `shared/`
3. inject config through `.env`
4. route logs to the shared logger
5. persist data to shared Postgres, Redis, and Qdrant

## Wrapper pattern

Typical wrapper choices:

- Python service adapter in `shared/clients/`
- Agent-facing orchestration layer in `agents/<agent>/service/`
- Infrastructure bridge in `infra/`

