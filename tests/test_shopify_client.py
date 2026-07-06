import hashlib
import hmac

import httpx

from shared.clients import ShopifyAuthClient, build_shopify_hmac_message, verify_shopify_oauth_hmac


def test_shopify_auth_client_uses_explicit_admin_token_without_http():
    client = ShopifyAuthClient(
        store_domain="example-store.myshopify.com",
        auth_mode="custom_admin_token",
        admin_access_token="shpat_static_token",
    )

    token = client.get_admin_access_token()

    assert token.access_token == "shpat_static_token"
    assert token.source == "admin_access_token"
    assert client.build_admin_headers()["X-Shopify-Access-Token"] == "shpat_static_token"


def test_shopify_auth_client_requests_client_credentials_token():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = request.content.decode("utf-8")
        return httpx.Response(
            200,
            json={
                "access_token": "shpat_dynamic_token",
                "scope": "write_products,read_products",
                "expires_in": 3600,
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = ShopifyAuthClient(
        store_domain="example-store.myshopify.com",
        auth_mode="client_credentials",
        client_id="client-id",
        client_secret="client-secret",
        http_client=http_client,
    )

    token = client.get_admin_access_token()

    assert captured["url"] == "https://example-store.myshopify.com/admin/oauth/access_token"
    assert "grant_type=client_credentials" in captured["body"]
    assert "client_id=client-id" in captured["body"]
    assert token.access_token == "shpat_dynamic_token"
    assert token.source == "oauth_client_credentials"


def test_shopify_authorize_url_uses_offline_default():
    client = ShopifyAuthClient(
        store_domain="example-store.myshopify.com",
        auth_mode="authorization_code",
        client_id="client-id",
        client_secret="client-secret",
    )

    url, state = client.build_authorize_url(
        scopes=["write_products", "read_orders"],
        redirect_uri="https://app.example.com/callback",
    )

    assert "client_id=client-id" in url
    assert "scope=write_products%2Cread_orders" in url
    assert "grant_options%5B%5D=per-user" not in url
    assert state


def test_verify_shopify_oauth_hmac_matches_generated_digest():
    params = {
        "code": "abc",
        "host": "ZXhhbXBsZS1zdG9yZS5teXNob3BpZnkuY29tL2FkbWlu",
        "shop": "example-store.myshopify.com",
        "state": "state-123",
        "timestamp": "1711111111",
    }
    message = build_shopify_hmac_message(params)
    digest = hmac.new(
        b"client-secret",
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    signed_params = dict(params)
    signed_params["hmac"] = digest

    assert verify_shopify_oauth_hmac(signed_params, "client-secret") is True


def test_shopify_graphql_helpers_cover_shop_variant_create_price_and_inventory():
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        payload = json.loads(request.content.decode("utf-8"))
        query = payload["query"]
        if "query ShopInfo" in query:
            return httpx.Response(
                200,
                json={"data": {"shop": {"id": "gid://shopify/Shop/1", "name": "LootCard AI", "myshopifyDomain": "example-store.myshopify.com", "currencyCode": "USD"}}},
            )
        if "query VariantBySku" in query:
            return httpx.Response(
                200,
                json={
                    "data": {
                        "productVariants": {
                            "edges": [
                                {
                                    "node": {
                                        "id": "gid://shopify/ProductVariant/1",
                                        "sku": "SKU-1",
                                        "price": "29.99",
                                        "inventoryQuantity": 5,
                                        "inventoryItem": {"id": "gid://shopify/InventoryItem/1"},
                                        "product": {
                                            "id": "gid://shopify/Product/1",
                                            "status": "DRAFT",
                                            "title": "Example Product",
                                        },
                                    }
                                }
                            ]
                        }
                    }
                },
            )
        if "mutation CreateDraftProduct" in query:
            return httpx.Response(
                200,
                json={
                    "data": {
                        "productCreate": {
                            "product": {
                                "id": "gid://shopify/Product/2",
                                "title": "Draft Product",
                                "status": "DRAFT",
                                "variants": {
                                    "edges": [
                                        {
                                            "node": {
                                                "id": "gid://shopify/ProductVariant/2",
                                                "sku": "SKU-2",
                                                "inventoryItem": {"id": "gid://shopify/InventoryItem/2"},
                                            }
                                        }
                                    ]
                                },
                            },
                            "userErrors": [],
                        }
                    }
                },
            )
        if "mutation UpdateVariantFields" in query:
            return httpx.Response(
                200,
                json={
                    "data": {
                        "productVariantsBulkUpdate": {
                            "productVariants": [
                                {
                                    "id": "gid://shopify/ProductVariant/1",
                                    "sku": "SKU-1",
                                    "price": "34.00",
                                    "compareAtPrice": None,
                                }
                            ],
                            "userErrors": [],
                        }
                    }
                },
            )
        if "mutation SetInventory" in query:
            return httpx.Response(
                200,
                json={
                    "data": {
                        "inventorySetQuantities": {
                            "inventoryAdjustmentGroup": {
                                "reason": "correction",
                                "changes": [{"name": "available", "delta": 3, "quantityAfterChange": 8}],
                            },
                            "userErrors": [],
                        }
                    }
                },
            )
        if "query PrimaryLocation" in query:
            return httpx.Response(
                200,
                json={
                    "data": {
                        "locations": {
                            "edges": [
                                {"node": {"id": "gid://shopify/Location/1", "name": "Main", "isActive": True}}
                            ]
                        }
                    }
                },
            )
        raise AssertionError(query)

    import json

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = ShopifyAuthClient(
        store_domain="example-store.myshopify.com",
        auth_mode="custom_admin_token",
        admin_access_token="shpat_static_token",
        http_client=http_client,
    )

    assert client.query_shop_info()["name"] == "LootCard AI"
    assert client.find_variant_by_sku("SKU-1")["id"] == "gid://shopify/ProductVariant/1"
    assert client.get_primary_location()["id"] == "gid://shopify/Location/1"
    assert client.create_draft_product({"title": "Draft Product"})["id"] == "gid://shopify/Product/2"
    assert client.update_variant_price(
        product_id="gid://shopify/Product/1",
        variant_id="gid://shopify/ProductVariant/1",
        price=34.0,
    )["price"] == "34.00"
    assert client.set_inventory_quantity(
        inventory_item_id="gid://shopify/InventoryItem/1",
        location_id="gid://shopify/Location/1",
        quantity=8,
        change_from_quantity=5,
    )["changes"][0]["delta"] == 3
    assert len(requests) == 6
