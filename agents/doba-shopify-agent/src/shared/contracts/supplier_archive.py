from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SnapshotHistorySummary(BaseModel):
    inventory_stability: str = "stable"
    price_change_7d: float = 0
    seller_rating_change_30d: float = 0
    inventory_snapshots: int = 0
    price_snapshots: int = 0
    seller_snapshots: int = 0


class SupplierProduct(BaseModel):
    supplier_name: str = "doba"
    supplier_id: str = ""
    supplier_spu_no: str = ""
    product_id: str = ""
    sku: str = ""
    sku_code: str = ""
    sku_id: str = ""
    item_no: str = ""
    title: str = ""
    brand: str = ""
    category_id: str = ""
    category_name: str = ""
    category_path: str = ""
    supplier_status: str = "active"
    source_vendor: str = "DOBA"
    source_channels: list[str] = Field(default_factory=list)
    cost: float = 0
    msrp: float = 0
    inventory: int = 0
    ship_from_country: str = ""
    ship_from_raw: str = ""
    ship_from_source: str = ""
    ship_from_confidence: str = ""
    warehouse_name: str = ""
    ships_to_countries: list[str] = Field(default_factory=list)
    shipping_cost: float = 0
    delivery_days: int = 0
    description: str = ""
    image_urls: list[str] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)
    variant_attributes: dict[str, Any] = Field(default_factory=dict)
    category_metafields: dict[str, Any] = Field(default_factory=dict)
    seller_name: str = ""
    seller_info: dict[str, Any] = Field(default_factory=dict)
    warehouse_info: dict[str, Any] = Field(default_factory=dict)


class ProductSnapshot(BaseModel):
    supplier_name: str = "doba"
    supplier_id: str = ""
    product_id: str = ""
    sku: str = ""
    snapshot_at: str = ""
    title: str = ""
    brand: str = ""
    category_id: str = ""
    category_name: str = ""
    supplier_status: str = "active"
    category_path: str = ""
    description: str = ""
    image_count: int = 0
    warehouse: str = ""
    source_vendor: str = "DOBA"
    source_channels: list[str] = Field(default_factory=list)
    delivery_days: float = 0
    ships_to_countries: list[str] = Field(default_factory=list)
    category_metafields: dict[str, Any] = Field(default_factory=dict)


class InventorySnapshot(BaseModel):
    supplier_name: str = "doba"
    supplier_id: str = ""
    product_id: str = ""
    sku: str
    snapshot_at: str = ""
    warehouse: str = ""
    warehouse_name: str = ""
    ship_from_country: str = ""
    supplier_inventory: int
    shopify_inventory: int = 0


class PriceSnapshot(BaseModel):
    supplier_name: str = "doba"
    supplier_id: str = ""
    product_id: str = ""
    sku: str
    snapshot_at: str = ""
    supplier_cost: float
    shipping_cost: float = 0
    true_cost: float = 0
    current_price: float = 0
    target_price: float = 0
    msrp: float = 0
    currency: str = "USD"


class SellerSnapshot(BaseModel):
    supplier_name: str = "doba"
    supplier_id: str = ""
    snapshot_at: str = ""
    seller_name: str = ""
    seller_status: str = "active"
    ship_from_country: str = ""
    rating: float = 0
    review_count: int = 0
    fulfillment_speed_days: float = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScreeningInput(BaseModel):
    supplier: str = "doba"
    supplier_id: str = ""
    product_id: str = ""
    supplier_sku: str = ""
    title: str = ""
    category: str = ""
    price: float = 0
    shipping_cost: float = 0
    inventory: int = 0
    warehouse: str = ""
    ship_from_country: str = ""
    seller_rating: float = 0
    review_count: int = 0
    fulfillment_speed_days: float = 0
    images_count: int = 0
    snapshot_history: SnapshotHistorySummary = Field(default_factory=SnapshotHistorySummary)


class ArchiveResult(BaseModel):
    supplier_name: str = "doba"
    archived_products: int = 0
    product_snapshots: int = 0
    inventory_snapshots: int = 0
    price_snapshots: int = 0
    seller_snapshots: int = 0
    screening_inputs: int = 0
    skipped_products: int = 0
    archive_statistics: dict[str, int | float | str] = Field(default_factory=dict)
    report_path: str = ""
    warnings: list[str] = Field(default_factory=list)
