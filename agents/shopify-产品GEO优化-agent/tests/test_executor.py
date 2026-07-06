import os

import bootstrap
from service.executor import execute_task
from shared.schemas import ExecuteRequest


def test_bootstrap_loads_root_environment():
    bootstrap.load_shared_environment()
    assert os.getenv("REPO_ROOT", "").endswith("AI-hermes-agent")
    assert os.getenv("OPENHANDS_BASE_URL") == "http://127.0.0.1:3002"
    assert bool(os.getenv("DEEPSEEK_API_KEY"))


def test_execute_task_returns_geo_audit_and_environment(monkeypatch):
    monkeypatch.setenv("SHOPIFY_GEO_LLM_PROVIDER", "deepseek")

    request = ExecuteRequest(
        task="audit_product_geo",
        capability="product-geo-audit",
        payload={
            "use_llm": False,
            "product": {
                "title": "UltraSoft Cooling Bed Sheet Set for Hot Sleepers",
                "description": "Breathable microfiber sheet set designed to reduce heat buildup "
                "and improve overnight comfort for warm sleepers.",
                "benefits": [
                    "Cooling feel",
                    "Easy care",
                    "Deep pocket fit",
                ],
                "specifications": {
                    "material": "Microfiber",
                    "fit": "Deep pocket",
                    "sizes": "Twin to King",
                    "care": "Machine washable",
                },
                "faq": [
                    "Will it fit thick mattresses?",
                    "Is it machine washable?",
                    "Does it feel cool overnight?",
                ],
                "brand": "North Loom",
                "category": "Bedding",
                "audience": "Hot sleepers",
                "use_cases": ["Summer bedding", "Guest room refresh"],
            }
        },
    )

    result = execute_task(request)

    assert result["data"]["geo_audit"]["score"] >= 80
    assert result["data"]["agentic_storefront_readiness"]["overall_status"] in {"ready", "partial"}
    assert result["data"]["environment"]["llm_provider"] == "deepseek"
    assert "Shopify Catalog" in result["data"]["environment"]["target_channels"]
