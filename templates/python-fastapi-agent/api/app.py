import os

from shared.agent_runtime import create_agent_app
from service.executor import execute_task

app = create_agent_app(
    agent_name=os.getenv("AGENT_NAME", "template-agent"),
    description="Reusable FastAPI template for Hermes agents.",
    executor=execute_task,
)
