from __future__ import annotations

import os
from collections.abc import Callable
from time import perf_counter
from typing import Any

from fastapi import FastAPI

try:
    from prometheus_fastapi_instrumentator import Instrumentator
except ImportError:  # pragma: no cover - optional dependency
    Instrumentator = None

from schemas import ExecuteRequest, ExecuteResponse, HealthResponse


def _prometheus_enabled() -> bool:
    return os.getenv("PROMETHEUS_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}


def _environment() -> str:
    return os.getenv("HERMES_ENV", "development")


def create_agent_app(
    agent_name: str,
    description: str,
    executor: Callable[[ExecuteRequest], dict[str, Any]],
    capabilities: list[str] | None = None,
    version: str = "0.1.0",
) -> FastAPI:
    app = FastAPI(title=agent_name, description=description, version=version)

    if _prometheus_enabled() and Instrumentator is not None:
        Instrumentator().instrument(app).expose(app, include_in_schema=False)

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            agent=agent_name,
            version=version,
            environment=_environment(),
            capabilities=capabilities or [],
        )

    @app.post("/execute", response_model=ExecuteResponse)
    def execute(request: ExecuteRequest) -> ExecuteResponse:
        started = perf_counter()
        result = executor(request)
        result = result if isinstance(result, dict) else {"raw_result": result}
        summary = str(result.get("summary", "") or "")
        data = dict(result.get("data", {})) if isinstance(result.get("data"), dict) else dict(result)
        latency_ms = round((perf_counter() - started) * 1000, 2)
        return ExecuteResponse(
            ok=True,
            agent=agent_name,
            capability=request.capability,
            request_id=request.request_id,
            status="success",
            summary=summary or f"{agent_name} completed task: {request.task}",
            data=data,
            errors=[],
            metrics={"latency_ms": latency_ms, "version": version},
        )

    return app
