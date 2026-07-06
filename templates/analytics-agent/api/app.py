import os

from shared.agent_runtime import create_agent_app
from service.executor import execute_task

app = create_agent_app(
    agent_name=os.getenv("AGENT_NAME", "analytics-agent-template"),
    description="Starter template for analytics and reporting agents.",
    executor=execute_task,
)

