from pathlib import Path
from unittest.mock import Mock, patch
import json

from src.modules.shopify_listing.application.live_publish_runtime import (
    SOURCE_VENDOR_NAME,
    DobaProductCandidate,
    DobaVariantCandidate,
    _build_archive_product_candidate,
    _build_archive_inputs_from_detail,
    _build_result_payload,
    _build_merge_key,
    _build_category_search_candidates,
    _build_product_input,
    _build_product_candidate,
    _normalize_option_name,
    _normalize_option_values,
    _configure_doba_client,
    _doba_trust_env_enabled,
    _diversify_candidate_pool_candidates,
    _derive_shopify_sale_price,
    _fetch_spu_page,
    _load_published_spu_nos,
    _candidate_runtime_policy_reason,
    _publish_candidate_to_shopify,
    _resolve_shopify_category,
    _set_product_metafields,
    _serialize_candidate,
    _set_variant_inventory,
    _update_or_create_variants,
    _update_product_basics,
    build_doba_publish_candidate_pool,
    publish_doba_products_live,
)
from src.modules.shopify_listing.application.content_enrichment import build_candidate_enrichment
from src.modules.shopify_listing.runners.publish_vendor_catalog import CategoryResolution
from src.shared.contracts.supplier_archive import SupplierProduct
from src.shared.repositories import SQLiteCandidatePoolRepository


def test_doba_trust_env_enabled_defaults_to_true(monkeypatch):
    monkeypatch.delenv("DOBA_TRUST_ENV", raising=False)
    assert _doba_trust_env_enabled() is True


def test_doba_trust_env_enabled_honors_false_values(monkeypatch):
    for value in ("0", "false", "False", "no", "off"):
        monkeypatch.setenv("DOBA_TRUST_ENV", value)
        assert _doba_trust_env_enabled() is False


def test_configure_doba_client_sets_trust_env(monkeypatch):
    monkeypatch.setenv("DOBA_TRUST_ENV", "false")
    client = Mock(trust_env=True)

    configured = _configure_doba_client(client)

    assert configured is client
    assert client.trust_env is False


def test_diversify_candidate_pool_candidates_avoids_same_category_and_seller_streaks():
    candidates = [
        {"spu_no": "GPS-1", "category_name": "Tracking Devices", "seller_name": "Green Market"},
        {"spu_no": "GPS-2", "category_name": "Tracking Devices", "seller_name": "Green Market"},
        {"spu_no": "HOME-1", "category_name": "Home Decor", "seller_name": "Home Life Boutique"},
        {"spu_no": "GPS-3", "category_name": "Tracking Devices", "seller_name": "Green Market"},
        {"spu_no": "PATIO-1", "category_name": "Patio Chairs", "seller_name": "South Depot"},
    ]

    diversified = _diversify_candidate_pool_candidates(candidates)

    assert [item["spu_no"] for item in diversified] == [
        "GPS-1",
        "HOME-1",
        "GPS-2",
        "PATIO-1",
        "GPS-3",
    ]


def test_candidate_runtime_policy_reason_blocks_green_market_and_tracking_devices_by_default():
    assert _candidate_runtime_policy_reason(
        seller_name="Green Market",
        category_name="Patio Chairs",
    ) == "seller_in_blocklist"
    assert _candidate_runtime_policy_reason(
        seller_name="Home Life Boutique",
        category_name="Tracking Devices",
    ) == "category_in_blocklist"


def test_build_product_candidate_merges_variants_and_calculates_costs():
    detail = {
        "spuId": "spu-1",
        "spuNo": "SPU-1",
        "busiId": "seller-1",
        "sellerName": "Seller A",
        "title": "Patio Storage Bench",
        "cateName": "Outdoor Furniture",
        "goodsDesc": "<p>Outdoor storage bench.</p>",
        "brand": "Doba Basics",
        "pictureUrl": "https://cdn.example.com/main.jpg",
        "children": [
            {
                "skuId": "sku-id-1",
                "skuCode": "sku-code-1",
                "skuPicList": ["https://cdn.example.com/red.jpg"],
                "variantProps": [{"propName": "Color", "propValue": "Red"}],
                "stocks": [{"regionId": "US", "itemNo": "ITEM-1", "availableNum": 14}],
            },
            {
                "skuId": "sku-id-2",
                "skuCode": "sku-code-2",
                "skuPicList": ["https://cdn.example.com/blue.jpg"],
                "variantProps": [{"propName": "Color", "propValue": "Blue"}],
                "stocks": [{"regionId": "US", "itemNo": "ITEM-2", "availableNum": 22}],
            },
        ],
    }
    stock_map = {
        "ITEM-1": {"itemNo": "ITEM-1", "sellingPrice": "49.99", "msrpPrice": "79.99", "availableNum": 14},
        "ITEM-2": {"itemNo": "ITEM-2", "sellingPrice": "54.99", "msrpPrice": "89.99", "availableNum": 22},
    }
    shipping_map = {
        "ITEM-1": {"cost": {"shipFee": 5, "shipName": "Ground", "shipTime": "3-7"}},
        "ITEM-2": {"cost": {"shipFee": 7, "shipName": "Ground", "shipTime": "4-9"}},
    }

    candidate, skip_reason = _build_product_candidate(
        detail=detail,
        stock_map=stock_map,
        shipping_map=shipping_map,
        seller_info={"supplierName": "Seller A"},
        inventory_threshold=10,
        target_country="US",
    )

    assert skip_reason is None
    assert candidate is not None
    assert candidate.spu_no == "SPU-1"
    assert len(candidate.variants) == 2
    assert [variant.sku for variant in candidate.variants] == ["ITEM-1", "ITEM-2"]
    assert candidate.variants[0].cost_price == 54.99
    assert candidate.variants[1].cost_price == 61.99
    assert candidate.variants[0].sale_price == 62.49
    assert candidate.variants[1].sale_price == 70.24


def test_normalize_option_values_folds_case_variants_into_single_option_name():
    normalized = _normalize_option_values(
        {
            "COLOR": "RED",
            "Color": "Red",
            "color": "red",
            "MATERIAL_TYPE": "Steel",
        }
    )

    assert normalized == {
        "Color": "RED",
        "Material Type": "Steel",
    }


def test_build_product_candidate_normalizes_duplicate_option_names_from_variant_props():
    detail = {
        "spuId": "spu-dup-1",
        "spuNo": "SPU-DUP-1",
        "busiId": "seller-1",
        "sellerName": "Seller A",
        "title": "Portable Music Stand Red",
        "cateName": "General Electronics",
        "goodsDesc": "<p>Portable music stand.</p>",
        "brand": "Doba Basics",
        "pictureUrl": "https://cdn.example.com/main.jpg",
        "children": [
            {
                "skuId": "sku-id-1",
                "skuCode": "MUS-FLD-RED",
                "skuPicList": ["https://cdn.example.com/red.jpg"],
                "variantProps": [
                    {"propName": "COLOR", "propValue": "RED"},
                    {"propName": "Color", "propValue": "Red"},
                ],
                "stocks": [{"regionId": "US", "itemNo": "ITEM-1", "availableNum": 18}],
            }
        ],
    }
    stock_map = {
        "ITEM-1": {"itemNo": "ITEM-1", "sellingPrice": "13.54", "msrpPrice": "20.00", "availableNum": 18},
    }
    shipping_map = {
        "ITEM-1": {"cost": {"shipFee": 0, "shipName": "Ground", "shipTime": "3-7"}},
    }

    candidate, skip_reason = _build_product_candidate(
        detail=detail,
        stock_map=stock_map,
        shipping_map=shipping_map,
        seller_info={"supplierName": "Seller A"},
        inventory_threshold=10,
        target_country="US",
    )

    assert skip_reason is None
    assert candidate is not None
    assert candidate.variants[0].option_values == {"Color": "RED"}


def test_build_product_input_deduplicates_product_option_names():
    candidate = DobaProductCandidate(
        spu_id="spu-opt-1",
        spu_no="SPU-OPT-1",
        supplier_id="seller-1",
        category_id="cat-1",
        merge_key="merge-opt-1",
        seller_name="Seller A",
        seller_info={},
        title="Portable Music Stand",
        category_name="General Electronics",
        description_html="<p>Portable music stand.</p>",
        brand="Doba Basics",
        ship_from_country="United States",
        processing_time=3,
        store_url="",
        image_urls=["https://cdn.example.com/main.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-1",
                sku_code="MUS-FLD-RED",
                sku_id="sku-id-1",
                option_values={"COLOR": "RED", "Color": "Red"},
                inventory=18,
                source_price=13.54,
                shipping_cost=0.0,
                cost_price=13.54,
                sale_price=15.57,
                compare_at_price=20.0,
                ship_time_days=5,
                item_no="ITEM-1",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/red.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    payload = _build_product_input(candidate)

    assert payload["productOptions"] == [
        {
            "name": "Color",
            "values": [{"name": "RED"}],
        }
    ]


def test_build_archive_product_candidate_skips_zero_cost_variants():
    products = [
        SupplierProduct(
            supplier_id="seller-1",
            supplier_spu_no="SPU-1",
            product_id="prod-1",
            sku="SKU-OK",
            sku_code="CODE-OK",
            item_no="SKU-OK",
            title="Travel Set",
            category_id="cat-1",
            category_name="Travel Accessories",
            category_path="Travel Accessories",
            seller_name="North Home",
            inventory=30,
            cost=50.0,
            shipping_cost=5.0,
            msrp=80.0,
            ship_from_country="United States",
            ship_from_source="archive",
            ship_from_confidence="medium",
            variant_attributes={"Color": "Black"},
            image_urls=["https://cdn.example.com/1.jpg"],
        ),
        SupplierProduct(
            supplier_id="seller-1",
            supplier_spu_no="SPU-1",
            product_id="prod-1",
            sku="SKU-FREE",
            sku_code="CODE-FREE",
            item_no="SKU-FREE",
            title="Travel Set",
            category_id="cat-1",
            category_name="Travel Accessories",
            category_path="Travel Accessories",
            seller_name="North Home",
            inventory=30,
            cost=0.0,
            shipping_cost=0.0,
            msrp=80.0,
            ship_from_country="United States",
            ship_from_source="archive",
            ship_from_confidence="medium",
            variant_attributes={"Color": "Red"},
            image_urls=["https://cdn.example.com/2.jpg"],
        ),
    ]

    candidate, reason = _build_archive_product_candidate(products, inventory_threshold=10)

    assert reason is None
    assert candidate is not None
    assert [variant.sku for variant in candidate.variants] == ["SKU-OK"]
    assert candidate.ship_from_country == "United States"
    assert candidate.variants[0].sale_price > 0
    assert candidate.variants[0].cost_price > 0


def test_build_candidate_enrichment_generates_projection_bundle():
    candidate = DobaProductCandidate(
        spu_id="spu-1",
        spu_no="SPU-1",
        supplier_id="seller-1",
        category_id="cat-1",
        merge_key="merge-1",
        seller_name="Seller A",
        seller_info={},
        title="Patio Storage Bench",
        category_name="Outdoor Furniture",
        description_html="<p>Outdoor storage bench for patios.</p>",
        brand="Doba Basics",
        ship_from_country="United States",
        image_urls=["https://cdn.example.com/main.jpg", "https://cdn.example.com/side.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-1",
                sku_code="SKU-1",
                sku_id="sku-id-1",
                option_values={"Color": "Red"},
                inventory=14,
                source_price=49.99,
                shipping_cost=5.0,
                cost_price=54.99,
                sale_price=62.49,
                compare_at_price=79.99,
                ship_time_days=4,
                item_no="ITEM-1",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/main.jpg"],
                warehouse_name="US Warehouse",
                ship_from_raw="United States",
                ship_from_source="archive",
                ship_from_confidence="high",
            )
        ],
        tags=["doba-import"],
        category_metafields={"shopify_category_id": "gid://shopify/TaxonomyCategory/1"},
    )

    bundle = build_candidate_enrichment(candidate).model_dump()

    assert bundle["semantic"]["product_type"] == "Outdoor Furniture"
    assert bundle["google_merchant"]["availability"] == "in stock"
    assert bundle["schema_projection"]["schema_type"] == "Product"
    assert bundle["geo_score"]["eligible"] is True
    assert len(bundle["image_alts"]) == 2


def test_build_doba_publish_candidate_pool_filters_archive_groups_and_writes_only_qualified_candidates(tmp_path):
    qualified = SupplierProduct(
        supplier_id="seller-1",
        supplier_spu_no="SPU-QUALIFIED",
        product_id="spu-qualified",
        sku="ITEM-1",
        sku_code="SKU-1",
        sku_id="sku-id-1",
        item_no="ITEM-1",
        title="Qualified Bench",
        brand="Doba Basics",
        category_id="cat-1",
        category_name="Outdoor Furniture",
        category_path="Outdoor Furniture",
        source_channels=["Inbox", "Shop"],
        cost=54.99,
        msrp=79.99,
        inventory=18,
        ship_from_country="United States",
        ship_from_raw="United States",
        warehouse_name="US Warehouse",
        shipping_cost=5,
        delivery_days=4,
        description="<p>Bench</p>",
        image_urls=["https://cdn.example.com/bench.jpg"],
        variant_attributes={"Color": "Red"},
        seller_name="Seller A",
    )
    low_inventory = qualified.model_copy(
        update={
            "supplier_spu_no": "SPU-LOW",
            "product_id": "spu-low",
            "sku": "ITEM-LOW",
            "item_no": "ITEM-LOW",
            "inventory": 5,
            "title": "Low Inventory Bench",
        }
    )
    non_us = qualified.model_copy(
        update={
            "supplier_spu_no": "SPU-HK",
            "product_id": "spu-hk",
            "sku": "ITEM-HK",
            "item_no": "ITEM-HK",
            "ship_from_country": "Hong Kong S.A.R.",
            "ship_from_raw": "Hong Kong S.A.R.",
            "title": "Hong Kong Bench",
        }
    )
    active = qualified.model_copy(
        update={
            "supplier_spu_no": "SPU-ACTIVE",
            "product_id": "spu-active",
            "sku": "ITEM-ACTIVE",
            "item_no": "ITEM-ACTIVE",
            "title": "Active Bench",
        }
    )

    archive_repository = Mock()
    archive_repository.list_supplier_products.return_value = [qualified, low_inventory, non_us, active]
    publish_mapping_repository = Mock()
    publish_mapping_repository.list_publish_mappings.return_value = []

    category_resolution = Mock(category_id="gid://shopify/TaxonomyCategory/1", taxonomy_search="Home > Outdoor")

    archive_repository.consume_changed_supplier_spu_nos.return_value = []
    with patch("src.modules.shopify_listing.application.live_publish_runtime.SQLiteSupplierArchiveRepository", return_value=archive_repository):
        with patch("src.modules.shopify_listing.application.live_publish_runtime.SQLitePublishMappingRepository", return_value=publish_mapping_repository):
            with patch("src.modules.shopify_listing.application.live_publish_runtime.ShopifyAuthClient.from_settings", return_value=object()):
                with patch(
                    "src.modules.shopify_listing.application.live_publish_runtime._resolve_shopify_category",
                    return_value=category_resolution,
                ):
                    with patch(
                        "src.modules.shopify_listing.application.live_publish_runtime._find_existing_product_by_merge_key",
                        side_effect=[None, {"status": "ACTIVE"}],
                    ):
                        with patch(
                            "src.modules.shopify_listing.application.live_publish_runtime._find_existing_product_by_spu_no",
                            return_value=(None, None),
                        ):
                            result = build_doba_publish_candidate_pool(
                                candidate_pool_path=str(tmp_path / "candidate-pool.json"),
                                inventory_threshold=10,
                            )

    assert result["summary"]["qualified_count"] == 1
    assert result["summary"]["skipped_by_reason"]["all_variants_inventory_below_threshold"] == 1
    assert result["summary"]["skipped_by_reason"]["ship_from_not_us_or_unknown"] == 1
    assert result["summary"]["skipped_by_reason"]["active_product_exists"] == 1
    assert result["summary"]["ship_from_summary"]["us"] == 3
    assert result["summary"]["ship_from_summary"]["non_us"] == 1
    assert len(result["qualified_candidates"]) == 1
    assert result["qualified_candidates"][0]["spu_no"] == "SPU-QUALIFIED"
    assert result["qualified_candidates"][0]["category_metafields"]["shopify_category_id"] == "gid://shopify/TaxonomyCategory/1"


def test_build_doba_publish_candidate_pool_blocks_green_market_tracking_devices_at_runtime_policy(tmp_path):
    blocked = SupplierProduct(
        supplier_id="seller-gps",
        supplier_spu_no="SPU-GPS-BLOCKED",
        product_id="spu-gps-blocked",
        sku="ITEM-GPS-1",
        sku_code="SKU-GPS-1",
        sku_id="sku-id-gps-1",
        item_no="ITEM-GPS-1",
        title="Realtime GPS Tracker",
        brand="Doba Basics",
        category_id="cat-gps",
        category_name="Tracking Devices",
        category_path="Tracking Devices",
        source_channels=["Inbox", "Shop"],
        cost=54.99,
        msrp=79.99,
        inventory=218,
        ship_from_country="United States",
        ship_from_raw="United States",
        warehouse_name="US Warehouse",
        shipping_cost=0,
        delivery_days=4,
        description="<p>GPS</p>",
        image_urls=["https://cdn.example.com/gps.jpg"],
        variant_attributes={"Color": "Black"},
        seller_name="Green Market",
    )

    archive_repository = Mock()
    archive_repository.list_supplier_products.return_value = [blocked]
    archive_repository.consume_changed_supplier_spu_nos.return_value = []
    publish_mapping_repository = Mock()
    publish_mapping_repository.list_publish_mappings.return_value = []

    with patch("src.modules.shopify_listing.application.live_publish_runtime.SQLiteSupplierArchiveRepository", return_value=archive_repository):
        with patch("src.modules.shopify_listing.application.live_publish_runtime.SQLitePublishMappingRepository", return_value=publish_mapping_repository):
            with patch("src.modules.shopify_listing.application.live_publish_runtime.ShopifyAuthClient.from_settings", return_value=object()):
                result = build_doba_publish_candidate_pool(
                    candidate_pool_path=str(tmp_path / "candidate-pool.json"),
                    inventory_threshold=10,
                )

    assert result["summary"]["qualified_count"] == 0
    assert result["summary"]["skipped_by_reason"]["seller_in_blocklist"] == 1
    assert result["qualified_candidates"] == []


def test_build_doba_publish_candidate_pool_emits_realtime_progress_logs(tmp_path):
    qualified = SupplierProduct(
        supplier_id="seller-1",
        supplier_spu_no="SPU-QUALIFIED",
        product_id="spu-qualified",
        sku="ITEM-1",
        sku_code="SKU-1",
        sku_id="sku-id-1",
        item_no="ITEM-1",
        title="Qualified Bench",
        brand="Doba Basics",
        category_id="cat-1",
        category_name="Outdoor Furniture",
        category_path="Outdoor Furniture",
        source_channels=["Inbox", "Shop"],
        cost=54.99,
        msrp=79.99,
        inventory=18,
        ship_from_country="United States",
        ship_from_raw="United States",
        warehouse_name="US Warehouse",
        shipping_cost=5,
        delivery_days=4,
        description="<p>Bench</p>",
        image_urls=["https://cdn.example.com/bench.jpg"],
        variant_attributes={"Color": "Red"},
        seller_name="Seller A",
    )
    archive_repository = Mock()
    archive_repository.list_supplier_products.return_value = [qualified]
    publish_mapping_repository = Mock()
    publish_mapping_repository.list_publish_mappings.return_value = []
    category_resolution = Mock(category_id="gid://shopify/TaxonomyCategory/1", taxonomy_search="Home > Outdoor")

    archive_repository.consume_changed_supplier_spu_nos.return_value = []
    with patch("src.modules.shopify_listing.application.live_publish_runtime.SQLiteSupplierArchiveRepository", return_value=archive_repository):
        with patch("src.modules.shopify_listing.application.live_publish_runtime.SQLitePublishMappingRepository", return_value=publish_mapping_repository):
            with patch("src.modules.shopify_listing.application.live_publish_runtime.ShopifyAuthClient.from_settings", return_value=object()):
                with patch("src.modules.shopify_listing.application.live_publish_runtime._resolve_shopify_category", return_value=category_resolution):
                    with patch("src.modules.shopify_listing.application.live_publish_runtime._find_existing_product_by_merge_key", return_value=None):
                        with patch("src.modules.shopify_listing.application.live_publish_runtime._find_existing_product_by_spu_no", return_value=(None, None)):
                            with patch("src.modules.shopify_listing.application.live_publish_runtime._log") as log:
                                build_doba_publish_candidate_pool(
                                    candidate_pool_path=str(tmp_path / "candidate-pool.json"),
                                    inventory_threshold=10,
                                )

    assert log.call_args_list[0].args[0] == "candidate_pool_start"
    assert any(call.args[0] == "candidate_pool_result" for call in log.call_args_list)
    assert log.call_args_list[-1].args[0] == "candidate_pool_summary"


def test_build_doba_publish_candidate_pool_incremental_spu_nos_only_refreshes_changed_group(tmp_path):
    keep_candidate = DobaProductCandidate(
        spu_id="spu-keep",
        spu_no="SPU-KEEP",
        supplier_id="seller-keep",
        category_id="cat-keep",
        merge_key="merge-keep",
        seller_name="Seller Keep",
        seller_info={},
        title="Keep Product",
        category_name="Outdoor Furniture",
        description_html="<p>Keep</p>",
        brand="Doba Basics",
        ship_from_country="United States",
        processing_time=3,
        store_url="",
        image_urls=["https://cdn.example.com/keep.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-KEEP-1",
                sku_code="SKU-KEEP-1",
                sku_id="sku-id-keep-1",
                option_values={"Color": "Blue"},
                inventory=21,
                source_price=40.0,
                shipping_cost=5.0,
                cost_price=45.0,
                sale_price=51.0,
                compare_at_price=60.0,
                ship_time_days=4,
                item_no="ITEM-KEEP-1",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/keep-blue.jpg"],
                warehouse_name="US Warehouse",
                ship_from_raw="United States",
            )
        ],
        tags=["doba-import"],
        category_metafields={
            "shopify_category_id": "gid://shopify/TaxonomyCategory/1",
            "shopify_category_name": "Home > Outdoor",
        },
    )
    candidate_repository = SQLiteCandidatePoolRepository(db_path=tmp_path / "runtime.sqlite3")
    candidate_repository.upsert_entry(
        supplier_spu_no="SPU-KEEP",
        supplier_product_id="spu-keep",
        title="Keep Product",
        seller_name="Seller Keep",
        category_name="Outdoor Furniture",
        status="qualified",
        skip_reason="",
        source_hash="keep-hash",
        payload=_serialize_candidate(keep_candidate),
        updated_at="2026-06-25T00:00:00+00:00",
    )

    changed = SupplierProduct(
        supplier_id="seller-1",
        supplier_spu_no="SPU-CHANGED",
        product_id="spu-changed",
        sku="ITEM-CHANGED-1",
        sku_code="SKU-CHANGED-1",
        sku_id="sku-id-changed-1",
        item_no="ITEM-CHANGED-1",
        title="Changed Bench",
        brand="Doba Basics",
        category_id="cat-1",
        category_name="Outdoor Furniture",
        category_path="Outdoor Furniture",
        source_channels=["Inbox", "Shop"],
        cost=54.99,
        msrp=79.99,
        inventory=18,
        ship_from_country="United States",
        ship_from_raw="United States",
        warehouse_name="US Warehouse",
        shipping_cost=5,
        delivery_days=4,
        description="<p>Bench</p>",
        image_urls=["https://cdn.example.com/bench.jpg"],
        variant_attributes={"Color": "Red"},
        seller_name="Seller A",
    )

    archive_repository = Mock()
    archive_repository.list_supplier_products_by_spu_nos.return_value = [changed]
    archive_repository.count_supplier_product_groups.return_value = 2
    publish_mapping_repository = Mock()
    publish_mapping_repository.list_publish_mappings.return_value = []
    category_resolution = Mock(category_id="gid://shopify/TaxonomyCategory/1", taxonomy_search="Home > Outdoor")
    pool_path = tmp_path / "candidate-pool.json"
    pool_path.write_text(
        json.dumps(
            {
                "generated_at": "2026-06-25T00:00:00+00:00",
                "updated_at": "2026-06-25T00:00:00+00:00",
                "source_mode": "archive_candidate_pool",
                "target_country": "US",
                "inventory_threshold": 10,
                "summary": {"archive_groups": 2, "qualified_count": 1},
                "progress": {"total_groups": 2, "current_index": 2, "next_index": 2, "completed": True},
                "qualified_candidates": [_serialize_candidate(keep_candidate)],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with patch("src.modules.shopify_listing.application.live_publish_runtime.SQLiteSupplierArchiveRepository", return_value=archive_repository):
        with patch("src.modules.shopify_listing.application.live_publish_runtime.SQLitePublishMappingRepository", return_value=publish_mapping_repository):
            with patch("src.modules.shopify_listing.application.live_publish_runtime.SQLiteCandidatePoolRepository", return_value=candidate_repository):
                with patch("src.modules.shopify_listing.application.live_publish_runtime.ShopifyAuthClient.from_settings", return_value=object()):
                    with patch("src.modules.shopify_listing.application.live_publish_runtime._resolve_shopify_category", return_value=category_resolution):
                        with patch("src.modules.shopify_listing.application.live_publish_runtime._find_existing_product_by_merge_key", return_value=None):
                            with patch("src.modules.shopify_listing.application.live_publish_runtime._find_existing_product_by_spu_no", return_value=(None, None)):
                                result = build_doba_publish_candidate_pool(
                                    candidate_pool_path=str(pool_path),
                                    inventory_threshold=10,
                                    incremental=True,
                                    incremental_spu_nos=["SPU-CHANGED"],
                                )

    qualified_spu_nos = {item["spu_no"] for item in result["qualified_candidates"]}
    assert qualified_spu_nos == {"SPU-KEEP", "SPU-CHANGED"}
    assert result["summary"]["archive_groups"] == 2


def test_build_doba_publish_candidate_pool_persists_missing_category_examples(tmp_path):
    unresolved = SupplierProduct(
        supplier_id="seller-1",
        supplier_spu_no="SPU-MISSING-CATEGORY",
        product_id="spu-missing-category",
        sku="ITEM-MISSING",
        sku_code="SKU-MISSING",
        sku_id="sku-id-missing",
        item_no="ITEM-MISSING",
        title="Portable Courtyard Metal Fire Pit with Accessories Black",
        brand="Doba Basics",
        category_id="cat-fire-pit",
        category_name="Other Patio, Lawn & Garden Supplies",
        category_path="Other Patio, Lawn & Garden Supplies",
        source_channels=["Inbox", "Shop"],
        cost=54.99,
        msrp=79.99,
        inventory=18,
        ship_from_country="United States",
        ship_from_raw="United States",
        warehouse_name="US Warehouse",
        shipping_cost=5,
        delivery_days=4,
        description="<p>Fire pit</p>",
        image_urls=["https://cdn.example.com/fire-pit.jpg"],
        variant_attributes={"Color": "Black"},
        seller_name="Seller A",
    )
    archive_repository = Mock()
    archive_repository.list_supplier_products.return_value = [unresolved]
    publish_mapping_repository = Mock()
    publish_mapping_repository.list_publish_mappings.return_value = []

    archive_repository.consume_changed_supplier_spu_nos.return_value = []
    with patch("src.modules.shopify_listing.application.live_publish_runtime.SQLiteSupplierArchiveRepository", return_value=archive_repository):
        with patch("src.modules.shopify_listing.application.live_publish_runtime.SQLitePublishMappingRepository", return_value=publish_mapping_repository):
            with patch("src.modules.shopify_listing.application.live_publish_runtime.ShopifyAuthClient.from_settings", return_value=object()):
                with patch("src.modules.shopify_listing.application.live_publish_runtime._resolve_shopify_category", return_value=None):
                    result = build_doba_publish_candidate_pool(
                        candidate_pool_path=str(tmp_path / "candidate-pool.json"),
                        inventory_threshold=10,
                    )

    assert result["summary"]["skipped_by_reason"]["missing_shopify_category"] == 1
    assert result["summary"]["missing_category_examples"] == [
        {
            "spu_id": "spu-missing-category",
            "spu_no": "SPU-MISSING-CATEGORY",
            "title": "Portable Courtyard Metal Fire Pit with Accessories Black",
            "category_name": "Other Patio, Lawn & Garden Supplies",
            "sku_list": ["ITEM-MISSING"],
        }
    ]


def test_build_doba_publish_candidate_pool_persists_partial_progress_on_interrupt(tmp_path):
    qualified = SupplierProduct(
        supplier_id="seller-1",
        supplier_spu_no="D0100QUALIFIED001",
        product_id="spu-qualified-1",
        sku="ITEM-1",
        sku_code="SKU-1",
        sku_id="sku-id-1",
        item_no="ITEM-1",
        title="Qualified Bench",
        brand="Doba Basics",
        category_id="cat-1",
        category_name="Outdoor Furniture",
        category_path="Outdoor Furniture",
        source_channels=["Inbox", "Shop"],
        cost=54.99,
        msrp=79.99,
        inventory=18,
        ship_from_country="United States",
        ship_from_raw="United States",
        warehouse_name="US Warehouse",
        shipping_cost=5,
        delivery_days=4,
        description="<p>Bench</p>",
        image_urls=["https://cdn.example.com/bench.jpg"],
        variant_attributes={"Color": "Red"},
        seller_name="Seller A",
    )
    second = qualified.model_copy(
        update={
            "supplier_spu_no": "D0100QUALIFIED002",
            "product_id": "spu-qualified-2",
            "sku": "ITEM-2",
            "item_no": "ITEM-2",
            "title": "Second Bench",
        }
    )
    archive_repository = Mock()
    archive_repository.list_supplier_products.return_value = [qualified, second]
    publish_mapping_repository = Mock()
    publish_mapping_repository.list_publish_mappings.return_value = []
    category_resolution = Mock(category_id="gid://shopify/TaxonomyCategory/1", taxonomy_search="Home > Outdoor")
    pool_path = tmp_path / "candidate-pool-interrupted.json"

    archive_repository.consume_changed_supplier_spu_nos.return_value = []
    with patch("src.modules.shopify_listing.application.live_publish_runtime.SQLiteSupplierArchiveRepository", return_value=archive_repository):
        with patch("src.modules.shopify_listing.application.live_publish_runtime.SQLitePublishMappingRepository", return_value=publish_mapping_repository):
            with patch("src.modules.shopify_listing.application.live_publish_runtime.ShopifyAuthClient.from_settings", return_value=object()):
                with patch(
                    "src.modules.shopify_listing.application.live_publish_runtime._resolve_shopify_category",
                    side_effect=[category_resolution, KeyboardInterrupt],
                ):
                    with patch("src.modules.shopify_listing.application.live_publish_runtime._find_existing_product_by_merge_key", return_value=None):
                        with patch("src.modules.shopify_listing.application.live_publish_runtime._find_existing_product_by_spu_no", return_value=(None, None)):
                            try:
                                build_doba_publish_candidate_pool(
                                    candidate_pool_path=str(pool_path),
                                    inventory_threshold=10,
                                )
                            except KeyboardInterrupt:
                                pass
                            else:
                                assert False, "Expected KeyboardInterrupt"

    payload = json.loads(pool_path.read_text(encoding="utf-8"))
    assert payload["progress"]["completed"] is False
    assert payload["progress"]["current_index"] == 1
    assert payload["progress"]["next_index"] == 1
    assert payload["summary"]["qualified_count"] == 1
    assert len(payload["qualified_candidates"]) == 1


def test_build_doba_publish_candidate_pool_resumes_from_partial_progress(tmp_path):
    qualified = SupplierProduct(
        supplier_id="seller-1",
        supplier_spu_no="D0100QUALIFIED001",
        product_id="spu-qualified-1",
        sku="ITEM-1",
        sku_code="SKU-1",
        sku_id="sku-id-1",
        item_no="ITEM-1",
        title="Qualified Bench",
        brand="Doba Basics",
        category_id="cat-1",
        category_name="Outdoor Furniture",
        category_path="Outdoor Furniture",
        source_channels=["Inbox", "Shop"],
        cost=54.99,
        msrp=79.99,
        inventory=18,
        ship_from_country="United States",
        ship_from_raw="United States",
        warehouse_name="US Warehouse",
        shipping_cost=5,
        delivery_days=4,
        description="<p>Bench</p>",
        image_urls=["https://cdn.example.com/bench.jpg"],
        variant_attributes={"Color": "Red"},
        seller_name="Seller A",
    )
    second = qualified.model_copy(
        update={
            "supplier_spu_no": "D0100QUALIFIED002",
            "product_id": "spu-qualified-2",
            "sku": "ITEM-2",
            "item_no": "ITEM-2",
            "title": "Second Bench",
        }
    )
    archive_repository = Mock()
    archive_repository.list_supplier_products.return_value = [qualified, second]
    publish_mapping_repository = Mock()
    publish_mapping_repository.list_publish_mappings.return_value = []
    category_resolution = Mock(category_id="gid://shopify/TaxonomyCategory/1", taxonomy_search="Home > Outdoor")
    pool_path = tmp_path / "candidate-pool-resume.json"
    pool_path.write_text(
        json.dumps(
            {
                "generated_at": "",
                "updated_at": "2026-06-17T00:00:00+00:00",
                "source_mode": "archive_candidate_pool",
                "target_country": "US",
                "inventory_threshold": 10,
                "summary": {
                    "archive_groups": 2,
                    "qualified_count": 1,
                    "skipped_by_reason": {},
                },
                "progress": {
                    "total_groups": 2,
                    "current_index": 1,
                    "next_index": 1,
                    "completed": False,
                },
                "qualified_candidates": [
                    {
                        "spu_id": "spu-qualified-1",
                        "spu_no": "D0100QUALIFIED001",
                        "supplier_id": "seller-1",
                        "category_id": "cat-1",
                        "merge_key": "merge-1",
                        "seller_name": "Seller A",
                        "seller_info": {},
                        "title": "Qualified Bench",
                        "category_name": "Outdoor Furniture",
                        "description_html": "<p>Bench</p>",
                        "brand": "Doba Basics",
                        "ship_from_country": "United States",
                        "processing_time": 4,
                        "store_url": "",
                        "image_urls": ["https://cdn.example.com/bench.jpg"],
                        "tags": ["doba-import"],
                        "category_metafields": {
                            "doba_category_id": "cat-1",
                            "doba_category_name": "Outdoor Furniture",
                            "shopify_category_id": "gid://shopify/TaxonomyCategory/1",
                            "shopify_category_name": "Home > Outdoor",
                        },
                        "source_vendor": SOURCE_VENDOR_NAME,
                        "source_channels": ["Inbox", "Shop"],
                        "variants": [
                            {
                                "sku": "ITEM-1",
                                "sku_code": "SKU-1",
                                "sku_id": "sku-id-1",
                                "option_values": {"Color": "Red"},
                                "inventory": 18,
                                "source_price": 54.99,
                                "shipping_cost": 5.0,
                                "cost_price": 54.99,
                                "sale_price": 68.74,
                                "compare_at_price": 79.99,
                                "ship_time_days": 4,
                                "item_no": "ITEM-1",
                                "ship_name": "Ground",
                                "warehouse": "United States",
                                "image_urls": ["https://cdn.example.com/bench.jpg"],
                                "warehouse_name": "US Warehouse",
                                "ship_from_raw": "United States",
                            }
                        ],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    archive_repository.consume_changed_supplier_spu_nos.return_value = []
    with patch("src.modules.shopify_listing.application.live_publish_runtime.SQLiteSupplierArchiveRepository", return_value=archive_repository):
        with patch("src.modules.shopify_listing.application.live_publish_runtime.SQLitePublishMappingRepository", return_value=publish_mapping_repository):
            with patch("src.modules.shopify_listing.application.live_publish_runtime.ShopifyAuthClient.from_settings", return_value=object()):
                with patch(
                    "src.modules.shopify_listing.application.live_publish_runtime._resolve_shopify_category",
                    return_value=category_resolution,
                ) as resolve_category:
                    with patch("src.modules.shopify_listing.application.live_publish_runtime._find_existing_product_by_merge_key", return_value=None):
                        with patch("src.modules.shopify_listing.application.live_publish_runtime._find_existing_product_by_spu_no", return_value=(None, None)):
                            result = build_doba_publish_candidate_pool(
                                candidate_pool_path=str(pool_path),
                                inventory_threshold=10,
                            )

    assert resolve_category.call_count == 1
    assert result["progress"]["completed"] is True
    assert result["progress"]["current_index"] == 2
    assert result["summary"]["qualified_count"] == 2
    assert len(result["qualified_candidates"]) == 2


def test_load_published_spu_nos_ignores_synthetic_test_spus():
    repository = Mock()
    repository.list_publish_mappings.return_value = [
        Mock(supplier_spu_no="SPU-TEST-1", status="published"),
        Mock(supplier_spu_no="D0100REAL123", status="published"),
        Mock(supplier_spu_no="D0100PENDING123", status="pending"),
    ]

    result = _load_published_spu_nos(repository)

    assert result == {"D0100REAL123"}


def test_derive_shopify_sale_price_uses_doba_selling_price_times_115_percent_plus_shipping():
    assert _derive_shopify_sale_price(300.0, 0.0) == 345.0
    assert _derive_shopify_sale_price(49.99, 5.0) == 62.49
    assert _derive_shopify_sale_price(54.99, 7.0) == 70.24


def test_build_merge_key_is_stable_for_same_product_group():
    key1 = _build_merge_key(
        title="3 Piece Patio Lounge Set with Cushions Poly Rattan Black",
        category_id="fPDYvVJtToba",
        supplier_id="CVbdDKqBlYvG",
        seller_name="Home Life Boutique",
    )
    key2 = _build_merge_key(
        title="3 Piece Patio Lounge Set with Cushions Poly Rattan Black",
        category_id="fPDYvVJtToba",
        supplier_id="CVbdDKqBlYvG",
        seller_name="Home Life Boutique",
    )

    assert key1 == key2


def test_build_merge_key_groups_same_family_titles_with_different_piece_color_material():
    key1 = _build_merge_key(
        title="10 Piece Patio Lounge Set with Cushions Poly Rattan Black",
        category_id="cat-patio-lounge",
        supplier_id="seller-lounge",
        seller_name="Home Life Boutique",
    )
    key2 = _build_merge_key(
        title="9 Piece Patio Lounge Set with Cushions Poly Rattan Black",
        category_id="cat-patio-lounge",
        supplier_id="seller-lounge",
        seller_name="Home Life Boutique",
    )
    key3 = _build_merge_key(
        title="4 Piece Patio Lounge Set with Cushion Solid Acacia Wood",
        category_id="cat-patio-lounge",
        supplier_id="seller-lounge",
        seller_name="Home Life Boutique",
    )

    assert key1 == key2 == key3


def test_build_product_candidate_adds_title_derived_variant_attributes_for_single_sku_products():
    detail = {
        "spuId": "spu-single",
        "spuNo": "SPU-SINGLE",
        "busiId": "seller-single",
        "sellerName": "Seller Single",
        "title": "10 Piece Patio Lounge Set with Cushions Poly Rattan Black",
        "cateName": "Other Patio Furniture Sets",
        "goodsDesc": "<p>Patio lounge set.</p>",
        "pictureUrl": "https://cdn.example.com/lounge.jpg",
        "children": [
            {
                "skuId": "sku-id-single",
                "skuCode": "sku-code-single",
                "skuPicList": ["https://cdn.example.com/lounge-variant.jpg"],
                "variantProps": [],
                "stocks": [{"regionId": "US", "regionName": "United States", "itemNo": "ITEM-SINGLE", "availableNum": 21}],
            }
        ],
    }

    candidate, skip_reason = _build_product_candidate(
        detail=detail,
        stock_map={"ITEM-SINGLE": {"itemNo": "ITEM-SINGLE", "sellingPrice": "100.00", "msrpPrice": "150.00", "availableNum": 21}},
        shipping_map={"ITEM-SINGLE": {"cost": {"shipFee": 10, "shipName": "Ground", "shipTime": "3-5", "stockRegion": "US"}}},
        seller_info={},
        inventory_threshold=10,
        target_country="US",
    )

    assert skip_reason is None
    assert candidate is not None
    assert candidate.variants[0].option_values["Set Size"] == "10 Piece"
    assert candidate.variants[0].option_values["Material"] == "Poly Rattan"
    assert candidate.variants[0].option_values["Color"] == "Black"


def test_build_archive_inputs_from_detail_does_not_duplicate_single_child_for_multiple_title_attributes():
    detail = {
        "spuId": "spu-archive-dup",
        "spuNo": "D0100ARCHIVE001",
        "busiId": "seller-archive",
        "sellerName": "Seller Archive",
        "title": "10 Piece Patio Lounge Set with Cushions Poly Rattan Black",
        "cateId": "cat-archive",
        "cateName": "Other Patio Furniture Sets",
        "goodsDesc": "<p>Archive detail.</p>",
        "pictureUrl": "https://cdn.example.com/archive.jpg",
        "children": [
            {
                "skuId": "sku-id-archive-1",
                "skuCode": "SKU-ARCHIVE-1",
                "skuPicList": ["https://cdn.example.com/archive-1.jpg"],
                "variantProps": [],
                "stocks": [{"regionId": "US", "regionName": "United States", "itemNo": "ITEM-ARCHIVE-1", "availableNum": 21}],
            }
        ],
    }

    rows = _build_archive_inputs_from_detail(
        detail=detail,
        stock_map={"ITEM-ARCHIVE-1": {"itemNo": "ITEM-ARCHIVE-1", "sellingPrice": "100.00", "msrpPrice": "150.00", "availableNum": 21}},
        shipping_map={"ITEM-ARCHIVE-1": {"cost": {"shipFee": 10, "shipName": "Ground", "shipTime": "3-5", "stockRegion": "US"}}},
        target_country="US",
    )

    assert len(rows) == 1
    assert rows[0].variant_attributes["Set Size"] == "10 Piece"
    assert rows[0].variant_attributes["Material"] == "Poly Rattan"
    assert rows[0].variant_attributes["Color"] == "Black"


def test_build_product_candidate_skips_when_all_variant_inventory_below_threshold():
    detail = {
        "spuId": "spu-2",
        "spuNo": "SPU-2",
        "busiId": "seller-2",
        "sellerName": "Seller B",
        "title": "Desk Lamp",
        "cateName": "Lighting",
        "goodsDesc": "<p>Lamp.</p>",
        "pictureUrl": "https://cdn.example.com/lamp.jpg",
        "children": [
            {
                "skuId": "sku-id-3",
                "skuCode": "sku-code-3",
                "skuPicList": ["https://cdn.example.com/lamp-red.jpg"],
                "variantProps": [{"propName": "Color", "propValue": "Red"}],
                "stocks": [{"regionId": "US", "itemNo": "ITEM-3", "availableNum": 9}],
            }
        ],
    }

    candidate, skip_reason = _build_product_candidate(
        detail=detail,
        stock_map={"ITEM-3": {"itemNo": "ITEM-3", "sellingPrice": "19.99", "msrpPrice": "29.99", "availableNum": 9}},
        shipping_map={"ITEM-3": {"cost": {"shipFee": 3, "shipName": "Ground", "shipTime": "3-5"}}},
        seller_info={},
        inventory_threshold=10,
        target_country="US",
    )

    assert candidate is None
    assert skip_reason == "all_variants_inventory_below_threshold"


def test_build_product_candidate_skips_when_ship_from_is_unknown():
    detail = {
        "spuId": "spu-unknown",
        "spuNo": "SPU-UNKNOWN",
        "busiId": "seller-unknown",
        "sellerName": "Seller Unknown",
        "title": "Mystery Shelf",
        "cateName": "Storage",
        "goodsDesc": "<p>Mystery shelf.</p>",
        "pictureUrl": "https://cdn.example.com/mystery.jpg",
        "children": [
            {
                "skuId": "sku-id-unknown",
                "skuCode": "sku-code-unknown",
                "skuPicList": ["https://cdn.example.com/mystery-variant.jpg"],
                "variantProps": [{"propName": "Color", "propValue": "White"}],
                "stocks": [{"regionId": "", "itemNo": "ITEM-UNKNOWN", "availableNum": 50}],
            }
        ],
    }

    candidate, skip_reason = _build_product_candidate(
        detail=detail,
        stock_map={"ITEM-UNKNOWN": {"itemNo": "ITEM-UNKNOWN", "sellingPrice": "39.99", "msrpPrice": "59.99", "availableNum": 50}},
        shipping_map={"ITEM-UNKNOWN": {"cost": {"shipFee": 5, "shipName": "Ground", "shipTime": "3-5"}}},
        seller_info={},
        inventory_threshold=10,
        target_country="US",
    )

    assert candidate is None
    assert skip_reason == "ship_from_not_us_or_unknown"


def test_build_product_candidate_prioritizes_non_us_ship_from_over_low_inventory():
    detail = {
        "spuId": "spu-hk-low-stock",
        "spuNo": "SPU-HK-LOW-STOCK",
        "busiId": "seller-hk",
        "sellerName": "Beauty Life",
        "title": "Powder Foundation",
        "cateName": "Face Makeup",
        "goodsDesc": "<p>Foundation.</p>",
        "pictureUrl": "https://cdn.example.com/foundation.jpg",
        "children": [
            {
                "skuId": "sku-id-hk",
                "skuCode": "sku-code-hk",
                "shipFrom": "Hong Kong S.A.R.",
                "skuPicList": ["https://cdn.example.com/foundation-variant.jpg"],
                "variantProps": [],
                "stocks": [{"regionId": "HK", "regionName": "Hong Kong S.A.R.", "itemNo": "ITEM-HK", "availableNum": 2}],
            }
        ],
    }

    candidate, skip_reason = _build_product_candidate(
        detail=detail,
        stock_map={"ITEM-HK": {"itemNo": "ITEM-HK", "sellingPrice": "39.99", "msrpPrice": "59.99", "availableNum": 2}},
        shipping_map={"ITEM-HK": {"cost": {"shipFee": 5, "shipName": "Ground", "shipTime": "3-5", "stockRegion": "Hong Kong S.A.R."}}},
        seller_info={},
        inventory_threshold=10,
        target_country="US",
    )

    assert candidate is None
    assert skip_reason == "ship_from_not_us_or_unknown"


def test_build_product_candidate_uses_child_item_no_and_inventory_fallbacks():
    detail = {
        "spuId": "spu-fallback",
        "spuNo": "SPU-FALLBACK",
        "busiId": "seller-fallback",
        "sellerName": "Seller Fallback",
        "title": "Fallback Serum",
        "cateName": "Beauty",
        "goodsDesc": "<p>Fallback serum.</p>",
        "pictureUrl": "https://cdn.example.com/fallback.jpg",
        "children": [
            {
                "skuId": "sku-id-fallback",
                "skuCode": "sku-code-fallback",
                "itemNo": "ITEM-FALLBACK",
                "availableNum": 25,
                "skuPicList": ["https://cdn.example.com/fallback-variant.jpg"],
                "variantProps": [{"propName": "Size", "propValue": "50ml"}],
                "stocks": [{"regionId": "US", "regionName": "United States"}],
            }
        ],
    }

    candidate, skip_reason = _build_product_candidate(
        detail=detail,
        stock_map={"ITEM-FALLBACK": {"itemNo": "ITEM-FALLBACK", "sellingPrice": "39.99", "msrpPrice": "59.99"}},
        shipping_map={"ITEM-FALLBACK": {"cost": {"shipFee": 5, "shipName": "Ground", "shipTime": "3-5", "stockRegion": "US"}}},
        seller_info={},
        inventory_threshold=10,
        target_country="US",
    )

    assert skip_reason is None
    assert candidate is not None
    assert [variant.sku for variant in candidate.variants] == ["ITEM-FALLBACK"]
    assert [variant.inventory for variant in candidate.variants] == [25]
    assert candidate.ship_from_country == "United States"


def test_build_product_candidate_skips_with_missing_variant_stock_data_when_no_item_no_or_inventory_chain_exists():
    detail = {
        "spuId": "spu-missing-data",
        "spuNo": "SPU-MISSING-DATA",
        "busiId": "seller-missing-data",
        "sellerName": "Beauty Life",
        "title": "Missing Data Shampoo",
        "cateName": "Beauty",
        "goodsDesc": "<p>Missing data shampoo.</p>",
        "pictureUrl": "https://cdn.example.com/missing-data.jpg",
        "children": [
            {
                "skuId": "sku-id-missing-data",
                "skuCode": "sku-code-missing-data",
                "skuPicList": ["https://cdn.example.com/missing-data-variant.jpg"],
                "variantProps": [],
                "stocks": [{"regionId": "US"}],
            }
        ],
    }

    candidate, skip_reason = _build_product_candidate(
        detail=detail,
        stock_map={},
        shipping_map={},
        seller_info={},
        inventory_threshold=10,
        target_country="US",
    )

    assert candidate is None
    assert skip_reason == "missing_variant_stock_data"


def test_build_product_candidate_prioritizes_missing_variant_stock_data_over_ship_from_when_stock_row_has_quantity_but_no_item_no():
    detail = {
        "spuId": "spu-missing-item-no",
        "spuNo": "SPU-MISSING-ITEM-NO",
        "busiId": "seller-missing-item-no",
        "sellerName": "Beauty Life",
        "title": "Pigmentclar Eyes Dark Circle Skin-Evening Corrector",
        "cateName": "Beauty",
        "goodsDesc": "<p>Eye corrector.</p>",
        "pictureUrl": "https://cdn.example.com/eye.jpg",
        "children": [
            {
                "skuId": "sku-id-eye",
                "skuCode": "sku-code-eye",
                "skuPicList": ["https://cdn.example.com/eye-variant.jpg"],
                "variantProps": [],
                "stocks": [{"regionId": "US", "availableNum": 40}],
            }
        ],
    }

    candidate, skip_reason = _build_product_candidate(
        detail=detail,
        stock_map={},
        shipping_map={},
        seller_info={},
        inventory_threshold=10,
        target_country="US",
    )

    assert candidate is None
    assert skip_reason == "missing_variant_stock_data"


def test_build_result_payload_includes_real_ship_from_fields():
    candidate = DobaProductCandidate(
        spu_id="spu-log",
        spu_no="SPU-LOG",
        supplier_id="seller-log",
        category_id="cat-log",
        merge_key="merge-log",
        seller_name="Seller Log",
        seller_info={},
        title="Ship From Test",
        category_name="Storage",
        description_html="<p>Storage</p>",
        brand="Brand Log",
        ship_from_country="United States",
        processing_time=2,
        store_url="https://www.doba.com/example-log",
        image_urls=["https://cdn.example.com/log.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-LOG",
                sku_code="SKU-LOG",
                sku_id="SKU-ID-LOG",
                option_values={"Color": "Black"},
                inventory=12,
                source_price=20.0,
                shipping_cost=3.0,
                cost_price=23.0,
                sale_price=25.0,
                compare_at_price=30.0,
                ship_time_days=4,
                item_no="ITEM-LOG",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/log-variant.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    payload = _build_result_payload(
        total_candidates=100,
        global_index=3,
        page_number=1,
        index_in_page=2,
        summary={"spuId": "spu-log", "spuNo": "SPU-LOG", "title": "Ship From Test"},
        detail=None,
        candidate=candidate,
        action="published",
        reason="",
        shopify_product_id="gid://shopify/Product/log",
        variant_count=1,
    )

    assert payload["ship_from_country"] == "United States"
    assert payload["ship_from_source"] == "unknown"
    assert payload["ship_from_list"] == ["United States"]


def test_build_result_payload_includes_category_metafields_and_channels():
    candidate = DobaProductCandidate(
        spu_id="spu-log",
        spu_no="SPU-LOG",
        supplier_id="seller-log",
        category_id="cat-log",
        merge_key="merge-log",
        seller_name="Seller Log",
        seller_info={},
        title="Ship From Test",
        category_name="Storage",
        description_html="<p>Storage</p>",
        brand="Brand Log",
        ship_from_country="United States",
        processing_time=2,
        store_url="https://www.doba.com/example-log",
        image_urls=["https://cdn.example.com/log.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-LOG",
                sku_code="SKU-LOG",
                sku_id="SKU-ID-LOG",
                option_values={"Color": "Black"},
                inventory=12,
                source_price=20.0,
                shipping_cost=3.0,
                cost_price=23.0,
                sale_price=25.0,
                compare_at_price=30.0,
                ship_time_days=4,
                item_no="ITEM-LOG",
                ship_name="Ground",
                warehouse="United States",
                warehouse_name="Nevada Warehouse",
                ship_from_raw="US",
                image_urls=["https://cdn.example.com/log-variant.jpg"],
            )
        ],
        tags=["doba-import"],
        category_metafields={"doba_category_id": "cat-log", "doba_category_name": "Storage"},
        source_channels=["Inbox", "Shop", "Pinterest", "Facebook & Instagram"],
    )

    payload = _build_result_payload(
        total_candidates=100,
        global_index=3,
        page_number=1,
        index_in_page=2,
        summary={"spuId": "spu-log", "spuNo": "SPU-LOG", "title": "Ship From Test"},
        detail={"cateId": "cat-log", "cateName": "Storage"},
        candidate=candidate,
        action="published",
        reason="",
        channels=["Inbox", "Shop", "Pinterest", "Facebook & Instagram"],
        shopify_product_id="gid://shopify/Product/log",
        variant_count=1,
        publish_result={
            "published_to": ["Inbox", "Shop"],
            "shopify_category_id": "gid://shopify/TaxonomyCategory/1",
            "shopify_category_name": "Home > Storage",
            "shopify_status": "ACTIVE",
        },
    )

    assert payload["target_channels"] == ["Inbox", "Shop", "Pinterest", "Facebook & Instagram"]
    assert payload["published_channels"] == ["Inbox", "Shop"]
    assert payload["category_metafields"]["doba_category_id"] == "cat-log"
    assert payload["category_metafields"]["shopify_category_id"] == "gid://shopify/TaxonomyCategory/1"
    assert payload["variant_details"][0]["warehouse_name"] == "Nevada Warehouse"
    assert payload["variant_details"][0]["ship_from_source"] == "unknown"


def test_build_result_payload_falls_back_to_detail_skus_when_candidate_missing():
    payload = _build_result_payload(
        total_candidates=100,
        global_index=3,
        page_number=1,
        index_in_page=2,
        summary={"spuId": "spu-log", "spuNo": "SPU-LOG", "title": "Ship From Test"},
        detail={
            "spuId": "spu-log",
            "spuNo": "SPU-LOG",
            "title": "Ship From Test",
            "sellerName": "Seller Log",
            "children": [
                {
                    "skuId": "SKU-ID-1",
                    "skuCode": "SKU-CODE-1",
                    "itemNo": "ITEM-1",
                    "shipFrom": "US",
                    "stocks": [{"regionId": "US", "regionName": "United States"}],
                }
            ],
        },
        candidate=None,
        action="skipped",
        reason="all_variants_inventory_below_threshold",
        channels=["Inbox"],
    )

    assert payload["sku_list"] == ["ITEM-1"]
    assert payload["sku_code_list"] == ["SKU-CODE-1"]
    assert payload["ship_from_country"] == "United States"
    assert payload["variant_details"][0]["sku"] == "ITEM-1"


def test_build_archive_inputs_from_detail_persists_real_doba_fields():
    detail = {
        "spuId": "spu-archive",
        "spuNo": "SPU-ARCHIVE",
        "busiId": "seller-archive",
        "sellerName": "Archive Seller",
        "title": "Archive Product",
        "cateId": "cat-archive",
        "cateName": "Outdoor Storage",
        "goodsDesc": "<p>Archive product.</p>",
        "brand": "Archive Brand",
        "pictureUrl": "https://cdn.example.com/archive.jpg",
        "processingTime": 3,
        "availableRegions": [{"regionId": "US"}],
        "children": [
            {
                "skuId": "sku-id-archive",
                "skuCode": "sku-code-archive",
                "shipFrom": "US",
                "skuPicList": ["https://cdn.example.com/archive-variant.jpg"],
                "variantProps": [{"propName": "Color", "propValue": "Black"}],
                "stocks": [{"regionId": "US", "regionName": "United States", "itemNo": "ITEM-ARCHIVE", "availableNum": 15}],
            }
        ],
    }

    archive_inputs = _build_archive_inputs_from_detail(
        detail=detail,
        stock_map={"ITEM-ARCHIVE": {"itemNo": "ITEM-ARCHIVE", "sellingPrice": "40", "msrpPrice": "55", "warehouseName": "Texas Warehouse"}},
        shipping_map={"ITEM-ARCHIVE": {"cost": {"shipFee": 5, "shipName": "Ground", "shipTime": "3-5", "stockRegion": "US", "warehouseName": "Texas Warehouse"}}},
        target_country="US",
    )

    row = archive_inputs[0]
    assert row.supplier_spu_no == "SPU-ARCHIVE"
    assert row.category_id == "cat-archive"
    assert row.category_name == "Outdoor Storage"
    assert row.source_vendor == "DOBA"
    assert row.source_channels == ["Inbox", "Shop", "Pinterest", "Facebook & Instagram"]
    assert row.ship_from_country == "United States"
    assert row.ship_from_raw == "US"
    assert row.ship_from_source == "child.shipFrom"
    assert row.ship_from_confidence == "high"
    assert row.warehouse_name == "Texas Warehouse"
    assert row.seller_name == "Archive Seller"
    assert row.category_metafields["doba_category_id"] == "cat-archive"


def test_publish_doba_products_live_resumes_from_checkpoint_and_continues(tmp_path):
    report_path = tmp_path / "live-report.json"
    report_path.write_text(
        json.dumps(
            {
                "started_at": "2026-06-15T00:00:00+00:00",
                "updated_at": "2026-06-15T00:00:00+00:00",
                "cursor": {"next_page": 1, "next_index": 0},
                "successful_spu_nos": ["D0100OLDSPU1"],
                "results": [],
                "summary": {
                    "total_candidates": 0,
                    "scanned_count": 0,
                    "published_count": 0,
                    "skipped_count": 0,
                    "failed_count": 0,
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    candidate = DobaProductCandidate(
        spu_id="spu-2",
        spu_no="D0100NEWSPU2",
        supplier_id="seller-2",
        category_id="cat-2",
        merge_key="merge-spu-2",
        seller_name="Seller B",
        seller_info={},
        title="Storage Shelf",
        category_name="Storage",
        description_html="<p>Shelf</p>",
        brand="Doba Basics",
        ship_from_country="US",
        processing_time=3,
        store_url="https://www.doba.com/example",
        image_urls=["https://cdn.example.com/shelf.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-2",
                sku_code="sku-code-2",
                sku_id="sku-id-2",
                option_values={"Color": "Black"},
                inventory=18,
                source_price=34.99,
                shipping_cost=4.5,
                cost_price=39.49,
                sale_price=79.99,
                compare_at_price=89.99,
                ship_time_days=7,
                item_no="ITEM-2",
                ship_name="Ground",
                warehouse="US",
                image_urls=["https://cdn.example.com/shelf-black.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    with patch("src.modules.shopify_listing.application.live_publish_runtime.DobaClient.from_settings") as doba_from_settings:
        with patch("src.modules.shopify_listing.application.live_publish_runtime.ShopifyAuthClient.from_settings") as shopify_from_settings:
            with patch(
                "src.modules.shopify_listing.application.live_publish_runtime._get_publication_map",
                return_value={
                    "Inbox": {"id": "pub-inbox"},
                    "Shop": {"id": "pub-shop"},
                    "Pinterest": {"id": "pub-pinterest"},
                    "Facebook & Instagram": {"id": "pub-fb"},
                },
            ):
                with patch("src.modules.shopify_listing.application.live_publish_runtime._ensure_collection", return_value={"id": "col-1"}):
                    with patch("src.modules.shopify_listing.application.live_publish_runtime._fetch_platform_id", return_value="platform-1"):
                        with patch("src.modules.shopify_listing.application.live_publish_runtime._fetch_spu_page") as fetch_spu_page:
                            with patch(
                                "src.modules.shopify_listing.application.live_publish_runtime._fetch_spu_details",
                                return_value={
                                    "D0100OLDSPU1": {"spuNo": "D0100OLDSPU1"},
                                    "D0100NEWSPU2": {"spuNo": "D0100NEWSPU2", "spuId": "spu-2", "title": "Storage Shelf"},
                                },
                            ):
                                with patch("src.modules.shopify_listing.application.live_publish_runtime._fetch_stock_map", return_value={}):
                                    with patch("src.modules.shopify_listing.application.live_publish_runtime._fetch_shipping_map", return_value={}):
                                        with patch("src.modules.shopify_listing.application.live_publish_runtime._fetch_seller_info", return_value={}):
                                            with patch("src.modules.shopify_listing.application.live_publish_runtime._build_product_candidate", return_value=(candidate, None)):
                                                with patch(
                                                    "src.modules.shopify_listing.application.live_publish_runtime._publish_candidate_to_shopify",
                                                    return_value={
                                                        "action": "published",
                                                        "reason": "",
                                                        "shopify_product_id": "gid://shopify/Product/2",
                                                        "variant_count": 1,
                                                        "published_to": ["Inbox", "Shop", "Pinterest", "Facebook & Instagram"],
                                                    },
                                                ):
                                                    doba_from_settings.return_value = object()
                                                    shopify_from_settings.return_value = object()
                                                    fetch_spu_page.side_effect = [
                                                        (
                                                            2,
                                                            [
                                                                {"spuId": "spu-1", "spuNo": "D0100OLDSPU1", "title": "Old Product"},
                                                                {"spuId": "spu-2", "spuNo": "D0100NEWSPU2", "title": "Storage Shelf"},
                                                            ],
                                                        ),
                                                        (2, []),
                                                    ]

                                                    result = publish_doba_products_live(
                                                        report_path=str(report_path),
                                                        resume=True,
                                                        prefer_candidate_pool=False,
                                                        page_size=20,
                                                        max_successes=1,
                                                    )

    assert result["summary"]["scanned_count"] == 2
    assert result["summary"]["skipped_count"] == 1
    assert result["summary"]["published_count"] == 1
    assert result["successful_spu_nos"] == ["D0100NEWSPU2", "D0100OLDSPU1"]
    assert result["results"][0]["reason"] == "already_successfully_published"
    assert result["results"][1]["shopify_product_id"] == "gid://shopify/Product/2"


def test_publish_doba_products_live_prefers_candidate_pool_and_skips_direct_doba_scan(tmp_path):
    report_path = tmp_path / "live-report-candidate-pool.json"
    report_path.write_text(
        json.dumps(
            {
                "started_at": "2026-06-17T00:00:00+00:00",
                "updated_at": "2026-06-17T00:00:00+00:00",
                "cursor": {"next_page": 1, "next_index": 0},
                "successful_spu_nos": [],
                "results": [],
                "summary": {
                    "total_candidates": 0,
                    "scanned_count": 0,
                    "published_count": 0,
                    "skipped_count": 0,
                    "failed_count": 0,
                },
                "source_mode": "candidate_pool",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    candidate = DobaProductCandidate(
        spu_id="spu-candidate-1",
        spu_no="SPU-CANDIDATE-1",
        supplier_id="seller-candidate-1",
        category_id="cat-1",
        merge_key="merge-candidate-1",
        seller_name="Seller A",
        seller_info={},
        title="Archive Candidate Product",
        category_name="Outdoor Furniture",
        description_html="<p>Archive candidate</p>",
        brand="Doba Basics",
        ship_from_country="United States",
        processing_time=3,
        store_url="",
        image_urls=["https://cdn.example.com/candidate.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-CANDIDATE-1",
                sku_code="SKU-CANDIDATE-1",
                sku_id="sku-id-candidate-1",
                option_values={"Color": "Blue"},
                inventory=20,
                source_price=40.0,
                shipping_cost=5.0,
                cost_price=45.0,
                sale_price=50.0,
                compare_at_price=60.0,
                ship_time_days=4,
                item_no="ITEM-CANDIDATE-1",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/candidate-blue.jpg"],
                warehouse_name="US Warehouse",
                ship_from_raw="United States",
            )
        ],
        tags=["doba-import"],
        category_metafields={
            "doba_category_id": "cat-1",
            "doba_category_name": "Outdoor Furniture",
            "shopify_category_id": "gid://shopify/TaxonomyCategory/1",
            "shopify_category_name": "Home > Outdoor",
        },
    )
    pool_payload = {
        "generated_at": "2026-06-17T00:00:00+00:00",
        "source_mode": "archive_candidate_pool",
        "summary": {"qualified_count": 1},
        "qualified_candidates": [_serialize_candidate(candidate)],
    }
    mapping_repository = Mock()
    mapping_repository.list_publish_mappings.return_value = []

    with patch("src.modules.shopify_listing.application.live_publish_runtime.SQLitePublishMappingRepository", return_value=mapping_repository):
        with patch("src.modules.shopify_listing.application.live_publish_runtime.ShopifyAuthClient.from_settings") as shopify_from_settings:
            with patch("src.modules.shopify_listing.application.live_publish_runtime.DobaClient.from_settings") as doba_from_settings:
                with patch(
                    "src.modules.shopify_listing.application.live_publish_runtime._get_publication_map",
                    return_value={
                        "Inbox": {"id": "pub-inbox"},
                        "Shop": {"id": "pub-shop"},
                        "Pinterest": {"id": "pub-pinterest"},
                        "Facebook & Instagram": {"id": "pub-fb"},
                    },
                ):
                    with patch("src.modules.shopify_listing.application.live_publish_runtime._ensure_collection", return_value={"id": "col-1"}):
                        with patch("src.modules.shopify_listing.application.live_publish_runtime._load_candidate_pool", return_value=pool_payload):
                            with patch(
                                "src.modules.shopify_listing.application.live_publish_runtime._publish_candidate_to_shopify",
                                    return_value={
                                        "action": "published",
                                        "reason": "",
                                        "shopify_product_id": "gid://shopify/Product/1",
                                        "variant_count": 1,
                                        "published_to": ["Inbox", "Shop", "Pinterest", "Facebook & Instagram"],
                                        "shopify_status": "ACTIVE",
                                        "shopify_category_id": "gid://shopify/TaxonomyCategory/1",
                                        "shopify_category_name": "Home > Outdoor",
                                    },
                                ):
                                shopify_from_settings.return_value = object()
                                result = publish_doba_products_live(
                                    report_path=str(report_path),
                                    prefer_candidate_pool=True,
                                    page_size=20,
                                )

    doba_from_settings.assert_not_called()
    assert result["summary"]["published_count"] == 1
    assert result["source_mode"] == "candidate_pool"
    assert result["results"][-1]["doba_spu_no"] == "SPU-CANDIDATE-1"
    assert result["results"][-1]["content_enrichment_summary"]["geo_score"] >= 70
    assert result["results"][-1]["post_publish_review"]["publish_ready"] is True


def test_publish_doba_products_live_targets_only_requested_candidate_spu_nos(tmp_path):
    report_path = tmp_path / "live-report-targeted-candidate-pool.json"
    candidate_one = DobaProductCandidate(
        spu_id="spu-candidate-1",
        spu_no="SPU-CANDIDATE-1",
        supplier_id="seller-candidate-1",
        category_id="cat-1",
        merge_key="merge-candidate-1",
        seller_name="Seller A",
        seller_info={},
        title="Archive Candidate Product 1",
        category_name="Outdoor Furniture",
        description_html="<p>Archive candidate 1</p>",
        brand="Doba Basics",
        ship_from_country="United States",
        processing_time=3,
        store_url="",
        image_urls=["https://cdn.example.com/candidate-1.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-CANDIDATE-1",
                sku_code="SKU-CANDIDATE-1",
                sku_id="sku-id-candidate-1",
                option_values={"Color": "Blue"},
                inventory=20,
                source_price=40.0,
                shipping_cost=5.0,
                cost_price=45.0,
                sale_price=50.0,
                compare_at_price=60.0,
                ship_time_days=4,
                item_no="ITEM-CANDIDATE-1",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/candidate-blue.jpg"],
                warehouse_name="US Warehouse",
                ship_from_raw="United States",
            )
        ],
        tags=["doba-import"],
        category_metafields={"shopify_category_id": "gid://shopify/TaxonomyCategory/1"},
    )
    candidate_two = DobaProductCandidate(
        spu_id="spu-candidate-2",
        spu_no="SPU-CANDIDATE-2",
        supplier_id="seller-candidate-2",
        category_id="cat-2",
        merge_key="merge-candidate-2",
        seller_name="Seller B",
        seller_info={},
        title="Archive Candidate Product 2",
        category_name="Outdoor Furniture",
        description_html="<p>Archive candidate 2</p>",
        brand="Doba Basics",
        ship_from_country="United States",
        processing_time=3,
        store_url="",
        image_urls=["https://cdn.example.com/candidate-2.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-CANDIDATE-2",
                sku_code="SKU-CANDIDATE-2",
                sku_id="sku-id-candidate-2",
                option_values={"Color": "Green"},
                inventory=18,
                source_price=41.0,
                shipping_cost=6.0,
                cost_price=47.0,
                sale_price=53.15,
                compare_at_price=63.0,
                ship_time_days=4,
                item_no="ITEM-CANDIDATE-2",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/candidate-green.jpg"],
                warehouse_name="US Warehouse",
                ship_from_raw="United States",
            )
        ],
        tags=["doba-import"],
        category_metafields={"shopify_category_id": "gid://shopify/TaxonomyCategory/1"},
    )
    pool_payload = {
        "generated_at": "2026-06-25T00:00:00+00:00",
        "source_mode": "archive_candidate_pool",
        "summary": {"qualified_count": 2},
        "qualified_candidates": [
            _serialize_candidate(candidate_one),
            _serialize_candidate(candidate_two),
        ],
    }
    mapping_repository = Mock()
    mapping_repository.list_publish_mappings.return_value = []

    with patch("src.modules.shopify_listing.application.live_publish_runtime.SQLitePublishMappingRepository", return_value=mapping_repository):
        with patch("src.modules.shopify_listing.application.live_publish_runtime.ShopifyAuthClient.from_settings", return_value=object()):
            with patch(
                "src.modules.shopify_listing.application.live_publish_runtime._get_publication_map",
                return_value={
                    "Inbox": {"id": "pub-inbox"},
                    "Shop": {"id": "pub-shop"},
                    "Pinterest": {"id": "pub-pinterest"},
                    "Facebook & Instagram": {"id": "pub-fb"},
                },
            ):
                with patch("src.modules.shopify_listing.application.live_publish_runtime._ensure_collection", return_value={"id": "col-1"}):
                    with patch("src.modules.shopify_listing.application.live_publish_runtime._load_candidate_pool", return_value=pool_payload):
                        with patch(
                            "src.modules.shopify_listing.application.live_publish_runtime._publish_candidate_to_shopify",
                            return_value={
                                "action": "published",
                                "reason": "",
                                "shopify_product_id": "gid://shopify/Product/2",
                                "variant_count": 1,
                                "published_to": ["Inbox", "Shop", "Pinterest", "Facebook & Instagram"],
                                "shopify_status": "ACTIVE",
                            },
                        ) as publish_mock:
                            result = publish_doba_products_live(
                                report_path=str(report_path),
                                prefer_candidate_pool=True,
                                candidate_spu_nos=["SPU-CANDIDATE-2"],
                                page_size=20,
                            )

    published_candidate = publish_mock.call_args.kwargs["candidate"]
    assert published_candidate.spu_no == "SPU-CANDIDATE-2"
    assert result["summary"]["published_count"] == 1
    assert result["summary"]["total_candidates"] == 1
    assert result["results"][-1]["doba_spu_no"] == "SPU-CANDIDATE-2"


def test_publish_doba_products_live_refreshes_candidate_pool_before_shopify_publications(tmp_path):
    report_path = tmp_path / "live-report-refresh-first.json"
    candidate = DobaProductCandidate(
        spu_id="spu-candidate-refresh",
        spu_no="SPU-CANDIDATE-REFRESH",
        supplier_id="seller-refresh",
        category_id="cat-refresh",
        merge_key="merge-refresh",
        seller_name="Seller Refresh",
        seller_info={},
        title="Refresh Candidate Product",
        category_name="Outdoor Furniture",
        description_html="<p>Refresh candidate</p>",
        brand="Doba Basics",
        ship_from_country="United States",
        processing_time=3,
        store_url="",
        image_urls=["https://cdn.example.com/refresh.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-REFRESH-1",
                sku_code="SKU-REFRESH-1",
                sku_id="sku-id-refresh-1",
                option_values={"Color": "Green"},
                inventory=19,
                source_price=41.0,
                shipping_cost=5.0,
                cost_price=46.0,
                sale_price=51.25,
                compare_at_price=61.0,
                ship_time_days=4,
                item_no="ITEM-REFRESH-1",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/refresh-green.jpg"],
                warehouse_name="US Warehouse",
                ship_from_raw="United States",
            )
        ],
        tags=["doba-import"],
        category_metafields={
            "doba_category_id": "cat-refresh",
            "doba_category_name": "Outdoor Furniture",
            "shopify_category_id": "gid://shopify/TaxonomyCategory/1",
            "shopify_category_name": "Home > Outdoor",
        },
    )
    pool_payload = {
        "generated_at": "2026-06-17T00:00:00+00:00",
        "source_mode": "archive_candidate_pool",
        "summary": {"qualified_count": 1},
        "qualified_candidates": [_serialize_candidate(candidate)],
    }
    call_order: list[str] = []
    mapping_repository = Mock()
    mapping_repository.list_publish_mappings.return_value = []

    def fake_build_candidate_pool(**kwargs):
        call_order.append("build_candidate_pool")
        candidate_pool_path = Path(str(kwargs["candidate_pool_path"]))
        candidate_pool_path.parent.mkdir(parents=True, exist_ok=True)
        candidate_pool_path.write_text(json.dumps(pool_payload, ensure_ascii=False), encoding="utf-8")
        return pool_payload

    def fake_get_publication_map(client):
        call_order.append("get_publication_map")
        return {
            "Inbox": {"id": "pub-inbox"},
            "Shop": {"id": "pub-shop"},
            "Pinterest": {"id": "pub-pinterest"},
            "Facebook & Instagram": {"id": "pub-fb"},
        }

    with patch("src.modules.shopify_listing.application.live_publish_runtime.SQLitePublishMappingRepository", return_value=mapping_repository):
        with patch("src.modules.shopify_listing.application.live_publish_runtime.ShopifyAuthClient.from_settings") as shopify_from_settings:
            with patch("src.modules.shopify_listing.application.live_publish_runtime.DobaClient.from_settings") as doba_from_settings:
                with patch(
                    "src.modules.shopify_listing.application.live_publish_runtime.build_doba_publish_candidate_pool",
                    side_effect=fake_build_candidate_pool,
                ):
                    with patch(
                        "src.modules.shopify_listing.application.live_publish_runtime._get_publication_map",
                        side_effect=fake_get_publication_map,
                    ):
                        with patch("src.modules.shopify_listing.application.live_publish_runtime._ensure_collection", return_value={"id": "col-1"}):
                            with patch(
                                "src.modules.shopify_listing.application.live_publish_runtime._publish_candidate_to_shopify",
                                return_value={
                                    "action": "published",
                                    "reason": "",
                                    "shopify_product_id": "gid://shopify/Product/refresh",
                                    "variant_count": 1,
                                    "published_to": ["Inbox", "Shop", "Pinterest", "Facebook & Instagram"],
                                    "shopify_status": "ACTIVE",
                                },
                            ):
                                shopify_from_settings.return_value = object()
                                result = publish_doba_products_live(
                                    report_path=str(report_path),
                                    prefer_candidate_pool=True,
                                    refresh_candidate_pool=True,
                                    page_size=20,
                                )

    doba_from_settings.assert_not_called()
    assert call_order[:2] == ["build_candidate_pool", "get_publication_map"]
    assert result["summary"]["published_count"] == 1


def test_publish_doba_products_live_refresh_candidate_pool_resets_stale_candidate_pool_report_but_keeps_published_dedup(tmp_path):
    report_path = tmp_path / "live-report-refresh-reset.json"
    report_path.write_text(
        json.dumps(
            {
                "started_at": "2026-06-17T00:00:00+00:00",
                "updated_at": "2026-06-17T00:00:00+00:00",
                "cursor": {"next_page": 4, "next_index": 9},
                "successful_spu_nos": [],
                "results": [{"doba_spu_no": "OLD-SPU", "action": "failed"}],
                "summary": {
                    "total_candidates": 99,
                    "scanned_count": 99,
                    "published_count": 3,
                    "skipped_count": 90,
                    "failed_count": 6,
                },
                "source_mode": "candidate_pool",
                "candidate_pool_generation": "2026-06-16T00:00:00+00:00",
                "last_failure": {"failed_spu_no": "OLD-SPU"},
                "completed": True,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    candidate = DobaProductCandidate(
        spu_id="spu-refresh-reset",
        spu_no="SPU-REFRESH-RESET",
        supplier_id="seller-refresh-reset",
        category_id="cat-refresh-reset",
        merge_key="merge-refresh-reset",
        seller_name="Seller Refresh Reset",
        seller_info={},
        title="Refresh Reset Candidate",
        category_name="Outdoor Furniture",
        description_html="<p>Refresh reset candidate</p>",
        brand="Doba Basics",
        ship_from_country="United States",
        processing_time=3,
        store_url="",
        image_urls=["https://cdn.example.com/refresh-reset.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-REFRESH-RESET-1",
                sku_code="SKU-REFRESH-RESET-1",
                sku_id="sku-id-refresh-reset-1",
                option_values={"Color": "Green"},
                inventory=19,
                source_price=41.0,
                shipping_cost=5.0,
                cost_price=46.0,
                sale_price=51.25,
                compare_at_price=61.0,
                ship_time_days=4,
                item_no="ITEM-REFRESH-RESET-1",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/refresh-reset-green.jpg"],
                warehouse_name="US Warehouse",
                ship_from_raw="United States",
            )
        ],
        tags=["doba-import"],
        category_metafields={
            "doba_category_id": "cat-refresh-reset",
            "doba_category_name": "Outdoor Furniture",
            "shopify_category_id": "gid://shopify/TaxonomyCategory/1",
            "shopify_category_name": "Home > Outdoor",
        },
    )
    pool_payload = {
        "generated_at": "2026-06-17T00:00:00+00:00",
        "source_mode": "archive_candidate_pool",
        "summary": {"qualified_count": 1},
        "qualified_candidates": [_serialize_candidate(candidate)],
    }

    published_record = Mock()
    published_record.supplier_spu_no = "D0100ALREADYPUB"
    published_record.status = "published"
    mapping_repository = Mock()
    mapping_repository.list_publish_mappings.return_value = [published_record]

    def fake_build_candidate_pool(**kwargs):
        candidate_pool_path = Path(str(kwargs["candidate_pool_path"]))
        candidate_pool_path.parent.mkdir(parents=True, exist_ok=True)
        candidate_pool_path.write_text(json.dumps(pool_payload, ensure_ascii=False), encoding="utf-8")
        return pool_payload

    with patch("src.modules.shopify_listing.application.live_publish_runtime.SQLitePublishMappingRepository", return_value=mapping_repository):
        with patch("src.modules.shopify_listing.application.live_publish_runtime.ShopifyAuthClient.from_settings") as shopify_from_settings:
            with patch(
                "src.modules.shopify_listing.application.live_publish_runtime.build_doba_publish_candidate_pool",
                side_effect=fake_build_candidate_pool,
            ):
                with patch(
                    "src.modules.shopify_listing.application.live_publish_runtime._get_publication_map",
                    return_value={
                        "Inbox": {"id": "pub-inbox"},
                        "Shop": {"id": "pub-shop"},
                        "Pinterest": {"id": "pub-pinterest"},
                        "Facebook & Instagram": {"id": "pub-fb"},
                    },
                ):
                    with patch("src.modules.shopify_listing.application.live_publish_runtime._ensure_collection", return_value={"id": "col-1"}):
                        with patch(
                            "src.modules.shopify_listing.application.live_publish_runtime._publish_candidate_to_shopify",
                            return_value={
                                "action": "published",
                                "reason": "",
                                "shopify_product_id": "gid://shopify/Product/refresh-reset",
                                "variant_count": 1,
                                "published_to": ["Inbox", "Shop", "Pinterest", "Facebook & Instagram"],
                                "shopify_status": "ACTIVE",
                            },
                        ):
                            shopify_from_settings.return_value = object()
                            result = publish_doba_products_live(
                                report_path=str(report_path),
                                prefer_candidate_pool=True,
                                refresh_candidate_pool=True,
                                page_size=20,
                            )

    assert result["cursor"] == {"next_page": 2, "next_index": 0}
    assert result["summary"]["total_candidates"] == 1
    assert result["summary"]["scanned_count"] == 1
    assert result["summary"]["published_count"] == 1
    assert len(result["results"]) == 1
    assert result["results"][0]["doba_spu_no"] == "SPU-REFRESH-RESET"
    assert "last_failure" not in result
    assert result["successful_spu_nos"] == ["D0100ALREADYPUB", "SPU-REFRESH-RESET"]


def test_publish_doba_products_live_handles_interrupt_during_candidate_pool_refresh(tmp_path):
    report_path = tmp_path / "live-report-candidate-pool-interrupted.json"
    mapping_repository = Mock()
    mapping_repository.list_publish_mappings.return_value = []
    candidate_pool_path = tmp_path / "candidate-pool.json"
    candidate_pool_path.write_text(
        json.dumps(
            {
                "generated_at": "",
                "updated_at": "2026-06-17T00:00:00+00:00",
                "source_mode": "archive_candidate_pool",
                "target_country": "US",
                "inventory_threshold": 10,
                "summary": {
                    "archive_groups": 20806,
                    "qualified_count": 0,
                    "skipped_by_reason": {"ship_from_not_us_or_unknown": 9233},
                },
                "progress": {
                    "total_groups": 20806,
                    "current_index": 9233,
                    "next_index": 9233,
                    "completed": False,
                },
                "qualified_candidates": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with patch("src.modules.shopify_listing.application.live_publish_runtime.SQLitePublishMappingRepository", return_value=mapping_repository):
        with patch(
            "src.modules.shopify_listing.application.live_publish_runtime.build_doba_publish_candidate_pool",
            side_effect=KeyboardInterrupt,
        ):
            result = publish_doba_products_live(
                report_path=str(report_path),
                prefer_candidate_pool=True,
                refresh_candidate_pool=True,
                candidate_pool_path=str(candidate_pool_path),
            )

    assert result["stopped_reason"] == "interrupted_by_user"
    assert result["candidate_pool_summary"]["archive_groups"] == 20806
    assert result["last_failure"]["failed_reason"] == "interrupted_by_user"
    assert result["last_failure"]["resume_position"]["candidate_pool_progress"]["current_index"] == 9233


def test_publish_doba_products_live_does_not_fallback_to_direct_scan_when_candidate_pool_is_empty(tmp_path):
    report_path = tmp_path / "live-report-empty-pool.json"
    pool_payload = {
        "generated_at": "2026-06-17T00:00:00+00:00",
        "source_mode": "archive_candidate_pool",
        "summary": {"qualified_count": 0, "skipped_by_reason": {"ship_from_not_us_or_unknown": 5}},
        "qualified_candidates": [],
    }

    with patch("src.modules.shopify_listing.application.live_publish_runtime._load_candidate_pool", return_value=pool_payload):
        with patch("src.modules.shopify_listing.application.live_publish_runtime.ShopifyAuthClient.from_settings") as shopify_from_settings:
            with patch("src.modules.shopify_listing.application.live_publish_runtime.DobaClient.from_settings") as doba_from_settings:
                result = publish_doba_products_live(
                    report_path=str(report_path),
                    prefer_candidate_pool=True,
                    refresh_candidate_pool=False,
                    page_size=20,
                )

    shopify_from_settings.assert_not_called()
    doba_from_settings.assert_not_called()
    assert result["source_mode"] == "candidate_pool"
    assert result["summary"]["total_candidates"] == 0
    assert result["completed"] is True


def test_publish_doba_products_live_reuses_existing_candidate_pool_progress_without_refresh(tmp_path):
    report_path = tmp_path / "live-report-existing-pool-progress.json"
    report_path.write_text(
        json.dumps(
            {
                "started_at": "2026-06-17T00:00:00+00:00",
                "updated_at": "2026-06-17T00:00:00+00:00",
                "cursor": {"next_page": 1, "next_index": 1},
                "successful_spu_nos": [],
                "results": [{"doba_spu_no": "SPU-FIRST", "action": "published"}],
                "summary": {
                    "total_candidates": 2,
                    "scanned_count": 1,
                    "published_count": 1,
                    "skipped_count": 0,
                    "failed_count": 0,
                },
                "source_mode": "candidate_pool",
                "candidate_pool_generation": "2026-06-17T00:00:00+00:00",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    first_candidate = DobaProductCandidate(
        spu_id="spu-first",
        spu_no="SPU-FIRST",
        supplier_id="seller-first",
        category_id="cat-first",
        merge_key="merge-first",
        seller_name="Seller First",
        seller_info={},
        title="First Candidate",
        category_name="Outdoor Furniture",
        description_html="<p>First candidate</p>",
        brand="Doba Basics",
        ship_from_country="United States",
        processing_time=3,
        store_url="",
        image_urls=["https://cdn.example.com/first.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-FIRST-1",
                sku_code="SKU-FIRST-1",
                sku_id="sku-id-first-1",
                option_values={"Color": "Blue"},
                inventory=20,
                source_price=40.0,
                shipping_cost=5.0,
                cost_price=45.0,
                sale_price=50.0,
                compare_at_price=60.0,
                ship_time_days=4,
                item_no="ITEM-FIRST-1",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/first-blue.jpg"],
                warehouse_name="US Warehouse",
                ship_from_raw="United States",
            )
        ],
        tags=["doba-import"],
        category_metafields={
            "doba_category_id": "cat-first",
            "doba_category_name": "Outdoor Furniture",
            "shopify_category_id": "gid://shopify/TaxonomyCategory/1",
            "shopify_category_name": "Home > Outdoor",
        },
    )
    second_candidate = DobaProductCandidate(
        spu_id="spu-second",
        spu_no="SPU-SECOND",
        supplier_id="seller-second",
        category_id="cat-second",
        merge_key="merge-second",
        seller_name="Seller Second",
        seller_info={},
        title="Second Candidate",
        category_name="Outdoor Furniture",
        description_html="<p>Second candidate</p>",
        brand="Doba Basics",
        ship_from_country="United States",
        processing_time=3,
        store_url="",
        image_urls=["https://cdn.example.com/second.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-SECOND-1",
                sku_code="SKU-SECOND-1",
                sku_id="sku-id-second-1",
                option_values={"Color": "Green"},
                inventory=18,
                source_price=41.0,
                shipping_cost=5.0,
                cost_price=46.0,
                sale_price=51.25,
                compare_at_price=61.0,
                ship_time_days=4,
                item_no="ITEM-SECOND-1",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/second-green.jpg"],
                warehouse_name="US Warehouse",
                ship_from_raw="United States",
            )
        ],
        tags=["doba-import"],
        category_metafields={
            "doba_category_id": "cat-second",
            "doba_category_name": "Outdoor Furniture",
            "shopify_category_id": "gid://shopify/TaxonomyCategory/1",
            "shopify_category_name": "Home > Outdoor",
        },
    )
    pool_payload = {
        "generated_at": "2026-06-17T00:00:00+00:00",
        "source_mode": "archive_candidate_pool",
        "summary": {"qualified_count": 2},
        "qualified_candidates": [_serialize_candidate(first_candidate), _serialize_candidate(second_candidate)],
    }
    mapping_repository = Mock()
    mapping_repository.list_publish_mappings.return_value = []

    with patch("src.modules.shopify_listing.application.live_publish_runtime.SQLitePublishMappingRepository", return_value=mapping_repository):
        with patch("src.modules.shopify_listing.application.live_publish_runtime._load_candidate_pool", return_value=pool_payload):
            with patch("src.modules.shopify_listing.application.live_publish_runtime.ShopifyAuthClient.from_settings") as shopify_from_settings:
                with patch(
                    "src.modules.shopify_listing.application.live_publish_runtime._get_publication_map",
                    return_value={
                        "Inbox": {"id": "pub-inbox"},
                        "Shop": {"id": "pub-shop"},
                        "Pinterest": {"id": "pub-pinterest"},
                        "Facebook & Instagram": {"id": "pub-fb"},
                    },
                ):
                    with patch("src.modules.shopify_listing.application.live_publish_runtime._ensure_collection", return_value={"id": "col-1"}):
                        with patch(
                            "src.modules.shopify_listing.application.live_publish_runtime._publish_candidate_to_shopify",
                            return_value={
                                "action": "published",
                                "reason": "",
                                "shopify_product_id": "gid://shopify/Product/second",
                                "variant_count": 1,
                                "published_to": ["Inbox", "Shop", "Pinterest", "Facebook & Instagram"],
                                "shopify_status": "ACTIVE",
                            },
                        ) as publish_candidate:
                            shopify_from_settings.return_value = object()
                            result = publish_doba_products_live(
                                report_path=str(report_path),
                                prefer_candidate_pool=True,
                                refresh_candidate_pool=False,
                                page_size=20,
                            )

    publish_candidate.assert_called_once()
    assert result["summary"]["scanned_count"] == 2
    assert result["summary"]["published_count"] == 2
    assert len(result["results"]) == 2
    assert result["results"][-1]["doba_spu_no"] == "SPU-SECOND"


def test_publish_doba_products_live_preserves_candidate_pool_resume_position_when_generation_changes(tmp_path):
    report_path = tmp_path / "live-report-generation-shift.json"
    report_path.write_text(
        json.dumps(
            {
                "started_at": "2026-06-17T00:00:00+00:00",
                "updated_at": "2026-06-17T00:00:00+00:00",
                "cursor": {"next_page": 1, "next_index": 1},
                "successful_spu_nos": ["SPU-FIRST"],
                "results": [{"doba_spu_no": "SPU-FIRST", "action": "published"}],
                "summary": {
                    "total_candidates": 2,
                    "scanned_count": 1,
                    "published_count": 1,
                    "skipped_count": 0,
                    "failed_count": 0,
                },
                "source_mode": "candidate_pool",
                "candidate_pool_generation": "2026-06-17T00:00:00+00:00",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    first_candidate = DobaProductCandidate(
        spu_id="spu-first",
        spu_no="SPU-FIRST",
        supplier_id="seller-first",
        category_id="cat-first",
        merge_key="merge-first",
        seller_name="Seller First",
        seller_info={},
        title="First Candidate",
        category_name="Outdoor Furniture",
        description_html="<p>First candidate</p>",
        brand="Doba Basics",
        ship_from_country="United States",
        processing_time=3,
        store_url="",
        image_urls=["https://cdn.example.com/first.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-FIRST-1",
                sku_code="SKU-FIRST-1",
                sku_id="sku-id-first-1",
                option_values={"Color": "Blue"},
                inventory=20,
                source_price=40.0,
                shipping_cost=5.0,
                cost_price=45.0,
                sale_price=50.0,
                compare_at_price=60.0,
                ship_time_days=4,
                item_no="ITEM-FIRST-1",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/first-blue.jpg"],
                warehouse_name="US Warehouse",
                ship_from_raw="United States",
            )
        ],
        tags=["doba-import"],
        category_metafields={
            "doba_category_id": "cat-first",
            "doba_category_name": "Outdoor Furniture",
            "shopify_category_id": "gid://shopify/TaxonomyCategory/1",
            "shopify_category_name": "Home > Outdoor",
        },
    )
    second_candidate = DobaProductCandidate(
        spu_id="spu-second",
        spu_no="SPU-SECOND",
        supplier_id="seller-second",
        category_id="cat-second",
        merge_key="merge-second",
        seller_name="Seller Second",
        seller_info={},
        title="Second Candidate",
        category_name="Patio Chairs",
        description_html="<p>Second candidate</p>",
        brand="Doba Basics",
        ship_from_country="United States",
        processing_time=3,
        store_url="",
        image_urls=["https://cdn.example.com/second.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-SECOND-1",
                sku_code="SKU-SECOND-1",
                sku_id="sku-id-second-1",
                option_values={"Color": "Green"},
                inventory=18,
                source_price=41.0,
                shipping_cost=5.0,
                cost_price=46.0,
                sale_price=51.25,
                compare_at_price=61.0,
                ship_time_days=4,
                item_no="ITEM-SECOND-1",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/second-green.jpg"],
                warehouse_name="US Warehouse",
                ship_from_raw="United States",
            )
        ],
        tags=["doba-import"],
        category_metafields={
            "doba_category_id": "cat-second",
            "doba_category_name": "Patio Chairs",
            "shopify_category_id": "gid://shopify/TaxonomyCategory/2",
            "shopify_category_name": "Home > Patio",
        },
    )
    third_candidate = DobaProductCandidate(
        spu_id="spu-third",
        spu_no="SPU-THIRD",
        supplier_id="seller-third",
        category_id="cat-third",
        merge_key="merge-third",
        seller_name="Seller Third",
        seller_info={},
        title="Third Candidate",
        category_name="Garden Raised Beds",
        description_html="<p>Third candidate</p>",
        brand="Doba Basics",
        ship_from_country="United States",
        processing_time=3,
        store_url="",
        image_urls=["https://cdn.example.com/third.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-THIRD-1",
                sku_code="SKU-THIRD-1",
                sku_id="sku-id-third-1",
                option_values={"Color": "White"},
                inventory=16,
                source_price=43.0,
                shipping_cost=5.0,
                cost_price=48.0,
                sale_price=54.45,
                compare_at_price=64.0,
                ship_time_days=4,
                item_no="ITEM-THIRD-1",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/third-white.jpg"],
                warehouse_name="US Warehouse",
                ship_from_raw="United States",
            )
        ],
        tags=["doba-import"],
        category_metafields={
            "doba_category_id": "cat-third",
            "doba_category_name": "Garden Raised Beds",
            "shopify_category_id": "gid://shopify/TaxonomyCategory/3",
            "shopify_category_name": "Garden",
        },
    )
    pool_payload = {
        "generated_at": "2026-06-18T00:00:00+00:00",
        "source_mode": "archive_candidate_pool",
        "summary": {"qualified_count": 3},
        "qualified_candidates": [
            _serialize_candidate(first_candidate),
            _serialize_candidate(second_candidate),
            _serialize_candidate(third_candidate),
        ],
    }
    mapping_repository = Mock()
    mapping_repository.list_publish_mappings.return_value = []

    with patch("src.modules.shopify_listing.application.live_publish_runtime.SQLitePublishMappingRepository", return_value=mapping_repository):
        with patch("src.modules.shopify_listing.application.live_publish_runtime._load_candidate_pool", return_value=pool_payload):
            with patch("src.modules.shopify_listing.application.live_publish_runtime.ShopifyAuthClient.from_settings") as shopify_from_settings:
                with patch(
                    "src.modules.shopify_listing.application.live_publish_runtime._get_publication_map",
                    return_value={
                        "Inbox": {"id": "pub-inbox"},
                        "Shop": {"id": "pub-shop"},
                        "Pinterest": {"id": "pub-pinterest"},
                        "Facebook & Instagram": {"id": "pub-fb"},
                    },
                ):
                    with patch("src.modules.shopify_listing.application.live_publish_runtime._ensure_collection", return_value={"id": "col-1"}):
                        with patch(
                            "src.modules.shopify_listing.application.live_publish_runtime._publish_candidate_to_shopify",
                            side_effect=[
                                {
                                    "action": "published",
                                    "reason": "",
                                    "shopify_product_id": "gid://shopify/Product/second",
                                    "variant_count": 1,
                                    "published_to": ["Inbox", "Shop", "Pinterest", "Facebook & Instagram"],
                                    "shopify_status": "ACTIVE",
                                },
                                {
                                    "action": "published",
                                    "reason": "",
                                    "shopify_product_id": "gid://shopify/Product/third",
                                    "variant_count": 1,
                                    "published_to": ["Inbox", "Shop", "Pinterest", "Facebook & Instagram"],
                                    "shopify_status": "ACTIVE",
                                },
                            ],
                        ) as publish_candidate:
                            shopify_from_settings.return_value = object()
                            result = publish_doba_products_live(
                                report_path=str(report_path),
                                prefer_candidate_pool=True,
                                refresh_candidate_pool=False,
                                page_size=20,
                            )

    assert publish_candidate.call_count == 2
    assert result["summary"]["scanned_count"] == 3
    assert result["summary"]["published_count"] == 3
    assert [item["doba_spu_no"] for item in result["results"]] == ["SPU-FIRST", "SPU-SECOND", "SPU-THIRD"]
    assert result["results"][1]["doba_spu_no"] == "SPU-SECOND"
    assert result["results"][2]["doba_spu_no"] == "SPU-THIRD"


def test_publish_different_spu_same_merge_group_updates_existing_product(tmp_path):
    report_path = tmp_path / "live-report-merge.json"
    candidate = DobaProductCandidate(
        spu_id="spu-merge-2",
        spu_no="SPU-MERGE-2",
        supplier_id="seller-merge",
        category_id="cat-merge",
        merge_key="merge-key-123",
        seller_name="Seller Merge",
        seller_info={},
        title="3 Piece Patio Lounge Set with Cushions Poly Rattan Black",
        category_name="Other Patio Furniture Sets",
        description_html="<p>Merge test</p>",
        brand="",
        ship_from_country="US",
        processing_time=3,
        store_url="https://www.doba.com/example-merge",
        image_urls=["https://cdn.example.com/merge.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-MERGE-2",
                sku_code="SKU-MERGE-2",
                sku_id="SKU-ID-MERGE-2",
                option_values={"Color": "Black"},
                inventory=18,
                source_price=34.99,
                shipping_cost=4.5,
                cost_price=39.49,
                sale_price=79.99,
                compare_at_price=89.99,
                ship_time_days=7,
                item_no="ITEM-MERGE-2",
                ship_name="Ground",
                warehouse="US",
                image_urls=["https://cdn.example.com/merge-black.jpg"],
            )
        ],
        tags=["doba-import", "doba-merge-key:merge-key-123"],
    )

    captured_publish_calls = []

    def fake_publish_candidate_to_shopify(*args, **kwargs):
        captured_publish_calls.append(kwargs["candidate"].merge_key)
        return {
            "action": "published",
            "reason": "",
            "shopify_product_id": "gid://shopify/Product/merge",
            "variant_count": 2,
            "published_to": ["Inbox", "Shop", "Pinterest", "Facebook & Instagram"],
        }

    with patch("src.modules.shopify_listing.application.live_publish_runtime.DobaClient.from_settings") as doba_from_settings:
        with patch("src.modules.shopify_listing.application.live_publish_runtime.ShopifyAuthClient.from_settings") as shopify_from_settings:
            with patch(
                "src.modules.shopify_listing.application.live_publish_runtime._get_publication_map",
                return_value={
                    "Inbox": {"id": "pub-inbox"},
                    "Shop": {"id": "pub-shop"},
                    "Pinterest": {"id": "pub-pinterest"},
                    "Facebook & Instagram": {"id": "pub-fb"},
                },
            ):
                with patch("src.modules.shopify_listing.application.live_publish_runtime._ensure_collection", return_value={"id": "col-1"}):
                    with patch("src.modules.shopify_listing.application.live_publish_runtime._fetch_platform_id", return_value="platform-1"):
                        with patch(
                            "src.modules.shopify_listing.application.live_publish_runtime._fetch_spu_page",
                            side_effect=[(1, [{"spuId": "spu-merge-2", "spuNo": "SPU-MERGE-2", "title": candidate.title}]), (1, [])],
                        ):
                            with patch(
                                "src.modules.shopify_listing.application.live_publish_runtime._fetch_spu_details",
                                return_value={"SPU-MERGE-2": {"spuNo": "SPU-MERGE-2", "spuId": "spu-merge-2", "title": candidate.title}},
                            ):
                                with patch("src.modules.shopify_listing.application.live_publish_runtime._fetch_stock_map", return_value={}):
                                    with patch("src.modules.shopify_listing.application.live_publish_runtime._fetch_shipping_map", return_value={}):
                                        with patch("src.modules.shopify_listing.application.live_publish_runtime._fetch_seller_info", return_value={}):
                                            with patch(
                                                "src.modules.shopify_listing.application.live_publish_runtime._build_product_candidate",
                                                return_value=(candidate, None),
                                            ):
                                                with patch(
                                                    "src.modules.shopify_listing.application.live_publish_runtime._publish_candidate_to_shopify",
                                                    side_effect=fake_publish_candidate_to_shopify,
                                                ):
                                                    doba_from_settings.return_value = object()
                                                    shopify_from_settings.return_value = object()
                                                    result = publish_doba_products_live(
                                                        report_path=str(report_path),
                                                        resume=False,
                                                        prefer_candidate_pool=False,
                                                        page_size=20,
                                                        max_successes=1,
                                                    )

    assert captured_publish_calls == ["merge-key-123"]
    assert result["summary"]["published_count"] == 1


def test_fetch_spu_page_passes_min_inventory_filter():
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "businessData": {
                    "businessStatus": "000000",
                    "data": {
                        "totalQuantity": 2,
                        "goodsList": [{"spuNo": "SPU-1"}, {"spuNo": "SPU-2"}],
                    },
                }
            }

    class FakeDobaClient:
        def __init__(self) -> None:
            self.calls = []

        def get(self, path, params=None):
            self.calls.append((path, params))
            return FakeResponse()

    client = FakeDobaClient()
    total, goods = _fetch_spu_page(
        client,
        page_number=3,
        page_size=20,
        ship_to_country="US",
        min_inventory=11,
    )

    assert total == 2
    assert len(goods) == 2
    assert client.calls[0][0] == "/api/goods/doba/spu/list"
    assert client.calls[0][1]["minInventory"] == 11


def test_build_product_input_uses_fixed_doba_vendor():
    candidate = DobaProductCandidate(
        spu_id="spu-9",
        spu_no="SPU-9",
        supplier_id="seller-9",
        category_id="cat-9",
        merge_key="merge-spu-9",
        seller_name="Original Seller",
        seller_info={},
        title="Accent Chair",
        category_name="Chairs & Accent Seating",
        description_html="<p>Chair</p>",
        brand="Brand X",
        ship_from_country="US",
        processing_time=2,
        store_url="https://www.doba.com/example-9",
        image_urls=["https://cdn.example.com/chair.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-9",
                sku_code="SKU-9",
                sku_id="SKU-ID-9",
                option_values={"Color": "Green"},
                inventory=19,
                source_price=50.0,
                shipping_cost=5.0,
                cost_price=55.0,
                sale_price=79.0,
                compare_at_price=89.0,
                ship_time_days=5,
                item_no="ITEM-9",
                ship_name="Ground",
                warehouse="US",
                image_urls=["https://cdn.example.com/chair-green.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    payload = _build_product_input(candidate)

    assert payload["vendor"] == SOURCE_VENDOR_NAME


def test_build_product_input_deduplicates_product_option_values():
    candidate = DobaProductCandidate(
        spu_id="spu-options",
        spu_no="SPU-OPTIONS",
        supplier_id="seller-options",
        category_id="cat-options",
        merge_key="merge-options",
        seller_name="Seller Options",
        seller_info={},
        title="Direct Wicker 5-Piece Aluminum Wicker Round Outdoor Dining Set with Cushions",
        category_name="Other Patio Furniture Sets",
        description_html="<p>Dining set</p>",
        brand="",
        ship_from_country="United States",
        processing_time=2,
        store_url="https://www.doba.com/example-options",
        image_urls=["https://cdn.example.com/options.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="SKU-1",
                sku_code="PAD-1709-B",
                sku_id="SKU-ID-1",
                option_values={"Color": "Black", "Variant": "Direct Wicker 5-Piece Aluminum Wicker Round Outdoor Dining Set with Cushions"},
                inventory=50,
                source_price=100.0,
                shipping_cost=5.0,
                cost_price=105.0,
                sale_price=125.0,
                compare_at_price=145.0,
                ship_time_days=5,
                item_no="ITEM-1",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/options-1.jpg"],
            ),
            DobaVariantCandidate(
                sku="SKU-2",
                sku_code="PAD-1709-G",
                sku_id="SKU-ID-2",
                option_values={"Color": "Gray", "Variant": "Direct Wicker 5-Piece Aluminum Wicker Round Outdoor Dining Set with Cushions"},
                inventory=50,
                source_price=100.0,
                shipping_cost=5.0,
                cost_price=105.0,
                sale_price=125.0,
                compare_at_price=145.0,
                ship_time_days=5,
                item_no="ITEM-2",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/options-2.jpg"],
            ),
        ],
        tags=["doba-import"],
    )

    payload = _build_product_input(candidate)

    option_map = {item["name"]: [value["name"] for value in item["values"]] for item in payload["productOptions"]}
    assert option_map["Color"] == ["Black", "Gray"]
    assert option_map["Variant"] == ["Direct Wicker 5-Piece Aluminum Wicker Round Outdoor Dining Set with Cushions"]


def test_update_or_create_variants_creates_all_variants_for_new_multi_sku_product():
    candidate = DobaProductCandidate(
        spu_id="spu-multi",
        spu_no="SPU-MULTI",
        supplier_id="seller-multi",
        category_id="cat-multi",
        merge_key="merge-multi",
        seller_name="Direct Wicker",
        seller_info={},
        title="Direct Wicker 7-Piece PE Rattan Wicker Patio Sectional Sofa Set with Cushions",
        category_name="Sectionals",
        description_html="<p>Sectional sofa set</p>",
        brand="",
        ship_from_country="United States",
        processing_time=2,
        store_url="https://www.doba.com/example-multi",
        image_urls=["https://cdn.example.com/multi.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-1",
                sku_code="PAS-1403B-Gray",
                sku_id="SKU-ID-1",
                option_values={"Color": "Gray"},
                inventory=50,
                source_price=100.0,
                shipping_cost=5.0,
                cost_price=105.0,
                sale_price=125.0,
                compare_at_price=145.0,
                ship_time_days=5,
                item_no="ITEM-1",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/multi-1.jpg"],
            ),
            DobaVariantCandidate(
                sku="ITEM-2",
                sku_code="PAS-1403B-Brown",
                sku_id="SKU-ID-2",
                option_values={"Color": "Brown"},
                inventory=50,
                source_price=100.0,
                shipping_cost=5.0,
                cost_price=105.0,
                sale_price=125.0,
                compare_at_price=145.0,
                ship_time_days=5,
                item_no="ITEM-2",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/multi-2.jpg"],
            ),
        ],
        tags=["doba-import"],
    )
    product = {
        "id": "gid://shopify/Product/1",
        "variants": {
            "edges": [
                {
                    "node": {
                        "id": "gid://shopify/ProductVariant/standalone",
                        "sku": "",
                        "inventoryItem": {"id": "gid://shopify/InventoryItem/standalone"},
                        "selectedOptions": [],
                    }
                }
            ]
        },
    }
    refreshed_product = {
        "variants": {
            "edges": [
                {
                    "node": {
                        "id": "gid://shopify/ProductVariant/1",
                        "sku": "ITEM-1",
                        "inventoryItem": {"id": "gid://shopify/InventoryItem/1"},
                        "selectedOptions": [{"name": "Color", "value": "Gray"}],
                    }
                },
                {
                    "node": {
                        "id": "gid://shopify/ProductVariant/2",
                        "sku": "ITEM-2",
                        "inventoryItem": {"id": "gid://shopify/InventoryItem/2"},
                        "selectedOptions": [{"name": "Color", "value": "Brown"}],
                    }
                },
            ]
        }
    }
    client = Mock()
    client.graphql.side_effect = [
        {
            "productVariantsBulkCreate": {
                "productVariants": [
                    {"id": "gid://shopify/ProductVariant/1", "sku": "ITEM-1"},
                    {"id": "gid://shopify/ProductVariant/2", "sku": "ITEM-2"},
                ],
                "userErrors": [],
            }
        },
        {"product": refreshed_product},
    ]

    variants = _update_or_create_variants(client, product=product, candidate=candidate)

    bulk_create_call = client.graphql.call_args_list[0]
    assert bulk_create_call.args[0].strip().startswith("mutation ProductVariantsBulkCreate")
    assert bulk_create_call.args[1]["variants"][0]["inventoryItem"]["sku"] == "ITEM-1"
    assert bulk_create_call.args[1]["variants"][1]["inventoryItem"]["sku"] == "ITEM-2"
    assert len(bulk_create_call.args[1]["variants"]) == 2
    assert [variant["sku"] for variant in variants] == ["ITEM-1", "ITEM-2"]


def test_update_or_create_variants_retries_until_all_shopify_skus_are_visible():
    candidate = DobaProductCandidate(
        spu_id="spu-retry",
        spu_no="SPU-RETRY",
        supplier_id="seller-retry",
        category_id="cat-retry",
        merge_key="merge-retry",
        seller_name="Direct Wicker",
        seller_info={},
        title="Direct Wicker 7-Piece Patio Sectional Sofa Set",
        category_name="Sectionals",
        description_html="<p>Retry sofa set</p>",
        brand="",
        ship_from_country="United States",
        processing_time=2,
        store_url="https://www.doba.com/example-retry",
        image_urls=["https://cdn.example.com/retry.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-A",
                sku_code="SKU-A",
                sku_id="SKU-ID-A",
                option_values={"Color": "Gray"},
                inventory=50,
                source_price=100.0,
                shipping_cost=5.0,
                cost_price=105.0,
                sale_price=125.0,
                compare_at_price=145.0,
                ship_time_days=5,
                item_no="ITEM-A",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/retry-a.jpg"],
            ),
            DobaVariantCandidate(
                sku="ITEM-B",
                sku_code="SKU-B",
                sku_id="SKU-ID-B",
                option_values={"Color": "Brown"},
                inventory=50,
                source_price=100.0,
                shipping_cost=5.0,
                cost_price=105.0,
                sale_price=125.0,
                compare_at_price=145.0,
                ship_time_days=5,
                item_no="ITEM-B",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/retry-b.jpg"],
            ),
        ],
        tags=["doba-import"],
    )
    product = {
        "id": "gid://shopify/Product/retry",
        "variants": {
            "edges": [
                {
                    "node": {
                        "id": "gid://shopify/ProductVariant/standalone",
                        "sku": "",
                        "inventoryItem": {"id": "gid://shopify/InventoryItem/standalone"},
                        "selectedOptions": [],
                    }
                }
            ]
        },
    }
    client = Mock()
    client.graphql.side_effect = [
        {
            "productVariantsBulkCreate": {
                "productVariants": [
                    {"id": "gid://shopify/ProductVariant/A", "sku": "ITEM-A"},
                    {"id": "gid://shopify/ProductVariant/B", "sku": "ITEM-B"},
                ],
                "userErrors": [],
            }
        },
        {
            "product": {
                "variants": {
                    "edges": [
                        {
                            "node": {
                                "id": "gid://shopify/ProductVariant/A",
                                "sku": "ITEM-A",
                                "inventoryItem": {"id": "gid://shopify/InventoryItem/A"},
                                "selectedOptions": [{"name": "Color", "value": "Gray"}],
                            }
                        }
                    ]
                }
            }
        },
        {
            "product": {
                "variants": {
                    "edges": [
                        {
                            "node": {
                                "id": "gid://shopify/ProductVariant/A",
                                "sku": "ITEM-A",
                                "inventoryItem": {"id": "gid://shopify/InventoryItem/A"},
                                "selectedOptions": [{"name": "Color", "value": "Gray"}],
                            }
                        },
                        {
                            "node": {
                                "id": "gid://shopify/ProductVariant/B",
                                "sku": "ITEM-B",
                                "inventoryItem": {"id": "gid://shopify/InventoryItem/B"},
                                "selectedOptions": [{"name": "Color", "value": "Brown"}],
                            }
                        },
                    ]
                }
            }
        },
    ]

    with patch("src.modules.shopify_listing.application.live_publish_runtime.time.sleep"):
        variants = _update_or_create_variants(client, product=product, candidate=candidate)

    assert [variant["sku"] for variant in variants] == ["ITEM-A", "ITEM-B"]


def test_update_or_create_variants_repairs_missing_shopify_sku_with_single_variant_recreate():
    candidate = DobaProductCandidate(
        spu_id="spu-repair",
        spu_no="SPU-REPAIR",
        supplier_id="seller-repair",
        category_id="cat-repair",
        merge_key="merge-repair",
        seller_name="Seller Repair",
        seller_info={},
        title="Outdoor Dining Set",
        category_name="Outdoor Furniture Sets",
        description_html="<p>Outdoor dining set.</p>",
        brand="Brand Repair",
        ship_from_country="United States",
        processing_time=2,
        store_url="https://www.doba.com/example-repair",
        image_urls=["https://cdn.example.com/repair.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-A",
                sku_code="SKU-A",
                sku_id="SKU-ID-A",
                option_values={"Color": "Gray"},
                inventory=50,
                source_price=100.0,
                shipping_cost=0.0,
                cost_price=100.0,
                sale_price=125.0,
                compare_at_price=145.0,
                ship_time_days=4,
                item_no="ITEM-A",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/a.jpg"],
            ),
            DobaVariantCandidate(
                sku="ITEM-B",
                sku_code="SKU-B",
                sku_id="SKU-ID-B",
                option_values={"Color": "Brown"},
                inventory=50,
                source_price=100.0,
                shipping_cost=0.0,
                cost_price=100.0,
                sale_price=125.0,
                compare_at_price=145.0,
                ship_time_days=4,
                item_no="ITEM-B",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/b.jpg"],
            ),
        ],
        tags=["doba-import"],
    )
    product = {
        "id": "gid://shopify/Product/repair",
        "variants": {
            "edges": [
                {
                    "node": {
                        "id": "gid://shopify/ProductVariant/standalone",
                        "sku": "",
                        "inventoryItem": {"id": "gid://shopify/InventoryItem/standalone"},
                        "selectedOptions": [],
                    }
                }
            ]
        },
    }
    client = Mock()
    client.graphql.side_effect = [
        {
            "productVariantsBulkCreate": {
                "productVariants": [
                    {"id": "gid://shopify/ProductVariant/A", "sku": "ITEM-A"},
                    {"id": "gid://shopify/ProductVariant/B", "sku": "ITEM-B"},
                ],
                "userErrors": [],
            }
        },
        {"product": {"variants": {"edges": [{"node": {"id": "gid://shopify/ProductVariant/A", "sku": "ITEM-A", "inventoryItem": {"id": "gid://shopify/InventoryItem/A"}}}]}}},
        {"product": {"variants": {"edges": [{"node": {"id": "gid://shopify/ProductVariant/A", "sku": "ITEM-A", "inventoryItem": {"id": "gid://shopify/InventoryItem/A"}}}]}}},
        {"productVariantsBulkCreate": {"productVariants": [{"id": "gid://shopify/ProductVariant/B", "sku": "ITEM-B"}], "userErrors": []}},
        {
            "product": {
                "variants": {
                    "edges": [
                        {"node": {"id": "gid://shopify/ProductVariant/A", "sku": "ITEM-A", "inventoryItem": {"id": "gid://shopify/InventoryItem/A"}}},
                        {"node": {"id": "gid://shopify/ProductVariant/B", "sku": "ITEM-B", "inventoryItem": {"id": "gid://shopify/InventoryItem/B"}}},
                    ]
                }
            }
        },
    ]

    with patch("src.modules.shopify_listing.application.live_publish_runtime.time.sleep"):
        variants = _update_or_create_variants(client, product=product, candidate=candidate)

    assert [variant["sku"] for variant in variants] == ["ITEM-A", "ITEM-B"]


def test_build_category_search_candidates_expands_parasol_base_terms():
    candidate = DobaProductCandidate(
        spu_id="spu-parasol",
        spu_no="SPU-PARASOL",
        supplier_id="seller-parasol",
        category_id="cat-parasol",
        merge_key="merge-parasol",
        seller_name="Seller Parasol",
        seller_info={},
        title="Parasol Base Granite 62.8 lb Round Black",
        category_name="Umbrellas & Shade",
        description_html="<p>Parasol base</p>",
        brand="Brand Parasol",
        ship_from_country="US",
        processing_time=2,
        store_url="https://www.doba.com/example-parasol",
        image_urls=["https://cdn.example.com/parasol.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-PARASOL",
                sku_code="SKU-PARASOL",
                sku_id="SKU-ID-PARASOL",
                option_values={"Color": "Black"},
                inventory=50,
                source_price=100.0,
                shipping_cost=10.0,
                cost_price=110.0,
                sale_price=149.0,
                compare_at_price=169.0,
                ship_time_days=4,
                item_no="ITEM-PARASOL",
                ship_name="Ground",
                warehouse="US",
                image_urls=["https://cdn.example.com/parasol-black.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    candidates = _build_category_search_candidates(candidate)

    assert "parasol base" in candidates
    assert "umbrella base" in candidates


def test_build_category_search_candidates_expands_pool_cover_terms():
    candidate = DobaProductCandidate(
        spu_id="spu-pool",
        spu_no="SPU-POOL",
        supplier_id="seller-pool",
        category_id="cat-pool",
        merge_key="merge-pool",
        seller_name="Seller Pool",
        seller_info={},
        title="Inflatable Winter Air Pillows for Above-Ground Pool Cover 10 pcs PVC",
        category_name="Pools, Hot Tubs & Supplies",
        description_html="<p>Pool cover pillow</p>",
        brand="Brand Pool",
        ship_from_country="US",
        processing_time=2,
        store_url="https://www.doba.com/example-pool",
        image_urls=["https://cdn.example.com/pool.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-POOL",
                sku_code="SKU-POOL",
                sku_id="SKU-ID-POOL",
                option_values={"Size": "10 pcs"},
                inventory=22,
                source_price=50.0,
                shipping_cost=2.49,
                cost_price=52.49,
                sale_price=71.39,
                compare_at_price=81.39,
                ship_time_days=4,
                item_no="ITEM-POOL",
                ship_name="Ground",
                warehouse="US",
                image_urls=["https://cdn.example.com/pool-variant.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    candidates = _build_category_search_candidates(candidate)

    assert "pool cover air pillows" in candidates
    assert "pool cover pillows" in candidates
    assert "winter pool cover pillows" in candidates


def test_build_category_search_candidates_expands_pool_filter_terms():
    candidate = DobaProductCandidate(
        spu_id="spu-filter",
        spu_no="SPU-FILTER",
        supplier_id="seller-filter",
        category_id="cat-filter",
        merge_key="merge-filter",
        seller_name="Seller Filter",
        seller_info={},
        title="Pool Filter Ball 1.5 lb PE",
        category_name="Pools, Hot Tubs & Supplies",
        description_html="<p>Pool filter ball</p>",
        brand="Brand Filter",
        ship_from_country="US",
        processing_time=2,
        store_url="https://www.doba.com/example-filter",
        image_urls=["https://cdn.example.com/filter.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-FILTER",
                sku_code="SKU-FILTER",
                sku_id="SKU-ID-FILTER",
                option_values={"Weight": "1.5 lb"},
                inventory=36,
                source_price=30.0,
                shipping_cost=1.24,
                cost_price=31.24,
                sale_price=42.49,
                compare_at_price=48.49,
                ship_time_days=4,
                item_no="ITEM-FILTER",
                ship_name="Ground",
                warehouse="US",
                image_urls=["https://cdn.example.com/filter-variant.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    candidates = _build_category_search_candidates(candidate)

    assert "pool filter balls" in candidates
    assert "pool filter media" in candidates
    assert "pool filters" in candidates


def test_build_category_search_candidates_expands_raised_garden_bed_terms():
    candidate = DobaProductCandidate(
        spu_id="spu-garden",
        spu_no="SPU-GARDEN",
        supplier_id="seller-garden",
        category_id="cat-garden",
        merge_key="merge-garden",
        seller_name="Seller Garden",
        seller_info={},
        title='Raised Garden Bed Anthracite 50.8"x50.8"x17.7" Galvanized Steel',
        category_name="Pots, Planters & Container Accessories",
        description_html="<p>Raised garden bed</p>",
        brand="Brand Garden",
        ship_from_country="United States",
        processing_time=2,
        store_url="https://www.doba.com/example-garden",
        image_urls=["https://cdn.example.com/garden.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-GARDEN",
                sku_code="SKU-GARDEN",
                sku_id="SKU-ID-GARDEN",
                option_values={"Color": "Anthracite"},
                inventory=14,
                source_price=45.0,
                shipping_cost=1.24,
                cost_price=46.24,
                sale_price=57.8,
                compare_at_price=62.8,
                ship_time_days=4,
                item_no="ITEM-GARDEN",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/garden-variant.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    candidates = _build_category_search_candidates(candidate)

    assert "raised garden beds" in candidates
    assert "garden raised beds" in candidates
    assert "planter boxes" in candidates


def test_build_category_search_candidates_expands_log_storage_shed_terms():
    candidate = DobaProductCandidate(
        spu_id="spu-log-shed",
        spu_no="SPU-LOG-SHED",
        supplier_id="seller-log-shed",
        category_id="cat-log-shed",
        merge_key="merge-log-shed",
        seller_name="Seller Log Shed",
        seller_info={},
        title='Garden Log Storage Shed Galvanized Steel 64.2"x32.7"x60.6" Brown',
        category_name="Other Patio, Lawn & Garden Supplies",
        description_html="<p>Garden log storage shed</p>",
        brand="Brand Shed",
        ship_from_country="United States",
        processing_time=2,
        store_url="https://www.doba.com/example-log-shed",
        image_urls=["https://cdn.example.com/log-shed.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-LOG-SHED",
                sku_code="SKU-LOG-SHED",
                sku_id="SKU-ID-LOG-SHED",
                option_values={"Color": "Brown"},
                inventory=16,
                source_price=124.99,
                shipping_cost=0.0,
                cost_price=124.99,
                sale_price=156.24,
                compare_at_price=176.24,
                ship_time_days=4,
                item_no="ITEM-LOG-SHED",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/log-shed-variant.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    candidates = _build_category_search_candidates(candidate)

    assert "outdoor storage sheds" in candidates
    assert "garden storage sheds" in candidates
    assert "storage sheds" in candidates


def test_build_category_search_candidates_expands_mannequin_terms():
    candidate = DobaProductCandidate(
        spu_id="spu-mannequin",
        spu_no="SPU-MANNEQUIN",
        supplier_id="seller-mannequin",
        category_id="cat-mannequin",
        merge_key="merge-mannequin",
        seller_name="Seller Mannequin",
        seller_info={},
        title="Mannequin Child A",
        category_name="Sewing Notions & Supplies",
        description_html="<p>Mannequin child.</p>",
        brand="Brand Mannequin",
        ship_from_country="United States",
        processing_time=2,
        store_url="https://www.doba.com/example-mannequin",
        image_urls=["https://cdn.example.com/mannequin.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-MANNEQUIN",
                sku_code="SKU-MANNEQUIN",
                sku_id="SKU-ID-MANNEQUIN",
                option_values={"Model": "Child A"},
                inventory=50,
                source_price=74.99,
                shipping_cost=18.75,
                cost_price=93.74,
                sale_price=117.17,
                compare_at_price=137.17,
                ship_time_days=4,
                item_no="ITEM-MANNEQUIN",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/mannequin-variant.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    candidates = _build_category_search_candidates(candidate)

    assert "mannequins" in candidates
    assert "dress forms" in candidates
    assert "retail display mannequins" in candidates


def test_build_category_search_candidates_expands_patio_storage_box_terms():
    candidate = DobaProductCandidate(
        spu_id="spu-storage-box",
        spu_no="SPU-STORAGE-BOX",
        supplier_id="seller-storage-box",
        category_id="cat-storage-box",
        merge_key="merge-storage-box",
        seller_name="Seller Storage Box",
        seller_info={},
        title='Patio Storage Box 23.6"x19.7"x22.8" Solid Wood Teak',
        category_name="Other Patio Furniture",
        description_html="<p>Patio storage box.</p>",
        brand="Brand Storage Box",
        ship_from_country="United States",
        processing_time=2,
        store_url="https://www.doba.com/example-storage-box",
        image_urls=["https://cdn.example.com/storage-box.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-STORAGE-BOX",
                sku_code="SKU-STORAGE-BOX",
                sku_id="SKU-ID-STORAGE-BOX",
                option_values={"Material": "Teak"},
                inventory=20,
                source_price=216.24,
                shipping_cost=0.0,
                cost_price=216.24,
                sale_price=270.3,
                compare_at_price=300.3,
                ship_time_days=4,
                item_no="ITEM-STORAGE-BOX",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/storage-box-variant.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    candidates = _build_category_search_candidates(candidate)

    assert "outdoor storage boxes" in candidates
    assert "deck boxes" in candidates
    assert "patio storage boxes" in candidates


def test_build_category_search_candidates_expands_spa_surround_terms():
    candidate = DobaProductCandidate(
        spu_id="spu-spa",
        spu_no="SPU-SPA",
        supplier_id="seller-spa",
        category_id="cat-spa",
        merge_key="merge-spa",
        seller_name="Seller Spa",
        seller_info={},
        title="Spa Surround Black Poly Rattan and Acacia Wood",
        category_name="Pools, Hot Tubs & Supplies",
        description_html="<p>Spa surround.</p>",
        brand="Brand Spa",
        ship_from_country="United States",
        processing_time=2,
        store_url="https://www.doba.com/example-spa",
        image_urls=["https://cdn.example.com/spa.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-SPA",
                sku_code="SKU-SPA",
                sku_id="SKU-ID-SPA",
                option_values={"Color": "Black"},
                inventory=14,
                source_price=557.49,
                shipping_cost=0.0,
                cost_price=557.49,
                sale_price=696.86,
                compare_at_price=736.86,
                ship_time_days=4,
                item_no="ITEM-SPA",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/spa-variant.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    candidates = _build_category_search_candidates(candidate)

    assert "hot tub surrounds" in candidates
    assert "spa surrounds" in candidates
    assert "hot tub accessories" in candidates


def test_build_category_search_candidates_expands_above_ground_strainer_terms():
    candidate = DobaProductCandidate(
        spu_id="spu-strainer",
        spu_no="SPU-STRAINER",
        supplier_id="seller-strainer",
        category_id="cat-strainer",
        merge_key="merge-strainer",
        seller_name="Seller Strainer",
        seller_info={},
        title="Above Ground Strainer Set 1.2",
        category_name="Pools, Hot Tubs & Supplies",
        description_html="<p>Above ground strainer set.</p>",
        brand="Brand Strainer",
        ship_from_country="United States",
        processing_time=2,
        store_url="https://www.doba.com/example-strainer",
        image_urls=["https://cdn.example.com/strainer.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-STRAINER",
                sku_code="SKU-STRAINER",
                sku_id="SKU-ID-STRAINER",
                option_values={"Size": "1.2"},
                inventory=32,
                source_price=17.49,
                shipping_cost=0.0,
                cost_price=17.49,
                sale_price=21.86,
                compare_at_price=25.86,
                ship_time_days=4,
                item_no="ITEM-STRAINER",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/strainer-variant.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    candidates = _build_category_search_candidates(candidate)

    assert "pool skimmer accessories" in candidates
    assert "pool strainer baskets" in candidates
    assert "above ground pool accessories" in candidates


def test_build_category_search_candidates_expands_home_office_furniture_terms():
    candidate = DobaProductCandidate(
        spu_id="spu-office",
        spu_no="SPU-OFFICE",
        supplier_id="seller-office",
        category_id="cat-office",
        merge_key="merge-office",
        seller_name="Seller Office",
        seller_info={},
        title="Studio Filing Cabinet",
        category_name="Home Office Furniture",
        description_html="<p>Office filing cabinet</p>",
        brand="Brand Office",
        ship_from_country="United States",
        processing_time=2,
        store_url="https://www.doba.com/example-office",
        image_urls=["https://cdn.example.com/office.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-OFFICE",
                sku_code="SKU-OFFICE",
                sku_id="SKU-ID-OFFICE",
                option_values={"Color": "White"},
                inventory=15,
                source_price=89.0,
                shipping_cost=0.0,
                cost_price=89.0,
                sale_price=111.25,
                compare_at_price=131.25,
                ship_time_days=4,
                item_no="ITEM-OFFICE",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/office-variant.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    candidates = _build_category_search_candidates(candidate)

    assert "filing cabinets" in candidates
    assert "office storage cabinets" in candidates


def test_build_category_search_candidates_expands_home_storage_terms():
    candidate = DobaProductCandidate(
        spu_id="spu-storage",
        spu_no="SPU-STORAGE",
        supplier_id="seller-storage",
        category_id="cat-storage",
        merge_key="merge-storage",
        seller_name="Seller Storage",
        seller_info={},
        title="Oceanstar Bamboo Folding X-Frame Laundry Hamper Sorter",
        category_name="Home Storage & Organization",
        description_html="<p>Laundry hamper sorter</p>",
        brand="Brand Storage",
        ship_from_country="United States",
        processing_time=2,
        store_url="https://www.doba.com/example-storage",
        image_urls=["https://cdn.example.com/storage.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-STORAGE",
                sku_code="SKU-STORAGE",
                sku_id="SKU-ID-STORAGE",
                option_values={"Color": "Natural"},
                inventory=15,
                source_price=49.0,
                shipping_cost=0.0,
                cost_price=49.0,
                sale_price=61.25,
                compare_at_price=71.25,
                ship_time_days=4,
                item_no="ITEM-STORAGE",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/storage-variant.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    candidates = _build_category_search_candidates(candidate)

    assert "laundry hampers" in candidates
    assert "laundry sorters" in candidates


def test_build_category_search_candidates_expands_home_audio_terms():
    candidate = DobaProductCandidate(
        spu_id="spu-audio",
        spu_no="SPU-AUDIO",
        supplier_id="seller-audio",
        category_id="cat-audio",
        merge_key="merge-audio",
        seller_name="Seller Audio",
        seller_info={},
        title="5.1 Channel DVD Home Theater System",
        category_name="Home Audio & Theater",
        description_html="<p>Home theater system</p>",
        brand="Brand Audio",
        ship_from_country="United States",
        processing_time=2,
        store_url="https://www.doba.com/example-audio",
        image_urls=["https://cdn.example.com/audio.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-AUDIO",
                sku_code="SKU-AUDIO",
                sku_id="SKU-ID-AUDIO",
                option_values={"Color": "Black"},
                inventory=15,
                source_price=120.0,
                shipping_cost=0.0,
                cost_price=120.0,
                sale_price=150.0,
                compare_at_price=170.0,
                ship_time_days=4,
                item_no="ITEM-AUDIO",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/audio-variant.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    candidates = _build_category_search_candidates(candidate)

    assert "home theater systems" in candidates
    assert "surround sound systems" in candidates


def test_build_category_search_candidates_expands_other_lab_storage_shelf_terms():
    candidate = DobaProductCandidate(
        spu_id="spu-lab-shelf",
        spu_no="SPU-LAB-SHELF",
        supplier_id="seller-lab-shelf",
        category_id="cat-lab-shelf",
        merge_key="merge-lab-shelf",
        seller_name="Seller Lab Shelf",
        seller_info={},
        title='Storage Shelf White 23.6"x11.8"x41.3" Engineered Wood',
        category_name="Other Lab & Scientific Products",
        description_html="<p>Storage shelf</p>",
        brand="Brand Lab Shelf",
        ship_from_country="United States",
        processing_time=2,
        store_url="https://www.doba.com/example-lab-shelf",
        image_urls=["https://cdn.example.com/lab-shelf.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-LAB-SHELF",
                sku_code="SKU-LAB-SHELF",
                sku_id="SKU-ID-LAB-SHELF",
                option_values={"Color": "White"},
                inventory=15,
                source_price=69.0,
                shipping_cost=0.0,
                cost_price=69.0,
                sale_price=86.25,
                compare_at_price=96.25,
                ship_time_days=4,
                item_no="ITEM-LAB-SHELF",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/lab-shelf-variant.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    candidates = _build_category_search_candidates(candidate)

    assert "storage shelves" in candidates
    assert "shelving units" in candidates


def test_build_category_search_candidates_expands_planter_accessory_terms():
    candidate = DobaProductCandidate(
        spu_id="spu-planter-accessory",
        spu_no="SPU-PLANTER-ACCESSORY",
        supplier_id="seller-planter-accessory",
        category_id="cat-planter-accessory",
        merge_key="merge-planter-accessory",
        seller_name="Seller Planter",
        seller_info={},
        title="2Pcs Free Splicing Injection Planting Box Brown",
        category_name="Pots, Planters & Container Accessories",
        description_html="<p>Planting box</p>",
        brand="Brand Planter",
        ship_from_country="United States",
        processing_time=2,
        store_url="https://www.doba.com/example-planter-accessory",
        image_urls=["https://cdn.example.com/planter-accessory.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-PLANTER-ACCESSORY",
                sku_code="SKU-PLANTER-ACCESSORY",
                sku_id="SKU-ID-PLANTER-ACCESSORY",
                option_values={"Color": "Brown"},
                inventory=18,
                source_price=29.99,
                shipping_cost=0.0,
                cost_price=29.99,
                sale_price=37.49,
                compare_at_price=42.49,
                ship_time_days=4,
                item_no="ITEM-PLANTER-ACCESSORY",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/planter-accessory-variant.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    candidates = _build_category_search_candidates(candidate)

    assert "planters" in candidates
    assert "plant pots" in candidates
    assert "planter boxes" in candidates


def test_build_category_search_candidates_expands_portable_folding_table_terms():
    candidate = DobaProductCandidate(
        spu_id="spu-folding-table",
        spu_no="SPU-FOLDING-TABLE",
        supplier_id="seller-folding-table",
        category_id="cat-folding-table",
        merge_key="merge-folding-table",
        seller_name="Seller Folding Table",
        seller_info={},
        title="360-Degree Rotation Multifunctional Portable Folding Table with Fan & Mouse Black",
        category_name="Home Office Furniture",
        description_html="<p>Portable folding table</p>",
        brand="Brand Folding Table",
        ship_from_country="United States",
        processing_time=2,
        store_url="https://www.doba.com/example-folding-table",
        image_urls=["https://cdn.example.com/folding-table.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-FOLDING-TABLE",
                sku_code="SKU-FOLDING-TABLE",
                sku_id="SKU-ID-FOLDING-TABLE",
                option_values={"Color": "Black"},
                inventory=16,
                source_price=54.99,
                shipping_cost=0.0,
                cost_price=54.99,
                sale_price=68.74,
                compare_at_price=73.74,
                ship_time_days=4,
                item_no="ITEM-FOLDING-TABLE",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/folding-table-variant.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    candidates = _build_category_search_candidates(candidate)

    assert "laptop stands" in candidates
    assert "lap desks" in candidates
    assert "bed trays" in candidates


def test_build_category_search_candidates_expands_chair_mat_terms():
    candidate = DobaProductCandidate(
        spu_id="spu-chair-mat",
        spu_no="SPU-CHAIR-MAT",
        supplier_id="seller-chair-mat",
        category_id="cat-chair-mat",
        merge_key="merge-chair-mat",
        seller_name="Seller Chair Mat",
        seller_info={},
        title="PVC Dull Polish Chair Mat Protection Floor Mat 90x120x0.2cm Rectangular",
        category_name="Other Patio, Lawn & Garden Supplies",
        description_html="<p>Chair mat</p>",
        brand="Brand Chair Mat",
        ship_from_country="United States",
        processing_time=2,
        store_url="https://www.doba.com/example-chair-mat",
        image_urls=["https://cdn.example.com/chair-mat.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-CHAIR-MAT",
                sku_code="SKU-CHAIR-MAT",
                sku_id="SKU-ID-CHAIR-MAT",
                option_values={"Shape": "Rectangular"},
                inventory=22,
                source_price=31.99,
                shipping_cost=0.0,
                cost_price=31.99,
                sale_price=39.99,
                compare_at_price=44.99,
                ship_time_days=4,
                item_no="ITEM-CHAIR-MAT",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/chair-mat-variant.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    candidates = _build_category_search_candidates(candidate)

    assert "chair mats" in candidates
    assert "floor mats" in candidates


def test_build_category_search_candidates_expands_waterfall_terms():
    candidate = DobaProductCandidate(
        spu_id="spu-waterfall",
        spu_no="SPU-WATERFALL",
        supplier_id="seller-waterfall",
        category_id="cat-waterfall",
        merge_key="merge-waterfall",
        seller_name="Seller Waterfall",
        seller_info={},
        title='Waterfall 17.7"x13.4"x5.5" Stainless Steel 304',
        category_name="Other Patio, Lawn & Garden Supplies",
        description_html="<p>Garden waterfall</p>",
        brand="Brand Waterfall",
        ship_from_country="United States",
        processing_time=2,
        store_url="https://www.doba.com/example-waterfall",
        image_urls=["https://cdn.example.com/waterfall.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-WATERFALL",
                sku_code="SKU-WATERFALL",
                sku_id="SKU-ID-WATERFALL",
                option_values={"Material": "Stainless Steel"},
                inventory=15,
                source_price=81.24,
                shipping_cost=0.0,
                cost_price=81.24,
                sale_price=101.55,
                compare_at_price=106.55,
                ship_time_days=4,
                item_no="ITEM-WATERFALL",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/waterfall-variant.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    candidates = _build_category_search_candidates(candidate)

    assert "garden waterfalls" in candidates
    assert "pond waterfalls" in candidates
    assert "waterfalls" in candidates


def test_build_category_search_candidates_expands_fire_pit_terms():
    candidate = DobaProductCandidate(
        spu_id="spu-fire-pit",
        spu_no="SPU-FIRE-PIT",
        supplier_id="seller-fire-pit",
        category_id="cat-fire-pit",
        merge_key="merge-fire-pit",
        seller_name="Seller Fire Pit",
        seller_info={},
        title="Portable Courtyard Metal Fire Pit with Accessories Black",
        category_name="Other Patio, Lawn & Garden Supplies",
        description_html="<p>Fire pit</p>",
        brand="Brand Fire Pit",
        ship_from_country="United States",
        processing_time=2,
        store_url="https://www.doba.com/example-fire-pit",
        image_urls=["https://cdn.example.com/fire-pit.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-FIRE-PIT",
                sku_code="SKU-FIRE-PIT",
                sku_id="SKU-ID-FIRE-PIT",
                option_values={"Color": "Black"},
                inventory=18,
                source_price=84.99,
                shipping_cost=0.0,
                cost_price=84.99,
                sale_price=106.24,
                compare_at_price=116.24,
                ship_time_days=4,
                item_no="ITEM-FIRE-PIT",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/fire-pit-variant.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    candidates = _build_category_search_candidates(candidate)

    assert "fire pits" in candidates
    assert "outdoor fire pits" in candidates
    assert "patio fire pits" in candidates


def test_build_category_search_candidates_expands_bat_house_terms():
    candidate = DobaProductCandidate(
        spu_id="spu-bat-house",
        spu_no="SPU-BAT-HOUSE",
        supplier_id="seller-bat-house",
        category_id="cat-bat-house",
        merge_key="merge-bat-house",
        seller_name="Seller Bat House",
        seller_info={},
        title='Bat House Solid Firwood 11.8"x7.9"x15"',
        category_name="Other Patio, Lawn & Garden Supplies",
        description_html="<p>Bat house</p>",
        brand="Brand Bat House",
        ship_from_country="United States",
        processing_time=2,
        store_url="https://www.doba.com/example-bat-house",
        image_urls=["https://cdn.example.com/bat-house.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-BAT-HOUSE",
                sku_code="SKU-BAT-HOUSE",
                sku_id="SKU-ID-BAT-HOUSE",
                option_values={"Material": "Firwood"},
                inventory=14,
                source_price=29.99,
                shipping_cost=0.0,
                cost_price=29.99,
                sale_price=37.49,
                compare_at_price=42.49,
                ship_time_days=4,
                item_no="ITEM-BAT-HOUSE",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/bat-house-variant.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    candidates = _build_category_search_candidates(candidate)

    assert "bat houses" in candidates
    assert "bat shelters" in candidates
    assert "wildlife houses" in candidates


def test_build_category_search_candidates_expands_vertical_planter_terms():
    candidate = DobaProductCandidate(
        spu_id="spu-vertical-planter",
        spu_no="SPU-VERTICAL-PLANTER",
        supplier_id="seller-vertical-planter",
        category_id="cat-vertical-planter",
        merge_key="merge-vertical-planter",
        seller_name="Seller Vertical Planter",
        seller_info={},
        title="5-tier Vertical Garden Planter Box Elevated Raised Bed with 5 Container",
        category_name="Other Home Improvement Supplies",
        description_html="<p>Vertical garden planter</p>",
        brand="Brand Vertical Planter",
        ship_from_country="United States",
        processing_time=2,
        store_url="https://www.doba.com/example-vertical-planter",
        image_urls=["https://cdn.example.com/vertical-planter.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-VERTICAL-PLANTER",
                sku_code="SKU-VERTICAL-PLANTER",
                sku_id="SKU-ID-VERTICAL-PLANTER",
                option_values={"Tier": "5"},
                inventory=17,
                source_price=68.99,
                shipping_cost=0.0,
                cost_price=68.99,
                sale_price=86.24,
                compare_at_price=91.24,
                ship_time_days=4,
                item_no="ITEM-VERTICAL-PLANTER",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/vertical-planter-variant.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    candidates = _build_category_search_candidates(candidate)

    assert "vertical planters" in candidates
    assert "garden planters" in candidates
    assert "planter boxes" in candidates


def test_build_category_search_candidates_expands_bench_cushion_terms():
    candidate = DobaProductCandidate(
        spu_id="spu-bench-cushion",
        spu_no="SPU-BENCH-CUSHION",
        supplier_id="seller-bench-cushion",
        category_id="cat-bench-cushion",
        merge_key="merge-bench-cushion",
        seller_name="Seller Bench Cushion",
        seller_info={},
        title='Garden Bench Cushion Beige 59.1"x19.7"x2.8" Oxford Fabric',
        category_name="Office & School Chairs and Accessories",
        description_html="<p>Bench cushion</p>",
        brand="Brand Bench Cushion",
        ship_from_country="United States",
        processing_time=2,
        store_url="https://www.doba.com/example-bench-cushion",
        image_urls=["https://cdn.example.com/bench-cushion.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-BENCH-CUSHION",
                sku_code="SKU-BENCH-CUSHION",
                sku_id="SKU-ID-BENCH-CUSHION",
                option_values={"Color": "Beige"},
                inventory=15,
                source_price=44.99,
                shipping_cost=0.0,
                cost_price=44.99,
                sale_price=56.24,
                compare_at_price=61.24,
                ship_time_days=4,
                item_no="ITEM-BENCH-CUSHION",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/bench-cushion-variant.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    candidates = _build_category_search_candidates(candidate)

    assert "bench cushions" in candidates
    assert "outdoor bench cushions" in candidates
    assert "chair cushions" in candidates


def test_resolve_shopify_category_falls_back_to_doba_search_when_rule_hydration_has_no_category_id():
    candidate = DobaProductCandidate(
        spu_id="spu-fallback",
        spu_no="SPU-FALLBACK",
        supplier_id="seller-fallback",
        category_id="cat-fallback",
        merge_key="merge-fallback",
        seller_name="Seller Fallback",
        seller_info={},
        title='Garden Bench Cushion Beige 59.1"x19.7"x2.8" Oxford Fabric',
        category_name="Office & School Chairs and Accessories",
        description_html="<p>Bench cushion</p>",
        brand="Brand Fallback",
        ship_from_country="United States",
        processing_time=2,
        store_url="https://www.doba.com/example-fallback",
        image_urls=["https://cdn.example.com/fallback.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-FALLBACK",
                sku_code="SKU-FALLBACK",
                sku_id="SKU-ID-FALLBACK",
                option_values={"Color": "Beige"},
                inventory=15,
                source_price=44.99,
                shipping_cost=0.0,
                cost_price=44.99,
                sale_price=56.24,
                compare_at_price=61.24,
                ship_time_days=4,
                item_no="ITEM-FALLBACK",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/fallback-variant.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    unresolved_rule = CategoryResolution(
        category_id=None,
        product_type="Patio Bench Cushions",
        category_label="patio-bench-cushions",
        tags=("outdoor-living",),
        matched_rule="keyword:patio-bench-cushions",
        taxonomy_search="patio bench cushions",
        taxonomy_path_tokens=("cushions", "patio"),
        allow_category_update=False,
    )

    def fake_search_taxonomy_category_id(*, search, **kwargs):
        if search == "bench cushions":
            return "gid://shopify/TaxonomyCategory/bench-cushions"
        return None

    with patch("src.modules.shopify_listing.application.live_publish_runtime._resolve_category", return_value=unresolved_rule):
        with patch("src.modules.shopify_listing.application.live_publish_runtime._hydrate_resolution", return_value=unresolved_rule):
            with patch(
                "src.modules.shopify_listing.application.live_publish_runtime._search_taxonomy_category_id",
                side_effect=fake_search_taxonomy_category_id,
            ):
                resolution = _resolve_shopify_category(
                    Mock(),
                    candidate=candidate,
                    taxonomy_cache={},
                )

    assert resolution is not None
    assert resolution.category_id == "gid://shopify/TaxonomyCategory/bench-cushions"
    assert resolution.taxonomy_search == "bench cushions"


def test_update_product_basics_does_not_send_product_options():
    class FakeClient:
        def __init__(self) -> None:
            self.last_variables = None

        def graphql(self, query, variables=None):
            self.last_variables = variables
            return {"productUpdate": {"product": {"id": "gid://shopify/Product/9"}, "userErrors": []}}

    candidate = DobaProductCandidate(
        spu_id="spu-upd",
        spu_no="SPU-UPD",
        supplier_id="seller-upd",
        category_id="cat-upd",
        merge_key="merge-upd",
        seller_name="Seller Update",
        seller_info={},
        title="Outdoor Sofa",
        category_name="Outdoor Sofas",
        description_html="<p>Sofa</p>",
        brand="Brand Update",
        ship_from_country="US",
        processing_time=2,
        store_url="https://www.doba.com/example-upd",
        image_urls=["https://cdn.example.com/sofa-upd.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-UPD",
                sku_code="SKU-UPD",
                sku_id="SKU-ID-UPD",
                option_values={"Color": "Grey"},
                inventory=13,
                source_price=80.0,
                shipping_cost=8.0,
                cost_price=88.0,
                sale_price=129.0,
                compare_at_price=149.0,
                ship_time_days=5,
                item_no="ITEM-UPD",
                ship_name="Ground",
                warehouse="US",
                image_urls=["https://cdn.example.com/sofa-grey.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    client = FakeClient()
    _update_product_basics(
        client,
        product_id="gid://shopify/Product/9",
        candidate=candidate,
        category_resolution=None,
    )

    product_payload = client.last_variables["product"]
    assert "productOptions" not in product_payload
    assert product_payload["id"] == "gid://shopify/Product/9"


def test_set_product_metafields_writes_doba_category_and_vendor():
    class FakeClient:
        def __init__(self) -> None:
            self.last_query = None
            self.last_variables = None

        def graphql(self, query, variables=None):
            self.last_query = query
            self.last_variables = variables
            return {"metafieldsSet": {"metafields": [], "userErrors": []}}

    candidate = DobaProductCandidate(
        spu_id="spu-10",
        spu_no="SPU-10",
        supplier_id="seller-10",
        category_id="cat-10",
        merge_key="merge-spu-10",
        seller_name="Seller Ten",
        seller_info={},
        title="Mirror",
        category_name="Wall Mirrors",
        description_html="<p>Mirror</p>",
        brand="Brand Ten",
        ship_from_country="US",
        processing_time=2,
        store_url="https://www.doba.com/example-10",
        image_urls=["https://cdn.example.com/mirror.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-10",
                sku_code="SKU-10",
                sku_id="SKU-ID-10",
                option_values={"Size": "18x40"},
                inventory=14,
                source_price=40.0,
                shipping_cost=4.0,
                cost_price=44.0,
                sale_price=69.0,
                compare_at_price=79.0,
                ship_time_days=4,
                item_no="ITEM-10",
                ship_name="Ground",
                warehouse="US",
                image_urls=["https://cdn.example.com/mirror-variant.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    class CategoryResolutionStub:
        category_id = "gid://shopify/TaxonomyCategory/hg-3-47-2"
        matched_rule = "doba_category_name"

    client = FakeClient()
    _set_product_metafields(
        client,
        product_id="gid://shopify/Product/10",
        candidate=candidate,
        category_resolution=CategoryResolutionStub(),
    )

    metafields = client.last_variables["metafields"]
    values_by_key = {item["key"]: item["value"] for item in metafields}
    assert values_by_key["doba_category_id"] == "cat-10"
    assert values_by_key["doba_category_name"] == "Wall Mirrors"
    assert values_by_key["shopify_category_id"] == "gid://shopify/TaxonomyCategory/hg-3-47-2"
    assert values_by_key["source_vendor"] == SOURCE_VENDOR_NAME
    assert values_by_key["doba_seller_name"] == "Seller Ten"
    assert values_by_key["ship_from_country"] == "US"
    assert json.loads(values_by_key["source_channels"]) == ["Inbox", "Shop", "Pinterest", "Facebook & Instagram"]


def test_set_product_metafields_skips_blank_values():
    class FakeClient:
        def __init__(self) -> None:
            self.last_variables = None

        def graphql(self, query, variables=None):
            self.last_variables = variables
            return {"metafieldsSet": {"metafields": [], "userErrors": []}}

    candidate = DobaProductCandidate(
        spu_id="spu-blank",
        spu_no="SPU-BLANK",
        supplier_id="seller-blank",
        category_id="cat-blank",
        merge_key="merge-blank",
        seller_name="Seller Blank",
        seller_info={},
        title="Patio Set",
        category_name="Patio Sets",
        description_html="<p>Patio Set</p>",
        brand="Brand Blank",
        ship_from_country="US",
        processing_time=4,
        store_url="https://www.doba.com/example-blank",
        image_urls=["https://cdn.example.com/patio.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-BLANK",
                sku_code="SKU-BLANK",
                sku_id="SKU-ID-BLANK",
                option_values={"Color": "Gray"},
                inventory=16,
                source_price=300.0,
                shipping_cost=20.0,
                cost_price=320.0,
                sale_price=430.0,
                compare_at_price=460.0,
                ship_time_days=7,
                item_no="ITEM-BLANK",
                ship_name="Ground",
                warehouse="US",
                image_urls=["https://cdn.example.com/patio-gray.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    class CategoryResolutionStub:
        category_id = ""
        matched_rule = ""

    client = FakeClient()
    _set_product_metafields(
        client,
        product_id="gid://shopify/Product/blank",
        candidate=candidate,
        category_resolution=CategoryResolutionStub(),
    )

    keys = [item["key"] for item in client.last_variables["metafields"]]
    assert "shopify_category_id" not in keys
    assert "shopify_category_rule" not in keys


def test_set_variant_inventory_ignores_compare_quantity_for_live_publish():
    class FakeClient:
        def __init__(self) -> None:
            self.calls = []

        def get_primary_location(self):
            return {"id": "gid://shopify/Location/1"}

        def set_inventory_quantity(self, **kwargs):
            self.calls.append(kwargs)
            return {}

    candidate = DobaProductCandidate(
        spu_id="spu-live",
        spu_no="SPU-LIVE",
        supplier_id="seller-live",
        category_id="cat-live",
        merge_key="merge-live",
        seller_name="Seller Live",
        seller_info={},
        title="Outdoor Lounge",
        category_name="Outdoor Lounge Chairs",
        description_html="<p>Lounge</p>",
        brand="Brand Live",
        ship_from_country="US",
        processing_time=3,
        store_url="https://www.doba.com/example-live",
        image_urls=["https://cdn.example.com/lounge.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-LIVE",
                sku_code="SKU-LIVE",
                sku_id="SKU-ID-LIVE",
                option_values={"Color": "Gray"},
                inventory=16,
                source_price=90.0,
                shipping_cost=8.0,
                cost_price=98.0,
                sale_price=139.0,
                compare_at_price=159.0,
                ship_time_days=6,
                item_no="ITEM-LIVE",
                ship_name="Ground",
                warehouse="US",
                image_urls=["https://cdn.example.com/lounge-gray.jpg"],
            )
        ],
        tags=["doba-import"],
    )
    variants = [{"sku": "ITEM-LIVE", "inventoryItem": {"id": "gid://shopify/InventoryItem/1"}}]
    client = FakeClient()

    _set_variant_inventory(client, variants=variants, candidate=candidate)

    assert client.calls[0]["change_from_quantity"] is None


def test_publish_doba_products_live_uses_requested_default_channels(tmp_path):
    report_path = tmp_path / "live-report-default-channels.json"
    captured_publication_inputs = {}
    candidate = DobaProductCandidate(
        spu_id="spu-11",
        spu_no="SPU-11",
        supplier_id="seller-11",
        category_id="cat-11",
        merge_key="merge-spu-11",
        seller_name="Seller Eleven",
        seller_info={},
        title="Sectional Sofa",
        category_name="Sectionals",
        description_html="<p>Sofa</p>",
        brand="Brand Eleven",
        ship_from_country="US",
        processing_time=3,
        store_url="https://www.doba.com/example-11",
        image_urls=["https://cdn.example.com/sofa.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-11",
                sku_code="SKU-11",
                sku_id="SKU-ID-11",
                option_values={"Color": "Beige"},
                inventory=20,
                source_price=100.0,
                shipping_cost=10.0,
                cost_price=110.0,
                sale_price=149.0,
                compare_at_price=169.0,
                ship_time_days=6,
                item_no="ITEM-11",
                ship_name="Ground",
                warehouse="US",
                image_urls=["https://cdn.example.com/sofa-beige.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    def fake_publish_candidate_to_shopify(*args, **kwargs):
        captured_publication_inputs["value"] = kwargs["publication_inputs"]
        return {
            "action": "published",
            "reason": "",
            "shopify_product_id": "gid://shopify/Product/11",
            "variant_count": 1,
            "published_to": ["Inbox", "Shop", "Pinterest", "Facebook & Instagram"],
        }

    with patch("src.modules.shopify_listing.application.live_publish_runtime.DobaClient.from_settings") as doba_from_settings:
        with patch("src.modules.shopify_listing.application.live_publish_runtime.ShopifyAuthClient.from_settings") as shopify_from_settings:
            with patch(
                "src.modules.shopify_listing.application.live_publish_runtime._get_publication_map",
                return_value={
                    "Inbox": {"id": "pub-inbox"},
                    "Shop": {"id": "pub-shop"},
                    "Pinterest": {"id": "pub-pinterest"},
                    "Facebook & Instagram": {"id": "pub-fb"},
                },
            ):
                with patch("src.modules.shopify_listing.application.live_publish_runtime._ensure_collection", return_value={"id": "col-1"}):
                    with patch("src.modules.shopify_listing.application.live_publish_runtime._fetch_platform_id", return_value="platform-1"):
                        with patch(
                            "src.modules.shopify_listing.application.live_publish_runtime._fetch_spu_page",
                            side_effect=[(1, [{"spuId": "spu-11", "spuNo": "SPU-11", "title": "Sectional Sofa"}]), (1, [])],
                        ):
                            with patch(
                                "src.modules.shopify_listing.application.live_publish_runtime._fetch_spu_details",
                                return_value={"SPU-11": {"spuNo": "SPU-11", "spuId": "spu-11", "title": "Sectional Sofa"}},
                            ):
                                with patch("src.modules.shopify_listing.application.live_publish_runtime._fetch_stock_map", return_value={}):
                                    with patch("src.modules.shopify_listing.application.live_publish_runtime._fetch_shipping_map", return_value={}):
                                        with patch("src.modules.shopify_listing.application.live_publish_runtime._fetch_seller_info", return_value={}):
                                            with patch(
                                                "src.modules.shopify_listing.application.live_publish_runtime._build_product_candidate",
                                                return_value=(candidate, None),
                                            ):
                                                with patch(
                                                    "src.modules.shopify_listing.application.live_publish_runtime._publish_candidate_to_shopify",
                                                    side_effect=fake_publish_candidate_to_shopify,
                                                ):
                                                    doba_from_settings.return_value = object()
                                                    shopify_from_settings.return_value = object()
                                                    publish_doba_products_live(
                                                        report_path=str(report_path),
                                                        resume=False,
                                                        prefer_candidate_pool=False,
                                                        page_size=20,
                                                        max_successes=1,
                                                    )

    assert captured_publication_inputs["value"] == [
        {"publicationId": "pub-inbox"},
        {"publicationId": "pub-shop"},
        {"publicationId": "pub-pinterest"},
        {"publicationId": "pub-fb"},
    ]


def test_publish_candidate_to_shopify_skips_any_active_existing_product_even_when_incoming_skus_differ():
    candidate = DobaProductCandidate(
        spu_id="spu-active",
        spu_no="SPU-ACTIVE",
        supplier_id="seller-active",
        category_id="cat-active",
        merge_key="merge-active",
        seller_name="Seller Active",
        seller_info={},
        title="Outdoor Chair",
        category_name="Outdoor Chairs",
        description_html="<p>Chair</p>",
        brand="Brand Active",
        ship_from_country="United States",
        processing_time=2,
        store_url="https://www.doba.com/example-active",
        image_urls=["https://cdn.example.com/active.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-NEW",
                sku_code="SKU-NEW",
                sku_id="SKU-ID-NEW",
                option_values={"Color": "Black"},
                inventory=22,
                source_price=50.0,
                shipping_cost=5.0,
                cost_price=55.0,
                sale_price=62.5,
                compare_at_price=72.5,
                ship_time_days=4,
                item_no="ITEM-NEW",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/active-variant.jpg"],
            )
        ],
        tags=["doba-import", "doba-merge-key:merge-active"],
    )

    with patch("src.modules.shopify_listing.application.live_publish_runtime._resolve_shopify_category") as resolve_category:
        with patch(
            "src.modules.shopify_listing.application.live_publish_runtime._find_existing_product_by_merge_key",
            return_value={"id": "gid://shopify/Product/existing", "status": "ACTIVE"},
        ):
            with patch(
                "src.modules.shopify_listing.application.live_publish_runtime._load_shopify_product",
                return_value={
                    "id": "gid://shopify/Product/existing",
                    "status": "ACTIVE",
                    "category": {"id": "gid://shopify/TaxonomyCategory/9", "fullName": "Home > Outdoor"},
                    "resourcePublicationsV2": {"edges": []},
                    "variants": {"edges": [{"node": {"id": "gid://shopify/ProductVariant/1", "sku": "ITEM-OLD"}}]},
                },
            ):
                resolve_category.return_value = Mock(category_id="gid://shopify/TaxonomyCategory/9", matched_rule="rule")
                result = _publish_candidate_to_shopify(
                    Mock(),
                    candidate=candidate,
                    publication_inputs=[{"publicationId": "pub-inbox"}],
                    collection_id="col-1",
                    target_channel_names=["Inbox"],
                )

    assert result["action"] == "skipped"
    assert result["reason"] == "active_product_exists"


def test_publish_doba_products_live_clears_stale_stopped_reason_on_failure(tmp_path):
    report_path = tmp_path / "live-report-stale-stop.json"
    report_path.write_text(
        json.dumps(
            {
                "started_at": "2026-06-15T00:00:00+00:00",
                "updated_at": "2026-06-15T00:00:00+00:00",
                "cursor": {"next_page": 1, "next_index": 0},
                "successful_spu_nos": [],
                "results": [],
                "summary": {
                    "total_candidates": 0,
                    "scanned_count": 0,
                    "published_count": 0,
                    "skipped_count": 0,
                    "failed_count": 0,
                },
                "stopped_reason": "max_successes_reached",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with patch("src.modules.shopify_listing.application.live_publish_runtime.DobaClient.from_settings") as doba_from_settings:
        with patch("src.modules.shopify_listing.application.live_publish_runtime.ShopifyAuthClient.from_settings") as shopify_from_settings:
            with patch(
                "src.modules.shopify_listing.application.live_publish_runtime._get_publication_map",
                return_value={
                    "Inbox": {"id": "pub-inbox"},
                    "Shop": {"id": "pub-shop"},
                    "Pinterest": {"id": "pub-pinterest"},
                    "Facebook & Instagram": {"id": "pub-fb"},
                },
            ):
                with patch("src.modules.shopify_listing.application.live_publish_runtime._ensure_collection", return_value={"id": "col-1"}):
                    with patch("src.modules.shopify_listing.application.live_publish_runtime._fetch_platform_id", return_value="platform-1"):
                        with patch(
                            "src.modules.shopify_listing.application.live_publish_runtime._fetch_spu_page",
                            side_effect=[
                                (1, [{"spuId": "spu-1", "spuNo": "SPU-1", "title": "Broken Product"}]),
                                (1, []),
                            ],
                        ):
                            with patch(
                                "src.modules.shopify_listing.application.live_publish_runtime._fetch_spu_details",
                                return_value={"SPU-1": {"spuNo": "SPU-1", "spuId": "spu-1", "title": "Broken Product", "children": []}},
                            ):
                                with patch("src.modules.shopify_listing.application.live_publish_runtime._fetch_stock_map", side_effect=RuntimeError("Server disconnected without sending a response.")):
                                    doba_from_settings.return_value = object()
                                    shopify_from_settings.return_value = object()
                                    result = publish_doba_products_live(
                                        report_path=str(report_path),
                                        resume=True,
                                        prefer_candidate_pool=False,
                                        page_size=20,
                                    )

    assert "stopped_reason" not in result
    assert result["last_failure"]["failed_reason"] == "Server disconnected without sending a response."
    assert result["summary"]["failed_count"] == 1
    assert result["completed"] is True


def test_publish_doba_products_live_continues_after_failure_to_next_product(tmp_path):
    report_path = tmp_path / "live-report-continue-after-failure.json"
    candidate = DobaProductCandidate(
        spu_id="spu-2",
        spu_no="SPU-2",
        supplier_id="seller-2",
        category_id="cat-2",
        merge_key="merge-spu-2",
        seller_name="Seller B",
        seller_info={},
        title="Storage Shelf",
        category_name="Storage",
        description_html="<p>Shelf</p>",
        brand="Doba Basics",
        ship_from_country="United States",
        processing_time=3,
        store_url="https://www.doba.com/example",
        image_urls=["https://cdn.example.com/shelf.jpg"],
        variants=[
            DobaVariantCandidate(
                sku="ITEM-2",
                sku_code="sku-code-2",
                sku_id="sku-id-2",
                option_values={"Color": "Black"},
                inventory=18,
                source_price=34.99,
                shipping_cost=4.5,
                cost_price=39.49,
                sale_price=79.99,
                compare_at_price=89.99,
                ship_time_days=7,
                item_no="ITEM-2",
                ship_name="Ground",
                warehouse="United States",
                image_urls=["https://cdn.example.com/shelf-black.jpg"],
            )
        ],
        tags=["doba-import"],
    )

    with patch("src.modules.shopify_listing.application.live_publish_runtime.DobaClient.from_settings") as doba_from_settings:
        with patch("src.modules.shopify_listing.application.live_publish_runtime.ShopifyAuthClient.from_settings") as shopify_from_settings:
            with patch(
                "src.modules.shopify_listing.application.live_publish_runtime._get_publication_map",
                return_value={
                    "Inbox": {"id": "pub-inbox"},
                    "Shop": {"id": "pub-shop"},
                    "Pinterest": {"id": "pub-pinterest"},
                    "Facebook & Instagram": {"id": "pub-fb"},
                },
            ):
                with patch("src.modules.shopify_listing.application.live_publish_runtime._ensure_collection", return_value={"id": "col-1"}):
                    with patch("src.modules.shopify_listing.application.live_publish_runtime._fetch_platform_id", return_value="platform-1"):
                        with patch(
                            "src.modules.shopify_listing.application.live_publish_runtime._fetch_spu_page",
                            side_effect=[
                                (
                                    2,
                                    [
                                        {"spuId": "spu-1", "spuNo": "SPU-1", "title": "Broken Product"},
                                        {"spuId": "spu-2", "spuNo": "SPU-2", "title": "Storage Shelf"},
                                    ],
                                ),
                                (2, []),
                            ],
                        ):
                            with patch(
                                "src.modules.shopify_listing.application.live_publish_runtime._fetch_spu_details",
                                return_value={
                                    "SPU-1": {"spuNo": "SPU-1", "spuId": "spu-1", "title": "Broken Product", "children": []},
                                    "SPU-2": {"spuNo": "SPU-2", "spuId": "spu-2", "title": "Storage Shelf"},
                                },
                            ):
                                with patch("src.modules.shopify_listing.application.live_publish_runtime._fetch_stock_map", return_value={}):
                                    with patch("src.modules.shopify_listing.application.live_publish_runtime._fetch_shipping_map", return_value={}):
                                        with patch("src.modules.shopify_listing.application.live_publish_runtime._fetch_seller_info", return_value={}):
                                            with patch(
                                                "src.modules.shopify_listing.application.live_publish_runtime._build_product_candidate",
                                                side_effect=[RuntimeError("first failure"), (candidate, None)],
                                            ):
                                                with patch(
                                                    "src.modules.shopify_listing.application.live_publish_runtime._publish_candidate_to_shopify",
                                                    return_value={
                                                        "action": "published",
                                                        "reason": "",
                                                        "shopify_product_id": "gid://shopify/Product/2",
                                                        "variant_count": 1,
                                                        "published_to": ["Inbox", "Shop", "Pinterest", "Facebook & Instagram"],
                                                        "shopify_status": "ACTIVE",
                                                    },
                                                ):
                                                    doba_from_settings.return_value = object()
                                                    shopify_from_settings.return_value = object()
                                                    result = publish_doba_products_live(
                                                        report_path=str(report_path),
                                                        resume=True,
                                                        prefer_candidate_pool=False,
                                                        page_size=20,
                                                    )

    assert result["summary"]["failed_count"] == 1
    assert result["summary"]["published_count"] == 1
    assert result["last_failure"]["failed_reason"] == "first failure"
    assert result["results"][-1]["action"] == "published"


def test_publish_doba_products_live_handles_keyboard_interrupt_and_persists_resume_position(tmp_path):
    report_path = tmp_path / "live-report-interrupted.json"

    with patch("src.modules.shopify_listing.application.live_publish_runtime.DobaClient.from_settings") as doba_from_settings:
        with patch("src.modules.shopify_listing.application.live_publish_runtime.ShopifyAuthClient.from_settings") as shopify_from_settings:
            with patch(
                "src.modules.shopify_listing.application.live_publish_runtime._get_publication_map",
                return_value={
                    "Inbox": {"id": "pub-inbox"},
                    "Shop": {"id": "pub-shop"},
                    "Pinterest": {"id": "pub-pinterest"},
                    "Facebook & Instagram": {"id": "pub-fb"},
                },
            ):
                with patch("src.modules.shopify_listing.application.live_publish_runtime._ensure_collection", return_value={"id": "col-1"}):
                    with patch("src.modules.shopify_listing.application.live_publish_runtime._fetch_platform_id", return_value="platform-1"):
                        with patch(
                            "src.modules.shopify_listing.application.live_publish_runtime._fetch_spu_page",
                            side_effect=[(1, [{"spuId": "spu-1", "spuNo": "SPU-1", "title": "Interrupted Product"}])],
                        ):
                            with patch(
                                "src.modules.shopify_listing.application.live_publish_runtime._fetch_spu_details",
                                return_value={
                                    "SPU-1": {
                                        "spuNo": "SPU-1",
                                        "spuId": "spu-1",
                                        "title": "Interrupted Product",
                                        "sellerName": "Seller Interrupt",
                                        "children": [{"skuCode": "SKU-1", "itemNo": "ITEM-1", "stocks": [{"regionId": "US"}]}],
                                    }
                                },
                            ):
                                with patch(
                                    "src.modules.shopify_listing.application.live_publish_runtime._fetch_stock_map",
                                    side_effect=KeyboardInterrupt,
                                ):
                                    doba_from_settings.return_value = object()
                                    shopify_from_settings.return_value = object()
                                    result = publish_doba_products_live(
                                        report_path=str(report_path),
                                        resume=True,
                                        prefer_candidate_pool=False,
                                        page_size=20,
                                    )

    assert result["stopped_reason"] == "interrupted_by_user"
    assert result["last_failure"]["failed_reason"] == "interrupted_by_user"
    assert result["last_failure"]["resume_position"] == {"next_page": 1, "next_index": 0}


def test_publish_doba_products_live_targeted_candidate_publish_clears_stale_results(tmp_path):
    report_path = tmp_path / "live-report-targeted-empty.json"
    candidate_pool_path = tmp_path / "candidate-pool.json"
    report_path.write_text(
        json.dumps(
            {
                "started_at": "2026-06-17T00:00:00+00:00",
                "updated_at": "2026-06-17T00:00:00+00:00",
                "cursor": {"next_page": 9, "next_index": 3},
                "successful_spu_nos": ["SPU-OLD-1"],
                "results": [
                    {
                        "doba_spu_no": "SPU-OLD-1",
                        "action": "published",
                        "shopify_product_id": "gid://shopify/Product/old",
                    }
                ],
                "summary": {
                    "total_candidates": 1,
                    "scanned_count": 1,
                    "published_count": 1,
                    "skipped_count": 0,
                    "failed_count": 0,
                },
                "source_mode": "candidate_pool",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    candidate_pool_path.write_text(
        json.dumps(
            {
                "generated_at": "2026-06-17T00:10:00+00:00",
                "summary": {
                    "qualified_count": 0,
                    "skipped_by_reason": {"already_successfully_published": 1},
                },
                "qualified_candidates": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = publish_doba_products_live(
        report_path=str(report_path),
        candidate_pool_path=str(candidate_pool_path),
        prefer_candidate_pool=True,
        refresh_candidate_pool=False,
        resume=True,
        candidate_spu_nos=["SPU-NEW-1"],
        max_successes=1,
    )

    assert result["completed"] is True
    assert result["results"] == []
    assert result["summary"]["total_candidates"] == 0
    assert result["summary"]["published_count"] == 0
