from __future__ import annotations

from pydantic import BaseModel, Field

from src.shared.contracts.listing import ShopifySEOContent


class ProductFAQEntry(BaseModel):
    question: str = ""
    answer: str = ""


class ProductImageAlt(BaseModel):
    url: str = ""
    alt_text: str = ""
    position: int = 0
    is_primary: bool = False


class StructuredProductDetails(BaseModel):
    headline: str = ""
    summary: str = ""
    highlights: list[str] = Field(default_factory=list)
    key_specs: dict[str, str] = Field(default_factory=dict)
    usage_scenarios: list[str] = Field(default_factory=list)
    care_instructions: list[str] = Field(default_factory=list)


class GoogleMerchantProjection(BaseModel):
    title: str = ""
    description: str = ""
    google_product_category: str = ""
    product_type: str = ""
    brand: str = ""
    condition: str = "new"
    availability: str = "in stock"
    price_amount: float = 0
    price_currency: str = "USD"
    image_link: str = ""
    additional_image_links: list[str] = Field(default_factory=list)
    custom_labels: list[str] = Field(default_factory=list)


class OpenAIProductFeedProjection(BaseModel):
    title: str = ""
    description: str = ""
    category_path: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    attributes: dict[str, str] = Field(default_factory=dict)
    seo_keywords: list[str] = Field(default_factory=list)


class SchemaProjection(BaseModel):
    schema_type: str = "Product"
    payload: dict[str, object] = Field(default_factory=dict)


class GeoScoreProjection(BaseModel):
    market: str = "US"
    score: int = 0
    eligible: bool = False
    reasons: list[str] = Field(default_factory=list)


class PostPublishReviewProjection(BaseModel):
    shopify_product_id: str = ""
    published_channels: list[str] = Field(default_factory=list)
    variant_count_expected: int = 0
    variant_count_actual: int = 0
    category_written: bool = False
    publish_ready: bool = False
    review_notes: list[str] = Field(default_factory=list)


class ProductSemanticSummary(BaseModel):
    product_type: str = ""
    category_label: str = ""
    summary: str = ""
    confidence: float = 0


class ProductEnrichmentBundle(BaseModel):
    semantic: ProductSemanticSummary = Field(default_factory=ProductSemanticSummary)
    details: StructuredProductDetails = Field(default_factory=StructuredProductDetails)
    seo: ShopifySEOContent = Field(default_factory=ShopifySEOContent)
    faq: list[ProductFAQEntry] = Field(default_factory=list)
    image_alts: list[ProductImageAlt] = Field(default_factory=list)
    google_merchant: GoogleMerchantProjection = Field(default_factory=GoogleMerchantProjection)
    openai_feed: OpenAIProductFeedProjection = Field(default_factory=OpenAIProductFeedProjection)
    schema_projection: SchemaProjection = Field(default_factory=SchemaProjection)
    geo_score: GeoScoreProjection = Field(default_factory=GeoScoreProjection)
    post_publish_review: PostPublishReviewProjection = Field(default_factory=PostPublishReviewProjection)
