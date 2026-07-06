from __future__ import annotations

from typing import Any

from shared.clients import ShopifyAuthClient
from shared.config import get_settings
from src.shared.contracts.inventory import InventorySyncPlan


class ShopifyInventorySyncService:
    def __init__(
        self,
        *,
        client: ShopifyAuthClient | Any | None = None,
        force_mode: str | None = None,
    ) -> None:
        self._settings = get_settings()
        self._client = client
        self.mode = force_mode or self._detect_mode(client)
        self.publish_calls = 0
        self.product_create_calls = 0
        self.price_update_calls = 0
        self.order_create_calls = 0

    def _detect_mode(self, client: ShopifyAuthClient | Any | None) -> str:
        if client is not None:
            return "real"
        store = (
            self._settings.shopify_store
            or self._settings.shopify_shop
            or self._settings.shopify_shop_domain
        ).strip()
        has_token = bool(
            self._settings.shopify_admin_access_token
            or self._settings.shopify_token
            or (
                self._settings.shopify_auth_mode == "client_credentials"
                and self._settings.shopify_client_id
                and self._settings.shopify_client_secret
            )
        )
        return "real" if store and has_token else "mock"

    def _get_client(self) -> ShopifyAuthClient | Any:
        if self._client is None:
            self._client = ShopifyAuthClient.from_settings(self._settings)
        return self._client

    def sync_inventory(self, plan: InventorySyncPlan) -> dict[str, Any]:
        if self.mode == "mock":
            return {
                "supplier_sku": plan.supplier_sku,
                "shopify_variant_id": plan.shopify_variant_id,
                "inventory": plan.target_inventory,
                "status": "synced",
                "mock_mode": True,
            }

        client = self._get_client()
        location = client.get_primary_location()
        if not location:
            raise RuntimeError("Missing Shopify inventory location.")
        variant = client.find_variant_by_sku(plan.supplier_sku)
        if not variant:
            raise RuntimeError("Missing Shopify variant for supplier_sku.")
        inventory_item = variant.get("inventoryItem") or {}
        inventory_item_id = inventory_item.get("id", "")
        if not inventory_item_id:
            raise RuntimeError("Missing Shopify inventory item id.")
        result = client.set_inventory_quantity(
            inventory_item_id=inventory_item_id,
            location_id=location["id"],
            quantity=plan.target_inventory,
            change_from_quantity=plan.current_inventory,
        )
        return {
            "supplier_sku": plan.supplier_sku,
            "shopify_variant_id": plan.shopify_variant_id,
            "inventory": plan.target_inventory,
            "status": "synced",
            "mock_mode": False,
            "result": result,
        }
