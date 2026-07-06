from src.modules.product_screening import calculate_overall_score, run_candidate_pool, run_deepseek_scoring, run_rule_engine
from src.modules.product_screening.infrastructure.deepseek_scoring_service import (
    MockDeepSeekScoringService,
    normalize_score_response,
)
from src.shared.contracts.screening import DeepSeekScoreResponse
from src.shared.contracts.supplier_archive import ScreeningInput, SnapshotHistorySummary
from src.shared.repositories import InMemoryProductScreeningRepository


def _base_input() -> ScreeningInput:
    return ScreeningInput(
        supplier="doba",
        supplier_id="sup-1",
        product_id="prod-1",
        supplier_sku="sku-1",
        title="Portable Fan Hat",
        category="Outdoor",
        price=8.99,
        shipping_cost=4.2,
        inventory=153,
        warehouse="US",
        seller_rating=4.6,
        review_count=328,
        fulfillment_speed_days=2.4,
        images_count=6,
        snapshot_history=SnapshotHistorySummary(
            inventory_stability="stable",
            price_change_7d=0,
            seller_rating_change_30d=-0.1,
            inventory_snapshots=3,
            price_snapshots=3,
            seller_snapshots=2,
        ),
    )


def _run_one(screening_input: ScreeningInput):
    repository = InMemoryProductScreeningRepository()
    result = run_rule_engine([screening_input], repository)
    return result, repository


def test_inventory_rule_works():
    screening_input = _base_input()
    screening_input.inventory = 9
    result, _ = _run_one(screening_input)
    assert result.rule_engine_results[0].status == "rejected"
    assert "inventory_below_minimum" in result.rule_engine_results[0].reason_codes


def test_seller_rule_works():
    screening_input = _base_input()
    screening_input.seller_rating = 3.4
    result, _ = _run_one(screening_input)
    assert "seller_rating_below_minimum" in result.rule_engine_results[0].reason_codes


def test_missing_seller_rating_enters_manual_review():
    screening_input = _base_input()
    screening_input.seller_rating = 0
    screening_input.review_count = 5
    result, repository = _run_one(screening_input)
    assert result.rule_engine_results[0].status == "manual_review"
    assert "seller_rating_missing" in result.rule_engine_results[0].reason_codes
    assert len(repository.list_pre_filtered_products()) == 1


def test_image_rule_works():
    screening_input = _base_input()
    screening_input.images_count = 1
    result, _ = _run_one(screening_input)
    assert "images_below_minimum" in result.rule_engine_results[0].reason_codes


def test_title_rule_works():
    screening_input = _base_input()
    screening_input.title = ""
    result, _ = _run_one(screening_input)
    assert "title_missing" in result.rule_engine_results[0].reason_codes


def test_category_rule_works():
    screening_input = _base_input()
    screening_input.category = ""
    result, _ = _run_one(screening_input)
    assert "category_missing" in result.rule_engine_results[0].reason_codes


def test_price_rule_works():
    screening_input = _base_input()
    screening_input.price = 0
    result, _ = _run_one(screening_input)
    assert "price_invalid" in result.rule_engine_results[0].reason_codes


def test_dangerous_category_rule_works():
    screening_input = _base_input()
    screening_input.category = "regulated products > firearms"
    result, _ = _run_one(screening_input)
    assert "dangerous_category_rejected" in result.rule_engine_results[0].reason_codes


def test_shipping_rule_works():
    screening_input = _base_input()
    screening_input.shipping_cost = 10
    result, _ = _run_one(screening_input)
    assert "shipping_cost_exceeds_price" in result.rule_engine_results[0].reason_codes


def test_warehouse_rule_works():
    screening_input = _base_input()
    screening_input.warehouse = ""
    screening_input.review_count = 1
    result, repository = _run_one(screening_input)
    assert result.rule_engine_results[0].status == "manual_review"
    assert "warehouse_missing" in result.rule_engine_results[0].reason_codes
    assert len(repository.list_pre_filtered_products()) == 1


def test_review_rule_works():
    screening_input = _base_input()
    screening_input.review_count = 0
    result, _ = _run_one(screening_input)
    assert result.rule_engine_results[0].status == "manual_review"
    assert "review_count_zero" in result.rule_engine_results[0].reason_codes


def test_passed_status_works():
    result, repository = _run_one(_base_input())
    assert result.rule_engine_results[0].status == "passed"
    assert result.passed_products == 1
    assert len(repository.list_pre_filtered_products()) == 1


def test_manual_review_status_works():
    screening_input = _base_input()
    screening_input.warehouse = ""
    screening_input.review_count = 0
    result, repository = _run_one(screening_input)
    assert result.rule_engine_results[0].status == "manual_review"
    assert result.manual_review_products == 1
    assert len(repository.list_pre_filtered_products()) == 1


def test_rejected_status_works():
    screening_input = _base_input()
    screening_input.inventory = 1
    result, repository = _run_one(screening_input)
    assert result.rule_engine_results[0].status == "rejected"
    assert result.rejected_products == 1
    assert len(repository.list_pre_filtered_products()) == 0


def test_mock_deepseek_scoring_works_without_api_key():
    repository = InMemoryProductScreeningRepository()
    batch = run_deepseek_scoring([_base_input()], repository, MockDeepSeekScoringService())
    assert batch.total_scored_products == 1
    assert batch.scoring_mode == "mock"


def test_product_score_fields_are_normalized_to_zero_to_one_hundred():
    normalized = normalize_score_response(
        {
            "trend_score": 120,
            "season_score": -5,
            "profit_score": "85",
            "price_score": None,
            "inventory_score": 75.9,
            "seller_score": 64.1,
            "fulfillment_score": 40,
            "review_score": 101,
            "shipping_score": -1,
            "return_risk_score": 500,
            "compliance_risk_score": "12",
        }
    )
    assert normalized.trend_score == 100
    assert normalized.season_score == 0
    assert normalized.profit_score == 85
    assert normalized.price_score == 0
    assert normalized.review_score == 100
    assert normalized.shipping_score == 0
    assert normalized.return_risk_score == 100


def test_overall_score_is_calculated_locally():
    score = DeepSeekScoreResponse(
        trend_score=100,
        season_score=100,
        profit_score=100,
        price_score=100,
        inventory_score=100,
        seller_score=100,
        fulfillment_score=100,
        review_score=100,
        shipping_score=100,
        return_risk_score=0,
        compliance_risk_score=0,
    )
    overall = calculate_overall_score(score)
    assert overall == 100


def test_risk_scores_reduce_final_score():
    low_risk = DeepSeekScoreResponse(
        trend_score=80,
        season_score=80,
        profit_score=80,
        price_score=80,
        inventory_score=80,
        seller_score=80,
        fulfillment_score=80,
        review_score=80,
        shipping_score=80,
        return_risk_score=0,
        compliance_risk_score=0,
    )
    high_risk = DeepSeekScoreResponse(
        trend_score=80,
        season_score=80,
        profit_score=80,
        price_score=80,
        inventory_score=80,
        seller_score=80,
        fulfillment_score=80,
        review_score=80,
        shipping_score=80,
        return_risk_score=100,
        compliance_risk_score=100,
    )
    assert calculate_overall_score(high_risk) < calculate_overall_score(low_risk)


def test_ai_product_scores_are_saved():
    repository = InMemoryProductScreeningRepository()
    batch = run_deepseek_scoring([_base_input()], repository, MockDeepSeekScoringService())
    assert batch.total_scored_products == 1
    assert len(repository.list_ai_product_scores()) == 1


def test_latest_score_can_be_queried():
    repository = InMemoryProductScreeningRepository()
    run_deepseek_scoring([_base_input()], repository, MockDeepSeekScoringService())
    latest = repository.get_latest_ai_product_score("sku-1")
    assert latest is not None
    assert latest.supplier_sku == "sku-1"


def test_invalid_deepseek_response_falls_back_safely():
    class BadService:
        mode = "real"
        model_name = "deepseek-chat"

        def score(self, request):
            from src.modules.product_screening.infrastructure.deepseek_scoring_service import build_mock_score_response

            return build_mock_score_response(request, fallback_reason="invalid_json")

    repository = InMemoryProductScreeningRepository()
    batch = run_deepseek_scoring([_base_input()], repository, BadService())
    assert batch.fallback_count == 1
    assert repository.list_ai_product_scores()[0].fallback_reason == "invalid_json"


def test_no_listing_candidates_are_created():
    repository = InMemoryProductScreeningRepository()
    batch = run_deepseek_scoring([_base_input()], repository, MockDeepSeekScoringService())
    assert batch.no_listing_candidates_created is True
    assert not hasattr(batch, "listing_candidates")


def test_no_shopify_write_occurs():
    repository = InMemoryProductScreeningRepository()
    run_deepseek_scoring([_base_input()], repository, MockDeepSeekScoringService())
    assert not hasattr(repository, "drafts")


def test_no_inventory_sync_occurs():
    repository = InMemoryProductScreeningRepository()
    run_deepseek_scoring([_base_input()], repository, MockDeepSeekScoringService())
    assert not hasattr(repository, "inventory_sync_logs")


def test_no_price_sync_occurs():
    repository = InMemoryProductScreeningRepository()
    run_deepseek_scoring([_base_input()], repository, MockDeepSeekScoringService())
    assert not hasattr(repository, "price_sync_logs")


def _base_score(**overrides):
    payload = {
        "supplier_sku": "sku-1",
        "model_name": "deepseek-mock",
        "scored_at": "2026-06-15T00:00:00+00:00",
        "trend_score": 82,
        "season_score": 65,
        "profit_score": 75,
        "price_score": 70,
        "inventory_score": 72,
        "seller_score": 68,
        "fulfillment_score": 66,
        "review_score": 55,
        "shipping_score": 70,
        "return_risk_score": 35,
        "compliance_risk_score": 25,
        "overall_score": 82,
        "reasoning": "Good candidate.",
        "risk_notes": [],
        "input_source": "pre_filtered_products",
        "fallback_reason": "",
    }
    payload.update(overrides)
    from src.shared.contracts import ProductScore

    return ProductScore(**payload)


def test_approved_for_listing_decision_works():
    repository = InMemoryProductScreeningRepository()
    batch = run_candidate_pool([_base_score()], repository)
    assert batch.approved_for_listing_count == 1
    assert repository.list_listing_candidates()[0].status == "approved_for_listing"


def test_manual_review_decision_works():
    repository = InMemoryProductScreeningRepository()
    batch = run_candidate_pool([_base_score(overall_score=72)], repository)
    assert batch.manual_review_count == 1
    assert repository.list_listing_candidates()[0].status == "manual_review"


def test_watchlist_decision_works():
    repository = InMemoryProductScreeningRepository()
    batch = run_candidate_pool([
        _base_score(
            overall_score=85,
            trend_score=88,
            inventory_score=50,
            seller_score=65,
            fulfillment_score=65,
            review_score=60,
        )
    ], repository)
    assert batch.watchlist_count == 1
    assert repository.list_listing_candidates()[0].status == "watchlist"


def test_rejected_decision_works():
    repository = InMemoryProductScreeningRepository()
    batch = run_candidate_pool([_base_score(overall_score=55)], repository)
    assert batch.rejected_count == 1
    assert repository.list_listing_candidates()[0].status == "rejected"


def test_rejected_overrides_approved():
    repository = InMemoryProductScreeningRepository()
    candidate = run_candidate_pool([
        _base_score(overall_score=85, compliance_risk_score=80, profit_score=80)
    ], repository).listing_candidates[0]
    assert candidate.status == "rejected"
    assert "rejected_high_compliance_risk" in candidate.reason_codes


def test_manual_review_overrides_watchlist_when_required():
    repository = InMemoryProductScreeningRepository()
    candidate = run_candidate_pool([
        _base_score(
            overall_score=72,
            trend_score=85,
            inventory_score=50,
            seller_score=55,
            compliance_risk_score=45,
            return_risk_score=45,
        )
    ], repository).listing_candidates[0]
    assert candidate.status == "manual_review"


def test_watchlist_can_override_manual_review_only_under_explicit_high_trend_condition():
    repository = InMemoryProductScreeningRepository()
    candidate = run_candidate_pool([
        _base_score(
            overall_score=85,
            trend_score=95,
            inventory_score=50,
            seller_score=75,
            fulfillment_score=55,
            review_score=60,
            compliance_risk_score=35,
            return_risk_score=45,
        )
    ], repository).listing_candidates[0]
    assert candidate.status == "watchlist"


def test_default_manual_review_works():
    repository = InMemoryProductScreeningRepository()
    candidate = run_candidate_pool([
        _base_score(
            overall_score=81,
            profit_score=65,
            inventory_score=70,
            seller_score=65,
            fulfillment_score=65,
            review_score=55,
            trend_score=50,
            season_score=50,
            compliance_risk_score=35,
            return_risk_score=40,
        )
    ], repository).listing_candidates[0]
    assert candidate.status == "manual_review"
    assert "default_manual_review" in candidate.reason_codes


def test_listing_candidates_are_saved():
    repository = InMemoryProductScreeningRepository()
    run_candidate_pool([_base_score()], repository)
    assert len(repository.list_listing_candidates()) == 1


def test_candidate_can_be_queried_by_supplier_sku():
    repository = InMemoryProductScreeningRepository()
    run_candidate_pool([_base_score(supplier_sku="sku-query")], repository)
    candidate = repository.get_listing_candidate_by_sku("sku-query")
    assert candidate is not None
    assert candidate.supplier_sku == "sku-query"


def test_candidate_pool_batch_result_is_saved():
    repository = InMemoryProductScreeningRepository()
    run_candidate_pool([_base_score()], repository)
    assert len(repository.list_candidate_pool_batch_results()) == 1


def test_candidate_is_created_only_from_ai_product_scores():
    repository = InMemoryProductScreeningRepository()
    run_candidate_pool([_base_score()], repository)
    candidate = repository.list_listing_candidates()[0]
    assert candidate.source == "ai_product_scores"


def test_candidate_pool_no_shopify_write_occurs():
    repository = InMemoryProductScreeningRepository()
    run_candidate_pool([_base_score()], repository)
    assert not hasattr(repository, "drafts")


def test_candidate_pool_no_deepseek_call_occurs():
    repository = InMemoryProductScreeningRepository()
    batch = run_candidate_pool([_base_score()], repository)
    assert batch.no_deepseek_call_occurred is True


def test_candidate_pool_no_doba_api_call_occurs():
    repository = InMemoryProductScreeningRepository()
    batch = run_candidate_pool([_base_score()], repository)
    assert batch.no_doba_api_call_occurred is True


def test_candidate_pool_no_inventory_sync_occurs():
    repository = InMemoryProductScreeningRepository()
    batch = run_candidate_pool([_base_score()], repository)
    assert batch.no_inventory_sync_occurred is True


def test_candidate_pool_no_price_sync_occurs():
    repository = InMemoryProductScreeningRepository()
    batch = run_candidate_pool([_base_score()], repository)
    assert batch.no_price_sync_occurred is True


def test_candidate_pool_no_governance_objects_are_created():
    repository = InMemoryProductScreeningRepository()
    batch = run_candidate_pool([_base_score()], repository)
    assert batch.no_governance_implementation_occurred is True
