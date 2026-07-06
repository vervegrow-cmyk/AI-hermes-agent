from src.shared.contracts import (
    ApprovalQueueItem,
    ArchiveResult,
    BlockedProduct,
    CandidatePoolBatchResult,
    CompetitorPriceData,
    GeoScoreProjection,
    GoogleMerchantProjection,
    DeepSeekScoreRequest,
    DeepSeekScoreResponse,
    DobaProductInput,
    InventoryChange,
    InventorySyncBatchResult,
    InventorySyncCommand,
    InventorySyncPlan,
    InventorySyncRecord,
    InventorySyncReport,
    ListingBatchResult,
    ListingCandidate,
    PlatformCost,
    PriceCalculation,
    PriceHealthScore,
    PriceSyncCommand,
    PriceSyncBatchResult,
    PriceSyncRecord,
    PriceSyncReport,
    PricingDecision,
    ProductScore,
    ProductScoreBatchResult,
    ProductEnrichmentBundle,
    ProductFAQEntry,
    ProductImageAlt,
    ProductSemanticSummary,
    ProductSnapshot,
    ResolveSkuCommand,
    RiskAssessmentResult,
    RiskBatchResult,
    RiskControlCommand,
    RiskEvent,
    RiskHealthSummary,
    RiskReport,
    RiskScore,
    RuleEngineBatchResult,
    RuleEngineResult,
    ScreeningInput,
    ScreenProductCommand,
    SellerSnapshot,
    ShopifyDraftProduct,
    ShopifyImageAsset,
    ShopifyInventoryState,
    ShopifyPriceState,
    ShopifyProductContent,
    ShopifyProductPayload,
    ShopifySEOContent,
    ShippingCost,
    SchemaProjection,
    SupplierCost,
    SupplierInventory,
    SupplierRiskScore,
    StructuredProductDetails,
    SkuMapping,
    SupplierProduct,
    WarehouseCost,
)
from src.shared.contracts.supplier_archive import SnapshotHistorySummary
from src.shared.contracts.product import NormalizedProduct


def test_product_contract_defaults_are_stable():
    product = DobaProductInput()
    assert product.supplier_status == "active"
    assert product.image_urls == []
    assert product.attributes == {}


def test_screening_contract_round_trips_with_nested_risk():
    normalized = NormalizedProduct(product_id="p-1", sku="sku-1", normalized_title="Title")
    command = ScreenProductCommand(
        product=DobaProductInput(product_id="p-1", sku="sku-1"),
        normalized_product=normalized,
        risk_assessment=RiskAssessmentResult(review_required=True, reasons=["check brand"]),
        target_market="US",
    )
    dumped = command.model_dump()
    restored = ScreenProductCommand.model_validate(dumped)
    assert restored.risk_assessment is not None
    assert restored.risk_assessment.reasons == ["check brand"]


def test_sync_contracts_keep_list_defaults():
    inventory = InventorySyncCommand()
    pricing = PriceSyncCommand()
    mapping = ResolveSkuCommand()
    assert inventory.snapshots == []
    assert inventory.supplier_inventories == []
    assert pricing.snapshots == []
    assert mapping.sku == ""


def test_supplier_archive_contracts_are_available():
    product = SupplierProduct(product_id="p-1", sku="sku-1", title="Demo")
    snapshot = ProductSnapshot(product_id="p-1", sku="sku-1", title="Demo")
    seller = SellerSnapshot(supplier_id="sup-1")
    screening_input = ScreeningInput(
        supplier_sku="sku-1",
        title="Demo",
        snapshot_history=SnapshotHistorySummary(inventory_snapshots=1),
    )
    result = ArchiveResult(archived_products=1, screening_inputs=1)
    assert product.supplier_name == "doba"
    assert snapshot.supplier_name == "doba"
    assert seller.supplier_name == "doba"
    assert screening_input.snapshot_history.inventory_snapshots == 1
    assert result.archived_products == 1
    assert result.screening_inputs == 1


def test_rule_engine_contracts_are_available():
    rule_result = RuleEngineResult(supplier_sku="sku-1", status="manual_review", reason_codes=["warehouse_missing"])
    batch_result = RuleEngineBatchResult(total_products=1, manual_review_products=1, rule_engine_results=[rule_result])
    assert rule_result.status == "manual_review"
    assert batch_result.rule_engine_results[0].supplier_sku == "sku-1"


def test_deepseek_scoring_contracts_are_available():
    screening_input = ScreeningInput(supplier_sku="sku-1", title="Demo")
    request = DeepSeekScoreRequest(product=screening_input, prompt="Return JSON only")
    response = DeepSeekScoreResponse(trend_score=80, risk_notes=["seasonal demand"])
    score = ProductScore(supplier_sku="sku-1", overall_score=78.5)
    batch = ProductScoreBatchResult(total_scored_products=1, ai_product_scores=[score])
    assert request.product.supplier_sku == "sku-1"
    assert response.trend_score == 80
    assert batch.ai_product_scores[0].overall_score == 78.5


def test_candidate_pool_contracts_are_available():
    candidate = ListingCandidate(supplier_sku="sku-1", status="watchlist", overall_score=72)
    batch = CandidatePoolBatchResult(total_scored_products_processed=1, watchlist_count=1, listing_candidates=[candidate])
    assert candidate.status == "watchlist"
    assert batch.listing_candidates[0].supplier_sku == "sku-1"


def test_shopify_listing_contracts_are_available():
    image = ShopifyImageAsset(url="https://example.com/item.jpg", alt_text="Demo image", position=1, is_primary=True)
    seo = ShopifySEOContent(seo_title="Demo Title", seo_description="Demo description", handle="demo-title")
    content = ShopifyProductContent(title="Demo Title", description="<p>Demo</p>", highlights=["Fast setup"], faq=["How is it used?"])
    payload = ShopifyProductPayload(
        supplier_sku="sku-1",
        supplier_product_id="product-1",
        product_hash="abc123",
        content=content,
        seo=seo,
        images=[image],
    )
    draft = ShopifyDraftProduct(supplier_sku="sku-1", title="Demo Title", handle="demo-title")
    mapping = SkuMapping(supplier_sku="sku-1", shopify_product_id="gid://shopify/Product/1")
    batch = ListingBatchResult(total_approved_products=1, draft_products=[draft], sku_mappings=[mapping.model_dump()])
    assert payload.images[0].is_primary is True
    assert draft.status == "draft"
    assert mapping.sku == "sku-1"
    assert batch.draft_products[0].supplier_sku == "sku-1"


def test_enrichment_contracts_are_available():
    faq = ProductFAQEntry(question="What is it?", answer="A demo product.")
    image_alt = ProductImageAlt(url="https://example.com/item.jpg", alt_text="Demo item", position=1, is_primary=True)
    details = StructuredProductDetails(headline="Demo", summary="Summary", highlights=["Fast setup"])
    merchant = GoogleMerchantProjection(title="Demo", product_type="General")
    schema = SchemaProjection(schema_type="Product", payload={"name": "Demo"})
    geo = GeoScoreProjection(score=78, eligible=True, reasons=["US ship-from confirmed"])
    semantic = ProductSemanticSummary(product_type="Kitchen & Dining", category_label="kitchen-dining", summary="Demo semantic summary", confidence=0.8)
    bundle = ProductEnrichmentBundle(
        semantic=semantic,
        details=details,
        faq=[faq],
        image_alts=[image_alt],
        google_merchant=merchant,
        schema_projection=schema,
        geo_score=geo,
    )
    assert bundle.semantic.category_label == "kitchen-dining"
    assert bundle.faq[0].question == "What is it?"
    assert bundle.image_alts[0].is_primary is True
    assert bundle.geo_score.eligible is True


def test_inventory_sync_contracts_are_available():
    supplier = SupplierInventory(supplier_sku="sku-1", inventory=9, warehouse="US")
    shopify = ShopifyInventoryState(supplier_sku="sku-1", shopify_variant_id="variant-1", inventory=5)
    change = InventoryChange(supplier_sku="sku-1", current_inventory=5, target_inventory=9, delta=4, change_type="increase")
    plan = InventorySyncPlan(supplier_sku="sku-1", shopify_variant_id="variant-1", current_inventory=5, target_inventory=9, change_type="increase", priority=70, requires_sync=True)
    record = InventorySyncRecord(supplier_sku="sku-1", shopify_variant_id="variant-1", old_inventory=5, new_inventory=9, change_type="increase", status="synced")
    report = InventorySyncReport(products_processed=1, successful_syncs=1, mode="mock")
    batch = InventorySyncBatchResult(plans=[plan], records=[record], report=report)
    assert supplier.inventory == 9
    assert shopify.shopify_variant_id == "variant-1"
    assert change.change_type == "increase"
    assert batch.plans[0].requires_sync is True


def test_price_sync_contracts_are_available():
    supplier_cost = SupplierCost(supplier_sku="sku-1", cost=10)
    shipping_cost = ShippingCost(supplier_sku="sku-1", cost=3)
    warehouse_cost = WarehouseCost(supplier_sku="sku-1", cost=1)
    platform_cost = PlatformCost(supplier_sku="sku-1", cost=2)
    competitor = CompetitorPriceData(supplier_sku="sku-1", competitor_low=20, competitor_avg=24, competitor_high=28)
    state = ShopifyPriceState(supplier_sku="sku-1", shopify_variant_id="variant-1", current_price=25)
    calculation = PriceCalculation(supplier_sku="sku-1", true_cost=16, break_even_price=16, minimum_safe_price=20, recommended_price=26.67)
    health = PriceHealthScore(supplier_sku="sku-1", score=82)
    decision = PricingDecision(supplier_sku="sku-1", decision="increase_price", old_price=20, new_price=26)
    record = PriceSyncRecord(supplier_sku="sku-1", variant_id="variant-1", old_price=20, new_price=26, decision="increase_price")
    report = PriceSyncReport(products_processed=1, successful_syncs=1, mode="mock")
    batch = PriceSyncBatchResult(decisions=[decision], records=[record], report=report)
    command = PriceSyncCommand(
        supplier_costs=[supplier_cost],
        shipping_costs=[shipping_cost],
        warehouse_costs=[warehouse_cost],
        platform_costs=[platform_cost],
        shopify_price_states=[state],
        competitor_prices=[competitor],
    )
    assert command.supplier_costs[0].cost == 10
    assert calculation.minimum_safe_price == 20
    assert health.score == 82
    assert batch.records[0].decision == "increase_price"


def test_risk_control_contracts_are_available():
    event = RiskEvent(risk_type="inventory_risk", risk_level="high", supplier_sku="sku-1", description="Inventory drift detected.")
    alert = event.model_dump()
    score = RiskScore(supplier_sku="sku-1", risk_type="inventory_risk", risk_score=72, risk_level="high")
    queue_item = ApprovalQueueItem(supplier_sku="sku-1", trigger_type="inventory_risk", risk_level="high", reason="Inventory dropped to zero.")
    blocked = BlockedProduct(supplier_sku="sku-1", risk_type="compliance_risk", reason="Restricted brand")
    supplier_risk = SupplierRiskScore(supplier_id="sup-1", overall_score=55, health_classification="risky")
    summary = RiskHealthSummary(total_events=1, high_count=1)
    report = RiskReport(health_summary=summary)
    command = RiskControlCommand()
    batch = RiskBatchResult(risk_events=[event], risk_scores=[score], approval_queue=[queue_item], blocked_products=[blocked], supplier_risk_scores=[supplier_risk], risk_report=report)
    assert alert["risk_type"] == "inventory_risk"
    assert score.risk_level == "high"
    assert command.supplier_products == []
    assert batch.blocked_products[0].supplier_sku == "sku-1"
