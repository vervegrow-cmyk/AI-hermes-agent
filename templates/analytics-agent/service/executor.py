from shared.schemas import ExecuteRequest


def execute_task(request: ExecuteRequest) -> dict:
    return {
        "metric": request.payload.get("metric", "revenue"),
        "task": request.task,
        "insight": "Replace this placeholder with BI logic and warehouse queries.",
    }

