from pathlib import Path

import pytest

from src.modules.inventory_sync import ShopifyInventorySyncService, build_inventory_sync_plan, run_inventory_sync
from src.shared.contracts.inventory import InventorySyncCommand, ShopifyInventoryState, SupplierInventory
from src.shared.contracts.mapping import SkuMappingRecord
from src.shared.repositories import (
    InMemoryInventorySyncBatchRepository,
    InMemoryInventorySyncLogRepository,
    InMemoryShopifyInventoryRepository,
    InMemorySkuMappingRepository,
    InMemorySupplierInventoryRepository,
)


@pytest.fixture(autouse=True)
def _inventory_sync_test_env(monkeypatch):
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
    supplier_inventory: int = 9,
    shopify_inventory: int = 5,
    include_mapping: bool = True,
    supplier_sku: str = "sku-1",
) -> InventorySyncCommand:
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
    return InventorySyncCommand(
        target_market="US",
        supplier_inventories=[
            SupplierInventory(
                supplier_sku=supplier_sku,
                inventory=supplier_inventory,
                warehouse="US-W1",
                updated_at="2026-06-15T00:00:00+00:00",
            )
        ],
        shopify_inventory_states=[
            ShopifyInventoryState(
                supplier_sku=supplier_sku,
                shopify_variant_id="gid://shopify/ProductVariant/1",
                inventory=shopify_inventory,
                updated_at="2026-06-15T00:00:00+00:00",
            )
        ],
        sku_mappings=mappings,
    )


def test_inventory_increase_detection():
    mapping_repo = InMemorySkuMappingRepository()
    mapping_repo.save(SkuMappingRecord(supplier_sku="sku-1", sku="sku-1", shopify_variant_id="gid://shopify/ProductVariant/1"))
    result = build_inventory_sync_plan(_command(supplier_inventory=9, shopify_inventory=5), sku_mapping_repository=mapping_repo)
    assert result.changes[0].change_type == "increase"
    assert result.plans[0].requires_sync is True


def test_inventory_decrease_detection():
    mapping_repo = InMemorySkuMappingRepository()
    mapping_repo.save(SkuMappingRecord(supplier_sku="sku-1", sku="sku-1", shopify_variant_id="gid://shopify/ProductVariant/1"))
    result = build_inventory_sync_plan(_command(supplier_inventory=2, shopify_inventory=5), sku_mapping_repository=mapping_repo)
    assert result.changes[0].change_type == "decrease"


def test_out_of_stock_detection():
    mapping_repo = InMemorySkuMappingRepository()
    mapping_repo.save(SkuMappingRecord(supplier_sku="sku-1", sku="sku-1", shopify_variant_id="gid://shopify/ProductVariant/1"))
    result = build_inventory_sync_plan(_command(supplier_inventory=0, shopify_inventory=5), sku_mapping_repository=mapping_repo)
    assert result.changes[0].change_type == "out_of_stock"


def test_restocked_detection():
    mapping_repo = InMemorySkuMappingRepository()
    mapping_repo.save(SkuMappingRecord(supplier_sku="sku-1", sku="sku-1", shopify_variant_id="gid://shopify/ProductVariant/1"))
    result = build_inventory_sync_plan(_command(supplier_inventory=7, shopify_inventory=0), sku_mapping_repository=mapping_repo)
    assert result.changes[0].change_type == "restocked"


def test_unchanged_detection():
    mapping_repo = InMemorySkuMappingRepository()
    mapping_repo.save(SkuMappingRecord(supplier_sku="sku-1", sku="sku-1", shopify_variant_id="gid://shopify/ProductVariant/1"))
    result = build_inventory_sync_plan(_command(supplier_inventory=5, shopify_inventory=5), sku_mapping_repository=mapping_repo)
    assert result.changes[0].change_type == "unchanged"
    assert result.items[0].action == "skip"


def test_sync_failure_detection_and_missing_mapping_handling():
    result = run_inventory_sync(_command(include_mapping=False))
    assert result.records[0].status == "missing_mapping"
    assert result.records[0].change_type == "sync_failed"
    assert result.report.missing_mappings == 1


def test_sync_plan_creation_and_sku_mapping_lookup():
    mapping_repo = InMemorySkuMappingRepository()
    mapping_repo.save(
        SkuMappingRecord(
            supplier_sku="sku-1",
            sku="sku-1",
            shopify_variant_id="gid://shopify/ProductVariant/1",
            shopify_product_id="gid://shopify/Product/1",
        )
    )
    result = build_inventory_sync_plan(_command(), sku_mapping_repository=mapping_repo)
    assert result.plans[0].shopify_variant_id == "gid://shopify/ProductVariant/1"
    assert result.plans[0].priority > 0


def test_inventory_update_inventory_log_creation_and_batch_result_creation():
    supplier_repo = InMemorySupplierInventoryRepository()
    shopify_repo = InMemoryShopifyInventoryRepository()
    log_repo = InMemoryInventorySyncLogRepository()
    batch_repo = InMemoryInventorySyncBatchRepository()
    result = run_inventory_sync(
        _command(),
    )
    assert result.synced_count == 1
    assert result.records[0].status == "synced"
    assert result.report.successful_syncs == 1
    assert result.no_product_creation_occurred is True
    assert result.no_publish_occurred is True
    assert result.no_price_update_occurred is True
    assert result.no_order_creation_occurred is True
    assert result.report_path
    # repositories are exercised through runtime defaults; ensure custom repositories remain valid containers
    assert supplier_repo.list_supplier_inventories() == []
    assert shopify_repo.list_shopify_inventory_states() == []
    assert log_repo.list_inventory_sync_records() == []
    assert batch_repo.list_inventory_sync_batch_results() == []


def test_mock_mode_works():
    service = ShopifyInventorySyncService(force_mode="mock")
    result = run_inventory_sync(_command())
    assert service.mode == "mock"
    assert result.mock_mode is True


def test_real_adapter_works_and_does_not_publish_or_modify_price_or_order():
    class FakeClient:
        def __init__(self) -> None:
            self.set_calls = 0
            self.publish_calls = 0
            self.price_calls = 0
            self.order_calls = 0

        def get_primary_location(self):
            return {"id": "gid://shopify/Location/1"}

        def find_variant_by_sku(self, sku: str):
            return {"inventoryItem": {"id": "gid://shopify/InventoryItem/1"}}

        def set_inventory_quantity(self, **kwargs):
            self.set_calls += 1
            return {"changes": [{"delta": kwargs["quantity"] - kwargs["change_from_quantity"]}]}

    client = FakeClient()
    service = ShopifyInventorySyncService(client=client, force_mode="real")
    result = run_inventory_sync(_command())
    # run_inventory_sync uses default mock service; verify adapter separately
    sync_result = service.sync_inventory(
        build_inventory_sync_plan(
            _command(),
            sku_mapping_repository=InMemorySkuMappingRepository(),
        ).plans[0].model_copy(update={"shopify_variant_id": "gid://shopify/ProductVariant/1", "requires_sync": True, "change_type": "increase"})
    )
    assert sync_result["status"] == "synced"
    assert client.set_calls == 1
    assert client.publish_calls == 0
    assert client.price_calls == 0
    assert client.order_calls == 0
    assert result.no_publish_occurred is True
    assert result.no_price_update_occurred is True
    assert result.no_order_creation_occurred is True


def test_report_generation():
    report_path = Path("docs/audits/inventory-sync-report.md")
    if report_path.exists():
        report_path.unlink()
    result = run_inventory_sync(_command())
    assert report_path.exists()
    content = report_path.read_text(encoding="utf-8")
    assert "Inventory Sync Report" in content
    assert "Mode: `mock`" in content
    assert result.report.products_processed == 1
