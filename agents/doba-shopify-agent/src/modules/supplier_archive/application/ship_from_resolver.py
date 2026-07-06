from __future__ import annotations

from dataclasses import dataclass
from typing import Any


US_ALIASES = {
    "u.s.",
    "u.s.a.",
    "united states",
    "united states of america",
    "usa",
    "us",
}

UNKNOWN_ALIASES = {
    "",
    "n/a",
    "na",
    "none",
    "null",
    "unknown",
}

REGION_ID_TO_COUNTRY = {
    "US": "United States",
    "USA": "United States",
    "HK": "Hong Kong S.A.R.",
    "CN": "China",
    "CA": "Canada",
    "GB": "United Kingdom",
    "UK": "United Kingdom",
    "AU": "Australia",
    "DE": "Germany",
    "FR": "France",
    "JP": "Japan",
}


@dataclass(slots=True)
class ShipFromResolution:
    country: str
    raw: str
    source: str
    confidence: str
    is_us: bool
    region_id: str = ""
    warehouse_name: str = ""


def normalize_ship_from_country(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "UNKNOWN"
    compact = raw.lower().replace("_", " ").strip()
    if compact in UNKNOWN_ALIASES:
        return "UNKNOWN"
    if compact in US_ALIASES:
        return "United States"
    mapped = REGION_ID_TO_COUNTRY.get(raw.upper())
    if mapped:
        return mapped
    return raw


def resolve_ship_from(
    *,
    detail: dict[str, Any] | None,
    child: dict[str, Any] | None,
    shipping_cost: dict[str, Any] | None,
    stock: dict[str, Any] | None,
    stock_hint: dict[str, Any] | None,
) -> ShipFromResolution:
    detail = detail or {}
    child = child or {}
    shipping_cost = shipping_cost or {}
    stock = stock or {}
    stock_hint = stock_hint or {}

    candidates = [
        ("child.shipFrom", child.get("shipFrom"), "high"),
        ("child.shipFromCountry", child.get("shipFromCountry"), "high"),
        ("detail.shipFrom", detail.get("shipFrom"), "high"),
        ("detail.shipFromCountry", detail.get("shipFromCountry"), "high"),
        ("shipping.cost.stockRegion", shipping_cost.get("stockRegion"), "medium"),
        ("shipping.cost.country", shipping_cost.get("country"), "medium"),
        ("stock.regionName", stock.get("regionName"), "medium"),
        ("stock_hint.regionName", stock_hint.get("regionName"), "medium"),
        ("stock.regionId", stock.get("regionId"), "medium"),
        ("stock_hint.regionId", stock_hint.get("regionId"), "medium"),
    ]
    for source, raw_value, confidence in candidates:
        raw = str(raw_value or "").strip()
        normalized = normalize_ship_from_country(raw)
        if normalized != "UNKNOWN":
            return ShipFromResolution(
                country=normalized,
                raw=raw,
                source=source,
                confidence=confidence,
                is_us=normalized == "United States",
                region_id=str(stock_hint.get("regionId") or stock.get("regionId") or "").strip(),
                warehouse_name=str(
                    shipping_cost.get("warehouseName")
                    or stock.get("warehouseName")
                    or stock_hint.get("warehouseName")
                    or ""
                ).strip(),
            )
    return ShipFromResolution(
        country="UNKNOWN",
        raw="",
        source="unknown",
        confidence="low",
        is_us=False,
        region_id=str(stock_hint.get("regionId") or stock.get("regionId") or "").strip(),
        warehouse_name=str(
            shipping_cost.get("warehouseName")
            or stock.get("warehouseName")
            or stock_hint.get("warehouseName")
            or ""
        ).strip(),
    )
