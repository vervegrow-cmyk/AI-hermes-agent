from __future__ import annotations

from src.modules.shopify_listing.infrastructure.shopify_gateway import get_shop_info


def query_shop_connection() -> dict:
    return get_shop_info()
