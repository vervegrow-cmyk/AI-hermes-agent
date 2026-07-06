from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


DecisionType = Literal["keep_price", "increase_price", "decrease_price", "manual_review", "skip"]
ItemStatus = Literal["planned", "skipped", "manual_review", "synced", "failed"]
BatchStatus = Literal["running", "completed", "failed"]
SyncScope = Literal["full", "incremental", "single_sku"]
RoundingMode = Literal["ending_99", "ending_95", "nearest_dollar", "no_rounding"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class DobaPriceSnapshot(BaseModel):
    store_name: str = ""
    doba_product_id: str = ""
    doba_sku: str
    supplier_cost: float | None = None
    shipping_cost: float | None = None
    handling_fee: float = 0.0
    warehouse_fee: float = 0.0
    estimated_total_cost: float = 0.0
    currency: str = "USD"
    inventory: int = 0
    status: str = "active"
    source_updated_at: str = ""
    raw_payload: dict = Field(default_factory=dict)
    raw_hash: str = ""


class SkuMappingRecord(BaseModel):
    store_name: str = ""
    supplier: str = "doba"
    doba_product_id: str = ""
    doba_sku: str
    shopify_product_id: str = ""
    shopify_variant_id: str = ""
    shopify_sku: str = ""
    mapping_status: str = "active"
    last_price_hash: str = ""
    last_doba_updated_at: str = ""
    last_shopify_synced_at: str = ""
    updated_at: str = ""


class ShopifyPriceState(BaseModel):
    store_name: str = ""
    shopify_product_id: str = ""
    shopify_variant_id: str = ""
    shopify_sku: str = ""
    current_price: float = 0.0
    updated_at: str = ""


class PriceCalculation(BaseModel):
    doba_sku: str
    supplier_cost: float = 0.0
    shipping_cost: float = 0.0
    handling_fee: float = 0.0
    warehouse_fee: float = 0.0
    estimated_total_cost: float = 0.0
    minimum_safe_price: float = 0.0
    target_price: float = 0.0
    rounding_mode: RoundingMode = "ending_99"


class PriceSyncItem(BaseModel):
    store_name: str = ""
    doba_product_id: str = ""
    doba_sku: str
    shopify_product_id: str = ""
    shopify_variant_id: str = ""
    shopify_sku: str = ""
    old_price: float = 0.0
    supplier_cost: float = 0.0
    shipping_cost: float = 0.0
    estimated_total_cost: float = 0.0
    target_price: float = 0.0
    delta: float = 0.0
    will_update_shopify: bool = False
    source_changed: bool = False
    target_price_changed: bool = False
    shopify_price_changed: bool = False
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
    report_path: str = ""
    items: list[PriceSyncItem] = Field(default_factory=list)


class PriceSyncRequest(BaseModel):
    store_name: str = ""
    sync_scope: SyncScope = "incremental"
    sku_list: list[str] = Field(default_factory=list)
    limit: int = 0
    start_index: int = 0
    end_index: int = 0
    dry_run_batch_id: str = ""
    force_recalculate: bool = False
    skip_incremental_cache: bool = False
    doba_snapshots: list[DobaPriceSnapshot] = Field(default_factory=list)
    mappings: list[SkuMappingRecord] = Field(default_factory=list)
    shopify_states: list[ShopifyPriceState] = Field(default_factory=list)
    print_detail: bool = True
    print_table: bool = True
    mode: Literal["dry-run", "apply"] = "dry-run"
