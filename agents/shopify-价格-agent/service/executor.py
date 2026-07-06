from __future__ import annotations

import json
from pathlib import Path
from typing import Callable
from uuid import uuid4

from models.price_sync import GigaPriceSnapshot, PriceSyncBatch, PriceSyncRequest, ShopifyPriceState, utc_now_iso
from service.giga_client import GigaClient
from service.mapping_repository import MappingRepository
from service.plan_builder import build_plan
from service.shopify_price_sync_service import ShopifyPriceSyncService
from service.sync_repository import SyncRepository
from shared.clients import ShopifyAuthClient
from shared.config import get_settings
from shared.schemas import ExecuteRequest


def _resolve_store_name(request: PriceSyncRequest) -> str:
    settings = get_settings()
    return (
        request.store_name
        or settings.shopify_shop
        or settings.shopify_store
        or settings.shopify_shop_domain
        or "unconfigured-store"
    )


def _build_state_key(store_name: str, giga_sku: str, variant_id: str) -> str:
    return f"{store_name}::{giga_sku}::{variant_id}"


def _refresh_batch_counts(batch: PriceSyncBatch) -> None:
    batch.processed_count = len(batch.items)
    batch.success_count = sum(1 for item in batch.items if item.status == "synced")
    batch.failed_count = sum(1 for item in batch.items if item.status == "failed")
    batch.skipped_count = sum(1 for item in batch.items if item.status == "skipped")
    batch.manual_review_count = sum(1 for item in batch.items if item.status == "manual_review")


def _write_report(batch: PriceSyncBatch, root: Path | None = None) -> str:
    output_root = root or (Path(__file__).resolve().parents[1] / "runtime" / "reports")
    output_root.mkdir(parents=True, exist_ok=True)
    json_path = output_root / f"{batch.batch_id}.json"
    md_path = output_root / f"{batch.batch_id}.md"
    json_path.write_text(json.dumps(batch.model_dump(mode="json"), ensure_ascii=True, indent=2), encoding="utf-8")
    lines = [
        f"# Price Sync Batch {batch.batch_id}",
        "",
        f"- Store: `{batch.store_name}`",
        f"- Mode: `{batch.mode}`",
        f"- Status: `{batch.status}`",
        f"- Processed: `{batch.processed_count}`",
        f"- Success: `{batch.success_count}`",
        f"- Failed: `{batch.failed_count}`",
        f"- Skipped: `{batch.skipped_count}`",
        f"- Manual review: `{batch.manual_review_count}`",
        "",
        "## Product View",
    ]
    grouped: dict[str, list[str]] = {}
    for item in batch.items:
        grouped.setdefault(item.shopify_product_id or "unmapped", []).append(
            f"{item.giga_sku}: {item.decision} -> {item.target_price:.2f} ({item.status})"
        )
    for product_id, rows in grouped.items():
        lines.append(f"- Product `{product_id}`")
        for row in rows:
            lines.append(f"  - {row}")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(json_path.resolve())


def run_price_sync(
    command: PriceSyncRequest,
    *,
    giga_client: GigaClient | None = None,
    mapping_repository: MappingRepository | None = None,
    sync_repository: SyncRepository | None = None,
    shopify_service: ShopifyPriceSyncService | None = None,
    progress_callback: Callable[[dict], None] | None = None,
) -> PriceSyncBatch:
    store_name = _resolve_store_name(command)
    batch = PriceSyncBatch(batch_id=str(uuid4()), store_name=store_name, mode=command.mode)

    def emit_stage(stage: str, **extra) -> None:
        if progress_callback is None:
            return
        progress_callback(
            {
                "event": "stage",
                "batch_id": batch.batch_id,
                "store_name": batch.store_name,
                "mode": batch.mode,
                "stage": stage,
                **extra,
            }
        )

    def emit_stage_payload(default_stage: str, payload: dict) -> None:
        actual_stage = payload.get("stage", default_stage)
        extra = {key: value for key, value in payload.items() if key != "stage"}
        emit_stage(actual_stage, **extra)

    giga = giga_client or GigaClient()
    mapping_repo = mapping_repository or MappingRepository()
    sync_repo = sync_repository or SyncRepository()
    shopify = shopify_service or ShopifyPriceSyncService()
    mappings_override = command.mappings or None
    snapshots_override = command.giga_snapshots or None
    shopify_states_override = command.shopify_states or None
    mappings = mapping_repo.load_records(mappings_override)
    emit_stage("start", sync_scope=command.sync_scope, requested_sku_count=len(command.sku_list), existing_mapping_count=len(mappings))

    should_refresh_discovery = mappings_override is None and command.sync_scope == "full"
    if should_refresh_discovery or not mappings:
        emit_stage("discover_shopify_mappings_started", refresh=should_refresh_discovery, current_mapping_count=len(mappings))
        try:
            discovered_mappings = shopify.discover_mappings(
                store_name=store_name,
                sku_list=command.sku_list or None,
                progress_callback=lambda payload: emit_stage_payload("discover_shopify_mappings_progress", payload),
            )
        except Exception:
            discovered_mappings = []
        emit_stage("discover_shopify_mappings_finished", discovered_mapping_count=len(discovered_mappings))
        if discovered_mappings:
            merged_by_key = {
                (item.store_name, item.giga_sku, item.shopify_variant_id): item
                for item in mappings
            }
            for item in discovered_mappings:
                merged_by_key[(item.store_name, item.giga_sku, item.shopify_variant_id)] = item
            mappings = list(merged_by_key.values())
            if mappings_override is None:
                mapping_repo.save_records(mappings)

    candidate_skus = list(dict.fromkeys(
        [sku for sku in command.sku_list if sku]
        or [record.giga_sku for record in mappings if record.store_name == store_name and record.giga_sku]
    ))
    emit_stage("candidate_skus_ready", candidate_sku_count=len(candidate_skus))

    last_successful_sync_at = ""
    if command.sync_scope != "full" and not command.skip_incremental_cache:
        for state in sync_repo.list_states().values():
            if state.get("store_name") == store_name and state.get("last_sync_status") == "synced":
                last_successful_sync_at = max(last_successful_sync_at, state.get("last_source_updated_at", ""))

    snapshots = giga.list_price_snapshots(
        store_name=store_name,
        sync_scope=command.sync_scope,
        updated_since=last_successful_sync_at,
        skus=candidate_skus,
        snapshots_override=snapshots_override,
        progress_callback=lambda payload: emit_stage_payload("giga_snapshots_progress", payload),
    )
    emit_stage("giga_snapshots_fetched", snapshot_count=len(snapshots))
    if command.sync_scope == "single_sku" and command.sku_list:
        snapshots = [item for item in snapshots if item.giga_sku in set(command.sku_list)]
        emit_stage("single_sku_filtered", snapshot_count=len(snapshots))

    validation_report = mapping_repo.build_validation_report(store_name=store_name, records=mappings)
    sync_repo.save_state(f"{store_name}::mapping_validation", validation_report)
    states = shopify.get_price_states(
        store_name=store_name,
        snapshots=snapshots,
        mappings=mappings,
        states_override=shopify_states_override,
        progress_callback=lambda payload: emit_stage_payload("shopify_states_progress", payload),
    )
    emit_stage("shopify_states_loaded", state_count=len(states))
    planned_items = build_plan(
        store_name=store_name,
        snapshots=snapshots,
        mappings=mappings,
        shopify_states=states,
        sync_scope=command.sync_scope,
        force_recalculate=command.force_recalculate or command.skip_incremental_cache,
        mapping_repository=mapping_repo,
        sync_repository=sync_repo,
    )

    batch.items = planned_items
    _refresh_batch_counts(batch)
    emit_stage(
        "plan_built",
        processed_count=batch.processed_count,
        planned_count=sum(1 for item in batch.items if item.status == "planned"),
        skipped_count=batch.skipped_count,
        manual_review_count=batch.manual_review_count,
    )

    if command.mode == "apply":
        total_items = len(batch.items)
        emitted_keys: set[tuple[str, str]] = set()

        def emit_progress(item, index: int) -> None:
            if progress_callback is None:
                return
            progress_callback(
                {
                    "event": "item",
                    "batch_id": batch.batch_id,
                    "store_name": batch.store_name,
                    "mode": batch.mode,
                    "index": index,
                    "total": total_items,
                    "item": item.model_dump(mode="json"),
                    "counts": {
                        "processed_count": batch.processed_count,
                        "success_count": batch.success_count,
                        "failed_count": batch.failed_count,
                        "skipped_count": batch.skipped_count,
                        "manual_review_count": batch.manual_review_count,
                    },
                }
            )

        planned = [item for item in planned_items if item.status == "planned"]
        states_by_sku = {item.giga_sku: item for item in snapshots}
        eligible = []
        for item in planned:
            source_snapshot = states_by_sku.get(item.giga_sku)
            if source_snapshot is None:
                continue
            idempotency_key = "::".join(
                [
                    store_name,
                    item.giga_sku,
                    item.shopify_variant_id,
                    f"{item.target_price:.2f}",
                    source_snapshot.source_updated_at,
                ]
            )
            previous = sync_repo.get_state(_build_state_key(store_name, item.giga_sku, item.shopify_variant_id)) or {}
            if previous.get("idempotency_key") == idempotency_key and previous.get("last_sync_status") == "synced":
                item.status = "skipped"
                item.reason_codes.append("idempotent_duplicate")
                batch.skipped_count += 1
                continue
            eligible.append(item)
        emit_stage("apply_queue_ready", eligible_count=len(eligible), total_items=total_items)

        for index, item in enumerate(batch.items, start=1):
            if item.status in {"skipped", "manual_review", "failed"}:
                emitted_keys.add((item.giga_sku, item.shopify_variant_id))
                emit_progress(item, index)

        for item in eligible:
            updated_items = shopify.apply_price_updates([item])
            replacement = updated_items[0] if updated_items else item.model_copy(
                update={"status": "failed", "error_message": "shopify_write_failed:no_result"}
            )
            batch.items = [
                replacement if existing.giga_sku == item.giga_sku and existing.shopify_variant_id == item.shopify_variant_id else existing
                for existing in batch.items
            ]
            _refresh_batch_counts(batch)
            sync_repo.save_batch(batch)
            _write_report(batch)
            replacement_index = next(
                (
                    idx
                    for idx, existing in enumerate(batch.items, start=1)
                    if existing.giga_sku == replacement.giga_sku and existing.shopify_variant_id == replacement.shopify_variant_id
                ),
                0,
            )
            emitted_keys.add((replacement.giga_sku, replacement.shopify_variant_id))
            emit_progress(replacement, replacement_index)

            source_snapshot = next((snap for snap in snapshots if snap.giga_sku == replacement.giga_sku), None)
            if source_snapshot is None:
                continue
            sync_repo.save_state(
                _build_state_key(store_name, replacement.giga_sku, replacement.shopify_variant_id),
                {
                    "store_name": store_name,
                    "giga_sku": replacement.giga_sku,
                    "shopify_variant_id": replacement.shopify_variant_id,
                    "last_source_hash": source_snapshot.raw_hash,
                    "last_source_updated_at": source_snapshot.source_updated_at,
                    "last_target_price": replacement.target_price,
                    "last_shopify_price": replacement.target_price if replacement.status == "synced" else replacement.old_price,
                    "last_decision": replacement.decision,
                    "last_sync_status": replacement.status,
                    "last_sync_batch_id": batch.batch_id,
                    "last_sync_at": utc_now_iso(),
                    "last_source_snapshot": {
                        "supplier_cost": source_snapshot.supplier_cost,
                        "shipping_cost": source_snapshot.shipping_cost,
                        "inventory": source_snapshot.inventory,
                        "status": source_snapshot.status,
                        "source_updated_at": source_snapshot.source_updated_at,
                    },
                    "idempotency_key": "::".join(
                        [
                            store_name,
                            replacement.giga_sku,
                            replacement.shopify_variant_id,
                            f"{replacement.target_price:.2f}",
                            source_snapshot.source_updated_at,
                        ]
                    ),
                },
            )

        for index, item in enumerate(batch.items, start=1):
            key = (item.giga_sku, item.shopify_variant_id)
            if key not in emitted_keys:
                emit_progress(item, index)
    else:
        batch.success_count = 0
        batch.failed_count = 0

    batch.status = "failed" if batch.failed_count and not batch.success_count else "completed"
    batch.finished_at = utc_now_iso()
    sync_repo.save_batch(batch)
    _write_report(batch)
    emit_stage(
        "finished",
        status=batch.status,
        processed_count=batch.processed_count,
        success_count=batch.success_count,
        failed_count=batch.failed_count,
        skipped_count=batch.skipped_count,
        manual_review_count=batch.manual_review_count,
    )
    return batch


def execute_task(request: ExecuteRequest) -> dict:
    settings = get_settings()
    shopify_auth = ShopifyAuthClient.from_settings(settings).describe_admin_session()
    payload = dict(request.payload or {})
    if request.task == "sync_single_sku" and payload.get("giga_sku"):
        payload["sync_scope"] = "single_sku"
        payload["sku_list"] = [payload["giga_sku"]]
    command = PriceSyncRequest(
        store_name=payload.get("store_name", payload.get("store", "")),
        sync_scope=payload.get("sync_scope", "incremental"),
        sku_list=payload.get("sku_list", []),
        force_recalculate=payload.get("force_recalculate", False),
        skip_incremental_cache=payload.get("skip_incremental_cache", False),
        giga_snapshots=[GigaPriceSnapshot.model_validate(item) for item in payload.get("giga_snapshots", [])],
        mappings=payload.get("mappings", []),
        shopify_states=[ShopifyPriceState.model_validate(item) for item in payload.get("shopify_states", [])],
        mode="apply" if request.task == "apply_price_sync" else "dry-run",
    )
    batch = run_price_sync(command)
    return {
        "summary": f"{request.task} processed {batch.processed_count} sku items for {batch.store_name}.",
        "data": {
            "store": batch.store_name,
            "environment": settings.hermes_env,
            "shopify_api_version": settings.shopify_api_version,
            "has_shopify_credentials": bool(
                settings.shopify_token
                or settings.shopify_admin_access_token
                or (settings.shopify_client_id and settings.shopify_client_secret)
            ),
            "shopify_auth": shopify_auth,
            "batch": batch.model_dump(mode="json"),
        },
    }
