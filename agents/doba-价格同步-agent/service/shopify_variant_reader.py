from __future__ import annotations

from typing import Any

from models.variant_mapping import ShopifyVariantSnapshot
from shared.clients import ShopifyAuthClient
from shared.config import get_settings


class ShopifyVariantReader:
    def __init__(self, *, client: ShopifyAuthClient | Any | None = None) -> None:
        self.settings = get_settings()
        self.client = client

    def list_variants(
        self,
        *,
        store_name: str,
        query: str = "vendor:Doba",
        variants_override: list[dict[str, Any]] | None = None,
    ) -> list[ShopifyVariantSnapshot]:
        if variants_override is not None:
            return [ShopifyVariantSnapshot.model_validate(item) for item in variants_override]
        client = self.client or ShopifyAuthClient.from_settings(self.settings)
        data = client.list_product_variants(query=query, page_size=100)
        snapshots: list[ShopifyVariantSnapshot] = []
        for item in data:
            product = item.get("product") or {}
            snapshots.append(
                ShopifyVariantSnapshot(
                    store_name=store_name,
                    shopify_product_id=str(product.get("id") or ""),
                    shopify_variant_id=str(item.get("id") or ""),
                    shopify_sku=str(item.get("sku") or ""),
                    shopify_product_title=str(product.get("title") or ""),
                    shopify_variant_title=str(item.get("title") or item.get("displayName") or ""),
                    shopify_vendor=str(product.get("vendor") or "Doba"),
                    status=str(product.get("status") or ""),
                )
            )
        return snapshots

