from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from src.shared.contracts.product import NormalizedProduct


RiskLevel = Literal["low", "medium", "high", "critical"]
RiskCategory = Literal[
    "inventory_risk",
    "price_risk",
    "seller_risk",
    "compliance_risk",
    "supplier_risk",
    "shopify_risk",
    "sync_risk",
    "profit_risk",
]


class RiskAssessmentCommand(BaseModel):
    normalized_product: NormalizedProduct
    target_market: str = "US"


class RiskAssessmentResult(BaseModel):
    level: RiskLevel = "low"
    blocked: bool = False
    review_required: bool = False
    reasons: list[str] = Field(default_factory=list)
    ai_score: float = 0
    ai_summary: str = ""


class RiskEvent(BaseModel):
    risk_type: RiskCategory
    risk_level: RiskLevel = "low"
    supplier_sku: str = ""
    shopify_variant_id: str = ""
    affected_entity: str = ""
    description: str = ""
    created_at: str = ""
    status: str = "open"
    risk_score: float = 0
    supplier_id: str = ""


class RiskAlert(BaseModel):
    risk_type: RiskCategory
    risk_level: RiskLevel
    supplier_sku: str = ""
    alert_message: str = ""
    created_at: str = ""
    status: str = "active"


class RiskScore(BaseModel):
    supplier_sku: str = ""
    risk_type: RiskCategory
    risk_score: float = 0
    risk_level: RiskLevel = "low"
    reasons: list[str] = Field(default_factory=list)


class ApprovalQueueItem(BaseModel):
    supplier_sku: str = ""
    trigger_type: RiskCategory = "price_risk"
    risk_level: RiskLevel = "medium"
    reason: str = ""
    created_at: str = ""
    status: str = "pending"


class BlockedProduct(BaseModel):
    supplier_sku: str = ""
    risk_type: RiskCategory
    risk_level: RiskLevel = "critical"
    reason: str = ""
    blocked_at: str = ""
    status: str = "blocked"


class SupplierRiskScore(BaseModel):
    supplier_id: str = ""
    stability_score: float = 0
    pricing_consistency_score: float = 0
    inventory_consistency_score: float = 0
    fulfillment_quality_score: float = 0
    overall_score: float = 0
    health_classification: Literal["healthy", "watch", "risky", "critical"] = "healthy"


class RiskHealthSummary(BaseModel):
    total_events: int = 0
    low_count: int = 0
    medium_count: int = 0
    high_count: int = 0
    critical_count: int = 0
    affected_products: int = 0
    affected_suppliers: int = 0
    supplier_health_summary: dict[str, int] = Field(default_factory=dict)
    approval_queue_count: int = 0
    blocked_product_count: int = 0


class RiskReport(BaseModel):
    health_summary: RiskHealthSummary = Field(default_factory=RiskHealthSummary)
    category_counts: dict[str, int] = Field(default_factory=dict)
    level_counts: dict[str, int] = Field(default_factory=dict)
    report_path: str = ""


class RiskControlCommand(BaseModel):
    supplier_products: list[Any] = Field(default_factory=list)
    inventory_snapshots: list[Any] = Field(default_factory=list)
    price_snapshots: list[Any] = Field(default_factory=list)
    seller_snapshots: list[Any] = Field(default_factory=list)
    ai_product_scores: list[Any] = Field(default_factory=list)
    listing_candidates: list[Any] = Field(default_factory=list)
    shopify_products: list[Any] = Field(default_factory=list)
    sku_mappings: list[Any] = Field(default_factory=list)
    inventory_sync_logs: list[Any] = Field(default_factory=list)
    price_sync_logs: list[Any] = Field(default_factory=list)
    pricing_decisions: list[Any] = Field(default_factory=list)


class RiskBatchResult(BaseModel):
    risk_events: list[RiskEvent] = Field(default_factory=list)
    risk_alerts: list[RiskAlert] = Field(default_factory=list)
    risk_scores: list[RiskScore] = Field(default_factory=list)
    approval_queue: list[ApprovalQueueItem] = Field(default_factory=list)
    blocked_products: list[BlockedProduct] = Field(default_factory=list)
    supplier_risk_scores: list[SupplierRiskScore] = Field(default_factory=list)
    risk_report: RiskReport = Field(default_factory=RiskReport)
    mock_mode: bool = True
    no_inventory_modification_occurred: bool = True
    no_price_modification_occurred: bool = True
    no_product_creation_occurred: bool = True
    no_order_creation_occurred: bool = True
