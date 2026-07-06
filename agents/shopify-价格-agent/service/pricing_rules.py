from __future__ import annotations

from models.price_sync import GigaPriceSnapshot, PriceCalculation
from shared.config import get_settings


def round_money(value: float) -> float:
    return round(max(value, 0.0), 2)


def round_delta(value: float) -> float:
    return round(value, 2)


def calculate_price(snapshot: GigaPriceSnapshot, current_price: float) -> PriceCalculation:
    settings = get_settings()
    platform_cost = 0.0
    warehouse_cost = 0.0
    true_cost = round_money(snapshot.supplier_cost + snapshot.shipping_cost)
    target_price = round_money((snapshot.supplier_cost * (1 + settings.price_sync_product_markup_rate)) + snapshot.shipping_cost)
    minimum_safe_price = target_price
    if current_price and abs(target_price - current_price) < settings.price_sync_min_delta_amount:
        target_price = round_money(current_price)
    return PriceCalculation(
        giga_sku=snapshot.giga_sku,
        supplier_cost=snapshot.supplier_cost,
        shipping_cost=snapshot.shipping_cost,
        platform_cost=platform_cost,
        warehouse_cost=warehouse_cost,
        true_cost=true_cost,
        minimum_safe_price=minimum_safe_price,
        target_price=target_price,
    )
