from pathlib import Path

from src.modules.product_screening import normalize_product
from src.modules.risk_control import assess_risk, run_risk_control
from src.modules.risk_control.infrastructure import ai_scoring_service
from src.shared.contracts.inventory import InventorySyncRecord
from src.shared.contracts.listing import ShopifyDraftProduct
from src.shared.contracts.mapping import SkuMappingRecord
from src.shared.contracts.pricing import PriceSnapshot, PriceSyncRecord, PricingDecision
from src.shared.contracts.product import DobaProductInput
from src.shared.contracts.risk import RiskAssessmentCommand, RiskControlCommand
from src.shared.contracts.screening import ListingCandidate, ProductScore
from src.shared.contracts.supplier_archive import InventorySnapshot, SellerSnapshot, SupplierProduct
from tests.conftest import load_fixture


def test_risk_control_blocks_restricted_product():
    product = DobaProductInput.model_validate(load_fixture("rejected_product.json"))
    normalized = normalize_product(product)
    result = assess_risk(RiskAssessmentCommand(normalized_product=normalized, target_market="US"))
    assert result.blocked is True
    assert result.level == "high"


def test_risk_control_flags_branded_product_for_review():
    product = DobaProductInput.model_validate(load_fixture("manual_review_product.json"))
    normalized = normalize_product(product)
    result = assess_risk(RiskAssessmentCommand(normalized_product=normalized, target_market="US"))
    assert result.review_required is True
    assert any("brand" in reason.lower() or "review" in reason.lower() for reason in result.reasons)


def test_ai_scoring_service_falls_back_without_deepseek_key(monkeypatch):
    monkeypatch.setattr(ai_scoring_service, "_get_client", lambda: None)
    product = DobaProductInput.model_validate(load_fixture("manual_review_product.json"))
    normalized = normalize_product(product)
    score, summary = ai_scoring_service.score_product_risk(normalized)
    assert score > 0
    assert "fallback" in summary


def test_ai_scoring_service_uses_deepseek_json_response(monkeypatch):
    class FakeClient:
        @staticmethod
        def generate(prompt, **kwargs):
            return {"text": '{"score": 0.61, "summary": "borderline brand risk"}', "raw": {}}

    monkeypatch.setattr(ai_scoring_service, "_get_client", lambda: FakeClient())
    product = DobaProductInput.model_validate(load_fixture("approved_product.json"))
    normalized = normalize_product(product)
    score, summary = ai_scoring_service.score_product_risk(normalized)
    assert score == 0.61
    assert summary == "borderline brand risk"


def _risk_command() -> RiskControlCommand:
    return RiskControlCommand(
        supplier_products=[
            SupplierProduct(
                supplier_id="sup-1",
                product_id="p-1",
                sku="sku-1",
                title="Apple Medical Device",
                brand="Apple",
                category_path="Medical Equipment",
                inventory=0,
                shipping_cost=5,
            )
        ],
        inventory_snapshots=[
            InventorySnapshot(
                supplier_id="sup-1",
                product_id="p-1",
                sku="sku-1",
                snapshot_at="2000-01-01T00:00:00+00:00",
                supplier_inventory=0,
                shopify_inventory=100,
            )
        ],
        price_snapshots=[
            PriceSnapshot(
                supplier_id="sup-1",
                product_id="p-1",
                sku="sku-1",
                snapshot_at="2026-06-01T00:00:00+00:00",
                supplier_cost=10,
                current_price=30,
            ),
            PriceSnapshot(
                supplier_id="sup-1",
                product_id="p-1",
                sku="sku-1",
                snapshot_at="2026-06-15T00:00:00+00:00",
                supplier_cost=14,
                current_price=30,
            ),
        ],
        seller_snapshots=[
            SellerSnapshot(supplier_id="sup-1", snapshot_at="2026-06-01T00:00:00+00:00", rating=4.6, fulfillment_speed_days=2),
            SellerSnapshot(supplier_id="sup-1", snapshot_at="2026-06-15T00:00:00+00:00", rating=3.4, fulfillment_speed_days=6),
        ],
        ai_product_scores=[
            ProductScore(supplier_sku="sku-1", compliance_risk_score=90, return_risk_score=80, overall_score=55)
        ],
        listing_candidates=[
            ListingCandidate(
                supplier_sku="sku-1",
                supplier_product_id="p-1",
                status="approved_for_listing",
                overall_score=55,
                source_title="Apple Medical Device for Children",
                source_description="FDA regulated hazmat style battery powered item",
                source_brand="Apple",
                source_category="Medical Device",
            )
        ],
        shopify_products=[
            ShopifyDraftProduct(
                supplier_sku="sku-1",
                shopify_product_id="gid://shopify/Product/1",
                shopify_variant_id="gid://shopify/ProductVariant/1",
                title="Apple Medical Device",
                handle="apple-medical-device",
            )
        ],
        sku_mappings=[
            SkuMappingRecord(
                supplier_sku="sku-1",
                sku="sku-1",
                shopify_product_id="gid://shopify/Product/1",
                shopify_variant_id="gid://shopify/ProductVariant/1",
            )
        ],
        inventory_sync_logs=[
            InventorySyncRecord(supplier_sku="sku-1", shopify_variant_id="gid://shopify/ProductVariant/1", old_inventory=100, new_inventory=0, change_type="out_of_stock", status="sync_failed", error_message="429 rate limited"),
            InventorySyncRecord(supplier_sku="sku-1", status="missing_mapping", change_type="sync_failed"),
            InventorySyncRecord(supplier_sku="sku-1", status="sync_failed", change_type="sync_failed"),
        ],
        price_sync_logs=[
            PriceSyncRecord(supplier_sku="sku-1", variant_id="gid://shopify/ProductVariant/1", old_price=30, new_price=18, decision="decrease_price", status="sync_failed", error_message="401 unauthorized"),
        ],
        pricing_decisions=[
            PricingDecision(
                supplier_sku="sku-1",
                decision="decrease_price",
                old_price=30,
                new_price=18,
                reason_codes=["competitor_pressure"],
                profit_before=12,
                profit_after=0.5,
                price_health_score=25,
            )
        ],
    )


def test_inventory_price_seller_compliance_supplier_shopify_and_sync_risk_detection():
    result = run_risk_control(_risk_command())
    categories = {event.risk_type for event in result.risk_events}
    assert "inventory_risk" in categories
    assert "price_risk" in categories
    assert "seller_risk" in categories
    assert "compliance_risk" in categories
    assert "supplier_risk" in categories
    assert "shopify_risk" in categories
    assert "sync_risk" in categories


def test_risk_score_and_level_classification_and_alert_creation_work():
    result = run_risk_control(_risk_command())
    assert result.risk_scores
    assert any(score.risk_level in {"high", "critical"} for score in result.risk_scores)
    assert result.risk_alerts
    assert all(alert.risk_level in {"high", "critical"} for alert in result.risk_alerts)


def test_approval_queue_and_blocked_product_creation_work():
    result = run_risk_control(_risk_command())
    assert result.approval_queue
    assert any(item.trigger_type == "compliance_risk" for item in result.approval_queue)
    assert result.blocked_products
    assert any(product.risk_type == "compliance_risk" for product in result.blocked_products)


def test_supplier_risk_score_and_health_classification_work():
    result = run_risk_control(_risk_command())
    assert result.supplier_risk_scores
    assert result.supplier_risk_scores[0].health_classification in {"risky", "critical", "watch", "healthy"}


def test_risk_report_generation_and_no_runtime_mutations_work():
    report_path = Path("docs/audits/risk-control-report.md")
    if report_path.exists():
        report_path.unlink()
    result = run_risk_control(_risk_command())
    assert report_path.exists()
    content = report_path.read_text(encoding="utf-8")
    assert "Risk Control Report" in content
    assert result.no_inventory_modification_occurred is True
    assert result.no_price_modification_occurred is True
    assert result.no_product_creation_occurred is True
    assert result.no_order_creation_occurred is True
