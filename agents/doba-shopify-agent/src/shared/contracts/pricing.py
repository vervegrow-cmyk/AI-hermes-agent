from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from src.shared.contracts.supplier_archive import InventorySnapshot, PriceSnapshot


PricingDecisionType = Literal["keep_price", "increase_price", "decrease_price", "clearance_price", "manual_review"]


class SupplierCost(BaseModel):
    supplier_sku: str = ""
    cost: float = 0
    currency: str = "USD"
    updated_at: str = ""


class ShippingCost(BaseModel):
    supplier_sku: str = ""
    cost: float = 0
    currency: str = "USD"
    updated_at: str = ""


class WarehouseCost(BaseModel):
    supplier_sku: str = ""
    cost: float = 0
    currency: str = "USD"
    updated_at: str = ""


class PlatformCost(BaseModel):
    supplier_sku: str = ""
    cost: float = 0
    currency: str = "USD"
    updated_at: str = ""


class CompetitorPriceData(BaseModel):
    supplier_sku: str = ""
    competitor_low: float = 0
    competitor_avg: float = 0
    competitor_high: float = 0


class ShopifyPriceState(BaseModel):
    supplier_sku: str = ""
    shopify_variant_id: str = ""
    current_price: float = 0
    updated_at: str = ""
    inventory: int = 0
    lifecycle_stage: str = "growth"


class PriceCalculation(BaseModel):
    supplier_sku: str = ""
    true_cost: float = 0
    break_even_price: float = 0
    minimum_safe_price: float = 0
    recommended_price: float = 0
    target_price: float = 0
    gross_margin: float = 0
    net_margin: float = 0
    profit_amount: float = 0
    roi: float = 0


class PriceHealthScore(BaseModel):
    supplier_sku: str = ""
    score: float = 0
    margin_score: float = 0
    competitiveness_score: float = 0
    stability_score: float = 0
    inventory_score: float = 0


class PricingDecision(BaseModel):
    supplier_sku: str = ""
    decision: PricingDecisionType = "keep_price"
    old_price: float = 0
    new_price: float = 0
    reason_codes: list[str] = Field(default_factory=list)
    profit_before: float = 0
    profit_after: float = 0
    price_health_score: float = 0


class PriceSyncRecord(BaseModel):
    supplier_sku: str = ""
    variant_id: str = ""
    old_price: float = 0
    new_price: float = 0
    profit_before: float = 0
    profit_after: float = 0
    decision: PricingDecisionType = "keep_price"
    timestamp: str = ""
    status: str = "skipped"
    error_message: str = ""


class PriceSyncReport(BaseModel):
    products_processed: int = 0
    price_changes_detected: int = 0
    price_increases: int = 0
    price_decreases: int = 0
    clearance_pricing_count: int = 0
    keep_price_count: int = 0
    manual_review_count: int = 0
    average_margin: float = 0
    lowest_margin: float = 0
    highest_margin: float = 0
    average_roi: float = 0
    price_health_score: float = 0
    successful_syncs: int = 0
    failed_syncs: int = 0
    mode: str = "mock"


class PriceSyncCommand(BaseModel):
    target_market: str = "US"
    snapshots: list[PriceSnapshot] = Field(default_factory=list)
    inventory_snapshots: list[InventorySnapshot] = Field(default_factory=list)
    supplier_costs: list[SupplierCost] = Field(default_factory=list)
    shipping_costs: list[ShippingCost] = Field(default_factory=list)
    warehouse_costs: list[WarehouseCost] = Field(default_factory=list)
    platform_costs: list[PlatformCost] = Field(default_factory=list)
    shopify_price_states: list[ShopifyPriceState] = Field(default_factory=list)
    sku_mappings: list[dict] = Field(default_factory=list)
    competitor_prices: list[CompetitorPriceData] = Field(default_factory=list)
    lifecycle_stages: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _hydrate_legacy_snapshots(self) -> "PriceSyncCommand":
        if self.snapshots and not self.supplier_costs:
            self.supplier_costs = [
                SupplierCost(
                    supplier_sku=snapshot.sku,
                    cost=snapshot.supplier_cost,
                    currency=snapshot.currency,
                    updated_at=snapshot.snapshot_at,
                )
                for snapshot in self.snapshots
            ]
        if self.snapshots and not self.shipping_costs:
            self.shipping_costs = [
                ShippingCost(
                    supplier_sku=snapshot.sku,
                    cost=snapshot.shipping_cost,
                    currency=snapshot.currency,
                    updated_at=snapshot.snapshot_at,
                )
                for snapshot in self.snapshots
            ]
        if self.snapshots and not self.shopify_price_states:
            inventory_map = {snapshot.sku: snapshot.supplier_inventory for snapshot in self.inventory_snapshots}
            self.shopify_price_states = [
                ShopifyPriceState(
                    supplier_sku=snapshot.sku,
                    current_price=snapshot.current_price,
                    updated_at=snapshot.snapshot_at,
                    inventory=inventory_map.get(snapshot.sku, 0),
                    lifecycle_stage=self.lifecycle_stages.get(snapshot.sku, "growth"),
                )
                for snapshot in self.snapshots
            ]
        return self


class PriceSyncItem(BaseModel):
    sku: str
    current_price: float
    target_price: float
    delta: float
    action: str


class PriceSyncBatchResult(BaseModel):
    target_market: str = "US"
    synced_count: int = 0
    skipped_count: int = 0
    items: list[PriceSyncItem] = Field(default_factory=list)
    calculations: list[PriceCalculation] = Field(default_factory=list)
    decisions: list[PricingDecision] = Field(default_factory=list)
    records: list[PriceSyncRecord] = Field(default_factory=list)
    report: PriceSyncReport = Field(default_factory=PriceSyncReport)
    report_path: str = ""
    mock_mode: bool = True
    no_product_creation_occurred: bool = True
    no_publish_occurred: bool = True
    no_inventory_update_occurred: bool = True
    no_order_creation_occurred: bool = True
    no_fulfillment_occurred: bool = True


class PriceSyncResult(PriceSyncBatchResult):
    pass
