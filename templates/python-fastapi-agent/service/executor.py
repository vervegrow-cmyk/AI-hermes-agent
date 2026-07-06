from shared.schemas import ExecuteRequest


def execute_task(request: ExecuteRequest) -> dict:
    return {
        "message": "Replace this executor with real business logic.",
        "task": request.task,
        "payload": request.payload,
    }

