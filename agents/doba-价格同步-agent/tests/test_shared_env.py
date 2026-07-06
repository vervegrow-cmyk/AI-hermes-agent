from pathlib import Path
import sys

AGENT_ROOT = Path(__file__).resolve().parents[1]
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from main import print_boot_info
from service.doba_client import DobaPriceSyncClient
from service.executor import execute_task
from shared.config import get_settings
from shared.config.settings import ENV_FILE_CANDIDATES, REPO_ROOT
from shared.schemas import ExecuteRequest


def test_bootstrap_points_to_repo_root():
    repo_root = ensure_repo_root_on_path()
    assert repo_root == REPO_ROOT
    assert any(Path(candidate) == REPO_ROOT.parent / f"{REPO_ROOT.name}.env" for candidate in ENV_FILE_CANDIDATES if not isinstance(candidate, str))


def test_get_settings_can_read_shared_parent_env(monkeypatch):
    env_path = REPO_ROOT.parent / f"{REPO_ROOT.name}.env"
    original = env_path.read_text(encoding="utf-8") if env_path.exists() else None
    env_path.write_text("HERMES_ENV=test-shared-env\nSHOPIFY_SHOP=shared-store.myshopify.com\n", encoding="utf-8")
    try:
        get_settings.cache_clear()
        settings = get_settings()
        assert settings.hermes_env == "test-shared-env"
        assert settings.shopify_shop == "shared-store.myshopify.com"
    finally:
        get_settings.cache_clear()
        if original is None:
            env_path.unlink(missing_ok=True)
        else:
            env_path.write_text(original, encoding="utf-8")


def test_agent_does_not_require_local_env():
    assert not (AGENT_ROOT / ".env").exists()


def test_executor_uses_shared_settings(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("HERMES_ENV", "test")
    monkeypatch.setenv("SHOPIFY_SHOP", "demo-shop.myshopify.com")
    monkeypatch.setenv("SHOPIFY_API_VERSION", "2026-01")
    monkeypatch.setenv("SHOPIFY_AUTH_MODE", "client_credentials")
    monkeypatch.setenv("SHOPIFY_CLIENT_ID", "client-id")
    monkeypatch.setenv("SHOPIFY_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("DOBA_API_BASE_URL", "https://openapi.doba.test")
    monkeypatch.setattr(DobaPriceSyncClient, "list_price_snapshots", lambda self, **kwargs: [])
    result = execute_task(ExecuteRequest(task="dry_run_price_sync"))
    assert result["data"]["environment"] == "test"
    assert result["data"]["store"] == "demo-shop.myshopify.com"
    assert result["data"]["shopify_api_version"] == "2026-01"
    assert result["data"]["shopify_auth"]["auth_source"] == "oauth_client_credentials"
    assert result["data"]["doba_base_url"] == "https://openapi.doba.test"
    get_settings.cache_clear()


def test_boot_output_contains_core_lines(monkeypatch, capsys):
    get_settings.cache_clear()
    monkeypatch.setenv("SHOPIFY_SHOP", "boot-store.myshopify.com")
    monkeypatch.setenv("DOBA_API_BASE_URL", "https://openapi.doba.test")
    print_boot_info()
    output = capsys.readouterr().out
    assert "[BOOT] Agent Name:" in output
    assert "[BOOT] Project Root:" in output
    assert "[BOOT] Shared .env Loaded:" in output
    assert "[BOOT] Registered Routes:" in output
    get_settings.cache_clear()
