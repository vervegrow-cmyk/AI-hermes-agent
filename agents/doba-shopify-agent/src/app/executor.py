from __future__ import annotations

import bootstrap
from shared.schemas import ExecuteRequest
from src.app.runners.registry import RUNNERS


def execute_task(request: ExecuteRequest) -> dict:
    runner = RUNNERS.get(request.task)
    if runner is None:
        return {
            "summary": f"Unsupported task {request.task}",
            "data": {
                "supported_tasks": sorted(RUNNERS),
            },
        }
    return runner(request.payload or {})
