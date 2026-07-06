from __future__ import annotations

from pathlib import Path
import sys

AGENT_ROOT = Path(__file__).resolve().parents[1]
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from models.inventory_sync import InventorySyncRequest
from service.giga_inventory_client import GigaInventoryClient, GigaInventoryClientError
from service.inventory_sync_service import InventorySyncService


class _StubShopifyClient:
    store_domain = "demo-store.myshopify.com"

    def __init__(self) -> None:
        self.inventory_updates = []
        self.product_status_updates = []

    def query_shop_info(self) -> dict:
        return {
            "id": "gid://shopify/Shop/1",
            "name": "Demo Store",
            "myshopifyDomain": "demo-store.myshopify.com",
        }

    def get_primary_location(self) -> dict:
        return {"id": "gid://shopify/Location/1", "name": "Main"}

    def graphql(self, query: str, variables: dict | None = None) -> dict:
        if "query VariantsBySku" in query:
            requested_sku = str((variables or {}).get("query", "")).replace("sku:", "")
            candidates = self.graphql("query ProductVariantsPage", None)["productVariants"]["edges"]
            edges = [edge for edge in candidates if edge["node"]["sku"] == requested_sku]
            return {"productVariants": {"edges": edges}}
        if "query ProductVariantsPage" in query:
            return {
                "productVariants": {
                    "edges": [
                        {
                            "node": {
                                "id": "gid://shopify/ProductVariant/1",
                                "sku": "SKU-1",
                                "inventoryQuantity": 5,
                                "inventoryItem": {"id": "gid://shopify/InventoryItem/1"},
                                "product": {
                                    "id": "gid://shopify/Product/1",
                                    "title": "One",
                                    "status": "ACTIVE",
                                    "vendor": "Dekuch",
                                },
                            }
                        },
                        {
                            "node": {
                                "id": "gid://shopify/ProductVariant/2",
                                "sku": "SKU-2",
                                "inventoryQuantity": 7,
                                "inventoryItem": {"id": "gid://shopify/InventoryItem/2"},
                                "product": {
                                    "id": "gid://shopify/Product/2",
                                    "title": "Two",
                                    "status": "ACTIVE",
                                    "vendor": "Dekuch",
                                },
                            }
                        },
                    ],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        raise AssertionError(query)

    def set_inventory_quantity(
        self,
        *,
        inventory_item_id: str,
        location_id: str,
        quantity: int,
        change_from_quantity: int | None = 0,
        reference_document_uri: str | None = None,
    ) -> dict:
        self.inventory_updates.append(
            {
                "inventory_item_id": inventory_item_id,
                "location_id": location_id,
                "quantity": quantity,
                "change_from_quantity": change_from_quantity,
            }
        )
        return {"changes": [{"name": "available", "quantityAfterChange": quantity}]}

    def update_product_status(self, *, product_id: str, status: str) -> dict:
        self.product_status_updates.append({"product_id": product_id, "status": status})
        return {"id": product_id, "status": status, "title": "Demo"}


class _StubGigaClient:
    def validate_connection(self) -> dict:
        return {"base_url": "https://openapi.gigab2b.com", "endpoint": "/inventory"}

    def fetch_inventory_by_sku(self, sku: str):
        if sku == "SKU-1":
            return [type("Record", (), {"sku": "SKU-1", "available_inventory": 8})()]
        if sku == "SKU-2":
            return [type("Record", (), {"sku": "SKU-2", "available_inventory": 7})()]
        return []


def test_inventory_sync_service_apply_updates_and_skips():
    events = []
    shopify_client = _StubShopifyClient()
    service = InventorySyncService(shopify_client=shopify_client, giga_client=_StubGigaClient())

    batch = service.run(
        InventorySyncRequest(store_name="demo-store.myshopify.com", mode="apply"),
        progress_callback=events.append,
    )

    assert batch.processed_count == 2
    assert batch.updated_count == 1
    assert batch.skipped_count == 1
    assert batch.failed_count == 0
    assert batch.items[0].status == "updated"
    assert batch.items[0].giga_inventory == 8
    assert batch.items[1].status == "skipped"
    assert batch.artifact_paths["report"].endswith(".json")
    assert any(event.get("stage") == "shopify_validated" for event in events)
    assert shopify_client.product_status_updates == []


class _DuplicateShopifyClient(_StubShopifyClient):
    def graphql(self, query: str, variables: dict | None = None) -> dict:
        if "query ProductVariantsPage" in query:
            return {
                "productVariants": {
                    "edges": [
                        {
                            "node": {
                                "id": "gid://shopify/ProductVariant/1",
                                "sku": "DUP-1",
                                "inventoryQuantity": 1,
                                "inventoryItem": {"id": "gid://shopify/InventoryItem/1"},
                                "product": {
                                    "id": "gid://shopify/Product/1",
                                    "title": "One",
                                    "status": "ACTIVE",
                                    "vendor": "Dekuch",
                                },
                            }
                        },
                        {
                            "node": {
                                "id": "gid://shopify/ProductVariant/2",
                                "sku": "DUP-1",
                                "inventoryQuantity": 2,
                                "inventoryItem": {"id": "gid://shopify/InventoryItem/2"},
                                "product": {
                                    "id": "gid://shopify/Product/2",
                                    "title": "Two",
                                    "status": "ACTIVE",
                                    "vendor": "Dekuch",
                                },
                            }
                        },
                    ],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        raise AssertionError(query)


def test_inventory_sync_service_skips_duplicate_shopify_sku():
    service = InventorySyncService(shopify_client=_DuplicateShopifyClient(), giga_client=_StubGigaClient())

    batch = service.run(InventorySyncRequest(store_name="demo-store.myshopify.com", mode="apply"))

    assert batch.processed_count == 2
    assert batch.updated_count == 0
    assert batch.skipped_count == 2
    assert batch.items[0].reason == "Shopify 中存在重复 SKU，已跳过"


class _SavedItemsErrorGigaClient(_StubGigaClient):
    def fetch_inventory_by_sku(self, sku: str):
        raise GigaInventoryClientError(
            "该 SKU 未加入 Saved Items，或当前没有备货库存 | 响应详情: {}"
        )


def test_inventory_sync_service_dry_run_delists_dekuch_product():
    shopify_client = _StubShopifyClient()
    service = InventorySyncService(shopify_client=shopify_client, giga_client=_SavedItemsErrorGigaClient())

    batch = service.run(
        InventorySyncRequest(
            store_name="demo-store.myshopify.com",
            mode="dry-run",
            sku_list=["SKU-1"],
        )
    )

    assert batch.processed_count == 1
    assert batch.updated_count == 0
    assert batch.skipped_count == 1
    assert batch.failed_count == 0
    assert batch.items[0].action == "delist_product"
    assert batch.items[0].status == "dry_run"
    assert batch.items[0].reason == "命中 Dekuch 下架规则，dry-run 未实际下架"
    assert batch.items[0].shopify_product_status_after == "DRAFT"
    assert shopify_client.product_status_updates == []


def test_inventory_sync_service_apply_delists_dekuch_product():
    shopify_client = _StubShopifyClient()
    service = InventorySyncService(shopify_client=shopify_client, giga_client=_SavedItemsErrorGigaClient())

    batch = service.run(
        InventorySyncRequest(
            store_name="demo-store.myshopify.com",
            mode="apply",
            sku_list=["SKU-1"],
        )
    )

    assert batch.processed_count == 1
    assert batch.updated_count == 1
    assert batch.skipped_count == 0
    assert batch.failed_count == 0
    assert batch.items[0].action == "delist_product"
    assert batch.items[0].status == "updated"
    assert batch.items[0].reason == "已下架：该 SKU 未加入 Saved Items，或当前没有备货库存"
    assert batch.items[0].shopify_product_status_after == "DRAFT"
    assert shopify_client.product_status_updates == [
        {"product_id": "gid://shopify/Product/1", "status": "DRAFT"}
    ]


class _LowInventoryMatchGigaClient(_StubGigaClient):
    def fetch_inventory_by_sku(self, sku: str):
        if sku == "SKU-1":
            return [type("Record", (), {"sku": "SKU-1", "available_inventory": 4})()]
        return super().fetch_inventory_by_sku(sku)


def test_inventory_sync_service_delists_when_inventory_is_already_low():
    shopify_client = _StubShopifyClient()
    service = InventorySyncService(shopify_client=shopify_client, giga_client=_LowInventoryMatchGigaClient())

    batch = service.run(
        InventorySyncRequest(
            store_name="demo-store.myshopify.com",
            mode="apply",
            sku_list=["SKU-1"],
        )
    )

    assert batch.processed_count == 1
    assert batch.updated_count == 1
    assert batch.failed_count == 0
    assert batch.items[0].action == "update_inventory_and_delist"
    assert batch.items[0].status == "updated"
    assert batch.items[0].giga_inventory == 4
    assert batch.items[0].reason == "已下架：库存低于 5，商品改为草稿"
    assert batch.items[0].shopify_product_status_after == "DRAFT"
    assert shopify_client.inventory_updates == [
        {
            "inventory_item_id": "gid://shopify/InventoryItem/1",
            "location_id": "gid://shopify/Location/1",
            "quantity": 4,
            "change_from_quantity": 5,
        }
    ]
    assert shopify_client.product_status_updates == [
        {"product_id": "gid://shopify/Product/1", "status": "DRAFT"}
    ]


class _AlreadyLowInventoryShopifyClient(_StubShopifyClient):
    def graphql(self, query: str, variables: dict | None = None) -> dict:
        data = super().graphql(query, variables)
        if "productVariants" in data:
            for edge in data["productVariants"].get("edges", []):
                if edge["node"]["sku"] == "SKU-1":
                    edge["node"]["inventoryQuantity"] = 4
        return data


def test_inventory_sync_service_delists_low_inventory_even_when_quantity_matches():
    shopify_client = _AlreadyLowInventoryShopifyClient()
    service = InventorySyncService(shopify_client=shopify_client, giga_client=_LowInventoryMatchGigaClient())

    batch = service.run(
        InventorySyncRequest(
            store_name="demo-store.myshopify.com",
            mode="apply",
            sku_list=["SKU-1"],
        )
    )

    assert batch.processed_count == 1
    assert batch.updated_count == 1
    assert batch.failed_count == 0
    assert batch.items[0].action == "delist_product"
    assert batch.items[0].status == "updated"
    assert batch.items[0].reason == "已下架：库存低于 5，商品改为草稿"
    assert batch.items[0].giga_inventory == 4
    assert shopify_client.inventory_updates == []
    assert shopify_client.product_status_updates == [
        {"product_id": "gid://shopify/Product/1", "status": "DRAFT"}
    ]


def test_giga_inventory_client_translates_interface_not_available():
    client = GigaInventoryClient.__new__(GigaInventoryClient)
    try:
        client._raise_for_business_error(
            {
                "success": False,
                "code": "401",
                "msg": "Interface not available.",
                "subMsg": "",
            },
            endpoint="/b2b-overseas-api/v1/buyer/inventory/quantity/v1",
            body={"skus": ["SKU-1"]},
        )
    except GigaInventoryClientError as exc:
        assert "API Key" in str(exc)
    else:
        raise AssertionError("Expected GigaInventoryClientError")


def test_giga_inventory_client_translates_saved_items_error():
    client = GigaInventoryClient.__new__(GigaInventoryClient)
    try:
        client._raise_for_business_error(
            {
                "success": False,
                "code": "B50003",
                "msg": "Invalid business access: Account or service permission invalid/Region restriction",
                "subMsg": "Request failed. The SKU is not added to Saved Items List or has no stockpiled inventory.",
            },
            endpoint="/b2b-overseas-api/v1/buyer/inventory/quantity/v2",
            body={"skus": ["SKU-1"]},
        )
    except GigaInventoryClientError as exc:
        assert "Saved Items" in str(exc)
    else:
        raise AssertionError("Expected GigaInventoryClientError")
