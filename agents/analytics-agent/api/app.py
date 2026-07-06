from service.executor import execute_task
from shared.agent_runtime import create_agent_app
from shared.registry import registry

_definition = registry.get_agent("analytics-agent") or {}

app = create_agent_app(
    agent_name="analytics-agent",
    description="Analytics interpretation and reporting agent.",
    executor=execute_task,
    capabilities=_definition.get("capabilities", []),
)
