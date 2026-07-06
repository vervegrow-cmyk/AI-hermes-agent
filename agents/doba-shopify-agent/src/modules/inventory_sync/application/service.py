from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from src.modules.inventory_sync.infrastructure.shopify_inventory_sync_service import ShopifyInventorySyncService
from src.shared.contracts.inventory import (
    InventoryChange,
    InventorySyncBatchResult,
    InventorySyncCommand,
    InventorySyncItem,
    InventorySyncPlan,
    InventorySyncRecord,
    InventorySyncReport,
    ShopifyInventoryState,
    SupplierInventory,
)
from src.shared.contracts.mapping import SkuMappingRecord
from src.shared.repositories import (
    InMemoryInventorySyncBatchRepository,
    InMemoryInventorySyncLogRepository,
    InMemoryShopifyInventoryRepository,
    InMemorySkuMappingRepository,
    InMemorySupplierInventoryRepository,
)
from src.shared.repositories.protocols import (
    InventorySyncBatchRepository,
    InventorySyncLogRepository,
    ShopifyInventoryRepository,
    SupplierArchiveRepository,
    SkuMappingRepository,
    SupplierInventoryRepository,
)


REPORT_PATH = Path("docs/audits/inventory-sync-report.md")


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _priority_for_change(change_type: str) -> int:
    priorities = {
        "out_of_stock": 100,
        "restocked": 90,
        "decrease": 80,
        "increase": 70,
        "unchanged": 0,
        "sync_failed": 95,
    }
    return priorities.get(change_type, 0)


def _detect_change(supplier: SupplierInventory, shopify: ShopifyInventoryState | None) -> InventoryChange:
    current = shopify.inventory if shopify is not None else 0
    target = max(0, supplier.inventory)
    delta = target - current
    if target < 0:
        return InventoryChange(
            supplier_sku=supplier.supplier_sku,
            current_inventory=current,
            target_inventory=target,
            delta=delta,
            change_type="sync_failed",
            warehouse=supplier.warehouse,
        )
    if target == current:
        change_type = "unchanged"
    elif target == 0:
        change_type = "out_of_stock"
    elif current == 0 and target > 0:
        change_type = "restocked"
    elif target > current:
        change_type = "increase"
    else:
        change_type = "decrease"
    return InventoryChange(
        supplier_sku=supplier.supplier_sku,
        current_inventory=current,
        target_inventory=target,
        delta=delta,
        change_type=change_type,
        warehouse=supplier.warehouse,
    )


def build_inventory_sync_plan(
    command: InventorySyncCommand,
    *,
    sku_mapping_repository: SkuMappingRepository | None = None,
) -> InventorySyncBatchResult:
    mapping_repository = sku_mapping_repository or InMemorySkuMappingRepository()
    changes: list[InventoryChange] = []
    plans: list[InventorySyncPlan] = []
    items: list[InventorySyncItem] = []

    shopify_by_sku = {state.supplier_sku.strip().lower(): state for state in command.shopify_inventory_states}
    for supplier in command.supplier_inventories:
        shopify = shopify_by_sku.get(supplier.supplier_sku.strip().lower())
        change = _detect_change(supplier, shopify)
        changes.append(change)

        mapping = mapping_repository.get_by_sku(supplier.supplier_sku)
        if mapping is None:
            change_type = "sync_failed"
            variant_id = ""
            requires_sync = True
        else:
            change_type = change.change_type
            variant_id = mapping.shopify_variant_id
            requires_sync = change_type != "unchanged"

        plan = InventorySyncPlan(
            supplier_sku=supplier.supplier_sku,
            shopify_variant_id=variant_id,
            current_inventory=change.current_inventory,
            target_inventory=change.target_inventory,
            change_type=change_type,
            priority=_priority_for_change(change_type),
            warehouse=supplier.warehouse,
            requires_sync=requires_sync,
        )
        plans.append(plan)
        items.append(
            InventorySyncItem(
                sku=supplier.supplier_sku,
                supplier_inventory=change.target_inventory,
                shopify_inventory=change.current_inventory,
                delta=change.delta,
                action="sync" if requires_sync and variant_id else ("sync_failed" if requires_sync else "skip"),
            )
        )

    synced_count = sum(1 for item in items if item.action == "sync")
    skipped_count = sum(1 for item in items if item.action != "sync")
    return InventorySyncBatchResult(
        target_market=command.target_market.upper(),
        synced_count=synced_count,
        skipped_count=skipped_count,
        items=items,
        changes=changes,
        plans=plans,
        mock_mode=True,
    )


def build_inventory_sync_command_from_archive(
    *,
    archive_repository: SupplierArchiveRepository,
    shopify_inventory_states: list[ShopifyInventoryState] | None = None,
    sku_mappings: list[dict] | None = None,
    supplier_skus: list[str] | None = None,
    target_market: str = "US",
) -> InventorySyncCommand:
    allowed_skus = {sku.strip().lower() for sku in list(supplier_skus or []) if str(sku).strip()}
    latest_by_sku: dict[str, InventorySnapshot] = {}
    for snapshot in archive_repository.list_inventory_snapshots():
        key = snapshot.sku.strip().lower()
        if allowed_skus and key not in allowed_skus:
            continue
        latest_by_sku[key] = snapshot
    return InventorySyncCommand(
        target_market=target_market,
        snapshots=list(latest_by_sku.values()),
        shopify_inventory_states=list(shopify_inventory_states or []),
        sku_mappings=list(sku_mappings or []),
    )


def _build_report(result: InventorySyncBatchResult) -> str:
    report = result.report
    lines = [
        "# Inventory Sync Report",
        "",
        "## Summary",
        f"- Products processed: `{report.products_processed}`",
        f"- Inventory changes detected: `{report.inventory_changes_detected}`",
        f"- Increases: `{report.increases}`",
        f"- Decreases: `{report.decreases}`",
        f"- Out of stock: `{report.out_of_stock}`",
        f"- Restocked: `{report.restocked}`",
        f"- Unchanged: `{report.unchanged}`",
        f"- Successful syncs: `{report.successful_syncs}`",
        f"- Failed syncs: `{report.failed_syncs}`",
        f"- Missing mappings: `{report.missing_mappings}`",
        f"- Mode: `{report.mode}`",
        f"- Inventory accuracy summary: {report.inventory_accuracy_summary}",
    ]
    return "\n".join(lines) + "\n"


def _write_report(result: InventorySyncBatchResult) -> str:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(_build_report(result), encoding="utf-8")
    return str(REPORT_PATH.resolve())


def run_inventory_sync_runtime(
    command: InventorySyncCommand,
    *,
    supplier_inventory_repository: SupplierInventoryRepository | None = None,
    shopify_inventory_repository: ShopifyInventoryRepository | None = None,
    inventory_sync_log_repository: InventorySyncLogRepository | None = None,
    inventory_sync_batch_repository: InventorySyncBatchRepository | None = None,
    sku_mapping_repository: SkuMappingRepository | None = None,
    sync_service: ShopifyInventorySyncService | None = None,
) -> InventorySyncBatchResult:
    supplier_repo = supplier_inventory_repository or InMemorySupplierInventoryRepository()
    shopify_repo = shopify_inventory_repository or InMemoryShopifyInventoryRepository()
    log_repo = inventory_sync_log_repository or InMemoryInventorySyncLogRepository()
    batch_repo = inventory_sync_batch_repository or InMemoryInventorySyncBatchRepository()
    mapping_repo = sku_mapping_repository or InMemorySkuMappingRepository()
    service = sync_service or ShopifyInventorySyncService()

    for mapping in command.sku_mappings:
        mapping_repo.save(SkuMappingRecord.model_validate(mapping))
    for supplier in command.supplier_inventories:
        supplier_repo.save_supplier_inventory(supplier)
    for state in command.shopify_inventory_states:
        shopify_repo.save_shopify_inventory_state(state)

    plan_result = build_inventory_sync_plan(
        InventorySyncCommand(
            target_market=command.target_market,
            supplier_inventories=supplier_repo.list_supplier_inventories(),
            shopify_inventory_states=shopify_repo.list_shopify_inventory_states(),
        ),
        sku_mapping_repository=mapping_repo,
    )

    records: list[InventorySyncRecord] = []
    successful_syncs = 0
    failed_syncs = 0
    missing_mappings = 0
    for plan in sorted(plan_result.plans, key=lambda item: item.priority, reverse=True):
        if plan.change_type == "unchanged":
            record = InventorySyncRecord(
                supplier_sku=plan.supplier_sku,
                shopify_variant_id=plan.shopify_variant_id,
                old_inventory=plan.current_inventory,
                new_inventory=plan.target_inventory,
                change_type=plan.change_type,
                status="skipped",
                sync_time=_now_iso(),
            )
        elif not plan.shopify_variant_id:
            missing_mappings += 1
            failed_syncs += 1
            record = InventorySyncRecord(
                supplier_sku=plan.supplier_sku,
                shopify_variant_id="",
                old_inventory=plan.current_inventory,
                new_inventory=plan.target_inventory,
                change_type="sync_failed",
                status="missing_mapping",
                sync_time=_now_iso(),
                error_message="Missing SKU mapping for supplier_sku.",
            )
        else:
            try:
                service.sync_inventory(plan)
                successful_syncs += 1
                record = InventorySyncRecord(
                    supplier_sku=plan.supplier_sku,
                    shopify_variant_id=plan.shopify_variant_id,
                    old_inventory=plan.current_inventory,
                    new_inventory=plan.target_inventory,
                    change_type=plan.change_type,
                    status="synced",
                    sync_time=_now_iso(),
                )
                shopify_repo.save_shopify_inventory_state(
                    ShopifyInventoryState(
                        supplier_sku=plan.supplier_sku,
                        shopify_variant_id=plan.shopify_variant_id,
                        inventory=plan.target_inventory,
                        updated_at=record.sync_time,
                    )
                )
            except Exception as exc:
                failed_syncs += 1
                record = InventorySyncRecord(
                    supplier_sku=plan.supplier_sku,
                    shopify_variant_id=plan.shopify_variant_id,
                    old_inventory=plan.current_inventory,
                    new_inventory=plan.target_inventory,
                    change_type="sync_failed",
                    status="sync_failed",
                    sync_time=_now_iso(),
                    error_message=str(exc),
                )
        log_repo.save_inventory_sync_record(record)
        records.append(record)

    change_counter = Counter(change.change_type for change in plan_result.changes)
    change_detected = sum(1 for change in plan_result.changes if change.change_type != "unchanged")
    report = InventorySyncReport(
        products_processed=len(plan_result.plans),
        inventory_changes_detected=change_detected,
        increases=change_counter.get("increase", 0),
        decreases=change_counter.get("decrease", 0),
        out_of_stock=change_counter.get("out_of_stock", 0),
        restocked=change_counter.get("restocked", 0),
        unchanged=change_counter.get("unchanged", 0),
        successful_syncs=successful_syncs,
        failed_syncs=failed_syncs,
        missing_mappings=missing_mappings,
        mode=service.mode,
        inventory_accuracy_summary=(
            f"{successful_syncs} synced, {failed_syncs} failed, {change_counter.get('unchanged', 0)} unchanged."
        ),
    )

    final_items = []
    record_by_sku = {record.supplier_sku: record for record in records}
    for item in plan_result.items:
        record = record_by_sku.get(item.sku)
        action = item.action if record is None else record.status
        final_items.append(
            InventorySyncItem(
                sku=item.sku,
                supplier_inventory=item.supplier_inventory,
                shopify_inventory=item.shopify_inventory,
                delta=item.delta,
                action=action,
            )
        )

    result = InventorySyncBatchResult(
        target_market=command.target_market.upper(),
        synced_count=successful_syncs,
        skipped_count=len(final_items) - successful_syncs,
        items=final_items,
        changes=plan_result.changes,
        plans=plan_result.plans,
        records=records,
        report=report,
        mock_mode=service.mode == "mock",
        no_product_creation_occurred=True,
        no_publish_occurred=True,
        no_price_update_occurred=True,
        no_order_creation_occurred=True,
    )
    result.report_path = _write_report(result)
    batch_repo.save_inventory_sync_batch_result(result)
    return result
