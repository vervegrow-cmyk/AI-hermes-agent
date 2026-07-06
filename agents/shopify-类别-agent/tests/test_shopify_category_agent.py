import importlib.util
import importlib
import sys
from pathlib import Path

from fastapi.testclient import TestClient

AGENT_ROOT = Path(__file__).resolve().parents[1]
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

for module_name in ["api", "api.app", "service", "service.executor"]:
    sys.modules.pop(module_name, None)

spec = importlib.util.spec_from_file_location("shopify_category_agent_app", AGENT_ROOT / "api" / "app.py")
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
app = module.app

client = TestClient(app)


def test_shopify_category_execute():
    class _FakeService:
        def run(self, command, *, task=""):
            return {
                "summary": "fake-category-run",
                "data": {
                    "task": task,
                    "store": command.store_name or "demo-shop.myshopify.com",
                    "mode": command.mode,
                    "product_query": command.product_query,
                    "processed_count": 1,
                    "items": [],
                    },
                }

    importlib.import_module("service.executor").get_category_optimization_service = lambda: _FakeService()
    response = client.post(
        "/execute",
        json={
            "task": "categorize-products",
            "payload": {
                "store": "demo-shop.myshopify.com",
                "mode": "dry-run",
                "product_query": "vendor:Dekuch",
            },
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["store"] == "demo-shop.myshopify.com"
    assert body["data"]["product_query"] == "vendor:Dekuch"
    assert body["data"]["processed_count"] == 1
