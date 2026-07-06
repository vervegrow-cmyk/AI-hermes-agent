from src.modules.supplier_archive.application.ship_from_resolver import (
    normalize_ship_from_country,
    resolve_ship_from,
)


def test_normalize_ship_from_country_standardizes_us_aliases():
    assert normalize_ship_from_country("US") == "United States"
    assert normalize_ship_from_country("usa") == "United States"
    assert normalize_ship_from_country("United States of America") == "United States"


def test_resolve_ship_from_prefers_child_ship_from_over_lower_priority_fields():
    resolution = resolve_ship_from(
        detail={"shipFrom": "Canada"},
        child={"shipFrom": "US"},
        shipping_cost={"stockRegion": "HK"},
        stock={"regionName": "Hong Kong S.A.R.", "regionId": "HK"},
        stock_hint={"regionName": "Hong Kong S.A.R.", "regionId": "HK"},
    )

    assert resolution.country == "United States"
    assert resolution.raw == "US"
    assert resolution.source == "child.shipFrom"
    assert resolution.confidence == "high"
    assert resolution.is_us is True


def test_resolve_ship_from_falls_back_to_shipping_then_stock_region():
    resolution = resolve_ship_from(
        detail={},
        child={},
        shipping_cost={"stockRegion": "HK", "warehouseName": "HK Warehouse"},
        stock={"regionName": "Hong Kong S.A.R.", "regionId": "HK"},
        stock_hint={"regionName": "Hong Kong S.A.R.", "regionId": "HK"},
    )

    assert resolution.country == "Hong Kong S.A.R."
    assert resolution.raw == "HK"
    assert resolution.source == "shipping.cost.stockRegion"
    assert resolution.warehouse_name == "HK Warehouse"
