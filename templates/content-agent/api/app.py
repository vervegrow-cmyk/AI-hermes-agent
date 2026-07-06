import os

from fastapi import APIRouter
from pydantic import BaseModel

from service.executor import execute_task
from service.generator import generate_asset
from shared.agent_runtime import create_agent_app

app = create_agent_app(
    agent_name=os.getenv("AGENT_NAME", "content-agent-template"),
    description="Starter template for short-form and commerce content agents.",
    executor=execute_task,
)

router = APIRouter()


class GenerateRequest(BaseModel):
    channel: str
    topic: str


@router.post("/generate")
def generate(request: GenerateRequest) -> dict:
    return generate_asset(channel=request.channel, topic=request.topic)


app.include_router(router)

