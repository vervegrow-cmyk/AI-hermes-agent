from __future__ import annotations

from pydantic import BaseModel, Field

from src.shared.contracts.screening import ScreeningDecision


class CreateDraftListingCommand(BaseModel):
    decision: ScreeningDecision
    target_market: str = "US"


class ShopifyImageAsset(BaseModel):
    url: str = ""
    alt_text: str = ""
    position: int = 0
    is_primary: bool = False


class ShopifySEOContent(BaseModel):
    seo_title: str = ""
    seo_description: str = ""
    handle: str = ""
    tags: list[str] = Field(default_factory=list)
    collection_suggestions: list[str] = Field(default_factory=list)


class ShopifyProductContent(BaseModel):
    title: str = ""
    description: str = ""
    highlights: list[str] = Field(default_factory=list)
    faq: list[str] = Field(default_factory=list)


class ShopifyProductPayload(BaseModel):
    supplier_sku: str = ""
    supplier_product_id: str = ""
    product_type: str = ""
    vendor: str = ""
    status: str = "draft"
    product_hash: str = ""
    content: ShopifyProductContent = Field(default_factory=ShopifyProductContent)
    seo: ShopifySEOContent = Field(default_factory=ShopifySEOContent)
    images: list[ShopifyImageAsset] = Field(default_factory=list)
    source_data: dict = Field(default_factory=dict)


class ShopifyDraftProduct(BaseModel):
    supplier_sku: str = ""
    shopify_product_id: str = ""
    shopify_variant_id: str = ""
    title: str = ""
    description: str = ""
    highlights: list[str] = Field(default_factory=list)
    faq: list[str] = Field(default_factory=list)
    seo_title: str = ""
    seo_description: str = ""
    handle: str = ""
    tags: list[str] = Field(default_factory=list)
    images: list[ShopifyImageAsset] = Field(default_factory=list)
    status: str = "draft"
    created_at: str = ""
    collection_suggestions: list[str] = Field(default_factory=list)
    product_hash: str = ""
    source_supplier_product_id: str = ""
    mock_mode: bool = True


class ListingResult(BaseModel):
    product_id: str = ""
    sku: str = ""
    target_market: str = "US"
    action: str = "skipped"
    draft_id: str | None = None
    store: str = ""
    reasons: list[str] = Field(default_factory=list)


class ListingBatchResult(BaseModel):
    total_approved_products: int = 0
    draft_products_created: int = 0
    duplicate_products_skipped: int = 0
    sku_mappings_created: int = 0
    failed_products: int = 0
    failure_reasons: dict[str, int] = Field(default_factory=dict)
    shopify_mode: str = "mock"
    publish_count: int = 0
    inventory_update_count: int = 0
    price_update_count: int = 0
    order_create_count: int = 0
    draft_products: list[ShopifyDraftProduct] = Field(default_factory=list)
    skipped_products: list[dict] = Field(default_factory=list)
    sku_mappings: list[dict] = Field(default_factory=list)
    report_path: str = ""
