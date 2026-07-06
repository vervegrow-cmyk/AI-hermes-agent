from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


ItemStatus = Literal["updated", "skipped", "failed", "dry_run"]
BatchStatus = Literal["running", "completed", "failed"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class ConnectionCheckResult(BaseModel):
    ok: bool
    system: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class GigaInventoryRecord(BaseModel):
    sku: str
    available_inventory: int
    raw: dict[str, Any] = Field(default_factory=dict)


class InventorySyncItem(BaseModel):
    sku: str
    shopify_variant_id: str = ""
    shopify_product_id: str = ""
    shopify_product_title: str = ""
    shopify_product_vendor: str = ""
    shopify_product_status_before: str = ""
    shopify_product_status_after: str = ""
    shopify_inventory_item_id: str = ""
    shopify_inventory_before: int | None = None
    giga_inventory: int | None = None
    action: str = "skip"
    status: ItemStatus = "skipped"
    reason: str = ""
    error_message: str = ""


class InventorySyncBatch(BaseModel):
    batch_id: str
    store_name: str
    mode: Literal["dry-run", "apply"] = "dry-run"
    status: BatchStatus = "running"
    processed_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    started_at: str = Field(default_factory=utc_now_iso)
    finished_at: str = ""
    shopify_connection: ConnectionCheckResult | None = None
    giga_connection: ConnectionCheckResult | None = None
    location_id: str = ""
    missing_sku_count: int = 0
    artifact_paths: dict[str, str] = Field(default_factory=dict)
    items: list[InventorySyncItem] = Field(default_factory=list)


class InventorySyncRequest(BaseModel):
    store_name: str = ""
    mode: Literal["dry-run", "apply"] = "dry-run"
    shopify_query: str = ""
    sku_list: list[str] = Field(default_factory=list)
    max_items: int = 0
    location_id: str = ""
    giga_probe_skus: list[str] = Field(default_factory=list)
