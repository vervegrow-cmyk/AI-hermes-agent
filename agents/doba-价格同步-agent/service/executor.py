from __future__ import annotations

import json
from pathlib import Path
from typing import Callable
from uuid import uuid4

from models.price_sync import DobaPriceSnapshot, PriceSyncBatch, PriceSyncItem, PriceSyncRequest, ShopifyPriceState, SkuMappingRecord, utc_now_iso
from service.doba_client import DobaPriceSyncClient
from service.mapping_repository import MappingRepository
from service.mapping_validator import MappingValidator
from service.plan_builder import build_plan
from service.progress_logger import ProgressLogger
from service.shopify_price_sync_service import ShopifyPriceSyncService
from service.sync_repository import SyncRepository
from service.terminal_reporter import build_batch_lines, emit_lines
from shared.clients import ShopifyAuthClient
from shared.config import get_settings
from shared.schemas import ExecuteRequest


REASON_TEXT_ZH = {
    "price_changed": "价格发生变化，需要更新",
    "shopify_price_already_correct": "Shopify 当前价格已经等于目标价，无需更新",
    "source_unchanged": "Doba 源数据没有变化，当前 SKU 跳过",
    "target_price_unchanged": "目标售价没有变化，当前 SKU 跳过",
    "missing_mapping": "当前 SKU 缺少有效映射",
    "duplicate_source_mapping": "同一个 Doba SKU 命中多个 Shopify Variant，需要人工处理",
    "duplicate_target_mapping": "多个 Doba SKU 命中同一个 Shopify Variant，需要人工处理",
    "variant_not_found": "Shopify Variant 不存在或无法读取",
    "shopify_admin_token_missing": "缺少 Shopify 写入凭证，无法执行 apply",
    "shopify_write_failed": "Shopify 写入失败，已跳过当前 SKU 并继续处理下一个",
    "success": "Shopify Variant 价格更新成功",
    "mapping_file_missing": "请先执行 /variant-mapping/build 生成可用映射",
    "interrupted_by_user": "用户中断任务，已保存当前处理进度",
    "runtime_exception": "运行时异常，已保存当前处理进度",
}


def _resolve_store_name(request: PriceSyncRequest) -> str:
    settings = get_settings()
    return request.store_name or settings.shopify_shop or settings.shopify_store or settings.shopify_shop_domain or "unconfigured-store"


def _build_state_key(store_name: str, doba_sku: str, variant_id: str) -> str:
    return f"{store_name}::{doba_sku}::{variant_id}"


def _refresh_batch_counts(batch: PriceSyncBatch) -> None:
    batch.processed_count = len(batch.items)
    batch.success_count = sum(1 for item in batch.items if item.status == "synced")
    batch.failed_count = sum(1 for item in batch.items if item.status == "failed")
    batch.skipped_count = sum(1 for item in batch.items if item.status == "skipped")
    batch.manual_review_count = sum(1 for item in batch.items if item.status == "manual_review")


def _report_root(sync_repo: SyncRepository) -> Path:
    return sync_repo.root / "reports"


def _build_report_payload(
    *,
    batch: PriceSyncBatch,
    mapping_summary: dict,
    doba_summary: dict,
    shopify_summary: dict,
    write_results: list[dict],
    errors: list[str],
    interrupted: bool = False,
    checkpoint_path: str = "",
) -> dict:
    return {
        "batch_id": batch.batch_id,
        "mode": batch.mode.replace("-", "_"),
        "store_name": batch.store_name,
        "started_at": batch.started_at,
        "completed_at": batch.finished_at,
        "interrupted": interrupted,
        "checkpoint_path": checkpoint_path,
        "summary": {
            "processed_count": batch.processed_count,
            "success_count": batch.success_count,
            "failed_count": batch.failed_count,
            "skipped_count": batch.skipped_count,
            "manual_review_count": batch.manual_review_count,
            "mapping": mapping_summary,
            "doba": doba_summary,
            "shopify": shopify_summary,
        },
        "items": [
            {
                "index": index,
                "total": len(batch.items),
                "doba_sku": item.doba_sku,
                "shopify_variant_id": item.shopify_variant_id,
                "supplier_cost": item.supplier_cost,
                "shipping_cost": item.shipping_cost,
                "current_shopify_price": item.old_price,
                "target_shopify_price": item.target_price,
                "price_delta": item.delta,
                "decision": item.status if item.status in {"synced", "failed", "skipped"} else item.decision,
                "reason_code": item.reason_codes[0] if item.reason_codes else "",
                "reason_text_zh": REASON_TEXT_ZH.get(item.reason_codes[0] if item.reason_codes else "", ""),
                "will_update_shopify": item.will_update_shopify,
                "write_status": _write_status(item, batch.mode),
                "processed_at": batch.finished_at or utc_now_iso(),
                "old_price": item.old_price,
                "new_price": item.target_price if item.status == "synced" else None,
                "error_message": item.error_message,
            }
            for index, item in enumerate(batch.items, start=1)
        ],
        "errors": errors,
        "shopify_write_results": write_results,
    }


def _write_status(item: PriceSyncItem, mode: str) -> str:
    if mode == "dry-run":
        return "not_written_dry_run"
    if item.status == "synced":
        return "success"
    if item.status == "failed":
        return "failed"
    return "skipped"


def _write_report(report_payload: dict, batch: PriceSyncBatch, root: Path) -> str:
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / f"price_sync_{batch.batch_id}.json"
    json_path.write_text(json.dumps(report_payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return str(json_path.resolve())


def _filter_active_mappings(command: PriceSyncRequest, mappings: list[SkuMappingRecord]) -> list[SkuMappingRecord]:
    active = [item for item in mappings if item.mapping_status == "active"]
    if command.sku_list:
        requested = set(command.sku_list)
        active = [item for item in active if item.doba_sku in requested]
    if command.start_index > 0 or command.end_index > 0:
        start = max(command.start_index - 1, 0)
        end = command.end_index if command.end_index > 0 else len(active)
        active = active[start:end]
    if command.limit > 0:
        active = active[: command.limit]
    return active


def _build_duplicate_maps(mappings: list[SkuMappingRecord]) -> tuple[dict[str, int], dict[str, int]]:
    source_counts: dict[str, int] = {}
    target_counts: dict[str, int] = {}
    for item in mappings:
        source_counts[item.doba_sku] = source_counts.get(item.doba_sku, 0) + 1
        if item.shopify_variant_id:
            target_counts[item.shopify_variant_id] = target_counts.get(item.shopify_variant_id, 0) + 1
    return source_counts, target_counts


def _updated_since(sync_repo: SyncRepository, store_name: str, command: PriceSyncRequest) -> str:
    if command.sync_scope == "full" or command.skip_incremental_cache:
        return ""
    value = ""
    for state in sync_repo.list_states().values():
        if state.get("store_name") == store_name and state.get("last_sync_status") == "synced":
            value = max(value, state.get("last_source_updated_at", ""))
    return value


def _append_result(
    *,
    batch: PriceSyncBatch,
    item: PriceSyncItem,
    report_root: Path,
    sync_repo: SyncRepository,
    mapping_summary: dict,
    doba_summary: dict,
    shopify_summary: dict,
    write_results: list[dict],
    errors: list[str],
    interrupted: bool,
    checkpoint_path: str,
) -> None:
    batch.items.append(item)
    _refresh_batch_counts(batch)
    payload = _build_report_payload(
        batch=batch,
        mapping_summary=mapping_summary,
        doba_summary=doba_summary,
        shopify_summary=shopify_summary,
        write_results=write_results,
        errors=errors,
        interrupted=interrupted,
        checkpoint_path=checkpoint_path,
    )
    batch.report_path = _write_report(payload, batch, report_root)
    sync_repo.save_batch(batch)


def _resolve_reason(item: PriceSyncItem) -> str:
    return item.reason_codes[0] if item.reason_codes else ""


def run_price_sync(
    command: PriceSyncRequest,
    *,
    doba_client: DobaPriceSyncClient | None = None,
    mapping_repository: MappingRepository | None = None,
    sync_repository: SyncRepository | None = None,
    shopify_service: ShopifyPriceSyncService | None = None,
    progress_callback: Callable[[dict], None] | None = None,
) -> PriceSyncBatch:
    settings = get_settings()
    store_name = _resolve_store_name(command)
    batch = PriceSyncBatch(batch_id=str(uuid4()), store_name=store_name, mode=command.mode)
    sync_repo = sync_repository or SyncRepository()
    sync_repo.ensure_runtime_layout()
    report_root = _report_root(sync_repo)
    logger = ProgressLogger(
        root=sync_repo.root,
        job_type="price_single" if command.sync_scope == "single_sku" else ("price_apply" if command.mode == "apply" else "price_dry_run"),
        batch_id=batch.batch_id,
        print_enabled=command.print_detail and settings.price_sync_print_detail,
    )
    mapping_repo = mapping_repository or MappingRepository()
    mapping_repo.ensure_layout()
    doba = doba_client or DobaPriceSyncClient()
    shopify = shopify_service or ShopifyPriceSyncService()
    write_results: list[dict] = []
    errors: list[str] = []
    interrupted = False
    checkpoint_path = ""
    last_item: PriceSyncItem | None = None

    if progress_callback is not None:
        progress_callback({"event": "stage", "stage": "start", "batch_id": batch.batch_id, "store_name": store_name})

    all_mappings = mapping_repo.load_records(command.mappings or None)
    active_mappings = _filter_active_mappings(command, all_mappings)
    duplicate_source_counts, duplicate_target_counts = _build_duplicate_maps(active_mappings)
    validation_report = mapping_repo.build_validation_report(store_name=store_name, records=all_mappings)
    mapping_summary = {
        "sync_scope": command.sync_scope,
        "total": len(all_mappings),
        "active": len(active_mappings),
        "duplicate": validation_report.get("duplicate_source_count", 0) + validation_report.get("duplicate_target_count", 0),
        "missing": validation_report.get("missing_mapping_count", 0),
    }
    doba_summary = {"response_items": 0, "normalized_items": 0, "failed_items": 0}
    shopify_summary = {"variants_requested": 0, "variants_found": 0, "variants_missing": 0}

    try:
        logger.step_start(phase="load_active_mappings", message="加载 active 映射")
        sync_repo.save_state(f"{store_name}::mapping_validation", validation_report)
        logger.step_done(phase="load_active_mappings", message=f"active={len(active_mappings)}", current_step=1, total_steps=4)

        if not active_mappings:
            errors.append("mapping_file_missing")
            batch.status = "failed"
            batch.finished_at = utc_now_iso()
            batch.report_path = _write_report(
                _build_report_payload(
                    batch=batch,
                    mapping_summary=mapping_summary,
                    doba_summary=doba_summary,
                    shopify_summary=shopify_summary,
                    write_results=write_results,
                    errors=errors,
                    interrupted=interrupted,
                    checkpoint_path=checkpoint_path,
                ),
                batch,
                report_root,
            )
            sync_repo.save_batch(batch)
            logger.line(label="提示", text="当前没有 active mappings，请先执行 /variant-mapping/build", phase="load_active_mappings", reason_code="mapping_file_missing")
            return batch

        if command.mode == "apply":
            logger.step_start(phase="validate_mappings", message="校验 active 映射")
            validation = MappingValidator().validate(
                store_name=store_name,
                records=[item for item in mapping_repo.load_variant_records() if item.store_name == store_name],
            )
            logger.step_done(phase="validate_mappings", message=f"result={validation.get('result', 'fail')}", current_step=1, total_steps=5)
            if validation.get("result") != "pass":
                errors.append("manual_review_required")
                batch.status = "failed"
                batch.finished_at = utc_now_iso()
                batch.report_path = _write_report(
                    _build_report_payload(
                        batch=batch,
                        mapping_summary=mapping_summary,
                        doba_summary=doba_summary,
                        shopify_summary=shopify_summary,
                        write_results=write_results,
                        errors=errors,
                        interrupted=interrupted,
                        checkpoint_path=checkpoint_path,
                    ),
                    batch,
                    report_root,
                )
                sync_repo.save_batch(batch)
                return batch
            shopify.ensure_write_ready()

        updated_since = _updated_since(sync_repo, store_name, command)
        total_items = len(active_mappings)
        for index, mapping in enumerate(active_mappings, start=1):
            logger.line(
                label="条目开始",
                text=f'序号={index}/{total_items} doba_sku={mapping.doba_sku} shopify_variant_id={mapping.shopify_variant_id} 说明="开始处理当前 SKU"',
                phase="process_item",
                doba_sku=mapping.doba_sku,
                shopify_variant_id=mapping.shopify_variant_id,
                current_item=index,
                total_items=total_items,
            )
            logger.line(label="读取Doba", text=f'doba_sku={mapping.doba_sku} 说明="正在读取 Doba 最新价格"', phase="process_item", doba_sku=mapping.doba_sku, current_item=index, total_items=total_items)
            if duplicate_source_counts.get(mapping.doba_sku, 0) > 1 or duplicate_target_counts.get(mapping.shopify_variant_id, 0) > 1:
                reason_code = "duplicate_source_mapping" if duplicate_source_counts.get(mapping.doba_sku, 0) > 1 else "duplicate_target_mapping"
                item = PriceSyncItem(
                    store_name=store_name,
                    doba_product_id=mapping.doba_product_id,
                    doba_sku=mapping.doba_sku,
                    shopify_product_id=mapping.shopify_product_id,
                    shopify_variant_id=mapping.shopify_variant_id,
                    shopify_sku=mapping.shopify_sku,
                    decision="manual_review",
                    status="manual_review",
                    reason_codes=[reason_code],
                    will_update_shopify=False,
                )
                _append_result(batch=batch, item=item, report_root=report_root, sync_repo=sync_repo, mapping_summary=mapping_summary, doba_summary=doba_summary, shopify_summary=shopify_summary, write_results=write_results, errors=errors, interrupted=interrupted, checkpoint_path=checkpoint_path)
                last_item = item
                logger.line(
                    label="跳过",
                    text=f'doba_sku={item.doba_sku} reason_code={reason_code} 说明="{REASON_TEXT_ZH.get(reason_code, "重复映射，已转人工处理")}"',
                    phase="process_item",
                    doba_sku=item.doba_sku,
                    shopify_variant_id=item.shopify_variant_id,
                    reason_code=reason_code,
                    status="manual_review",
                    current_item=index,
                    total_items=total_items,
                )
                continue
            snapshot_list = doba.list_price_snapshots(
                store_name=store_name,
                sync_scope="single_sku",
                updated_since=updated_since,
                skus=[mapping.doba_sku],
                snapshots_override=[item for item in command.doba_snapshots if item.doba_sku == mapping.doba_sku] or None,
            )
            doba_summary["response_items"] += 1
            if not snapshot_list:
                item = PriceSyncItem(
                    store_name=store_name,
                    doba_product_id=mapping.doba_product_id,
                    doba_sku=mapping.doba_sku,
                    shopify_product_id=mapping.shopify_product_id,
                    shopify_variant_id=mapping.shopify_variant_id,
                    shopify_sku=mapping.shopify_sku,
                    decision="skip",
                    status="skipped",
                    reason_codes=["doba_empty_response"],
                    will_update_shopify=False,
                )
                _append_result(batch=batch, item=item, report_root=report_root, sync_repo=sync_repo, mapping_summary=mapping_summary, doba_summary=doba_summary, shopify_summary=shopify_summary, write_results=write_results, errors=errors, interrupted=interrupted, checkpoint_path=checkpoint_path)
                last_item = item
                logger.line(label="跳过", text=f'doba_sku={mapping.doba_sku} reason_code=doba_empty_response 说明="Doba 未返回该 SKU 最新价格，已跳过"', phase="process_item", doba_sku=mapping.doba_sku, reason_code="doba_empty_response", status="skipped", current_item=index, total_items=total_items)
                continue
            snapshot = snapshot_list[0]
            doba_summary["normalized_items"] += 1

            logger.line(label="读取Shopify", text=f'shopify_variant_id={mapping.shopify_variant_id} 说明="正在读取 Shopify 当前价格"', phase="process_item", doba_sku=mapping.doba_sku, shopify_variant_id=mapping.shopify_variant_id, current_item=index, total_items=total_items)
            state_list = shopify.get_price_states(
                store_name=store_name,
                snapshots=[snapshot],
                mappings=[mapping],
                states_override=[item for item in command.shopify_states if item.shopify_variant_id == mapping.shopify_variant_id] or None,
            )
            shopify_summary["variants_requested"] += 1
            if state_list:
                shopify_summary["variants_found"] += 1
            else:
                shopify_summary["variants_missing"] += 1

            plan_items = build_plan(
                store_name=store_name,
                snapshots=[snapshot],
                mappings=[mapping],
                shopify_states=state_list,
                sync_scope=command.sync_scope,
                force_recalculate=command.force_recalculate or command.skip_incremental_cache,
                mapping_repository=mapping_repo,
                sync_repository=sync_repo,
            )
            item = plan_items[0]
            item.will_update_shopify = False if command.mode == "dry-run" else item.will_update_shopify
            logger.line(
                label="计算价格",
                text=f'doba_sku={item.doba_sku} supplier_cost={item.supplier_cost:.2f} shipping_cost={item.shipping_cost:.2f} target_price={item.target_price:.2f} 说明="目标售价计算完成"',
                phase="process_item",
                doba_sku=item.doba_sku,
                shopify_variant_id=item.shopify_variant_id,
                current_item=index,
                total_items=total_items,
            )

            if command.mode == "dry-run":
                logger.line(
                    label="判断结果",
                    text=f'doba_sku={item.doba_sku} old_price={item.old_price:.2f} target_price={item.target_price:.2f} decision={item.status if item.status != "planned" else "planned"} reason_code={_resolve_reason(item)} 说明="dry-run 已记录，不会写 Shopify"',
                    phase="process_item",
                    doba_sku=item.doba_sku,
                    shopify_variant_id=item.shopify_variant_id,
                    reason_code=_resolve_reason(item),
                    status=item.status,
                    current_item=index,
                    total_items=total_items,
                )
                _append_result(batch=batch, item=item, report_root=report_root, sync_repo=sync_repo, mapping_summary=mapping_summary, doba_summary=doba_summary, shopify_summary=shopify_summary, write_results=write_results, errors=errors, interrupted=interrupted, checkpoint_path=checkpoint_path)
                last_item = item
                logger.line(label="条目完成", text=f'doba_sku={item.doba_sku} 说明="当前 SKU 处理完成，继续下一个"', phase="process_item", doba_sku=item.doba_sku, current_item=index, total_items=total_items)
                continue

            if item.status != "planned":
                _append_result(batch=batch, item=item, report_root=report_root, sync_repo=sync_repo, mapping_summary=mapping_summary, doba_summary=doba_summary, shopify_summary=shopify_summary, write_results=write_results, errors=errors, interrupted=interrupted, checkpoint_path=checkpoint_path)
                last_item = item
                logger.line(
                    label="跳过",
                    text=f'doba_sku={item.doba_sku} reason_code={_resolve_reason(item)} 说明="{REASON_TEXT_ZH.get(_resolve_reason(item), "当前 SKU 无需更新")}"',
                    phase="process_item",
                    doba_sku=item.doba_sku,
                    shopify_variant_id=item.shopify_variant_id,
                    reason_code=_resolve_reason(item),
                    status=item.status,
                    current_item=index,
                    total_items=total_items,
                )
                continue

            logger.line(
                label="写入计划",
                text=f'doba_sku={item.doba_sku} old_price={item.old_price:.2f} target_price={item.target_price:.2f} 说明="当前 SKU 需要更新，准备写入 Shopify"',
                phase="process_item",
                doba_sku=item.doba_sku,
                shopify_variant_id=item.shopify_variant_id,
                reason_code="price_changed",
                current_item=index,
                total_items=total_items,
            )
            updated = shopify.apply_price_updates([item])[0]
            if updated.status == "synced":
                updated.reason_codes = ["success"]
                write_results.append(
                    {
                        "doba_sku": updated.doba_sku,
                        "shopify_variant_id": updated.shopify_variant_id,
                        "old_price": updated.old_price,
                        "new_price": updated.target_price,
                        "status": "synced",
                        "error_type": "",
                        "error_message": "",
                    }
                )
                logger.line(
                    label="写入成功",
                    text=f'doba_sku={updated.doba_sku} shopify_variant_id={updated.shopify_variant_id} old_price={updated.old_price:.2f} new_price={updated.target_price:.2f} 说明="Shopify Variant 价格已更新"',
                    phase="process_item",
                    doba_sku=updated.doba_sku,
                    shopify_variant_id=updated.shopify_variant_id,
                    reason_code="success",
                    status="synced",
                    current_item=index,
                    total_items=total_items,
                )
            else:
                if "shopify_write_failed" not in updated.reason_codes:
                    updated.reason_codes = [*updated.reason_codes, "shopify_write_failed"]
                write_results.append(
                    {
                        "doba_sku": updated.doba_sku,
                        "shopify_variant_id": updated.shopify_variant_id,
                        "old_price": updated.old_price,
                        "new_price": updated.target_price,
                        "status": "failed",
                        "error_type": "shopify_write_failed",
                        "error_message": updated.error_message,
                    }
                )
                errors.append(updated.error_message or "shopify_write_failed")
                logger.line(
                    label="写入失败",
                    text=f'doba_sku={updated.doba_sku} shopify_variant_id={updated.shopify_variant_id} reason_code=shopify_write_failed 错误="{updated.error_message or "Shopify 写入失败，已记录失败并继续处理下一个 SKU"}"',
                    phase="process_item",
                    doba_sku=updated.doba_sku,
                    shopify_variant_id=updated.shopify_variant_id,
                    reason_code="shopify_write_failed",
                    status="failed",
                    current_item=index,
                    total_items=total_items,
                )

            _append_result(batch=batch, item=updated, report_root=report_root, sync_repo=sync_repo, mapping_summary=mapping_summary, doba_summary=doba_summary, shopify_summary=shopify_summary, write_results=write_results, errors=errors, interrupted=interrupted, checkpoint_path=checkpoint_path)
            last_item = updated
            if updated.status == "synced":
                sync_repo.save_state(
                    _build_state_key(store_name, updated.doba_sku, updated.shopify_variant_id),
                    {
                        "store_name": store_name,
                        "doba_sku": updated.doba_sku,
                        "shopify_variant_id": updated.shopify_variant_id,
                        "last_source_hash": snapshot.raw_hash,
                        "last_source_updated_at": snapshot.source_updated_at,
                        "last_target_price": updated.target_price,
                        "last_shopify_price": updated.target_price,
                        "last_sync_status": updated.status,
                        "last_sync_batch_id": batch.batch_id,
                        "last_sync_at": utc_now_iso(),
                    },
                )
            logger.line(label="条目完成", text=f'doba_sku={updated.doba_sku} 说明="当前 SKU 处理完成，继续下一个"', phase="process_item", doba_sku=updated.doba_sku, shopify_variant_id=updated.shopify_variant_id, current_item=index, total_items=total_items)

    except KeyboardInterrupt:
        interrupted = True
        checkpoint_path = logger.save_checkpoint(
            phase="process_item",
            index=batch.processed_count,
            total_items=max(len(active_mappings), batch.processed_count),
            last_doba_sku=last_item.doba_sku if last_item else "",
            last_shopify_variant_id=last_item.shopify_variant_id if last_item else "",
            last_output_files=[batch.report_path, str(logger.log_path.resolve())] if batch.report_path else [str(logger.log_path.resolve())],
            reason_code="interrupted_by_user",
            reason_text_zh=REASON_TEXT_ZH["interrupted_by_user"],
            last_decision=last_item.status if last_item else "",
            last_reason_code=_resolve_reason(last_item) if last_item else "",
            interrupted=True,
        )
        logger.interrupted(
            phase="process_item",
            index=batch.processed_count,
            total=max(len(active_mappings), batch.processed_count),
            reason_code="interrupted_by_user",
            last_doba_sku=last_item.doba_sku if last_item else "",
            last_shopify_variant_id=last_item.shopify_variant_id if last_item else "",
            checkpoint_path=checkpoint_path,
        )
        errors.append("interrupted_by_user")
        batch.status = "failed"
    except RuntimeError as exc:
        errors.append(str(exc))
        checkpoint_path = logger.save_checkpoint(
            phase="process_item",
            index=batch.processed_count,
            total_items=max(len(active_mappings), batch.processed_count),
            last_doba_sku=last_item.doba_sku if last_item else "",
            last_shopify_variant_id=last_item.shopify_variant_id if last_item else "",
            last_output_files=[batch.report_path, str(logger.log_path.resolve())] if batch.report_path else [str(logger.log_path.resolve())],
            reason_code="runtime_exception" if str(exc) != "shopify_admin_token_missing" else "shopify_admin_token_missing",
            reason_text_zh=REASON_TEXT_ZH.get(str(exc), REASON_TEXT_ZH["runtime_exception"]),
            last_decision=last_item.status if last_item else "",
            last_reason_code=_resolve_reason(last_item) if last_item else "",
            interrupted=False,
        )
        logger.error(
            phase="process_item",
            index=batch.processed_count,
            reason_code="runtime_exception" if str(exc) != "shopify_admin_token_missing" else "shopify_admin_token_missing",
            error_message=str(exc),
            doba_sku=last_item.doba_sku if last_item else "",
            shopify_variant_id=last_item.shopify_variant_id if last_item else "",
        )
        batch.status = "failed"
        batch.finished_at = utc_now_iso()
        batch.report_path = _write_report(
            _build_report_payload(
                batch=batch,
                mapping_summary=mapping_summary,
                doba_summary=doba_summary,
                shopify_summary=shopify_summary,
                write_results=write_results,
                errors=errors,
                interrupted=interrupted,
                checkpoint_path=checkpoint_path,
            ),
            batch,
            report_root,
        )
        sync_repo.save_batch(batch)
        raise

    batch.status = "failed" if batch.failed_count and not batch.success_count and command.mode == "apply" else "completed"
    batch.finished_at = utc_now_iso()
    batch.report_path = _write_report(
        _build_report_payload(
            batch=batch,
            mapping_summary=mapping_summary,
            doba_summary=doba_summary,
            shopify_summary=shopify_summary,
            write_results=write_results,
            errors=errors,
            interrupted=interrupted,
            checkpoint_path=checkpoint_path,
        ),
        batch,
        report_root,
    )
    sync_repo.save_batch(batch)
    if command.print_detail and settings.price_sync_print_detail:
        emit_lines(
            build_batch_lines(
                batch=batch,
                report_path=batch.report_path,
                mapping_summary=mapping_summary,
                doba_summary=doba_summary,
                shopify_summary=shopify_summary,
                write_results=write_results,
                single_mode=command.sync_scope == "single_sku",
            )
        )
    if progress_callback is not None:
        progress_callback({"event": "stage", "stage": "finished", "batch_id": batch.batch_id, "status": batch.status})
    return batch


def execute_task(request: ExecuteRequest) -> dict:
    settings = get_settings()
    payload = dict(request.payload or {})
    if request.task == "sync_single_sku" and payload.get("doba_sku"):
        payload["sync_scope"] = "single_sku"
        payload["sku_list"] = [payload["doba_sku"]]
    command = PriceSyncRequest(
        store_name=payload.get("store_name", payload.get("store", "")),
        sync_scope=payload.get("sync_scope", "incremental"),
        sku_list=payload.get("sku_list", []),
        limit=payload.get("limit", 0),
        start_index=payload.get("start_index", 0),
        end_index=payload.get("end_index", 0),
        dry_run_batch_id=payload.get("dry_run_batch_id", ""),
        force_recalculate=payload.get("force_recalculate", False),
        skip_incremental_cache=payload.get("skip_incremental_cache", False),
        doba_snapshots=[DobaPriceSnapshot.model_validate(item) for item in payload.get("doba_snapshots", [])],
        mappings=payload.get("mappings", []),
        shopify_states=[ShopifyPriceState.model_validate(item) for item in payload.get("shopify_states", [])],
        print_detail=payload.get("print_detail", True),
        print_table=payload.get("print_table", True),
        mode="apply" if request.task == "apply_price_sync" else "dry-run",
    )
    batch = run_price_sync(command)
    shopify_auth = ShopifyAuthClient.from_settings(settings).describe_admin_session()
    return {
        "summary": f"{request.task or 'price_sync'} processed {batch.processed_count} sku items for {batch.store_name}.",
        "data": {
            "store": batch.store_name,
            "environment": settings.hermes_env,
            "shopify_api_version": settings.shopify_api_version,
            "shopify_auth": shopify_auth,
            "doba_base_url": settings.doba_api_base_url,
            "batch": batch.model_dump(mode="json"),
        },
    }
