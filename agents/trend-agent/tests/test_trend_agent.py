import importlib.util
import sys
from pathlib import Path

from fastapi.testclient import TestClient

AGENT_ROOT = Path(__file__).resolve().parents[1]
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

for module_name in ["api", "api.app", "service", "service.executor", "service.trend_service"]:
    sys.modules.pop(module_name, None)

spec = importlib.util.spec_from_file_location("trend_agent_app", AGENT_ROOT / "api" / "app.py")
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
app = module.app


client = TestClient(app)


def test_trend_discover():
    response = client.post("/discover", json={"niche": "kitchen gadgets"})
    assert response.status_code == 200
    body = response.json()
    assert body["opportunity_score"] >= 0
    assert body["keyword"]
