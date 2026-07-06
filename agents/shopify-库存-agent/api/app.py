from service.executor import execute_task
from shared.agent_runtime import create_agent_app
from shared.registry import registry

_definition = registry.get_agent("shopify-inventory-agent") or {}

app = create_agent_app(
    agent_name="shopify-inventory-agent",
    description="Sync Shopify inventory from Giga OpenAPI by SKU with sequential progress output.",
    executor=execute_task,
    capabilities=_definition.get("capabilities", []),
)
