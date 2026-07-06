from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from src.shared.contracts.supplier_archive import InventorySnapshot


InventoryChangeType = Literal["increase", "decrease", "out_of_stock", "restocked", "unchanged", "sync_failed"]


class SupplierInventory(BaseModel):
    supplier_sku: str = ""
    inventory: int = 0
    warehouse: str = ""
    updated_at: str = ""


class ShopifyInventoryState(BaseModel):
    supplier_sku: str = ""
    shopify_variant_id: str = ""
    inventory: int = 0
    updated_at: str = ""


class InventoryChange(BaseModel):
    supplier_sku: str = ""
    current_inventory: int = 0
    target_inventory: int = 0
    delta: int = 0
    change_type: InventoryChangeType = "unchanged"
    warehouse: str = ""


class InventorySyncPlan(BaseModel):
    supplier_sku: str = ""
    shopify_variant_id: str = ""
    current_inventory: int = 0
    target_inventory: int = 0
    change_type: InventoryChangeType = "unchanged"
    priority: int = 0
    warehouse: str = ""
    requires_sync: bool = False


class InventorySyncRecord(BaseModel):
    supplier_sku: str = ""
    shopify_variant_id: str = ""
    old_inventory: int = 0
    new_inventory: int = 0
    change_type: InventoryChangeType = "unchanged"
    status: str = "skipped"
    sync_time: str = ""
    error_message: str = ""


class InventorySyncReport(BaseModel):
    products_processed: int = 0
    inventory_changes_detected: int = 0
    increases: int = 0
    decreases: int = 0
    out_of_stock: int = 0
    restocked: int = 0
    unchanged: int = 0
    successful_syncs: int = 0
    failed_syncs: int = 0
    missing_mappings: int = 0
    mode: str = "mock"
    inventory_accuracy_summary: str = ""


class InventorySyncCommand(BaseModel):
    target_market: str = "US"
    snapshots: list[InventorySnapshot] = Field(default_factory=list)
    supplier_inventories: list[SupplierInventory] = Field(default_factory=list)
    shopify_inventory_states: list[ShopifyInventoryState] = Field(default_factory=list)
    sku_mappings: list[dict] = Field(default_factory=list)

    @model_validator(mode="after")
    def _hydrate_legacy_snapshots(self) -> "InventorySyncCommand":
        if self.snapshots and not self.supplier_inventories:
            self.supplier_inventories = [
                SupplierInventory(
                    supplier_sku=snapshot.sku,
                    inventory=snapshot.supplier_inventory,
                    warehouse=snapshot.warehouse,
                    updated_at=snapshot.snapshot_at,
                )
                for snapshot in self.snapshots
            ]
        if self.snapshots and not self.shopify_inventory_states:
            self.shopify_inventory_states = [
                ShopifyInventoryState(
                    supplier_sku=snapshot.sku,
                    inventory=snapshot.shopify_inventory,
                    updated_at=snapshot.snapshot_at,
                )
                for snapshot in self.snapshots
            ]
        return self


class InventorySyncItem(BaseModel):
    sku: str
    supplier_inventory: int
    shopify_inventory: int
    delta: int
    action: str


class InventorySyncBatchResult(BaseModel):
    target_market: str = "US"
    synced_count: int = 0
    skipped_count: int = 0
    items: list[InventorySyncItem] = Field(default_factory=list)
    changes: list[InventoryChange] = Field(default_factory=list)
    plans: list[InventorySyncPlan] = Field(default_factory=list)
    records: list[InventorySyncRecord] = Field(default_factory=list)
    report: InventorySyncReport = Field(default_factory=InventorySyncReport)
    report_path: str = ""
    mock_mode: bool = True
    no_product_creation_occurred: bool = True
    no_publish_occurred: bool = True
    no_price_update_occurred: bool = True
    no_order_creation_occurred: bool = True


class InventorySyncResult(InventorySyncBatchResult):
    pass
