from __future__ import annotations

import re

from src.shared.contracts.product import DobaProductInput, NormalizedProduct


def _clean_title(title: str) -> str:
    cleaned = re.sub(r"\s+", " ", title).strip()
    return cleaned[:120]


def _derive_target_price(product: DobaProductInput) -> float:
    reference_price = product.msrp if product.msrp > 0 else product.cost * 2.2
    return round(max(reference_price, 25.0), 2)


def normalize_product(product: DobaProductInput) -> NormalizedProduct:
    normalized_title = _clean_title(product.title)
    category_tokens = [
        token.strip().lower()
        for token in re.split(r"[>/|,]", product.category_path)
        if token.strip()
    ]
    return NormalizedProduct(
        supplier_id=product.supplier_id,
        product_id=product.product_id,
        sku=product.sku.strip(),
        title=product.title.strip(),
        normalized_title=normalized_title,
        brand=product.brand.strip(),
        category_path=product.category_path.strip(),
        supplier_status=product.supplier_status.strip().lower(),
        cost=round(product.cost, 2),
        target_sale_price=_derive_target_price(product),
        inventory=product.inventory,
        ship_from_country=product.ship_from_country.strip().upper(),
        ships_to_countries=[item.strip().upper() for item in product.ships_to_countries if item.strip()],
        shipping_cost=round(product.shipping_cost, 2),
        delivery_days=product.delivery_days,
        description=product.description.strip(),
        image_urls=[url.strip() for url in product.image_urls if url.strip()],
        variant_attributes=product.variant_attributes,
        attributes=product.attributes,
        category_tokens=category_tokens,
        duplicate_key=(product.sku or product.product_id).strip().lower(),
    )

