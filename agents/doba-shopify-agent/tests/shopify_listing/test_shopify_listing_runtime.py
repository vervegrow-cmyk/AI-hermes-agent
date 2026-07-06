from pathlib import Path

import pytest

from src.modules.shopify_listing import ShopifyDraftListingService, run_shopify_listing
from src.modules.shopify_listing.application.runtime import (
    _build_payload,
    _map_collections,
    _process_images,
)
from src.shared.contracts.listing import ShopifyProductPayload
from src.shared.contracts.screening import ListingCandidate
from src.shared.repositories import InMemoryListingRepository, InMemorySkuMappingRepository


def _approved_candidate(**overrides) -> ListingCandidate:
    payload = {
        "supplier_sku": "sku-100",
        "supplier_product_id": "supplier-product-100",
        "status": "approved_for_listing",
        "overall_score": 91,
        "source_title": "compact outdoor storage bench with cushion",
        "source_description": "A weather-friendly storage bench for patios, entryways, and garden corners.",
        "source_brand": "Doba Basics",
        "source_category": "Outdoor Furniture",
        "source_price": 89.99,
        "source_inventory": 42,
        "source_image_urls": [
            "https://cdn.example.com/storage-bench.jpg",
            "https://cdn.example.com/storage-bench.jpg?cache=1",
            "https://cdn.example.com/storage-bench-side.png",
            "ftp://invalid.example.com/skip.png",
        ],
        "source_attributes": {
            "material": "Powder-coated steel",
            "color": "Natural",
        },
    }
    payload.update(overrides)
    return ListingCandidate.model_validate(payload)


def test_approved_for_listing_products_can_be_transformed():
    payload = _build_payload(_approved_candidate())
    assert payload.supplier_sku == "sku-100"
    assert payload.status == "draft"
    assert payload.content.title
    assert payload.images


def test_title_description_faq_and_seo_generation_work():
    payload = _build_payload(_approved_candidate())
    assert "Compact Outdoor Storage Bench With Cushion" in payload.content.title
    assert "<h2>Key Features</h2>" in payload.content.description
    assert len(payload.content.faq) >= 3
    assert payload.seo.seo_title
    assert payload.seo.seo_description
    assert payload.seo.handle.startswith("doba-basics-compact-outdoor-storage-bench")


def test_image_processing_and_collection_mapping_work():
    candidate = _approved_candidate()
    images = _process_images(
        {
            "image_urls": candidate.source_image_urls,
            "title": candidate.source_title,
        },
        "Demo Product",
    )
    collections = _map_collections(
        {
            "title": candidate.source_title,
            "category": candidate.source_category,
            "description": candidate.source_description,
        }
    )
    assert len(images) == 2
    assert images[0].is_primary is True
    assert "Outdoor" in collections


def test_duplicate_detection_works_for_existing_supplier_sku():
    listing_repository = InMemoryListingRepository()
    mapping_repository = InMemorySkuMappingRepository()
    service = ShopifyDraftListingService(force_mode="mock")

    first = run_shopify_listing([_approved_candidate()], listing_repository, mapping_repository, service)
    second = run_shopify_listing([_approved_candidate()], listing_repository, mapping_repository, service)

    assert first.draft_products_created == 1
    assert second.duplicate_products_skipped == 1
    assert second.skipped_products[0]["reason"] == "duplicate_supplier_sku"


def test_duplicate_detection_works_for_existing_handle_and_product_hash():
    listing_repository = InMemoryListingRepository()
    mapping_repository = InMemorySkuMappingRepository()
    service = ShopifyDraftListingService(force_mode="mock")

    first_candidate = _approved_candidate()
    second_candidate = _approved_candidate(
        supplier_sku="sku-101",
        supplier_product_id="supplier-product-101",
        source_image_urls=["https://cdn.example.com/another-bench.jpg"],
        source_description="Alternate supplier copy for the same handle test.",
    )
    third_candidate = _approved_candidate(
        supplier_sku="sku-102",
        supplier_product_id="supplier-product-102",
        source_title="weather-ready patio bench for storage and seating",
    )

    run_shopify_listing([first_candidate], listing_repository, mapping_repository, service)
    handle_result = run_shopify_listing([second_candidate], listing_repository, InMemorySkuMappingRepository(), service)
    hash_result = run_shopify_listing([third_candidate], listing_repository, InMemorySkuMappingRepository(), service)

    assert handle_result.duplicate_products_skipped == 1
    assert handle_result.skipped_products[0]["reason"] == "duplicate_handle"
    assert hash_result.duplicate_products_skipped == 1
    assert hash_result.skipped_products[0]["reason"] == "duplicate_product_hash"


def test_sku_mapping_creation_and_draft_product_creation_work():
    listing_repository = InMemoryListingRepository()
    mapping_repository = InMemorySkuMappingRepository()
    result = run_shopify_listing(
        [_approved_candidate()],
        listing_repository,
        mapping_repository,
        ShopifyDraftListingService(force_mode="mock"),
    )
    assert result.draft_products_created == 1
    assert result.sku_mappings_created == 1
    assert mapping_repository.get_by_sku("sku-100") is not None
    assert listing_repository.get_shopify_product_by_supplier_sku("sku-100") is not None


def test_mock_shopify_mode_works_and_status_remains_draft():
    result = run_shopify_listing(
        [_approved_candidate()],
        InMemoryListingRepository(),
        InMemorySkuMappingRepository(),
        ShopifyDraftListingService(force_mode="mock"),
    )
    assert result.shopify_mode == "mock"
    assert result.draft_products[0].mock_mode is True
    assert result.draft_products[0].status == "draft"


def test_real_shopify_service_adapter_works_without_publish_inventory_or_price_updates():
    class FakeClient:
        def __init__(self) -> None:
            self.create_calls = 0
            self.publish_calls = 0
            self.inventory_calls = 0
            self.price_calls = 0

        def describe_admin_session(self):
            return {"store_domain": "unit-test-store.myshopify.com"}

        def create_draft_product(self, product_input):
            self.create_calls += 1
            return {
                "id": "gid://shopify/Product/500",
                "status": "DRAFT",
                "variants": {
                    "edges": [
                        {
                            "node": {
                                "id": "gid://shopify/ProductVariant/600",
                            }
                        }
                    ]
                },
            }

    candidate = _approved_candidate()
    payload = _build_payload(candidate)
    client = FakeClient()
    service = ShopifyDraftListingService(client=client, force_mode="real")
    created = service.create_draft_product(payload)

    assert created["shopify_product_id"] == "gid://shopify/Product/500"
    assert created["shopify_variant_id"] == "gid://shopify/ProductVariant/600"
    assert created["status"] == "draft"
    assert client.create_calls == 1
    assert client.publish_calls == 0
    assert client.inventory_calls == 0
    assert client.price_calls == 0


def test_publish_inventory_price_and_order_counts_remain_zero():
    result = run_shopify_listing(
        [_approved_candidate()],
        InMemoryListingRepository(),
        InMemorySkuMappingRepository(),
        ShopifyDraftListingService(force_mode="mock"),
    )
    assert result.publish_count == 0
    assert result.inventory_update_count == 0
    assert result.price_update_count == 0
    assert result.order_create_count == 0


def test_listing_report_generation_works():
    report_path = Path("docs/audits/shopify-listing-report.md")
    if report_path.exists():
        report_path.unlink()

    result = run_shopify_listing(
        [_approved_candidate()],
        InMemoryListingRepository(),
        InMemorySkuMappingRepository(),
        ShopifyDraftListingService(force_mode="mock"),
    )

    assert report_path.exists()
    content = report_path.read_text(encoding="utf-8")
    assert result.report_path
    assert "Draft products created" in content
    assert "Publish count: `0`" in content


def test_non_approved_listing_candidates_are_ignored():
    listing_repository = InMemoryListingRepository()
    mapping_repository = InMemorySkuMappingRepository()
    manual_review = _approved_candidate(status="manual_review", supplier_sku="sku-200")
    result = run_shopify_listing([manual_review], listing_repository, mapping_repository, ShopifyDraftListingService(force_mode="mock"))
    assert result.total_approved_products == 0
    assert result.draft_products_created == 0
    assert mapping_repository.list_all() == []


def test_service_accepts_shopify_product_payload_contract():
    payload = ShopifyProductPayload(supplier_sku="sku-1")
    service = ShopifyDraftListingService(force_mode="mock")
    created = service.create_draft_product(payload)
    assert created["status"] == "draft"
