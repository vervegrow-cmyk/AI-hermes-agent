from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from src.shared.contracts.product import DobaProductInput, NormalizedProduct
from src.shared.contracts.risk import RiskAssessmentResult
from src.shared.contracts.supplier_archive import ScreeningInput


DecisionStatus = Literal["approved", "manual_review", "rejected"]
RuleEngineStatus = Literal["passed", "manual_review", "rejected"]
ListingCandidateStatus = Literal["approved_for_listing", "manual_review", "watchlist", "rejected"]


class ScreenProductCommand(BaseModel):
    product: DobaProductInput
    normalized_product: NormalizedProduct
    risk_assessment: RiskAssessmentResult | None = None
    target_market: str = "US"


class ScreeningDecision(BaseModel):
    status: DecisionStatus
    product_id: str = ""
    sku: str = ""
    normalized_title: str = ""
    target_market: str = "US"
    reasons: list[str] = Field(default_factory=list)
    expected_profit: float = 0
    margin_rate: float = 0
    shipping_ratio: float = 0
    score: float = 0
    shopify_draft_id: str | None = None
    publish_action: str = "skipped"
    normalized_product: NormalizedProduct
    risk_assessment: RiskAssessmentResult | None = None


class RuleEngineResult(BaseModel):
    supplier_sku: str = ""
    status: RuleEngineStatus = "passed"
    reason_codes: list[str] = Field(default_factory=list)
    passed_rules: list[str] = Field(default_factory=list)
    failed_rules: list[str] = Field(default_factory=list)


class RuleEngineBatchResult(BaseModel):
    total_products: int = 0
    passed_products: int = 0
    manual_review_products: int = 0
    rejected_products: int = 0
    rule_engine_results: list[RuleEngineResult] = Field(default_factory=list)
    pre_filtered_products: list[ScreeningInput] = Field(default_factory=list)
    top_rejection_reasons: dict[str, int] = Field(default_factory=dict)
    report_path: str = ""


class DeepSeekScoreRequest(BaseModel):
    product: ScreeningInput
    prompt: str = ""


class DeepSeekScoreResponse(BaseModel):
    trend_score: int = 0
    season_score: int = 0
    profit_score: int = 0
    price_score: int = 0
    inventory_score: int = 0
    seller_score: int = 0
    fulfillment_score: int = 0
    review_score: int = 0
    shipping_score: int = 0
    return_risk_score: int = 0
    compliance_risk_score: int = 0
    reasoning: str = ""
    risk_notes: list[str] = Field(default_factory=list)
    fallback_reason: str = ""


class ProductScore(BaseModel):
    supplier_sku: str = ""
    model_name: str = ""
    scored_at: str = ""
    trend_score: int = 0
    season_score: int = 0
    profit_score: int = 0
    price_score: int = 0
    inventory_score: int = 0
    seller_score: int = 0
    fulfillment_score: int = 0
    review_score: int = 0
    shipping_score: int = 0
    return_risk_score: int = 0
    compliance_risk_score: int = 0
    overall_score: float = 0
    reasoning: str = ""
    risk_notes: list[str] = Field(default_factory=list)
    input_source: str = "pre_filtered_products"
    fallback_reason: str = ""


class ProductScoreBatchResult(BaseModel):
    total_pre_filtered_products: int = 0
    total_scored_products: int = 0
    scoring_mode: str = "mock"
    average_overall_score: float = 0
    top_scoring_products: list[ProductScore] = Field(default_factory=list)
    high_return_risk_products: list[ProductScore] = Field(default_factory=list)
    high_compliance_risk_products: list[ProductScore] = Field(default_factory=list)
    fallback_count: int = 0
    no_listing_candidates_created: bool = True
    ai_product_scores: list[ProductScore] = Field(default_factory=list)
    report_path: str = ""


class ListingCandidate(BaseModel):
    supplier_sku: str = ""
    status: ListingCandidateStatus = "manual_review"
    overall_score: float = 0
    reason_codes: list[str] = Field(default_factory=list)
    score_snapshot: dict[str, int | float | str | list[str]] = Field(default_factory=dict)
    created_at: str = ""
    source: str = "ai_product_scores"
    supplier_product_id: str = ""
    source_title: str = ""
    source_description: str = ""
    source_brand: str = ""
    source_category: str = ""
    source_price: float = 0
    source_inventory: int = 0
    source_image_urls: list[str] = Field(default_factory=list)
    source_attributes: dict[str, str] = Field(default_factory=dict)
    source_variant_attributes: dict[str, str] = Field(default_factory=dict)
    source_product: dict[str, Any] = Field(default_factory=dict)


class CandidatePoolBatchResult(BaseModel):
    total_scored_products_processed: int = 0
    approved_for_listing_count: int = 0
    manual_review_count: int = 0
    watchlist_count: int = 0
    rejected_count: int = 0
    top_approved_products: list[ListingCandidate] = Field(default_factory=list)
    top_rejection_reasons: dict[str, int] = Field(default_factory=dict)
    average_score_by_status: dict[str, float] = Field(default_factory=dict)
    candidate_status_distribution: dict[str, int] = Field(default_factory=dict)
    no_shopify_writes_occurred: bool = True
    no_deepseek_call_occurred: bool = True
    no_doba_api_call_occurred: bool = True
    no_inventory_sync_occurred: bool = True
    no_price_sync_occurred: bool = True
    no_governance_implementation_occurred: bool = True
    listing_candidates: list[ListingCandidate] = Field(default_factory=list)
    report_path: str = ""
