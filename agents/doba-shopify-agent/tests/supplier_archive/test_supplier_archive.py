from pathlib import Path
from unittest.mock import Mock, patch

import httpx

from shared.clients.doba import DobaAPIError
from src.app.runners.run_supplier_archive_online import _print_doba_connectivity_hint
from src.modules.supplier_archive import archive_supplier_products
from src.modules.supplier_archive.application.online_archive_runtime import run_doba_online_archive
from src.modules.supplier_archive.application.service import build_screening_input
from src.modules.supplier_archive.infrastructure.supplier_adapters.mock_doba import load_mock_doba_products
from src.modules.supplier_archive.runners.archive import run_supplier_archive
from src.shared.contracts import DobaProductInput
from src.shared.repositories import InMemorySupplierArchiveRepository, LocalJsonSupplierArchiveRepository, SQLiteSupplierArchiveRepository


def test_print_doba_connectivity_hint_for_whitelist_failure(capsys):
    _print_doba_connectivity_hint(
        DobaAPIError(
            status_code=403,
            path="/api/platform/list",
            response_code="999999",
            response_message="IP whitelist check failed",
            response_text='{"responseCode":"999999","responseMessage":"IP whitelist check failed"}',
        )
    )

    captured = capsys.readouterr().out
    assert '"error_type": "doba_api_error"' in captured
    assert '"response_message": "IP whitelist check failed"' in captured


def test_print_doba_connectivity_hint_for_connect_error(capsys):
    _print_doba_connectivity_hint(httpx.ConnectError("[WinError 10013] blocked"))

    captured = capsys.readouterr().out
    assert '"error_type": "network_connect_error"' in captured
    assert 'WinError 10013' in captured


def test_supplier_archive_persists_all_snapshot_types():
    repository = InMemorySupplierArchiveRepository()
    result = archive_supplier_products(load_mock_doba_products(), repository)

    assert result.archived_products == 2
    assert result.product_snapshots == 2
    assert result.inventory_snapshots == 2
    assert result.price_snapshots == 2
    assert result.seller_snapshots == 2
    assert result.screening_inputs == 2
    assert len(repository.list_supplier_products()) == 2
    assert len(repository.list_product_snapshots()) == 2
    assert len(repository.list_inventory_snapshots()) == 2
    assert len(repository.list_price_snapshots()) == 2
    assert len(repository.list_seller_snapshots()) == 2
    assert len(repository.list_screening_inputs()) == 2


def test_supplier_archive_skips_invalid_products():
    repository = InMemorySupplierArchiveRepository()
    products = load_mock_doba_products() + [DobaProductInput(supplier_id="sup-x", product_id="", sku="")]
    result = archive_supplier_products(products, repository)

    assert result.archived_products == 2
    assert result.skipped_products == 1
    assert result.warnings


def test_archived_product_can_generate_screening_input_without_ai_or_listing():
    repository = InMemorySupplierArchiveRepository()
    archive_supplier_products(load_mock_doba_products(), repository)

    supplier_product = repository.list_supplier_products()[0]
    screening_input = build_screening_input(
        supplier_product=supplier_product,
        product_snapshots=[repository.list_product_snapshots()[0]],
        inventory_snapshots=[repository.list_inventory_snapshots()[0]],
        price_snapshots=[repository.list_price_snapshots()[0]],
        seller_snapshots=[repository.list_seller_snapshots()[0]],
    )

    assert screening_input.inventory == repository.list_inventory_snapshots()[0].supplier_inventory
    assert screening_input.price == repository.list_price_snapshots()[0].supplier_cost
    assert screening_input.warehouse == repository.list_inventory_snapshots()[0].warehouse
    assert screening_input.snapshot_history.inventory_stability == "stable"
    assert screening_input.snapshot_history.price_change_7d == 0
    assert screening_input.snapshot_history.seller_rating_change_30d == 0
    assert not hasattr(screening_input, "ai_score")
    assert not hasattr(screening_input, "listing_candidate")


def test_screening_input_contains_inventory_price_seller_warehouse_and_snapshot_summary():
    repository = InMemorySupplierArchiveRepository()
    archive_supplier_products(load_mock_doba_products(), repository)

    screening_input = repository.list_screening_inputs()[0]

    assert screening_input.inventory > 0
    assert screening_input.price > 0
    assert screening_input.seller_rating == 0
    assert screening_input.warehouse == "US"
    assert screening_input.snapshot_history.inventory_snapshots == 1
    assert screening_input.snapshot_history.price_snapshots == 1
    assert screening_input.snapshot_history.seller_snapshots == 1


def test_supplier_archive_persists_rich_doba_archive_fields():
    repository = InMemorySupplierArchiveRepository()
    products = [
        DobaProductInput(
            supplier_id="sup-1",
            supplier_spu_no="SPU-1",
            product_id="prod-1",
            sku="ITEM-1",
            sku_code="SKU-CODE-1",
            sku_id="SKU-ID-1",
            item_no="ITEM-1",
            title="Patio Chair",
            brand="Doba Basics",
            category_id="cat-1",
            category_name="Outdoor Furniture",
            category_path="Outdoor > Furniture",
            source_vendor="DOBA",
            source_channels=["Inbox", "Shop", "Pinterest", "Facebook & Instagram"],
            cost=50,
            msrp=80,
            inventory=16,
            ship_from_country="United States",
            ship_from_raw="US",
            ship_from_source="child.shipFrom",
            ship_from_confidence="high",
            warehouse_name="California Warehouse",
            ships_to_countries=["US"],
            shipping_cost=8,
            delivery_days=4,
            description="Patio chair.",
            image_urls=["https://cdn.example.com/chair.jpg"],
            variant_attributes={"Color": "Black"},
            category_metafields={"doba_category_id": "cat-1", "doba_category_name": "Outdoor Furniture"},
            seller_name="DOBA Seller",
            seller_info={"supplierName": "DOBA Seller"},
            warehouse_info={"warehouse_name": "California Warehouse"},
            attributes={"vendor": "DOBA"},
        )
    ]

    archive_supplier_products(products, repository)

    supplier_product = repository.list_supplier_products()[0]
    inventory_snapshot = repository.list_inventory_snapshots()[0]
    price_snapshot = repository.list_price_snapshots()[0]
    product_snapshot = repository.list_product_snapshots()[0]
    screening_input = repository.list_screening_inputs()[0]

    assert supplier_product.supplier_spu_no == "SPU-1"
    assert supplier_product.category_id == "cat-1"
    assert supplier_product.source_vendor == "DOBA"
    assert supplier_product.source_channels == ["Inbox", "Shop", "Pinterest", "Facebook & Instagram"]
    assert supplier_product.seller_name == "DOBA Seller"
    assert supplier_product.ship_from_source == "child.shipFrom"
    assert supplier_product.ship_from_confidence == "high"
    assert inventory_snapshot.ship_from_country == "United States"
    assert inventory_snapshot.warehouse_name == "California Warehouse"
    assert price_snapshot.true_cost == 58
    assert product_snapshot.category_metafields["doba_category_id"] == "cat-1"
    assert screening_input.ship_from_country == "United States"


def test_supplier_archive_runner_returns_archive_result():
    result = run_supplier_archive()
    assert result.supplier_name == "doba"
    assert result.archived_products == 2
    assert result.screening_inputs == 2
    assert Path(result.report_path).exists()


def test_run_doba_online_archive_persists_local_archive_and_checkpoint(tmp_path):
    report_path = tmp_path / "online-archive-report.json"
    checkpoint_path = tmp_path / "online-archive-checkpoint.json"
    archive_repository = SQLiteSupplierArchiveRepository(
        db_path=tmp_path / "runtime.sqlite3",
        legacy_base_dir=tmp_path / "supplier_archive",
    )
    detail = {
        "spuId": "spu-1",
        "spuNo": "D0100ONLINE001",
        "busiId": "seller-1",
        "sellerName": "Seller A",
        "title": "Patio Storage Bench",
        "cateId": "cat-1",
        "cateName": "Outdoor Furniture",
        "goodsDesc": "<p>Bench</p>",
        "brand": "Doba Basics",
        "pictureUrl": "https://cdn.example.com/bench.jpg",
        "availableRegions": [{"regionId": "US"}],
        "children": [
            {
                "skuId": "sku-id-1",
                "skuCode": "SKU-1",
                "skuPicList": ["https://cdn.example.com/bench-red.jpg"],
                "variantProps": [{"propName": "Color", "propValue": "Red"}],
                "stocks": [{"regionId": "US", "regionName": "United States", "itemNo": "ITEM-1", "availableNum": 14}],
            }
        ],
    }

    with patch("src.modules.supplier_archive.application.online_archive_runtime.SQLiteSupplierArchiveRepository", return_value=archive_repository):
        with patch("src.modules.supplier_archive.application.online_archive_runtime.DobaClient.from_settings", return_value=object()):
            with patch("src.modules.supplier_archive.application.online_archive_runtime._fetch_platform_id", return_value="platform-1"):
                with patch(
                    "src.modules.supplier_archive.application.online_archive_runtime._fetch_spu_page",
                    side_effect=[(1, [{"spuId": "spu-1", "spuNo": "D0100ONLINE001", "title": "Patio Storage Bench"}]), (1, [])],
                ):
                    with patch(
                        "src.modules.supplier_archive.application.online_archive_runtime._fetch_spu_details",
                        return_value={"D0100ONLINE001": detail},
                    ):
                        with patch(
                            "src.modules.supplier_archive.application.online_archive_runtime._fetch_stock_map",
                            return_value={"ITEM-1": {"itemNo": "ITEM-1", "sellingPrice": "49.99", "msrpPrice": "79.99", "availableNum": 14}},
                        ):
                            with patch(
                                "src.modules.supplier_archive.application.online_archive_runtime._fetch_shipping_map",
                                return_value={"ITEM-1": {"cost": {"shipFee": 5, "shipTime": "3-5", "shipName": "Ground", "stockRegion": "US"}}},
                            ):
                                with patch(
                                    "src.modules.supplier_archive.application.online_archive_runtime._fetch_seller_info",
                                    return_value={"supplierName": "Seller A"},
                                ):
                                    result = run_doba_online_archive(
                                        report_path=str(report_path),
                                        checkpoint_path=str(checkpoint_path),
                                        page_size=20,
                                        target_country="US",
                                        resume=False,
                                    )

    assert result["completed"] is True
    assert result["progress"]["processed_spu"] == 1
    assert result["progress"]["archived_sku"] == 1
    assert result["ship_from_summary"]["us"] == 1
    assert checkpoint_path.exists()
    assert report_path.exists()
    assert len(archive_repository.list_supplier_products()) == 1
    assert archive_repository.list_supplier_products()[0].supplier_spu_no == "D0100ONLINE001"


def test_run_doba_online_archive_resumes_from_variant_checkpoint(tmp_path):
    report_path = tmp_path / "online-archive-report.json"
    checkpoint_path = tmp_path / "online-archive-checkpoint.json"
    archive_repository = SQLiteSupplierArchiveRepository(
        db_path=tmp_path / "runtime.sqlite3",
        legacy_base_dir=tmp_path / "supplier_archive",
    )
    checkpoint_path.write_text(
        """
{
  "started_at": "2026-06-17T00:00:00+00:00",
  "updated_at": "2026-06-17T00:00:00+00:00",
  "completed": false,
  "report_path": "",
  "checkpoint_path": "",
  "resume_command": "",
  "config": {
    "page_size": 20,
    "target_country": "US",
    "min_inventory": null
  },
  "progress": {
    "total_spu": 1,
    "processed_spu": 0,
    "archived_sku": 1,
    "skipped_spu": 0,
    "page_number": 1,
    "index_in_page": 0,
    "variant_index": 1
  },
  "warnings": [],
  "last_event": {}
}
""".strip(),
        encoding="utf-8",
    )
    detail = {
        "spuId": "spu-1",
        "spuNo": "D0100ONLINE001",
        "busiId": "seller-1",
        "sellerName": "Seller A",
        "title": "Patio Storage Bench",
        "cateId": "cat-1",
        "cateName": "Outdoor Furniture",
        "goodsDesc": "<p>Bench</p>",
        "brand": "Doba Basics",
        "pictureUrl": "https://cdn.example.com/bench.jpg",
        "availableRegions": [{"regionId": "US"}],
        "children": [
            {
                "skuId": "sku-id-1",
                "skuCode": "SKU-1",
                "skuPicList": ["https://cdn.example.com/bench-red.jpg"],
                "variantProps": [{"propName": "Color", "propValue": "Red"}],
                "stocks": [{"regionId": "US", "regionName": "United States", "itemNo": "ITEM-1", "availableNum": 14}],
            },
            {
                "skuId": "sku-id-2",
                "skuCode": "SKU-2",
                "skuPicList": ["https://cdn.example.com/bench-blue.jpg"],
                "variantProps": [{"propName": "Color", "propValue": "Blue"}],
                "stocks": [{"regionId": "US", "regionName": "United States", "itemNo": "ITEM-2", "availableNum": 18}],
            },
        ],
    }

    with patch("src.modules.supplier_archive.application.online_archive_runtime.SQLiteSupplierArchiveRepository", return_value=archive_repository):
        with patch("src.modules.supplier_archive.application.online_archive_runtime.DobaClient.from_settings", return_value=object()):
            with patch("src.modules.supplier_archive.application.online_archive_runtime._fetch_platform_id", return_value="platform-1"):
                with patch(
                    "src.modules.supplier_archive.application.online_archive_runtime._fetch_spu_page",
                    side_effect=[(1, [{"spuId": "spu-1", "spuNo": "D0100ONLINE001", "title": "Patio Storage Bench"}]), (1, [])],
                ):
                    with patch(
                        "src.modules.supplier_archive.application.online_archive_runtime._fetch_spu_details",
                        return_value={"D0100ONLINE001": detail},
                    ):
                        with patch(
                            "src.modules.supplier_archive.application.online_archive_runtime._fetch_stock_map",
                            return_value={
                                "ITEM-1": {"itemNo": "ITEM-1", "sellingPrice": "49.99", "msrpPrice": "79.99", "availableNum": 14},
                                "ITEM-2": {"itemNo": "ITEM-2", "sellingPrice": "54.99", "msrpPrice": "89.99", "availableNum": 18},
                            },
                        ):
                            with patch(
                                "src.modules.supplier_archive.application.online_archive_runtime._fetch_shipping_map",
                                return_value={
                                    "ITEM-1": {"cost": {"shipFee": 5, "shipTime": "3-5", "shipName": "Ground", "stockRegion": "US"}},
                                    "ITEM-2": {"cost": {"shipFee": 7, "shipTime": "3-5", "shipName": "Ground", "stockRegion": "US"}},
                                },
                            ):
                                with patch(
                                    "src.modules.supplier_archive.application.online_archive_runtime._fetch_seller_info",
                                    return_value={"supplierName": "Seller A"},
                                ):
                                    result = run_doba_online_archive(
                                        report_path=str(report_path),
                                        checkpoint_path=str(checkpoint_path),
                                        page_size=20,
                                        target_country="US",
                                        resume=True,
                                    )

    assert result["completed"] is True
    assert result["progress"]["processed_spu"] == 1
    assert result["progress"]["archived_sku"] == 2
    assert len(archive_repository.list_supplier_products()) == 1
    assert archive_repository.list_supplier_products()[0].sku == "ITEM-2"


def test_run_doba_online_archive_archive_eligible_only_filters_non_us_and_low_inventory(tmp_path):
    report_path = tmp_path / "online-archive-report.json"
    checkpoint_path = tmp_path / "online-archive-checkpoint.json"
    archive_repository = SQLiteSupplierArchiveRepository(
        db_path=tmp_path / "runtime.sqlite3",
        legacy_base_dir=tmp_path / "supplier_archive",
    )
    detail = {
        "spuId": "spu-1",
        "spuNo": "D0100ONLINE001",
        "busiId": "seller-1",
        "sellerName": "Seller A",
        "title": "Mixed Variants Product",
        "cateId": "cat-1",
        "cateName": "Outdoor Furniture",
        "goodsDesc": "<p>Bench</p>",
        "brand": "Doba Basics",
        "pictureUrl": "https://cdn.example.com/bench.jpg",
        "availableRegions": [{"regionId": "US"}],
        "children": [
            {
                "skuId": "sku-id-1",
                "skuCode": "SKU-1",
                "skuPicList": ["https://cdn.example.com/bench-red.jpg"],
                "variantProps": [{"propName": "Color", "propValue": "Red"}],
                "stocks": [{"regionId": "US", "regionName": "United States", "itemNo": "ITEM-1", "availableNum": 14}],
                "shipFrom": "United States",
            },
            {
                "skuId": "sku-id-2",
                "skuCode": "SKU-2",
                "skuPicList": ["https://cdn.example.com/bench-blue.jpg"],
                "variantProps": [{"propName": "Color", "propValue": "Blue"}],
                "stocks": [{"regionId": "US", "regionName": "Hong Kong S.A.R.", "itemNo": "ITEM-2", "availableNum": 30}],
                "shipFrom": "Hong Kong S.A.R.",
            },
            {
                "skuId": "sku-id-3",
                "skuCode": "SKU-3",
                "skuPicList": ["https://cdn.example.com/bench-green.jpg"],
                "variantProps": [{"propName": "Color", "propValue": "Green"}],
                "stocks": [{"regionId": "US", "regionName": "United States", "itemNo": "ITEM-3", "availableNum": 6}],
                "shipFrom": "United States",
            },
        ],
    }

    with patch("src.modules.supplier_archive.application.online_archive_runtime.SQLiteSupplierArchiveRepository", return_value=archive_repository):
        with patch("src.modules.supplier_archive.application.online_archive_runtime.DobaClient.from_settings", return_value=object()):
            with patch("src.modules.supplier_archive.application.online_archive_runtime._fetch_platform_id", return_value="platform-1"):
                with patch(
                    "src.modules.supplier_archive.application.online_archive_runtime._fetch_spu_page",
                    side_effect=[(1, [{"spuId": "spu-1", "spuNo": "D0100ONLINE001", "title": "Mixed Variants Product"}]), (1, [])],
                ):
                    with patch(
                        "src.modules.supplier_archive.application.online_archive_runtime._fetch_spu_details",
                        return_value={"D0100ONLINE001": detail},
                    ):
                        with patch(
                            "src.modules.supplier_archive.application.online_archive_runtime._fetch_stock_map",
                            return_value={
                                "ITEM-1": {"itemNo": "ITEM-1", "sellingPrice": "49.99", "msrpPrice": "79.99", "availableNum": 14, "regionName": "United States"},
                                "ITEM-2": {"itemNo": "ITEM-2", "sellingPrice": "54.99", "msrpPrice": "89.99", "availableNum": 30, "regionName": "Hong Kong S.A.R."},
                                "ITEM-3": {"itemNo": "ITEM-3", "sellingPrice": "19.99", "msrpPrice": "29.99", "availableNum": 6, "regionName": "United States"},
                            },
                        ):
                            with patch(
                                "src.modules.supplier_archive.application.online_archive_runtime._fetch_shipping_map",
                                return_value={
                                    "ITEM-1": {"cost": {"shipFee": 5, "shipTime": "3-5", "shipName": "Ground", "stockRegion": "US"}},
                                    "ITEM-2": {"cost": {"shipFee": 7, "shipTime": "3-5", "shipName": "Ground", "stockRegion": "HK"}},
                                    "ITEM-3": {"cost": {"shipFee": 3, "shipTime": "3-5", "shipName": "Ground", "stockRegion": "US"}},
                                },
                            ):
                                with patch(
                                    "src.modules.supplier_archive.application.online_archive_runtime._fetch_seller_info",
                                    return_value={"supplierName": "Seller A"},
                                ):
                                    result = run_doba_online_archive(
                                        report_path=str(report_path),
                                        checkpoint_path=str(checkpoint_path),
                                        page_size=20,
                                        target_country="US",
                                        archive_eligible_only=True,
                                        eligible_inventory_threshold=10,
                                        resume=False,
                                    )

    assert result["completed"] is True
    assert result["progress"]["processed_spu"] == 1
    assert result["progress"]["eligible_spu"] == 1
    assert result["progress"]["eligible_sku"] == 1
    assert result["progress"]["filtered_sku"] == 2
    assert result["progress"]["archived_sku"] == 1
    assert result["ship_from_summary"]["us"] == 2
    assert result["ship_from_summary"]["non_us"] == 1
    archived_products = archive_repository.list_supplier_products()
    assert len(archived_products) == 1
    assert archived_products[0].sku == "ITEM-1"


def test_run_doba_online_archive_stops_cleanly_on_doba_whitelist_failure(tmp_path):
    report_path = tmp_path / "online-archive-report.json"
    checkpoint_path = tmp_path / "online-archive-checkpoint.json"
    archive_repository = SQLiteSupplierArchiveRepository(
        db_path=tmp_path / "runtime.sqlite3",
        legacy_base_dir=tmp_path / "supplier_archive",
    )

    with patch("src.modules.supplier_archive.application.online_archive_runtime.SQLiteSupplierArchiveRepository", return_value=archive_repository):
        with patch("src.modules.supplier_archive.application.online_archive_runtime.DobaClient.from_settings", return_value=object()):
            with patch("src.modules.supplier_archive.application.online_archive_runtime._fetch_platform_id", return_value="platform-1"):
                with patch(
                    "src.modules.supplier_archive.application.online_archive_runtime._fetch_spu_page",
                    side_effect=DobaAPIError(
                        status_code=403,
                        path="/api/goods/doba/spu/list",
                        response_code="999999",
                        response_message="IP whitelist check failed",
                        response_text='{"responseCode":"999999","responseMessage":"IP whitelist check failed"}',
                    ),
                ):
                    result = run_doba_online_archive(
                        report_path=str(report_path),
                        checkpoint_path=str(checkpoint_path),
                        page_size=20,
                        target_country="US",
                        resume=False,
                    )

    assert result["completed"] is False
    assert result["stopped_reason"] == "doba_ip_whitelist_check_failed"
    assert result["last_failure"]["response_message"] == "IP whitelist check failed"
    assert result["last_failure"]["resume_position"] == {
        "page_number": 1,
        "index_in_page": 0,
        "variant_index": 0,
    }
    assert checkpoint_path.exists()
    assert report_path.exists()


def test_run_doba_online_archive_stops_cleanly_on_platform_list_whitelist_failure(tmp_path):
    report_path = tmp_path / "online-archive-report.json"
    checkpoint_path = tmp_path / "online-archive-checkpoint.json"
    archive_repository = SQLiteSupplierArchiveRepository(
        db_path=tmp_path / "runtime.sqlite3",
        legacy_base_dir=tmp_path / "supplier_archive",
    )

    with patch("src.modules.supplier_archive.application.online_archive_runtime.SQLiteSupplierArchiveRepository", return_value=archive_repository):
        with patch("src.modules.supplier_archive.application.online_archive_runtime.DobaClient.from_settings", return_value=object()):
            with patch(
                "src.modules.supplier_archive.application.online_archive_runtime._fetch_platform_id",
                side_effect=DobaAPIError(
                    status_code=403,
                    path="/api/platform/list",
                    response_code="999999",
                    response_message="IP whitelist check failed",
                    response_text='{"responseCode":"999999","responseMessage":"IP whitelist check failed"}',
                ),
            ):
                result = run_doba_online_archive(
                    report_path=str(report_path),
                    checkpoint_path=str(checkpoint_path),
                    page_size=20,
                    target_country="US",
                    resume=False,
                )

    assert result["completed"] is False
    assert result["stopped_reason"] == "doba_ip_whitelist_check_failed"
    assert result["last_failure"]["path"] == "/api/platform/list"
    assert result["last_failure"]["response_message"] == "IP whitelist check failed"
    assert result["last_failure"]["resume_position"] == {
        "page_number": 1,
        "index_in_page": 0,
        "variant_index": 0,
    }
