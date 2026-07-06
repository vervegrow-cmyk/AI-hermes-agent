from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


DecisionType = Literal["keep_price", "increase_price", "decrease_price", "manual_review", "skip"]
ItemStatus = Literal["planned", "skipped", "manual_review", "synced", "failed"]
BatchStatus = Literal["running", "completed", "failed"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class GigaPriceSnapshot(BaseModel):
    store_name: str = ""
    giga_product_id: str = ""
    giga_sku: str
    supplier_cost: float = 0
    shipping_cost: float = 0
    currency: str = "USD"
    inventory: int = 0
    status: str = "active"
    source_updated_at: str = ""
    raw_hash: str = ""


class SkuMappingRecord(BaseModel):
    store_name: str = ""
    giga_sku: str
    shopify_product_id: str = ""
    shopify_variant_id: str = ""
    shopify_sku: str = ""
    mapping_status: str = "active"
    updated_at: str = ""


class ShopifyPriceState(BaseModel):
    store_name: str = ""
    shopify_product_id: str = ""
    shopify_variant_id: str = ""
    shopify_sku: str = ""
    current_price: float = 0
    updated_at: str = ""


class PriceCalculation(BaseModel):
    giga_sku: str
    supplier_cost: float = 0
    shipping_cost: float = 0
    platform_cost: float = 0
    warehouse_cost: float = 0
    true_cost: float = 0
    minimum_safe_price: float = 0
    target_price: float = 0


class PriceSyncItem(BaseModel):
    store_name: str = ""
    giga_sku: str
    shopify_product_id: str = ""
    shopify_variant_id: str = ""
    old_price: float = 0
    supplier_cost: float = 0
    target_price: float = 0
    delta: float = 0
    decision: DecisionType = "skip"
    reason_codes: list[str] = Field(default_factory=list)
    status: ItemStatus = "planned"
    error_message: str = ""


class PriceSyncBatch(BaseModel):
    batch_id: str
    store_name: str
    mode: str = "dry-run"
    status: BatchStatus = "running"
    processed_count: int = 0
    success_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    manual_review_count: int = 0
    started_at: str = Field(default_factory=utc_now_iso)
    finished_at: str = ""
    items: list[PriceSyncItem] = Field(default_factory=list)


class PriceSyncRequest(BaseModel):
    store_name: str = ""
    sync_scope: Literal["full", "incremental", "single_sku"] = "incremental"
    sku_list: list[str] = Field(default_factory=list)
    force_recalculate: bool = False
    skip_incremental_cache: bool = False
    giga_snapshots: list[GigaPriceSnapshot] = Field(default_factory=list)
    mappings: list[SkuMappingRecord] = Field(default_factory=list)
    shopify_states: list[ShopifyPriceState] = Field(default_factory=list)
    mode: Literal["dry-run", "apply"] = "dry-run"
