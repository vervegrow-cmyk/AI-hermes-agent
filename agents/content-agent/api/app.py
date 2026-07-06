from fastapi import APIRouter
from pydantic import BaseModel

from service.content_service import generate_content
from service.executor import execute_task
from shared.agent_runtime import create_agent_app
from shared.registry import registry

_definition = registry.get_agent("content-agent") or {}

app = create_agent_app(
    agent_name="content-agent",
    description="Content generation agent for short-form and commerce content.",
    executor=execute_task,
    capabilities=_definition.get("capabilities", []),
)

router = APIRouter()


class ContentGenerateRequest(BaseModel):
    channel: str
    topic: str
    tone: str = "engaging"


@router.post("/generate")
def generate(request: ContentGenerateRequest) -> dict:
    return generate_content(channel=request.channel, topic=request.topic, tone=request.tone)


app.include_router(router)
