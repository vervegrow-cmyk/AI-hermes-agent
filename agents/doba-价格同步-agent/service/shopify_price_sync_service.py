from __future__ import annotations

from collections import defaultdict
from typing import Any

from models.price_sync import DobaPriceSnapshot, PriceSyncItem, ShopifyPriceState, SkuMappingRecord
from shared.clients import ShopifyAuthClient, ShopifyGraphQLError
from shared.config import get_settings


class ShopifyPriceSyncService:
    def __init__(self, *, client: ShopifyAuthClient | Any | None = None, force_mode: str | None = None) -> None:
        self.settings = get_settings()
        self._client = client
        self._force_mode = force_mode

    @property
    def mode(self) -> str:
        if self._force_mode:
            return self._force_mode
        store = self.settings.shopify_store or self.settings.shopify_shop or self.settings.shopify_shop_domain
        token_ready = bool(
            self.settings.shopify_admin_access_token
            or self.settings.shopify_token
            or (self.settings.shopify_client_id and self.settings.shopify_client_secret)
        )
        return "real" if (self._client or (store and token_ready)) else "mock"

    def ensure_write_ready(self) -> None:
        if self.mode == "mock":
            raise RuntimeError("shopify_admin_token_missing")

    def get_price_states(
        self,
        *,
        store_name: str,
        snapshots: list[DobaPriceSnapshot],
        mappings: list[SkuMappingRecord],
        states_override: list[ShopifyPriceState] | list[dict] | None = None,
    ) -> list[ShopifyPriceState]:
        if states_override is not None:
            return [
                item if isinstance(item, ShopifyPriceState) else ShopifyPriceState.model_validate(item)
                for item in states_override
            ]
        if self.mode == "mock":
            records = []
            for snapshot in snapshots:
                mapping = next(
                    (
                        item
                        for item in mappings
                        if item.store_name == store_name
                        and item.doba_sku == snapshot.doba_sku
                        and item.mapping_status == "active"
                    ),
                    None,
                )
                if mapping is None:
                    continue
                records.append(
                    ShopifyPriceState(
                        store_name=store_name,
                        shopify_product_id=mapping.shopify_product_id,
                        shopify_variant_id=mapping.shopify_variant_id,
                        shopify_sku=mapping.shopify_sku,
                        current_price=0.0,
                    )
                )
            return records

        client = self._client or ShopifyAuthClient.from_settings(self.settings)
        states = []
        for snapshot in snapshots:
            mapping = next(
                (
                    item
                    for item in mappings
                    if item.store_name == store_name
                    and item.doba_sku == snapshot.doba_sku
                    and item.mapping_status == "active"
                ),
                None,
            )
            if mapping is None:
                continue
            variant = self._get_variant(client, mapping.shopify_variant_id, mapping.shopify_sku or snapshot.doba_sku)
            if not variant:
                continue
            product = variant.get("product") or {}
            states.append(
                ShopifyPriceState(
                    store_name=store_name,
                    shopify_product_id=str(product.get("id", "") or mapping.shopify_product_id),
                    shopify_variant_id=str(variant.get("id", "") or mapping.shopify_variant_id),
                    shopify_sku=str(variant.get("sku", "") or mapping.shopify_sku),
                    current_price=float(variant.get("price", 0) or 0),
                )
            )
        return states

    def apply_price_updates(self, items: list[PriceSyncItem]) -> list[PriceSyncItem]:
        if self.mode == "mock":
            return [item.model_copy(update={"status": "synced"}) for item in items if item.status == "planned"]

        client = self._client or ShopifyAuthClient.from_settings(self.settings)
        grouped: dict[str, list[PriceSyncItem]] = defaultdict(list)
        for item in items:
            grouped[item.shopify_product_id].append(item)

        updated: list[PriceSyncItem] = []
        for product_id, group in grouped.items():
            if hasattr(client, "graphql"):
                payload_variants = [{"id": item.shopify_variant_id, "price": round(item.target_price, 2)} for item in group]
                try:
                    data = client.graphql(
                        """
                        mutation UpdateVariantPrices($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
                          productVariantsBulkUpdate(productId: $productId, variants: $variants) {
                            productVariants {
                              id
                              price
                            }
                            userErrors {
                              field
                              message
                            }
                          }
                        }
                        """,
                        {"productId": product_id, "variants": payload_variants},
                    )
                    result = data.get("productVariantsBulkUpdate") or {}
                    errors = result.get("userErrors") or []
                    if errors:
                        raise ShopifyGraphQLError(str(errors))
                    price_by_id = {row.get("id", ""): float(row.get("price", 0) or 0) for row in result.get("productVariants", [])}
                    for item in group:
                        actual_price = price_by_id.get(item.shopify_variant_id, item.target_price)
                        status = "synced" if abs(actual_price - item.target_price) < 0.01 else "failed"
                        updated.append(
                            item.model_copy(
                                update={
                                    "status": status,
                                    "error_message": "" if status == "synced" else "shopify_write_failed",
                                    "reason_codes": item.reason_codes if status == "synced" else [*item.reason_codes, "shopify_write_failed"],
                                }
                            )
                        )
                except Exception as exc:
                    for item in group:
                        updated.append(
                            item.model_copy(
                                update={
                                    "status": "failed",
                                    "error_message": f"shopify_write_failed:{exc}",
                                    "reason_codes": [*item.reason_codes, "shopify_write_failed"],
                                }
                            )
                        )
            else:
                for item in group:
                    updated.append(
                        item.model_copy(
                            update={
                                "status": "failed",
                                "error_message": "shopify_user_error",
                                "reason_codes": [*item.reason_codes, "shopify_user_error"],
                            }
                        )
                    )
        return updated

    def _get_variant(self, client: Any, variant_id: str, sku: str) -> dict[str, Any] | None:
        if variant_id and hasattr(client, "graphql"):
            data = client.graphql(
                """
                query VariantById($id: ID!) {
                  productVariant(id: $id) {
                    id
                    sku
                    price
                    product {
                      id
                    }
                  }
                }
                """,
                {"id": variant_id},
            )
            variant = data.get("productVariant")
            if variant:
                return variant
        return client.find_variant_by_sku(sku)

