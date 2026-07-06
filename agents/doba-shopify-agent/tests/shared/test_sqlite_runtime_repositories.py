from src.shared.contracts import InventorySnapshot, PriceSnapshot, ScreeningInput, SellerSnapshot, ShopifyPublishMappingRecord, SupplierProduct
from src.shared.repositories import SQLiteCandidatePoolRepository, SQLitePublishMappingRepository, SQLiteSupplierArchiveRepository


def test_sqlite_supplier_archive_repository_persists_and_reads_runtime_archive(tmp_path):
    repository = SQLiteSupplierArchiveRepository(
        db_path=tmp_path / "runtime.sqlite3",
        legacy_base_dir=tmp_path / "archive",
    )
    repository.save_supplier_product(SupplierProduct(supplier_id="sup-1", supplier_spu_no="SPU-1", product_id="prod-1", sku="SKU-1", title="Chair"))
    repository.save_inventory_snapshot(
        InventorySnapshot(
            supplier_id="sup-1",
            product_id="prod-1",
            sku="SKU-1",
            snapshot_at="2026-06-23T00:00:00+00:00",
            warehouse="United States",
            supplier_inventory=12,
        )
    )
    repository.save_price_snapshot(
        PriceSnapshot(
            supplier_id="sup-1",
            product_id="prod-1",
            sku="SKU-1",
            snapshot_at="2026-06-23T00:00:00+00:00",
            supplier_cost=10.0,
            shipping_cost=2.0,
        )
    )
    repository.save_seller_snapshot(
        SellerSnapshot(
            supplier_id="sup-1",
            snapshot_at="2026-06-23T00:00:00+00:00",
            seller_name="Seller A",
        )
    )
    repository.save_screening_input(
        ScreeningInput(
            supplier_id="sup-1",
            product_id="prod-1",
            supplier_sku="SKU-1",
            title="Chair",
        )
    )

    assert len(repository.list_supplier_products()) == 1
    assert len(repository.list_supplier_products_by_spu_nos(["SPU-1"])) == 1
    changed = repository.consume_changed_supplier_spu_nos()
    assert changed == ["SPU-1"]
    assert repository.consume_changed_supplier_spu_nos() == []


def test_sqlite_publish_mapping_repository_persists_mappings(tmp_path):
    repository = SQLitePublishMappingRepository(
        db_path=tmp_path / "runtime.sqlite3",
        legacy_path=tmp_path / "listing" / "publish_mappings.json",
    )
    repository.save_publish_mapping(
        ShopifyPublishMappingRecord(
            supplier_product_id="prod-1",
            supplier_spu_no="SPU-1",
            supplier_sku="SKU-1",
            shopify_product_id="gid://shopify/Product/1",
            shopify_variant_id="gid://shopify/ProductVariant/1",
            status="published",
            updated_at="2026-06-23T00:00:00+00:00",
        )
    )

    assert len(repository.list_publish_mappings()) == 1
    assert repository.list_sku_mappings()[0].shopify_variant_id == "gid://shopify/ProductVariant/1"


def test_sqlite_candidate_pool_repository_tracks_qualified_and_skipped(tmp_path):
    repository = SQLiteCandidatePoolRepository(db_path=tmp_path / "runtime.sqlite3")
    repository.upsert_entry(
        supplier_spu_no="SPU-QUALIFIED",
        supplier_product_id="prod-1",
        title="Chair",
        seller_name="Seller A",
        category_name="Furniture",
        status="qualified",
        skip_reason="",
        source_hash="hash-1",
        payload={"spu_no": "SPU-QUALIFIED", "title": "Chair"},
        updated_at="2026-06-23T00:00:00+00:00",
    )
    repository.upsert_entry(
        supplier_spu_no="SPU-SKIP",
        supplier_product_id="prod-2",
        title="Lamp",
        seller_name="Seller B",
        category_name="Lighting",
        status="skipped",
        skip_reason="missing_shopify_category",
        source_hash="hash-2",
        payload={"spu_no": "SPU-SKIP", "title": "Lamp", "category_name": "Lighting", "sku_list": ["SKU-2"]},
        updated_at="2026-06-23T00:00:00+00:00",
    )

    summary = repository.build_summary()
    assert repository.has_entries() is True
    assert len(repository.list_qualified_candidates()) == 1
    assert summary["qualified_count"] == 1
    assert summary["skipped_by_reason"]["missing_shopify_category"] == 1


def test_sqlite_runtime_repositories_support_incremental_spu_refresh(tmp_path):
    archive_repository = SQLiteSupplierArchiveRepository(
        db_path=tmp_path / "runtime.sqlite3",
        legacy_base_dir=tmp_path / "archive",
    )
    archive_repository.save_supplier_product(
        SupplierProduct(supplier_id="sup-1", supplier_spu_no="SPU-1", product_id="prod-1", sku="SKU-1", title="Chair")
    )
    archive_repository.save_supplier_product(
        SupplierProduct(supplier_id="sup-1", supplier_spu_no="SPU-2", product_id="prod-2", sku="SKU-2", title="Lamp")
    )
    assert archive_repository.count_supplier_product_groups() == 2

    candidate_repository = SQLiteCandidatePoolRepository(db_path=tmp_path / "runtime.sqlite3")
    candidate_repository.upsert_entry(
        supplier_spu_no="SPU-1",
        supplier_product_id="prod-1",
        title="Chair",
        seller_name="Seller A",
        category_name="Furniture",
        status="qualified",
        skip_reason="",
        source_hash="hash-1",
        payload={"spu_no": "SPU-1", "title": "Chair"},
        updated_at="2026-06-25T00:00:00+00:00",
    )
    candidate_repository.upsert_entry(
        supplier_spu_no="SPU-2",
        supplier_product_id="prod-2",
        title="Lamp",
        seller_name="Seller B",
        category_name="Lighting",
        status="qualified",
        skip_reason="",
        source_hash="hash-2",
        payload={"spu_no": "SPU-2", "title": "Lamp"},
        updated_at="2026-06-25T00:00:00+00:00",
    )

    candidate_repository.delete_entries_by_spu_nos(["SPU-1"])
    remaining = candidate_repository.list_candidates_by_spu_nos(["SPU-1", "SPU-2"], status="qualified")
    assert [item["spu_no"] for item in remaining] == ["SPU-2"]


def test_sqlite_supplier_archive_repository_reads_spu_batches_without_single_huge_in_clause(tmp_path):
    repository = SQLiteSupplierArchiveRepository(
        db_path=tmp_path / "runtime.sqlite3",
        legacy_base_dir=tmp_path / "archive",
    )
    for index in range(0, 1205):
        repository.save_supplier_product(
            SupplierProduct(
                supplier_id="sup-1",
                supplier_spu_no=f"SPU-{index}",
                product_id=f"prod-{index}",
                sku=f"SKU-{index}",
                title=f"Product {index}",
            )
        )

    rows = repository.list_supplier_products_by_spu_nos([f"SPU-{index}" for index in range(0, 1205)])
    assert len(rows) == 1205
