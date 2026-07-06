from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DobaProductInput(BaseModel):
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
    weight_kg: float = 0
    package_length_cm: float = 0
    package_width_cm: float = 0
    package_height_cm: float = 0
    description: str = ""
    image_urls: list[str] = Field(default_factory=list)
    variant_attributes: dict[str, Any] = Field(default_factory=dict)
    category_metafields: dict[str, Any] = Field(default_factory=dict)
    seller_name: str = ""
    seller_info: dict[str, Any] = Field(default_factory=dict)
    warehouse_info: dict[str, Any] = Field(default_factory=dict)
    attributes: dict[str, Any] = Field(default_factory=dict)


class NormalizedProduct(BaseModel):
    supplier_id: str = ""
    product_id: str = ""
    sku: str = ""
    title: str = ""
    normalized_title: str = ""
    brand: str = ""
    category_path: str = ""
    supplier_status: str = "active"
    cost: float = 0
    target_sale_price: float = 0
    inventory: int = 0
    ship_from_country: str = ""
    ships_to_countries: list[str] = Field(default_factory=list)
    shipping_cost: float = 0
    delivery_days: int = 0
    description: str = ""
    image_urls: list[str] = Field(default_factory=list)
    variant_attributes: dict[str, Any] = Field(default_factory=dict)
    attributes: dict[str, Any] = Field(default_factory=dict)
    category_tokens: list[str] = Field(default_factory=list)
    duplicate_key: str = ""
