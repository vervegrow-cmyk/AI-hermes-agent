import os

import bootstrap
from shared.agent_runtime import create_agent_app
from service.executor import execute_task

bootstrap.load_shared_environment()

app = create_agent_app(
    agent_name=os.getenv("AGENT_NAME", "shopify-geo-optimization-agent"),
    description=(
        "Optimizes Shopify product data for GEO, AI search understanding, "
        "citation, recommendation, and agentic storefront readiness."
    ),
    executor=execute_task,
    capabilities=[
        "product-geo-audit",
        "agentic-storefront-readiness",
        "deepseek-product-rewrite",
        "shopify-catalog-readiness",
    ],
)
