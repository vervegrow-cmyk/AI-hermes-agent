from src.modules.inventory_sync.application.service import build_inventory_sync_command_from_archive
from src.modules.price_sync.application.service import build_price_sync_command_from_archive
from src.modules.risk_control.application.service import build_risk_control_command_from_archive
from src.shared.contracts import (
    InventorySnapshot,
    PriceSnapshot,
    ProductSnapshot,
    ScreeningInput,
    SellerSnapshot,
    ShopifyPublishMappingRecord,
    SupplierProduct,
)
from src.shared.repositories import LocalJsonPublishMappingRepository, LocalJsonSupplierArchiveRepository


def test_local_json_supplier_archive_repository_persists_runtime_archive(tmp_path):
    repository = LocalJsonSupplierArchiveRepository(tmp_path / "supplier_archive")
    product = SupplierProduct(supplier_id="sup-1", product_id="prod-1", sku="SKU-1", title="Chair")
    product_snapshot = ProductSnapshot(supplier_id="sup-1", product_id="prod-1", sku="SKU-1", snapshot_at="2026-06-15T00:00:00+00:00")
    inventory_snapshot = InventorySnapshot(supplier_id="sup-1", product_id="prod-1", sku="SKU-1", snapshot_at="2026-06-15T00:00:00+00:00", warehouse="United States", supplier_inventory=12)
    price_snapshot = PriceSnapshot(supplier_id="sup-1", product_id="prod-1", sku="SKU-1", snapshot_at="2026-06-15T00:00:00+00:00", supplier_cost=10.0, shipping_cost=2.0)
    seller_snapshot = SellerSnapshot(supplier_id="sup-1", snapshot_at="2026-06-15T00:00:00+00:00", seller_name="Seller A")
    screening_input = ScreeningInput(supplier_id="sup-1", product_id="prod-1", supplier_sku="SKU-1", title="Chair")

    repository.save_supplier_product(product)
    repository.save_product_snapshot(product_snapshot)
    repository.save_inventory_snapshot(inventory_snapshot)
    repository.save_price_snapshot(price_snapshot)
    repository.save_seller_snapshot(seller_snapshot)
    repository.save_screening_input(screening_input)

    assert len(repository.list_supplier_products()) == 1
    assert len(repository.list_inventory_snapshots()) == 1
    assert (tmp_path / "supplier_archive" / "supplier_products.json").exists()
    assert (tmp_path / "supplier_archive" / "inventory_snapshots.json").exists()


def test_local_json_publish_mapping_repository_persists_listing_mapping(tmp_path):
    repository = LocalJsonPublishMappingRepository(tmp_path / "listing" / "publish_mappings.json")
    record = ShopifyPublishMappingRecord(
        supplier_product_id="prod-1",
        supplier_spu_no="SPU-1",
        supplier_sku="SKU-1",
        sku_code="CODE-1",
        merge_key="merge-1",
        shopify_product_id="gid://shopify/Product/1",
        shopify_variant_id="gid://shopify/ProductVariant/1",
        shopify_handle="chair",
        status="published",
        published_at="2026-06-15T00:00:00+00:00",
        updated_at="2026-06-15T00:00:00+00:00",
    )

    repository.save_publish_mapping(record)

    mappings = repository.list_publish_mappings()
    sku_mappings = repository.list_sku_mappings()
    assert len(mappings) == 1
    assert mappings[0].shopify_product_id == "gid://shopify/Product/1"
    assert sku_mappings[0].shopify_variant_id == "gid://shopify/ProductVariant/1"
    assert (tmp_path / "listing" / "publish_mappings.json").exists()


def test_archive_builders_feed_inventory_price_and_risk_modules(tmp_path):
    repository = LocalJsonSupplierArchiveRepository(tmp_path / "archive")
    repository.save_supplier_product(SupplierProduct(supplier_id="sup-1", product_id="prod-1", sku="SKU-1", title="Chair"))
    repository.save_inventory_snapshot(
        InventorySnapshot(
            supplier_id="sup-1",
            product_id="prod-1",
            sku="SKU-1",
            snapshot_at="2026-06-15T00:00:00+00:00",
            warehouse="United States",
            supplier_inventory=12,
        )
    )
    repository.save_price_snapshot(
        PriceSnapshot(
            supplier_id="sup-1",
            product_id="prod-1",
            sku="SKU-1",
            snapshot_at="2026-06-15T00:00:00+00:00",
            supplier_cost=10.0,
            shipping_cost=2.0,
        )
    )
    repository.save_seller_snapshot(
        SellerSnapshot(
            supplier_id="sup-1",
            snapshot_at="2026-06-15T00:00:00+00:00",
            seller_name="Seller A",
        )
    )

    inventory_command = build_inventory_sync_command_from_archive(archive_repository=repository)
    price_command = build_price_sync_command_from_archive(archive_repository=repository)
    risk_command = build_risk_control_command_from_archive(archive_repository=repository)

    assert inventory_command.supplier_inventories[0].supplier_sku == "SKU-1"
    assert price_command.supplier_costs[0].supplier_sku == "SKU-1"
    assert risk_command.supplier_products[0].sku == "SKU-1"


def test_archive_builders_can_filter_to_current_supplier_skus(tmp_path):
    repository = LocalJsonSupplierArchiveRepository(tmp_path / "archive")
    repository.save_supplier_product(SupplierProduct(supplier_id="sup-1", product_id="prod-1", sku="SKU-1", title="Chair"))
    repository.save_supplier_product(SupplierProduct(supplier_id="sup-2", product_id="prod-2", sku="SKU-2", title="Desk"))
    repository.save_inventory_snapshot(
        InventorySnapshot(
            supplier_id="sup-1",
            product_id="prod-1",
            sku="SKU-1",
            snapshot_at="2026-06-15T00:00:00+00:00",
            warehouse="United States",
            supplier_inventory=12,
        )
    )
    repository.save_inventory_snapshot(
        InventorySnapshot(
            supplier_id="sup-2",
            product_id="prod-2",
            sku="SKU-2",
            snapshot_at="2026-06-15T00:00:00+00:00",
            warehouse="United States",
            supplier_inventory=20,
        )
    )
    repository.save_price_snapshot(
        PriceSnapshot(
            supplier_id="sup-1",
            product_id="prod-1",
            sku="SKU-1",
            snapshot_at="2026-06-15T00:00:00+00:00",
            supplier_cost=10.0,
            shipping_cost=2.0,
        )
    )
    repository.save_price_snapshot(
        PriceSnapshot(
            supplier_id="sup-2",
            product_id="prod-2",
            sku="SKU-2",
            snapshot_at="2026-06-15T00:00:00+00:00",
            supplier_cost=20.0,
            shipping_cost=3.0,
        )
    )
    repository.save_seller_snapshot(SellerSnapshot(supplier_id="sup-1", snapshot_at="2026-06-15T00:00:00+00:00", seller_name="Seller A"))
    repository.save_seller_snapshot(SellerSnapshot(supplier_id="sup-2", snapshot_at="2026-06-15T00:00:00+00:00", seller_name="Seller B"))

    inventory_command = build_inventory_sync_command_from_archive(archive_repository=repository, supplier_skus=["SKU-1"])
    price_command = build_price_sync_command_from_archive(archive_repository=repository, supplier_skus=["SKU-1"])
    risk_command = build_risk_control_command_from_archive(archive_repository=repository, supplier_skus=["SKU-1"])

    assert [item.supplier_sku for item in inventory_command.supplier_inventories] == ["SKU-1"]
    assert [item.supplier_sku for item in price_command.supplier_costs] == ["SKU-1"]
    assert [item.sku for item in risk_command.supplier_products] == ["SKU-1"]
    assert {item.supplier_id for item in risk_command.seller_snapshots} == {"sup-1"}
