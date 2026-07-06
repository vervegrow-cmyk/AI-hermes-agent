from pathlib import Path
import io
import json
import sys

import pytest

AGENT_ROOT = Path(__file__).resolve().parents[1]
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from models.price_sync import DobaPriceSnapshot, PriceSyncRequest, ShopifyPriceState
from service.executor import run_price_sync
from service.mapping_repository import MappingRepository
from service.progress_logger import ProgressLogger
from service.shopify_price_sync_service import ShopifyPriceSyncService
from service.sync_repository import SyncRepository
from service.variant_mapping_builder import VariantMappingBuilder


def test_progress_logger_prints_and_writes_files(tmp_path, monkeypatch):
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    logger = ProgressLogger(root=tmp_path, job_type="mapping_build", batch_id="b1", print_enabled=True)
    logger.step_start(phase="fetch", message="start")
    logger.progress(
        phase="fetch",
        current_step=1,
        total_steps=2,
        current_item=1,
        total_items=2,
        ok_count=1,
        skipped_count=0,
        failed_count=0,
        message="halfway",
    )
    checkpoint = logger.save_checkpoint(
        phase="fetch",
        index=1,
        total_items=2,
        last_doba_sku="SKU-1",
        interrupted=True,
        reason_text_zh="用户中断任务，已保存当前处理进度",
        last_decision="synced",
        last_reason_code="success",
    )
    logger.interrupted(phase="fetch", index=1, total=2, reason_code="interrupted_by_user", last_doba_sku="SKU-1", checkpoint_path=checkpoint)
    output = captured.getvalue()
    assert "[STEP-START]" in output
    assert "[PROGRESS]" in output
    assert "[CHECKPOINT]" in output
    assert logger.log_path.exists()
    assert logger.progress_path.exists()
    assert logger.checkpoint_path.exists()
    payload = json.loads(logger.checkpoint_path.read_text(encoding="utf-8"))
    assert payload["last_decision"] == "synced"
    assert payload["last_reason_code"] == "success"


def test_variant_mapping_builder_writes_interrupt_checkpoint(tmp_path):
    class _InterruptingDobaClient:
        def list_price_snapshots(self, **kwargs):
            raise KeyboardInterrupt()

    repository = MappingRepository(path=tmp_path / "runtime" / "mappings.json")
    builder = VariantMappingBuilder(repository=repository, doba_client=_InterruptingDobaClient())
    with pytest.raises(KeyboardInterrupt):
        builder.build({"store_name": "demo-store", "sync_scope": "full", "shopify_variants": [], "print_detail": False})
    checkpoints = list((tmp_path / "runtime" / "checkpoints").glob("mapping_build_*.json"))
    reports = list((tmp_path / "runtime" / "reports").glob("mapping_build_*.json"))
    assert checkpoints
    assert reports
    report = json.loads(reports[0].read_text(encoding="utf-8"))
    assert report["interrupted"] is True


def test_price_sync_writes_runtime_exception_checkpoint(tmp_path):
    class _ExplodingShopifyService(ShopifyPriceSyncService):
        def get_price_states(self, **kwargs):
            raise RuntimeError("boom")

    repository = MappingRepository(path=tmp_path / "runtime" / "mappings.json")
    repository.save_records(
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
            }
        ]
    )
    with pytest.raises(RuntimeError):
        run_price_sync(
            PriceSyncRequest(
                store_name="demo-store",
                sync_scope="full",
                doba_snapshots=[DobaPriceSnapshot(store_name="demo-store", doba_product_id="prod-SKU-1", doba_sku="SKU-1", supplier_cost=10, shipping_cost=2, estimated_total_cost=12, raw_hash="hash-SKU-1")],
                mode="dry-run",
            ),
            mapping_repository=repository,
            sync_repository=SyncRepository(root=tmp_path / "runtime"),
            shopify_service=_ExplodingShopifyService(force_mode="mock"),
        )
    checkpoints = list((tmp_path / "runtime" / "checkpoints").glob("price_dry_run_*.json"))
    reports = list((tmp_path / "runtime" / "reports").glob("price_sync_*.json"))
    assert checkpoints
    assert reports
    report = json.loads(reports[0].read_text(encoding="utf-8"))
    assert report["checkpoint_path"]
    assert report["interrupted"] is False


def test_price_sync_streaming_report_updates_per_item(tmp_path):
    repository = MappingRepository(path=tmp_path / "runtime" / "mappings.json")
    repository.save_records(
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
            },
            {
                "store_name": "demo-store",
                "supplier": "doba",
                "doba_product_id": "prod-SKU-2",
                "doba_sku": "SKU-2",
                "shopify_product_id": "gid://shopify/Product/2",
                "shopify_variant_id": "gid://shopify/ProductVariant/2",
                "shopify_sku": "SKU-2",
                "mapping_status": "active",
            },
        ]
    )

    class _StreamingShopifyService(ShopifyPriceSyncService):
        def get_price_states(self, **kwargs):
            mapping = kwargs["mappings"][0]
            return [
                ShopifyPriceState(
                    store_name="demo-store",
                    shopify_product_id=mapping.shopify_product_id,
                    shopify_variant_id=mapping.shopify_variant_id,
                    shopify_sku=mapping.shopify_sku,
                    current_price=8.0,
                )
            ]

    batch = run_price_sync(
        PriceSyncRequest(
            store_name="demo-store",
            sync_scope="full",
            doba_snapshots=[
                DobaPriceSnapshot(store_name="demo-store", doba_product_id="prod-SKU-1", doba_sku="SKU-1", supplier_cost=10, shipping_cost=2, estimated_total_cost=12, raw_hash="hash-SKU-1"),
                DobaPriceSnapshot(store_name="demo-store", doba_product_id="prod-SKU-2", doba_sku="SKU-2", supplier_cost=10, shipping_cost=2, estimated_total_cost=12, raw_hash="hash-SKU-2"),
            ],
            mode="dry-run",
        ),
        mapping_repository=repository,
        sync_repository=SyncRepository(root=tmp_path / "runtime"),
        shopify_service=_StreamingShopifyService(force_mode="mock"),
    )
    report = json.loads(Path(batch.report_path).read_text(encoding="utf-8"))
    assert len(report["items"]) == 2
    log_text = next((tmp_path / "runtime" / "logs").glob("price_dry_run_*.log")).read_text(encoding="utf-8")
    assert "[条目开始]" in log_text
    assert "[条目完成]" in log_text
