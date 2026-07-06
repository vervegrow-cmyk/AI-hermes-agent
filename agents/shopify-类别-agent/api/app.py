from service.executor import execute_task
from shared.agent_runtime import create_agent_app
from shared.registry import registry

_definition = registry.get_agent("shopify-category-agent") or {}

app = create_agent_app(
    agent_name="shopify-category-agent",
    description="Prepares Shopify category classification workflows on the shared Hermes foundation.",
    executor=execute_task,
    capabilities=_definition.get("capabilities", []),
)
