from shared.schemas import ExecuteRequest

from service.content_service import generate_content


def execute_task(request: ExecuteRequest) -> dict:
    return generate_content(
        channel=request.payload.get("channel", "tiktok"),
        topic=request.payload.get("topic", request.task),
        tone=request.payload.get("tone", "engaging"),
    )
