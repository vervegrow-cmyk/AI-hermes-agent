from __future__ import annotations

import math

from models.price_sync import DobaPriceSnapshot, PriceCalculation, RoundingMode
from shared.config import get_settings


def round_money(value: float) -> float:
    return round(max(value, 0.0), 2)


def round_delta(value: float) -> float:
    return round(value, 2)


def apply_rounding(value: float, mode: RoundingMode) -> float:
    safe_value = max(value, 0.0)
    if mode == "no_rounding":
        return round(safe_value, 2)
    if mode == "nearest_dollar":
        return round(float(round(safe_value)), 2)
    base = math.floor(safe_value)
    fractional_target = 0.99 if mode == "ending_99" else 0.95
    rounded = base + fractional_target
    if rounded < safe_value:
        rounded = base + 1 + fractional_target
    return round(rounded, 2)


def calculate_price(snapshot: DobaPriceSnapshot, current_price: float) -> PriceCalculation:
    settings = get_settings()
    supplier_cost = float(snapshot.supplier_cost or 0.0)
    shipping_cost = float(snapshot.shipping_cost or 0.0)
    handling_fee = float(snapshot.handling_fee or 0.0)
    warehouse_fee = float(snapshot.warehouse_fee or 0.0)
    estimated_total_cost = round_money(
        snapshot.estimated_total_cost or supplier_cost + shipping_cost + handling_fee + warehouse_fee
    )
    base_target = (supplier_cost * (1 + settings.price_sync_product_markup_rate)) + shipping_cost
    minimum_margin_target = estimated_total_cost * (1 + settings.price_sync_min_margin_rate)
    minimum_safe_price = round_money(max(base_target, minimum_margin_target, estimated_total_cost))
    target_price = apply_rounding(minimum_safe_price, settings.price_sync_rounding_mode)
    if current_price and abs(target_price - current_price) < settings.price_sync_min_delta_amount:
        target_price = round_money(current_price)
    return PriceCalculation(
        doba_sku=snapshot.doba_sku,
        supplier_cost=supplier_cost,
        shipping_cost=shipping_cost,
        handling_fee=handling_fee,
        warehouse_fee=warehouse_fee,
        estimated_total_cost=estimated_total_cost,
        minimum_safe_price=minimum_safe_price,
        target_price=target_price,
        rounding_mode=settings.price_sync_rounding_mode,
    )
