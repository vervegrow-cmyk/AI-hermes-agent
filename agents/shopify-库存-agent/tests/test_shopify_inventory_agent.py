import importlib.util
import sys
from pathlib import Path

from fastapi.testclient import TestClient

AGENT_ROOT = Path(__file__).resolve().parents[1]
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

for module_name in ["api", "api.app", "service", "service.executor"]:
    sys.modules.pop(module_name, None)

spec = importlib.util.spec_from_file_location("shopify_inventory_agent_app", AGENT_ROOT / "api" / "app.py")
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
app = module.app

client = TestClient(app)


def test_shopify_inventory_execute_returns_failed_startup_summary():
    response = client.post(
        "/execute",
        json={"task": "sync-inventory", "payload": {"store_name": "demo-store.myshopify.com", "mode": "dry-run"}},
    )
    assert response.status_code == 200
    assert "库存同步启动失败" in response.json()["summary"]
