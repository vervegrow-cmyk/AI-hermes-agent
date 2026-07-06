from __future__ import annotations

from dataclasses import dataclass

import bootstrap
from shared.config import get_settings


@dataclass
class ScreeningConfig:
    allowed_ship_from_countries: set[str]
    min_inventory: int
    min_margin_dollars: float
    min_margin_rate: float
    max_shipping_ratio: float
    max_delivery_days: int
    ad_buffer: float
    shopify_fee_buffer: float


def _split_csv(raw_value: str, default: list[str]) -> set[str]:
    if not raw_value.strip():
        return {item.upper() for item in default}
    return {item.strip().upper() for item in raw_value.split(",") if item.strip()}


def get_screening_config() -> ScreeningConfig:
    settings = get_settings()
    return ScreeningConfig(
        allowed_ship_from_countries=_split_csv(settings.doba_allowed_ship_from_countries, ["US", "CN", "CA"]),
        min_inventory=settings.doba_min_inventory,
        min_margin_dollars=settings.doba_min_margin_dollars,
        min_margin_rate=settings.doba_min_margin_rate,
        max_shipping_ratio=settings.doba_max_shipping_ratio,
        max_delivery_days=settings.doba_max_delivery_days,
        ad_buffer=settings.doba_ad_buffer,
        shopify_fee_buffer=settings.doba_shopify_fee_buffer,
    )
