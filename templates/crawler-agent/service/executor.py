from shared.schemas import ExecuteRequest


def execute_task(request: ExecuteRequest) -> dict:
    return {
        "message": "Add your Crawlee or Playwright workflow here.",
        "seed_url": request.payload.get("seed_url", ""),
        "task": request.task,
    }

