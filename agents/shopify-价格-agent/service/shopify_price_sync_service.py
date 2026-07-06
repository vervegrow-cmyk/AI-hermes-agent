from __future__ import annotations

from collections import defaultdict
from typing import Any

from models.price_sync import GigaPriceSnapshot, PriceSyncItem, ShopifyPriceState, SkuMappingRecord
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

    def get_price_states(
        self,
        *,
        store_name: str,
        snapshots: list[GigaPriceSnapshot],
        mappings: list[SkuMappingRecord],
        states_override: list[ShopifyPriceState] | list[dict] | None = None,
        progress_callback: Any | None = None,
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
                        and item.giga_sku == snapshot.giga_sku
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
                        current_price=0,
                    )
                )
            return records

        client = self._client or ShopifyAuthClient.from_settings(self.settings)
        states = []
        total = len(snapshots)
        for index, snapshot in enumerate(snapshots, start=1):
            mapping = next(
                (
                    item
                    for item in mappings
                    if item.store_name == store_name
                    and item.giga_sku == snapshot.giga_sku
                    and item.mapping_status == "active"
                ),
                None,
            )
            if mapping is None:
                if progress_callback is not None:
                    progress_callback(
                        {
                            "index": index,
                            "total": total,
                            "giga_sku": snapshot.giga_sku,
                            "status": "missing_mapping",
                            "loaded_count": len(states),
                        }
                    )
                continue
            variant = self._get_variant(client, mapping.shopify_variant_id, mapping.shopify_sku or snapshot.giga_sku)
            if not variant:
                if progress_callback is not None:
                    progress_callback(
                        {
                            "index": index,
                            "total": total,
                            "giga_sku": snapshot.giga_sku,
                            "shopify_variant_id": mapping.shopify_variant_id,
                            "status": "variant_not_found",
                            "loaded_count": len(states),
                        }
                    )
                continue
            product = variant.get("product") or {}
            states.append(
                ShopifyPriceState(
                    store_name=store_name,
                    shopify_product_id=product.get("id", "") or mapping.shopify_product_id,
                    shopify_variant_id=variant.get("id", "") or mapping.shopify_variant_id,
                    shopify_sku=variant.get("sku", "") or mapping.shopify_sku,
                    current_price=float(variant.get("price", 0) or 0),
                )
            )
            if progress_callback is not None:
                progress_callback(
                    {
                        "index": index,
                        "total": total,
                        "giga_sku": snapshot.giga_sku,
                        "shopify_variant_id": variant.get("id", "") or mapping.shopify_variant_id,
                        "status": "loaded",
                        "loaded_count": len(states),
                    }
                )
        return states

    def discover_mappings(
        self,
        *,
        store_name: str,
        sku_list: list[str] | None = None,
        progress_callback: Any | None = None,
    ) -> list[SkuMappingRecord]:
        if self.mode == "mock":
            return []

        client = self._client or ShopifyAuthClient.from_settings(self.settings)
        variants: list[dict[str, Any]] = []
        requested_skus = [sku.strip() for sku in (sku_list or []) if sku and sku.strip()]
        if requested_skus:
            for sku in requested_skus:
                variant = client.find_variant_by_sku(sku)
                if variant:
                    variants.append(variant)
                    if progress_callback is not None:
                        progress_callback(
                            {
                                "mode": "single_lookup",
                                "sku": sku,
                                "fetched_total": len(variants),
                            }
                        )
        else:
            variants = client.list_product_variants(
                query="status:active",
                page_size=100,
                progress_callback=progress_callback,
            )

        mappings_by_sku: dict[str, SkuMappingRecord] = {}
        for variant in variants:
            shopify_sku = str(variant.get("sku", "") or "").strip()
            if not shopify_sku:
                continue
            product = variant.get("product") or {}
            mappings_by_sku[shopify_sku] = SkuMappingRecord(
                store_name=store_name,
                giga_sku=shopify_sku,
                shopify_product_id=str(product.get("id", "") or ""),
                shopify_variant_id=str(variant.get("id", "") or ""),
                shopify_sku=shopify_sku,
                mapping_status="active",
            )
        return list(mappings_by_sku.values())

    def apply_price_updates(self, items: list[PriceSyncItem]) -> list[PriceSyncItem]:
        if self.mode == "mock":
            return [
                item.model_copy(update={"status": "synced"})
                for item in items
                if item.status == "planned"
            ]

        client = self._client or ShopifyAuthClient.from_settings(self.settings)
        grouped: dict[str, list[PriceSyncItem]] = defaultdict(list)
        for item in items:
            grouped[item.shopify_product_id].append(item)

        updated: list[PriceSyncItem] = []
        for product_id, group in grouped.items():
            if hasattr(client, "graphql"):
                payload_variants = [
                    {"id": item.shopify_variant_id, "price": round(item.target_price, 2)}
                    for item in group
                ]
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
                                    "error_message": "" if status == "synced" else "shopify_price_verification_failed",
                                }
                            )
                        )
                except Exception as exc:
                    fallback_results = self._apply_individual_fallback(client, product_id, group, str(exc))
                    updated.extend(fallback_results)
            else:
                for item in group:
                    updated.append(item.model_copy(update={"status": "failed", "error_message": "shopify_unsupported_client"}))
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

    def _apply_individual_fallback(
        self,
        client: Any,
        product_id: str,
        group: list[PriceSyncItem],
        parent_error: str,
    ) -> list[PriceSyncItem]:
        updated: list[PriceSyncItem] = []
        for item in group:
            try:
                result = client.update_variant_price(
                    product_id=product_id,
                    variant_id=item.shopify_variant_id,
                    price=item.target_price,
                )
                actual_price = float(result.get("price", 0) or 0)
                if abs(actual_price - item.target_price) < 0.01:
                    updated.append(item.model_copy(update={"status": "synced", "error_message": ""}))
                else:
                    updated.append(
                        item.model_copy(
                            update={
                                "status": "failed",
                                "error_message": "shopify_write_failed:verification_mismatch",
                            }
                        )
                    )
            except Exception as exc:
                updated.append(
                    item.model_copy(
                        update={
                            "status": "failed",
                            "error_message": f"shopify_write_failed:{exc}; bulk_error={parent_error}",
                        }
                    )
                )
        return updated
