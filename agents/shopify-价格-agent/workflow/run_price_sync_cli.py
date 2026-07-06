from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

AGENT_ROOT = Path(__file__).resolve().parents[1]
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from models.price_sync import PriceSyncRequest
from service.executor import run_price_sync


def _now_label() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _fmt_money(value: float | int) -> str:
    return f"{float(value):.2f}"


def _print_text(message: str) -> None:
    print(f"[{_now_label()}] {message}", flush=True)


def _render_stage_message(event: dict) -> str:
    stage = event.get("stage", "")
    if stage == "cli_started":
        return f"开始执行价格同步，店铺={event.get('store_name')}, 模式={event.get('mode')}, 范围={event.get('sync_scope')}, 指定SKU数={event.get('requested_sku_count', 0)}"
    if stage == "start":
        return f"任务已启动，批次={event.get('batch_id')}，现有映射={event.get('existing_mapping_count', 0)}"
    if stage == "discover_shopify_mappings_started":
        return f"开始扫描 Shopify 全店商品映射，当前映射={event.get('current_mapping_count', 0)}"
    if stage == "discover_shopify_mappings_progress":
        return f"正在扫描 Shopify 第 {event.get('page', 0)} 页，本页 {event.get('fetched_in_page', 0)} 个，累计 {event.get('fetched_total', 0)} 个 SKU"
    if stage == "discover_shopify_mappings_finished":
        return f"Shopify 扫描完成，发现 {event.get('discovered_mapping_count', 0)} 条可用映射"
    if stage == "candidate_skus_ready":
        return f"候选 SKU 已整理完成，共 {event.get('candidate_sku_count', 0)} 条"
    if stage == "giga_snapshots_progress":
        return (
            f"正在请求 Giga 第 {event.get('chunk_index', 0)}/{event.get('chunk_count', 0)} 批，"
            f"本批请求 {event.get('requested_sku_count', 0)} 条，累计返回 {event.get('received_total', 0)} 条"
        )
    if stage == "giga_chunk_split_retry":
        return (
            f"Giga 第 {event.get('chunk_index', 0)}/{event.get('chunk_count', 0)} 批请求异常，"
            f"正在拆分重试：{event.get('requested_sku_count', 0)} -> "
            f"{event.get('left_size', 0)} + {event.get('right_size', 0)}"
        )
    if stage == "giga_chunk_failed":
        failed_skus = event.get("failed_skus", [])
        failed_preview = ",".join(failed_skus[:3])
        if len(failed_skus) > 3:
            failed_preview += "..."
        return f"Giga 读取失败，已跳过 {len(failed_skus)} 个 SKU：{failed_preview}"
    if stage == "giga_snapshots_fetched":
        return f"Giga 价格读取完成，共获得 {event.get('snapshot_count', 0)} 条价格快照"
    if stage == "single_sku_filtered":
        return f"单 SKU 过滤完成，保留 {event.get('snapshot_count', 0)} 条"
    if stage == "shopify_states_progress":
        state = event.get("status")
        if state == "loaded":
            return (
                f"正在读取 Shopify 当前价格：{event.get('index', 0)}/{event.get('total', 0)}，"
                f"SKU {event.get('giga_sku')} 读取成功，累计 {event.get('loaded_count', 0)} 条"
            )
        if state == "variant_not_found":
            return (
                f"正在读取 Shopify 当前价格：{event.get('index', 0)}/{event.get('total', 0)}，"
                f"SKU {event.get('giga_sku')} 未找到 variant"
            )
        if state == "missing_mapping":
            return (
                f"正在读取 Shopify 当前价格：{event.get('index', 0)}/{event.get('total', 0)}，"
                f"SKU {event.get('giga_sku')} 缺少映射"
            )
    if stage == "shopify_states_loaded":
        return f"Shopify 当前价格读取完成，共 {event.get('state_count', 0)} 条"
    if stage == "plan_built":
        return (
            f"同步计划已生成：processed={event.get('processed_count', 0)}，"
            f"planned={event.get('planned_count', 0)}，skipped={event.get('skipped_count', 0)}，"
            f"manual_review={event.get('manual_review_count', 0)}"
        )
    if stage == "apply_queue_ready":
        return f"准备开始真实更新，待执行 {event.get('eligible_count', 0)} 条，共 {event.get('total_items', 0)} 条计划"
    if stage == "finished":
        return (
            f"任务完成：status={event.get('status')}，processed={event.get('processed_count', 0)}，"
            f"success={event.get('success_count', 0)}，failed={event.get('failed_count', 0)}，"
            f"skipped={event.get('skipped_count', 0)}，manual_review={event.get('manual_review_count', 0)}"
        )
    return f"阶段进度：{stage}"


def _render_item_message(event: dict) -> str:
    item = event["item"]
    sku = item["giga_sku"]
    old_price = _fmt_money(item["old_price"])
    target_price = _fmt_money(item["target_price"])
    status = item["status"]
    decision = item["decision"]
    reason_text = "，".join(item.get("reason_codes", [])) if item.get("reason_codes") else "无"
    prefix = f"{event.get('index', 0)}/{event.get('total', 0)} SKU {sku}"

    if status == "synced":
        return f"{prefix} 更新成功：{old_price} -> {target_price}"
    if status == "skipped" and decision == "keep_price":
        return f"{prefix} 价格无变化，跳过：{old_price} -> {target_price}"
    if status == "skipped":
        return f"{prefix} 跳过：{old_price} -> {target_price}，原因={reason_text}"
    if status == "manual_review":
        return f"{prefix} 需人工处理：{old_price} -> {target_price}，原因={reason_text}"
    if status == "failed":
        return f"{prefix} 更新失败：{old_price} -> {target_price}，错误={item.get('error_message') or reason_text}"
    return f"{prefix} 状态={status}：{old_price} -> {target_price}"


def _progress_printer(event: dict) -> None:
    event_type = event.get("event", "item")
    if event_type == "stage":
        _print_text(_render_stage_message(event))
        return

    _print_text(_render_item_message(event))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Shopify price sync sequentially and print one terminal result per SKU."
    )
    parser.add_argument("--store-name", default="", help="Shopify store domain.")
    parser.add_argument("--mode", choices=["dry-run", "apply"], default="apply")
    parser.add_argument("--sync-scope", choices=["full", "incremental", "single_sku"], default="full")
    parser.add_argument("--sku", action="append", default=[], help="Specific SKU to sync. Can be repeated.")
    parser.add_argument("--force-recalculate", action="store_true")
    parser.add_argument("--skip-incremental-cache", action="store_true")
    args = parser.parse_args()

    command = PriceSyncRequest(
        store_name=args.store_name,
        mode=args.mode,
        sync_scope=args.sync_scope,
        sku_list=args.sku,
        force_recalculate=args.force_recalculate,
        skip_incremental_cache=args.skip_incremental_cache,
    )
    _progress_printer(
        {
            "event": "stage",
            "stage": "cli_started",
            "store_name": command.store_name,
            "mode": command.mode,
            "sync_scope": command.sync_scope,
            "requested_sku_count": len(command.sku_list),
        }
    )
    batch = run_price_sync(command, progress_callback=_progress_printer)
    _print_text(
        "批次汇总："
        f" batch_id={batch.batch_id}，status={batch.status}，processed={batch.processed_count}，"
        f"success={batch.success_count}，failed={batch.failed_count}，"
        f"skipped={batch.skipped_count}，manual_review={batch.manual_review_count}"
    )


if __name__ == "__main__":
    main()
