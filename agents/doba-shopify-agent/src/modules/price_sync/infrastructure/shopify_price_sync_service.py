from __future__ import annotations

from typing import Any

from shared.clients import ShopifyAuthClient
from shared.config import get_settings


class ShopifyPriceSyncService:
    def __init__(
        self,
        *,
        client: ShopifyAuthClient | Any | None = None,
        force_mode: str | None = None,
    ) -> None:
        self._settings = get_settings()
        self._client = client
        self.mode = force_mode or self._detect_mode(client)
        self.product_create_calls = 0
        self.publish_calls = 0
        self.inventory_update_calls = 0
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

    def sync_price(self, shopify_variant_id: str, new_price: float, supplier_sku: str) -> dict[str, Any]:
        if self.mode == "mock":
            return {
                "supplier_sku": supplier_sku,
                "shopify_variant_id": shopify_variant_id,
                "new_price": new_price,
                "status": "synced",
                "mock_mode": True,
            }

        client = self._get_client()
        variant = client.find_variant_by_sku(supplier_sku)
        if not variant:
            raise RuntimeError("Missing Shopify variant for supplier_sku.")
        product = variant.get("product") or {}
        product_id = product.get("id", "")
        variant_id = variant.get("id", "") or shopify_variant_id
        if not product_id or not variant_id:
            raise RuntimeError("Missing Shopify product or variant id.")
        result = client.update_variant_price(
            product_id=product_id,
            variant_id=variant_id,
            price=new_price,
        )
        return {
            "supplier_sku": supplier_sku,
            "shopify_variant_id": variant_id,
            "new_price": new_price,
            "status": "synced",
            "mock_mode": False,
            "result": result,
        }
