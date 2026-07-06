from __future__ import annotations

import re
from typing import Any

import bootstrap
from shared.clients import ShopifyAuthClient
from shared.config import get_settings
from src.shared.contracts.screening import ScreeningDecision


def get_shop_info() -> dict[str, Any]:
    settings = get_settings()
    client = ShopifyAuthClient.from_settings(settings)
    auth_summary = client.describe_admin_session()
    shop = client.query_shop_info()
    return {
        "store": auth_summary["store_domain"],
        "auth_mode": auth_summary["auth_mode"],
        "auth_source": auth_summary["auth_source"],
        "auth_ready": auth_summary["auth_ready"],
        "shop": shop,
    }


def find_existing_variant_by_sku(sku: str) -> dict[str, Any] | None:
    settings = get_settings()
    client = ShopifyAuthClient.from_settings(settings)
    return client.find_variant_by_sku(sku)


def create_draft(decision: ScreeningDecision) -> dict[str, Any]:
    settings = get_settings()
    client = ShopifyAuthClient.from_settings(settings)
    auth_summary = client.describe_admin_session()

    if not settings.shopify_pilot_create_approved:
        return {
            "store": auth_summary["store_domain"],
            "draft_id": f"draft-{decision.sku or decision.product_id}",
            "status": "draft_created",
            "title": decision.normalized_title,
            "live_mode": False,
        }

    existing_variant = client.find_variant_by_sku(decision.sku)
    if existing_variant:
        return {
            "store": auth_summary["store_domain"],
            "draft_id": existing_variant["product"]["id"],
            "status": "already_exists_remote",
            "title": existing_variant["product"]["title"],
            "live_mode": True,
        }

    product = client.create_draft_product(_build_product_input(decision))
    first_variant = ((product.get("variants") or {}).get("edges") or [{}])[0].get("node") or {}
    if product.get("id") and first_variant.get("id"):
        updated_variant = client.update_variant_fields(
            product_id=product["id"],
            variant_id=first_variant["id"],
            sku=decision.sku,
            price=decision.normalized_product.target_sale_price,
        )
        if updated_variant:
            first_variant["sku"] = updated_variant.get("sku", first_variant.get("sku"))
    return {
        "store": auth_summary["store_domain"],
        "draft_id": product.get("id", ""),
        "status": "draft_created",
        "title": product.get("title", decision.normalized_title),
        "variant_id": first_variant.get("id", ""),
        "inventory_item_id": ((first_variant.get("inventoryItem") or {}).get("id", "")),
        "live_mode": True,
    }


def _build_product_input(decision: ScreeningDecision) -> dict[str, Any]:
    normalized = decision.normalized_product
    category_tokens = [token.title() for token in normalized.category_tokens[:3]]
    tags = [
        "hermes-agent",
        "doba-import",
        f"supplier:{normalized.supplier_id}" if normalized.supplier_id else "",
        f"product:{normalized.product_id}" if normalized.product_id else "",
        f"ship-from:{normalized.ship_from_country}" if normalized.ship_from_country else "",
        *category_tokens,
    ]
    clean_tags = [tag for tag in tags if tag]
    body_html = _build_description_html(decision)

    product_input: dict[str, Any] = {
        "title": decision.normalized_title,
        "descriptionHtml": body_html,
        "productType": _derive_product_type(normalized.category_tokens),
        "vendor": normalized.brand or "Doba",
        "status": "DRAFT",
        "handle": _slugify(f"{decision.normalized_title}-{decision.sku or decision.product_id}"),
        "tags": clean_tags[:20],
        "seo": {
            "title": decision.normalized_title[:70],
            "description": (normalized.description or decision.normalized_title)[:320],
        },
    }

    return product_input


def _build_description_html(decision: ScreeningDecision) -> str:
    normalized = decision.normalized_product
    highlights = [
        f"<li>SKU: {normalized.sku}</li>" if normalized.sku else "",
        f"<li>Target price: ${normalized.target_sale_price:.2f}</li>" if normalized.target_sale_price else "",
        f"<li>Supplier inventory: {normalized.inventory}</li>",
        f"<li>Ships from: {normalized.ship_from_country}</li>" if normalized.ship_from_country else "",
        f"<li>Estimated delivery: {normalized.delivery_days} days</li>" if normalized.delivery_days else "",
    ]
    highlight_list = "".join(item for item in highlights if item)
    description = normalized.description or decision.normalized_title
    return f"<p>{description}</p><ul>{highlight_list}</ul>"


def _derive_product_type(category_tokens: list[str]) -> str:
    if not category_tokens:
        return "General"
    return category_tokens[-1].title()[:255]


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:255] or "hermes-product"
