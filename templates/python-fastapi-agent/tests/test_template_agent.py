import importlib.util
import sys
from pathlib import Path

from fastapi.testclient import TestClient

TEMPLATE_ROOT = Path(__file__).resolve().parents[1]
if str(TEMPLATE_ROOT) not in sys.path:
    sys.path.insert(0, str(TEMPLATE_ROOT))

for module_name in ["api", "api.app", "service", "service.executor"]:
    sys.modules.pop(module_name, None)

spec = importlib.util.spec_from_file_location(
    "template_agent_app",
    TEMPLATE_ROOT / "api" / "app.py",
)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
app = module.app


client = TestClient(app)


def test_template_agent_health():
    response = client.get("/health")
    assert response.status_code == 200
