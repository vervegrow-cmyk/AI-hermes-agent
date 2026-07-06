from __future__ import annotations

from models.inventory_sync import InventorySyncRequest
from service.inventory_sync_service import InventorySyncStartupError, run_inventory_sync
from shared.schemas import ExecuteRequest


def execute_task(request: ExecuteRequest) -> dict:
    payload = dict(request.payload or {})
    command = InventorySyncRequest.model_validate(
        {
            "store_name": payload.get("store_name") or payload.get("store") or "",
            "mode": payload.get("mode", "dry-run"),
            "shopify_query": payload.get("shopify_query", ""),
            "sku_list": payload.get("sku_list", []),
            "max_items": payload.get("max_items", 0),
            "location_id": payload.get("location_id", ""),
            "giga_probe_skus": payload.get("giga_probe_skus", []),
        }
    )
    try:
        batch = run_inventory_sync(command)
        return {
            "summary": (
                f"库存同步完成，共处理 {batch.processed_count} 条，"
                f"更新 {batch.updated_count} 条，跳过 {batch.skipped_count} 条，失败 {batch.failed_count} 条。"
            ),
            "data": batch.model_dump(mode='json'),
        }
    except InventorySyncStartupError as exc:
        return {
            "summary": f"库存同步启动失败: {exc}",
            "data": {"status": "failed", "error": str(exc)},
        }
