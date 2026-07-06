from pathlib import Path
import sys

AGENT_ROOT = Path(__file__).resolve().parents[1]
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from service.executor import execute_task
from shared.clients.shopify import ShopifyAuthClient
from shared.config import get_settings
from shared.config.settings import REPO_ROOT
from shared.schemas import ExecuteRequest


def test_bootstrap_points_to_repo_root():
    repo_root = ensure_repo_root_on_path()
    assert repo_root == REPO_ROOT
    assert (repo_root / ".env").exists()


def test_executor_uses_shared_settings(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("HERMES_ENV", "test")
    monkeypatch.setenv("SHOPIFY_SHOP", "demo-shop.myshopify.com")
    monkeypatch.setenv("SHOPIFY_API_VERSION", "2026-01")
    monkeypatch.setenv("SHOPIFY_AUTH_MODE", "client_credentials")
    monkeypatch.setenv("SHOPIFY_CLIENT_ID", "client-id")
    monkeypatch.setenv("SHOPIFY_CLIENT_SECRET", "client-secret")

    result = execute_task(ExecuteRequest(task="price-check"))

    assert result["data"]["environment"] == "test"
    assert result["data"]["store"] == "demo-shop.myshopify.com"
    assert result["data"]["shopify_api_version"] == "2026-01"
    assert result["data"]["shopify_auth"]["auth_mode"] == "client_credentials"
    assert result["data"]["shopify_auth"]["auth_source"] == "oauth_client_credentials"
    get_settings.cache_clear()


def test_shopify_auth_client_supports_client_credentials():
    class _Response:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "access_token": "test-access-token",
                "expires_in": 3600,
                "scope": "write_products",
            }

    class _HttpClient:
        def post(self, *args, **kwargs):
            assert kwargs["data"]["grant_type"] == "client_credentials"
            return _Response()

    client = ShopifyAuthClient(
        store_domain="demo-store.myshopify.com",
        auth_mode="client_credentials",
        client_id="client-id",
        client_secret="client-secret",
        http_client=_HttpClient(),
    )
    token = client.get_admin_access_token()
    assert token.access_token == "test-access-token"
    assert token.source == "oauth_client_credentials"
