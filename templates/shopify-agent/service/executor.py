from shared.schemas import ExecuteRequest


def execute_task(request: ExecuteRequest) -> dict:
    return {
        "store": request.payload.get("store", "your-shop"),
        "task": request.task,
        "note": "Add Shopify API calls and shared database persistence here.",
    }

