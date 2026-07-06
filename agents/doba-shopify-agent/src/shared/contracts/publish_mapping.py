from __future__ import annotations

from pydantic import BaseModel, Field


class ShopifyPublishMappingRecord(BaseModel):
    supplier_name: str = "doba"
    source_vendor: str = "DOBA"
    supplier_id: str = ""
    supplier_product_id: str = ""
    supplier_spu_no: str = ""
    supplier_sku: str = ""
    sku_code: str = ""
    merge_key: str = ""
    shopify_product_id: str = ""
    shopify_variant_id: str = ""
    shopify_handle: str = ""
    shopify_category_id: str = ""
    shopify_category_name: str = ""
    doba_category_id: str = ""
    doba_category_name: str = ""
    ship_from_country: str = ""
    ship_from_raw: str = ""
    ship_from_source: str = ""
    ship_from_confidence: str = ""
    warehouse: str = ""
    inventory: int = 0
    cost_price: float = 0
    sale_price: float = 0
    compare_at_price: float = 0
    target_channels: list[str] = Field(default_factory=list)
    published_channels: list[str] = Field(default_factory=list)
    status: str = "pending"
    last_error: str = ""
    published_at: str = ""
    updated_at: str = ""
