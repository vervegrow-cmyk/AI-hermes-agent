from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sys

AGENT_ROOT = Path(__file__).resolve().parents[1]
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from models.inventory_sync import InventorySyncRequest
from service.inventory_sync_service import run_inventory_sync


def _now_label() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _print_text(message: str) -> None:
    print(f"[{_now_label()}] {message}", flush=True)


def _render_stage_message(event: dict) -> str:
    stage = event.get("stage", "")
    if stage == "start":
        return f"[任务开始] 批次 {event.get('batch_id')}，店铺 {event.get('store_name')}，模式 {event.get('mode')}"
    if stage == "shopify_validated":
        return f"[连接检查] Shopify 验证成功，店铺 {event.get('store_name')}，Location {event.get('location_id')}"
    if stage == "giga_validated":
        return f"[连接检查] Giga 验证成功，地址 {event.get('base_url')}，接口 {event.get('endpoint')}"
    if stage == "shopify_scan_progress":
        if event.get("page"):
            return (
                f"[扫描进度] 第 {event.get('page')} 页，本页 {event.get('fetched_in_page', 0)} 条，"
                f"累计 {event.get('fetched_total', 0)} 条"
            )
        return (
            f"[扫描进度] 指定 SKU 扫描 {event.get('current', 0)}/{event.get('total', 0)}，"
            f"当前 SKU {event.get('sku', '')}"
        )
    if stage == "shopify_scan_finished":
        return f"[扫描完成] 共发现 {event.get('variant_count', 0)} 条待处理变体"
    if stage == "finished":
        return (
            f"[任务汇总] 总数 {event.get('processed_count', 0)}，更新 {event.get('updated_count', 0)}，"
            f"跳过 {event.get('skipped_count', 0)}，失败 {event.get('failed_count', 0)}"
        )
    return f"[阶段] {stage}"


def _render_item_message(event: dict) -> str:
    item = event["item"]
    extra = ""
    if item.get("action") == "delist_product":
        extra = f"，商品状态 {item.get('shopify_product_status_before') or '-'} -> {item.get('shopify_product_status_after') or '-'}"
    return (
        f"[处理进度] 第 {event.get('index', 0)}/{event.get('total', 0)} 条，SKU: {item.get('sku', '')}，"
        f"Vendor={item.get('shopify_product_vendor', '')}，Shopify={item.get('shopify_inventory_before')}，"
        f"Giga={item.get('giga_inventory')}，结果={item.get('status')}，动作={item.get('action')}{extra}，"
        f"原因={item.get('reason') or item.get('error_message') or '-'}"
    )


def _progress_printer(event: dict) -> None:
    if event.get("event") == "stage":
        _print_text(_render_stage_message(event))
        return
    _print_text(_render_item_message(event))


def main() -> None:
    parser = argparse.ArgumentParser(description="Sequential Shopify inventory sync by SKU.")
    parser.add_argument("--store-name", default="", help="Shopify 店铺域名。")
    parser.add_argument("--mode", choices=["dry-run", "apply"], default="dry-run")
    parser.add_argument("--shopify-query", default="", help="Shopify 变体筛选 query。")
    parser.add_argument("--sku", action="append", default=[], help="指定 SKU，可重复传入。")
    parser.add_argument("--max-items", type=int, default=0, help="本次最多处理多少条。")
    parser.add_argument("--location-id", default="", help="指定 Shopify location id。")
    args = parser.parse_args()

    command = InventorySyncRequest(
        store_name=args.store_name,
        mode=args.mode,
        shopify_query=args.shopify_query,
        sku_list=args.sku,
        max_items=args.max_items,
        location_id=args.location_id,
    )
    batch = run_inventory_sync(command, progress_callback=_progress_printer)
    if batch.artifact_paths:
        _print_text(f"[报告输出] 任务报告: {batch.artifact_paths.get('report', '')}")
        _print_text(f"[报告输出] 缺 SKU 清单: {batch.artifact_paths.get('missing_skus', '')}")
        _print_text(f"[报告输出] 重试清单: {batch.artifact_paths.get('retry_items', '')}")


if __name__ == "__main__":
    main()
