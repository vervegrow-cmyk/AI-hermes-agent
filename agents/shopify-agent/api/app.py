from service.executor import execute_task
from shared.agent_runtime import create_agent_app
from shared.registry import registry

_definition = registry.get_agent("shopify-agent") or {}

app = create_agent_app(
    agent_name="shopify-agent",
    description="Shopify operations and store workflow agent.",
    executor=execute_task,
    capabilities=_definition.get("capabilities", []),
)
