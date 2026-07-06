from __future__ import annotations

from typing import Any

from shared.clients import ShopifyAuthClient
from shared.config import get_settings
from src.shared.contracts.listing import ShopifyProductPayload


class ShopifyDraftListingService:
    def __init__(
        self,
        *,
        client: ShopifyAuthClient | Any | None = None,
        force_mode: str | None = None,
    ) -> None:
        self._client = client
        self._settings = get_settings()
        self.mode = force_mode or self._detect_mode(client)
        self.store = self._resolve_store()

    @property
    def is_mock_mode(self) -> bool:
        return self.mode == "mock"

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

    def _resolve_store(self) -> str:
        if self._client is not None and hasattr(self._client, "describe_admin_session"):
            summary = self._client.describe_admin_session()
            return str(summary.get("store_domain") or "")
        return (
            self._settings.shopify_store
            or self._settings.shopify_shop
            or self._settings.shopify_shop_domain
            or "mock-shopify.local"
        )

    def _get_client(self) -> ShopifyAuthClient | Any:
        if self._client is None:
            self._client = ShopifyAuthClient.from_settings(self._settings)
        return self._client

    def create_draft_product(self, payload: ShopifyProductPayload) -> dict[str, Any]:
        if self.is_mock_mode:
            suffix = payload.product_hash[:12] or payload.supplier_sku or "draft"
            return {
                "shopify_product_id": f"mock-product-{suffix}",
                "shopify_variant_id": f"mock-variant-{suffix}",
                "store": self.store,
                "mock_mode": True,
                "status": "draft",
            }

        client = self._get_client()
        product = client.create_draft_product(self._build_shopify_input(payload))
        first_variant = ((product.get("variants") or {}).get("edges") or [{}])[0].get("node") or {}
        return {
            "shopify_product_id": product.get("id", ""),
            "shopify_variant_id": first_variant.get("id", ""),
            "store": self.store,
            "mock_mode": False,
            "status": str(product.get("status") or "DRAFT").lower(),
        }

    def _build_shopify_input(self, payload: ShopifyProductPayload) -> dict[str, Any]:
        return {
            "title": payload.content.title,
            "descriptionHtml": payload.content.description,
            "vendor": payload.vendor or "Doba",
            "productType": payload.product_type or "General",
            "status": "DRAFT",
            "handle": payload.seo.handle,
            "tags": payload.seo.tags[:250],
            "seo": {
                "title": payload.seo.seo_title,
                "description": payload.seo.seo_description,
            },
        }
