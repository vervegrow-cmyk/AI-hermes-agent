import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from tests.conftest import load_fixture

AGENT_ROOT = Path(__file__).resolve().parents[2]


def _load_app_module():
    for module_name in [
        "api",
        "api.app",
        "src.app.api.app",
    ]:
        sys.modules.pop(module_name, None)

    spec = importlib.util.spec_from_file_location(
        "doba_shopify_agent_app",
        AGENT_ROOT / "api" / "app.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_evaluate_product_route_approves_publishable_product():
    module = _load_app_module()
    client = TestClient(module.app)

    response = client.post(
        "/evaluate-product",
        json={"product": load_fixture("approved_product.json"), "target_market": "US"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "approved"
    assert body["publish_action"] == "skipped"


def test_execute_endpoint_handles_publish_workflow_once():
    module = _load_app_module()
    client = TestClient(module.app)

    response = client.post(
        "/execute",
        json={
            "request_id": "req-1",
            "task": "publish-approved",
            "payload": {"target_market": "US", "products": [load_fixture("approved_product.json")]},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["published_count"] == 1
    assert body["data"]["published"][0]["status"] == "draft_created"


def test_evaluate_batch_route_uses_fixture_mix():
    module = _load_app_module()
    client = TestClient(module.app)

    response = client.post(
        "/evaluate-batch",
        json={"products": load_fixture("batch_products.json"), "target_market": "US"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 3
    assert body["approved"] == 1
    assert body["manual_review"] == 1
    assert body["rejected"] == 1


def test_shopify_shop_info_route_returns_connection_payload():
    module = _load_app_module()
    client = TestClient(module.app)

    with patch("src.app.api.app.query_shop_connection") as query_shop_connection:
        query_shop_connection.return_value = {
            "store": "example-store.myshopify.com",
            "auth_mode": "client_credentials",
            "auth_source": "oauth_client_credentials",
            "auth_ready": True,
            "shop": {"name": "LootCard AI"},
        }
        response = client.get("/shopify/shop-info")

    assert response.status_code == 200
    assert response.json()["shop"]["name"] == "LootCard AI"
