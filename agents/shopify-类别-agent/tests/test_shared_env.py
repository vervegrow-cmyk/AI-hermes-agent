from pathlib import Path
import sys

AGENT_ROOT = Path(__file__).resolve().parents[1]
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from service.executor import execute_task
import service.executor as executor_module
from shared.config import get_settings
from shared.config.settings import REPO_ROOT
from shared.schemas import ExecuteRequest


def test_bootstrap_points_to_repo_root():
    repo_root = ensure_repo_root_on_path()
    assert repo_root == REPO_ROOT
    assert (repo_root / ".env").exists()


def test_executor_uses_shared_settings(monkeypatch):
    class _FakeService:
        def run(self, command, *, task=""):
            return {
                "summary": "fake-summary",
                "data": {
                    "task": task,
                    "store": command.store_name or "demo-shop.myshopify.com",
                    "mode": command.mode,
                    "processed_count": 0,
                    "items": [],
                },
            }

    get_settings.cache_clear()
    monkeypatch.setenv("HERMES_ENV", "test")
    monkeypatch.setenv("SHOPIFY_SHOP", "demo-shop.myshopify.com")
    monkeypatch.setenv("SHOPIFY_API_VERSION", "2026-01")
    monkeypatch.setattr(executor_module, "get_category_optimization_service", lambda: _FakeService())

    result = execute_task(
        ExecuteRequest(
            task="category-check",
            payload={"mode": "dry-run", "candidate_category": "Home & Garden > Patio"},
        )
    )

    assert result["data"]["environment"] == "test"
    assert result["data"]["store"] == "demo-shop.myshopify.com"
    assert result["data"]["shopify_api_version"] == "2026-01"
    assert result["data"]["candidate_category"] == "Home & Garden > Patio"
    get_settings.cache_clear()
