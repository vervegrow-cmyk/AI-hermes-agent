from shared.schemas import ExecuteRequest

from service.generator import generate_asset


def execute_task(request: ExecuteRequest) -> dict:
    return generate_asset(
        channel=request.payload.get("channel", "tiktok"),
        topic=request.payload.get("topic", request.task),
    )

