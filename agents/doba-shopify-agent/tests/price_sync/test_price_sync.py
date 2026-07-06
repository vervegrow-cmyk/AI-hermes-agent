from pathlib import Path

import pytest

from src.modules.price_sync import ShopifyPriceSyncService, build_price_sync_plan, run_price_sync
from src.modules.price_sync.application.service import calculate_price_metrics
from src.shared.contracts.mapping import SkuMappingRecord
from src.shared.contracts.pricing import (
    CompetitorPriceData,
    PlatformCost,
    PriceSyncCommand,
    ShippingCost,
    ShopifyPriceState,
    SupplierCost,
    WarehouseCost,
)


@pytest.fixture(autouse=True)
def _price_sync_test_env(monkeypatch):
    from shared.config.settings import get_settings

    monkeypatch.setenv("SHOPIFY_STORE", "")
    monkeypatch.setenv("SHOPIFY_SHOP", "")
    monkeypatch.setenv("SHOPIFY_SHOP_DOMAIN", "")
    monkeypatch.setenv("SHOPIFY_TOKEN", "")
    monkeypatch.setenv("SHOPIFY_ADMIN_ACCESS_TOKEN", "")
    monkeypatch.setenv("SHOPIFY_CLIENT_ID", "")
    monkeypatch.setenv("SHOPIFY_CLIENT_SECRET", "")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _command(
    *,
    supplier_cost: float = 10,
    shipping_cost: float = 3,
    warehouse_cost: float = 1,
    platform_cost: float = 2,
    current_price: float = 25,
    inventory: int = 120,
    lifecycle_stage: str = "growth",
    include_mapping: bool = True,
    competitor_low: float = 24,
    competitor_avg: float = 28,
    competitor_high: float = 32,
    supplier_sku: str = "sku-1",
) -> PriceSyncCommand:
    mappings = []
    if include_mapping:
        mappings.append(
            SkuMappingRecord(
                supplier_sku=supplier_sku,
                sku=supplier_sku,
                shopify_variant_id="gid://shopify/ProductVariant/1",
                shopify_product_id="gid://shopify/Product/1",
            ).model_dump()
        )
    return PriceSyncCommand(
        target_market="US",
        supplier_costs=[SupplierCost(supplier_sku=supplier_sku, cost=supplier_cost, updated_at="2026-06-15T00:00:00+00:00")],
        shipping_costs=[ShippingCost(supplier_sku=supplier_sku, cost=shipping_cost, updated_at="2026-06-15T00:00:00+00:00")],
        warehouse_costs=[WarehouseCost(supplier_sku=supplier_sku, cost=warehouse_cost, updated_at="2026-06-15T00:00:00+00:00")],
        platform_costs=[PlatformCost(supplier_sku=supplier_sku, cost=platform_cost, updated_at="2026-06-15T00:00:00+00:00")],
        shopify_price_states=[
            ShopifyPriceState(
                supplier_sku=supplier_sku,
                shopify_variant_id="gid://shopify/ProductVariant/1",
                current_price=current_price,
                inventory=inventory,
                lifecycle_stage=lifecycle_stage,
                updated_at="2026-06-15T00:00:00+00:00",
            )
        ],
        sku_mappings=mappings,
        competitor_prices=[
            CompetitorPriceData(
                supplier_sku=supplier_sku,
                competitor_low=competitor_low,
                competitor_avg=competitor_avg,
                competitor_high=competitor_high,
            )
        ],
        lifecycle_stages={supplier_sku: lifecycle_stage},
    )


def test_supplier_cost_true_cost_break_even_minimum_safe_recommended_and_roi_work():
    calculation = calculate_price_metrics(
        supplier_cost=SupplierCost(supplier_sku="sku-1", cost=10),
        shipping_cost=ShippingCost(supplier_sku="sku-1", cost=3),
        warehouse_cost=WarehouseCost(supplier_sku="sku-1", cost=1),
        platform_cost=PlatformCost(supplier_sku="sku-1", cost=2),
        current_price=30,
    )
    assert calculation.true_cost == 16
    assert calculation.break_even_price == 16
    assert calculation.minimum_safe_price == 20
    assert round(calculation.recommended_price, 2) == 26.67
    assert calculation.roi > 0


def test_increase_price_decision_works():
    result = run_price_sync(_command(current_price=18, inventory=40))
    assert result.decisions[0].decision == "increase_price"


def test_decrease_price_decision_works_with_inventory_and_competitor_pressure():
    result = run_price_sync(_command(current_price=40, inventory=1500, competitor_high=22, competitor_avg=21, competitor_low=20))
    assert result.decisions[0].decision == "decrease_price"


def test_clearance_price_decision_works():
    result = run_price_sync(_command(current_price=35, inventory=1800, lifecycle_stage="clearance", competitor_high=26, competitor_avg=24, competitor_low=22))
    assert result.decisions[0].decision == "clearance_price"


def test_keep_price_decision_works():
    result = run_price_sync(_command(current_price=27, inventory=120, competitor_high=30, competitor_avg=27, competitor_low=24))
    assert result.decisions[0].decision == "keep_price"


def test_manual_review_decision_works_for_critical_inventory():
    result = run_price_sync(_command(current_price=26, inventory=5))
    assert result.decisions[0].decision == "manual_review"


def test_inventory_aware_lifecycle_and_competitor_pricing_work():
    result = build_price_sync_plan(_command(current_price=35, inventory=1200, lifecycle_stage="declining", competitor_high=21, competitor_avg=20, competitor_low=19))
    decision = result.decisions[0]
    assert "inventory_high" in decision.reason_codes
    assert "lifecycle_declining" in decision.reason_codes
    assert "competitor_pressure" in decision.reason_codes


def test_sku_mapping_validation_and_missing_mapping_handling_work():
    result = run_price_sync(_command(include_mapping=False, current_price=18, inventory=40))
    assert result.records[0].status == "missing_mapping"


def test_shopify_price_update_and_log_and_batch_result_creation_work():
    result = run_price_sync(_command(current_price=18, inventory=40))
    assert result.synced_count == 1
    assert result.records[0].status == "synced"
    assert result.report.successful_syncs == 1
    assert result.report.products_processed == 1


def test_price_health_score_and_report_generation_work():
    report_path = Path("docs/audits/price-sync-report.md")
    if report_path.exists():
        report_path.unlink()
    result = run_price_sync(_command(current_price=18, inventory=40))
    assert result.decisions[0].price_health_score > 0
    assert report_path.exists()
    content = report_path.read_text(encoding="utf-8")
    assert "Price Sync Report" in content
    assert "Mode: `mock`" in content


def test_mock_mode_works():
    service = ShopifyPriceSyncService(force_mode="mock")
    result = run_price_sync(_command(current_price=18, inventory=40))
    assert service.mode == "mock"
    assert result.mock_mode is True


def test_real_adapter_works_and_no_product_publish_inventory_order_side_effects_occur():
    class FakeClient:
        def __init__(self) -> None:
            self.update_calls = 0
            self.product_create_calls = 0
            self.publish_calls = 0
            self.inventory_calls = 0
            self.order_calls = 0

        def find_variant_by_sku(self, sku: str):
            return {
                "id": "gid://shopify/ProductVariant/1",
                "product": {"id": "gid://shopify/Product/1"},
            }

        def update_variant_price(self, *, product_id: str, variant_id: str, price: float):
            self.update_calls += 1
            return {"id": variant_id, "price": price}

    service = ShopifyPriceSyncService(client=FakeClient(), force_mode="real")
    payload = service.sync_price("gid://shopify/ProductVariant/1", 29.5, "sku-1")
    assert payload["status"] == "synced"
    assert payload["new_price"] == 29.5
    assert service._client.update_calls == 1
    assert service._client.product_create_calls == 0
    assert service._client.publish_calls == 0
    assert service._client.inventory_calls == 0
    assert service._client.order_calls == 0
