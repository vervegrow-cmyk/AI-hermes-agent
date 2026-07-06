from pathlib import Path
import sys

AGENT_ROOT = Path(__file__).resolve().parents[1]
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from models.price_sync import DobaPriceSnapshot, PriceSyncRequest, ShopifyPriceState
from models.variant_mapping import ShopifyVariantSnapshot
from service.executor import run_price_sync
from service.mapping_importer import MappingImporter
from service.mapping_repository import MappingRepository
from service.mapping_validator import MappingValidator
from service.shopify_price_sync_service import ShopifyPriceSyncService
from service.sync_repository import SyncRepository
from service.variant_mapping_builder import VariantMappingBuilder
from service.doba_client import DobaPriceSyncClient


def _snapshot(sku: str, *, product_id: str | None = None):
    return DobaPriceSnapshot(
        store_name="demo-store",
        doba_product_id=product_id or f"prod-{sku}",
        doba_sku=sku,
        supplier_cost=10.0,
        shipping_cost=2.0,
        estimated_total_cost=12.0,
        source_updated_at="2026-06-30T10:00:00+00:00",
        raw_hash=f"hash-{sku}",
    )


def _variant(sku: str, variant_id: str, *, product_id: str = "gid://shopify/Product/1"):
    return ShopifyVariantSnapshot(
        store_name="demo-store",
        shopify_product_id=product_id,
        shopify_variant_id=variant_id,
        shopify_sku=sku,
        shopify_product_title="Demo Product",
        shopify_variant_title="Default Title",
        shopify_vendor="Doba",
        status="ACTIVE",
    )


def _sync_repo(tmp_path):
    return SyncRepository(root=tmp_path / "runtime")


def test_variant_mapping_build_exact_sku_creates_active_mapping(tmp_path):
    repository = MappingRepository(path=tmp_path / "runtime" / "mappings.json")
    report = VariantMappingBuilder(repository=repository).build(
        request={
            "store_name": "demo-store",
            "sync_scope": "full",
            "doba_snapshots": [_snapshot("SKU-1").model_dump(mode="json")],
            "shopify_variants": [_variant("SKU-1", "gid://shopify/ProductVariant/1").model_dump(mode="json")],
            "print_detail": False,
        }
    )
    records = repository.load_variant_records()
    assert report["summary"]["active_mappings"] == 1
    assert records[0].mapping_status == "active"
    assert records[0].match_type == "exact_sku"


def test_variant_mapping_build_marks_duplicate_source(tmp_path):
    repository = MappingRepository(path=tmp_path / "runtime" / "mappings.json")
    VariantMappingBuilder(repository=repository).build(
        request={
            "store_name": "demo-store",
            "sync_scope": "full",
            "doba_snapshots": [_snapshot("SKU-1").model_dump(mode="json")],
            "shopify_variants": [
                _variant("SKU-1", "gid://shopify/ProductVariant/1").model_dump(mode="json"),
                _variant("SKU-1", "gid://shopify/ProductVariant/2").model_dump(mode="json"),
            ],
            "print_detail": False,
        }
    )
    records = repository.load_variant_records()
    assert len([item for item in records if item.mapping_status == "duplicate_source"]) == 2


def test_variant_mapping_build_marks_duplicate_target(tmp_path):
    repository = MappingRepository(path=tmp_path / "runtime" / "mappings.json")
    repository.save_variant_records(
        [
            {
                "store_name": "demo-store",
                "supplier": "doba",
                "doba_product_id": "prod-SKU-1",
                "doba_sku": "SKU-1",
                "shopify_product_id": "gid://shopify/Product/1",
                "shopify_variant_id": "gid://shopify/ProductVariant/1",
                "shopify_sku": "SKU-1",
                "mapping_status": "active",
                "match_type": "manual_import",
                "match_confidence": 100,
                "reason_code": "matched_by_manual_import",
            }
        ]
    )
    VariantMappingBuilder(repository=repository).build(
        request={
            "store_name": "demo-store",
            "sync_scope": "full",
            "doba_snapshots": [
                _snapshot("SKU-1").model_dump(mode="json"),
                _snapshot("SKU-2").model_dump(mode="json"),
            ],
            "shopify_variants": [
                _variant("SKU-2", "gid://shopify/ProductVariant/1").model_dump(mode="json"),
            ],
            "print_detail": False,
        }
    )
    records = repository.load_variant_records()
    duplicate_target = [item for item in records if item.mapping_status == "duplicate_target"]
    assert len(duplicate_target) == 2


def test_variant_mapping_build_outputs_unmatched_lists(tmp_path):
    repository = MappingRepository(path=tmp_path / "runtime" / "mappings.json")
    report = VariantMappingBuilder(repository=repository).build(
        request={
            "store_name": "demo-store",
            "sync_scope": "full",
            "doba_snapshots": [_snapshot("SKU-1").model_dump(mode="json")],
            "shopify_variants": [_variant("SKU-2", "gid://shopify/ProductVariant/2").model_dump(mode="json")],
            "print_detail": False,
        }
    )
    records = repository.load_variant_records()
    assert any(item.mapping_status == "unmatched_doba" for item in records)
    assert Path(report["outputs"]["review_csv"]).exists()


def test_variant_mapping_build_marks_unmatched_shopify_without_candidate_sku(tmp_path):
    repository = MappingRepository(path=tmp_path / "runtime" / "mappings.json")
    class _NoLookupDobaClient:
        def list_price_snapshots(self, **kwargs):
            assert kwargs.get("skus") == []
            return []

    report = VariantMappingBuilder(repository=repository, doba_client=_NoLookupDobaClient()).build(
        request={
            "store_name": "demo-store",
            "sync_scope": "full",
            "doba_snapshots": [],
            "shopify_variants": [_variant("", "gid://shopify/ProductVariant/9").model_dump(mode="json")],
            "print_detail": False,
        }
    )
    records = repository.load_variant_records()
    assert any(item.mapping_status == "unmatched_shopify" for item in records)
    assert Path(report["outputs"]["review_csv"]).exists()


def test_import_reviewed_promotes_active_mapping_and_price_sync_consumes_active_only(tmp_path):
    repository = MappingRepository(path=tmp_path / "runtime" / "mappings.json")
    build_result = VariantMappingBuilder(repository=repository).build(
        request={
            "store_name": "demo-store",
            "sync_scope": "full",
            "doba_snapshots": [_snapshot("SKU-1").model_dump(mode="json")],
            "shopify_variants": [],
            "print_detail": False,
        }
    )
    review_path = Path(build_result["outputs"]["review_csv"])
    review_path.write_text(
        "\n".join(
            [
                "store_name,supplier,doba_product_id,doba_sku,doba_title,shopify_product_id,shopify_variant_id,shopify_sku,shopify_product_title,shopify_variant_title,match_type,match_confidence,mapping_status,reason_code,manual_note",
                "demo-store,doba,prod-SKU-1,SKU-1,,gid://shopify/Product/1,gid://shopify/ProductVariant/1,SKU-1,Demo Product,Default Title,manual_import,100,active,matched_by_manual_import,",
            ]
        ),
        encoding="utf-8",
    )
    import_result = MappingImporter(repository=repository).import_reviewed(
        store_name="demo-store",
        file_path=str(review_path),
    )
    assert import_result["imported"] == 1
    validation = MappingValidator().validate(
        store_name="demo-store",
        records=repository.load_variant_records(),
    )
    assert validation["result"] == "pass"

    batch = run_price_sync(
        PriceSyncRequest(
            store_name="demo-store",
            sync_scope="full",
            doba_snapshots=[_snapshot("SKU-1")],
            shopify_states=[
                ShopifyPriceState(
                    store_name="demo-store",
                    shopify_product_id="gid://shopify/Product/1",
                    shopify_variant_id="gid://shopify/ProductVariant/1",
                    shopify_sku="SKU-1",
                    current_price=8.0,
                )
            ],
            mode="dry-run",
        ),
        mapping_repository=repository,
        sync_repository=_sync_repo(tmp_path),
        shopify_service=ShopifyPriceSyncService(force_mode="mock"),
    )
    assert batch.processed_count == 1
    assert batch.items[0].shopify_variant_id == "gid://shopify/ProductVariant/1"


def test_price_sync_fails_cleanly_without_active_mappings(tmp_path):
    repository = MappingRepository(path=tmp_path / "runtime" / "mappings.json")
    repository.save_variant_records(
        [
            {
                "store_name": "demo-store",
                "supplier": "doba",
                "doba_product_id": "prod-SKU-1",
                "doba_sku": "SKU-1",
                "mapping_status": "unmatched_doba",
                "match_type": "unknown",
                "reason_code": "unmatched_doba",
            }
        ]
    )
    batch = run_price_sync(
        PriceSyncRequest(
            store_name="demo-store",
            sync_scope="full",
            doba_snapshots=[_snapshot("SKU-1")],
            mode="dry-run",
        ),
        mapping_repository=repository,
        sync_repository=_sync_repo(tmp_path),
        shopify_service=ShopifyPriceSyncService(force_mode="mock"),
    )
    assert batch.status == "failed"
    assert batch.processed_count == 0


def test_variant_mapping_build_uses_shopify_candidate_skus_only(tmp_path):
    repository = MappingRepository(path=tmp_path / "runtime" / "mappings.json")
    seen: dict[str, object] = {}

    class _DobaClient:
        def list_price_snapshots(self, **kwargs):
            seen["skus"] = kwargs.get("skus")
            seen["sync_scope"] = kwargs.get("sync_scope")
            return [_snapshot("SKU-1")]

    VariantMappingBuilder(repository=repository, doba_client=_DobaClient()).build(
        request={
            "store_name": "demo-store",
            "sync_scope": "full",
            "shopify_variants": [_variant("SKU-1", "gid://shopify/ProductVariant/1").model_dump(mode="json")],
            "print_detail": False,
        }
    )
    assert seen["skus"] == ["SKU-1"]
    assert seen["sync_scope"] == "single_sku"


def test_doba_full_scan_disabled_by_default(monkeypatch):
    get_settings = __import__("shared.config", fromlist=["get_settings"]).get_settings
    get_settings.cache_clear()
    monkeypatch.delenv("DOBA_ALLOW_FULL_SCAN", raising=False)
    client = DobaPriceSyncClient(http_client=object())
    try:
        client.list_price_snapshots(store_name="demo-store", sync_scope="full")
        raise AssertionError("expected doba_full_scan_disabled")
    except RuntimeError as exc:
        assert str(exc) == "doba_full_scan_disabled"
    finally:
        get_settings.cache_clear()
