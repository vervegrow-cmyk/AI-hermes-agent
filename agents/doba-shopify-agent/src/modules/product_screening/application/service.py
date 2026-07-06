from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from src.modules.product_screening.domain.policy import get_screening_config
from src.modules.product_screening.infrastructure.deepseek_scoring_service import (
    ProductScoringService,
    build_deepseek_prompt,
    get_product_scoring_service,
)
from src.shared.contracts.screening import (
    CandidatePoolBatchResult,
    DeepSeekScoreRequest,
    ListingCandidate,
    ProductScore,
    ProductScoreBatchResult,
    RuleEngineBatchResult,
    RuleEngineResult,
    ScreenProductCommand,
    ScreeningDecision,
)
from src.shared.contracts.supplier_archive import ScreeningInput
from src.shared.repositories.protocols import ProductScreeningRepository


DANGEROUS_CATEGORY_TOKENS = {
    "weapons",
    "firearms",
    "ammunition",
    "explosives",
    "adult products",
    "illegal products",
    "regulated products",
}
RULE_REPORT_PATH = Path("docs/audits/product-screening-rule-engine-report.md")
DEEPSEEK_REPORT_PATH = Path("docs/audits/deepseek-product-scoring-report.md")
CANDIDATE_POOL_REPORT_PATH = Path("docs/audits/candidate-pool-report.md")


def screen_product(command: ScreenProductCommand) -> ScreeningDecision:
    config = get_screening_config()
    normalized = command.normalized_product
    reasons: list[str] = []

    if not normalized.product_id and not normalized.sku:
        reasons.append("Missing stable supplier identifier or SKU.")
    if not normalized.title:
        reasons.append("Missing title.")
    if normalized.cost <= 0:
        reasons.append("Missing supplier cost or zero cost.")
    if normalized.inventory < config.min_inventory:
        reasons.append(f"Inventory below minimum threshold of {config.min_inventory}.")
    if not normalized.image_urls:
        reasons.append("Missing main image.")
    if normalized.supplier_status in {"inactive", "discontinued", "backordered"}:
        reasons.append(f"Supplier status is not eligible: {normalized.supplier_status}.")
    if command.target_market.upper() not in normalized.ships_to_countries:
        reasons.append(f"Product cannot ship to target market {command.target_market.upper()}.")
    if normalized.ship_from_country and normalized.ship_from_country not in config.allowed_ship_from_countries:
        reasons.append(f"Ship-from country {normalized.ship_from_country} is outside the allowed set.")
    if not normalized.description and len(normalized.attributes) < 2:
        reasons.append("Not enough product content to build a Shopify listing.")

    expected_profit = round(
        normalized.target_sale_price
        - normalized.cost
        - normalized.shipping_cost
        - config.shopify_fee_buffer
        - config.ad_buffer,
        2,
    )
    margin_rate = round(expected_profit / normalized.target_sale_price, 4) if normalized.target_sale_price else 0
    shipping_ratio = round(normalized.shipping_cost / normalized.target_sale_price, 4) if normalized.target_sale_price else 0

    risk_result = command.risk_assessment
    if risk_result and risk_result.blocked:
        reasons.extend(risk_result.reasons)

    if reasons:
        return ScreeningDecision(
            status="rejected",
            product_id=normalized.product_id,
            sku=normalized.sku,
            normalized_title=normalized.normalized_title,
            target_market=command.target_market.upper(),
            reasons=reasons,
            expected_profit=expected_profit,
            margin_rate=margin_rate,
            shipping_ratio=shipping_ratio,
            score=0,
            normalized_product=normalized,
            risk_assessment=risk_result,
        )

    review_reasons: list[str] = []
    if expected_profit < config.min_margin_dollars:
        review_reasons.append("Expected profit is below target threshold.")
    if margin_rate < config.min_margin_rate:
        review_reasons.append("Margin rate is below target threshold.")
    if shipping_ratio > config.max_shipping_ratio:
        review_reasons.append("Shipping ratio is above target threshold.")
    if normalized.delivery_days > config.max_delivery_days:
        review_reasons.append("Delivery time exceeds automatic approval SLA.")
    if len(normalized.image_urls) < 2:
        review_reasons.append("Only one usable image is available.")
    if risk_result and risk_result.review_required:
        review_reasons.extend(risk_result.reasons)

    quality_score = 100.0
    quality_score -= max(0, (config.min_margin_dollars - expected_profit) * 2)
    quality_score -= max(0, (config.min_margin_rate - margin_rate) * 100)
    quality_score -= max(0, (shipping_ratio - config.max_shipping_ratio) * 120)
    quality_score -= 8 if len(normalized.image_urls) < 2 else 0
    quality_score -= 10 if normalized.delivery_days > config.max_delivery_days else 0
    quality_score -= 12 if risk_result and risk_result.review_required else 0

    status = "approved" if not review_reasons else "manual_review"
    return ScreeningDecision(
        status=status,
        product_id=normalized.product_id,
        sku=normalized.sku,
        normalized_title=normalized.normalized_title,
        target_market=command.target_market.upper(),
        reasons=review_reasons or ["Product passed hard filters and meets auto-approval thresholds."],
        expected_profit=expected_profit,
        margin_rate=margin_rate,
        shipping_ratio=shipping_ratio,
        score=round(max(0, min(100, quality_score)), 2),
        normalized_product=normalized,
        risk_assessment=risk_result,
    )


def _evaluate_rules(screening_input: ScreeningInput) -> RuleEngineResult:
    passed_rules: list[str] = []
    failed_rules: list[str] = []
    reason_codes: list[str] = []

    if screening_input.inventory >= 10:
        passed_rules.append("inventory_minimum")
    else:
        failed_rules.append("inventory_minimum")
        reason_codes.append("inventory_below_minimum")

    seller_rating = float(screening_input.seller_rating or 0)
    if seller_rating >= 3.5:
        passed_rules.append("seller_rating_minimum")
    elif seller_rating > 0:
        failed_rules.append("seller_rating_minimum")
        reason_codes.append("seller_rating_below_minimum")

    if screening_input.images_count >= 2:
        passed_rules.append("image_count_minimum")
    else:
        failed_rules.append("image_count_minimum")
        reason_codes.append("images_below_minimum")

    if screening_input.title.strip():
        passed_rules.append("title_present")
    else:
        failed_rules.append("title_present")
        reason_codes.append("title_missing")

    if screening_input.category.strip():
        passed_rules.append("category_present")
    else:
        failed_rules.append("category_present")
        reason_codes.append("category_missing")

    if screening_input.price > 0:
        passed_rules.append("price_valid")
    else:
        failed_rules.append("price_valid")
        reason_codes.append("price_invalid")

    normalized_category = screening_input.category.strip().lower()
    if not any(token in normalized_category for token in DANGEROUS_CATEGORY_TOKENS):
        passed_rules.append("dangerous_category_check")
    else:
        failed_rules.append("dangerous_category_check")
        reason_codes.append("dangerous_category_rejected")

    if screening_input.shipping_cost <= screening_input.price:
        passed_rules.append("shipping_cost_check")
    else:
        failed_rules.append("shipping_cost_check")
        reason_codes.append("shipping_cost_exceeds_price")

    manual_review_reasons: list[str] = []
    if seller_rating <= 0:
        failed_rules.append("seller_rating_present")
        manual_review_reasons.append("seller_rating_missing")
    else:
        passed_rules.append("seller_rating_present")

    if screening_input.warehouse.strip():
        passed_rules.append("warehouse_present")
    else:
        failed_rules.append("warehouse_present")
        manual_review_reasons.append("warehouse_missing")

    if screening_input.review_count > 0:
        passed_rules.append("review_count_present")
    else:
        failed_rules.append("review_count_present")
        manual_review_reasons.append("review_count_zero")

    reject_reason_codes = [
        code
        for code in reason_codes
        if code
        in {
            "inventory_below_minimum",
            "seller_rating_below_minimum",
            "images_below_minimum",
            "title_missing",
            "category_missing",
            "price_invalid",
            "dangerous_category_rejected",
            "shipping_cost_exceeds_price",
        }
    ]
    if reject_reason_codes:
        status = "rejected"
        final_reason_codes = reject_reason_codes + manual_review_reasons
    elif manual_review_reasons:
        status = "manual_review"
        final_reason_codes = manual_review_reasons
    else:
        status = "passed"
        final_reason_codes = []

    return RuleEngineResult(
        supplier_sku=screening_input.supplier_sku,
        status=status,
        reason_codes=final_reason_codes,
        passed_rules=passed_rules,
        failed_rules=failed_rules,
    )


def _build_rule_report(result: RuleEngineBatchResult) -> str:
    lines = [
        "# Product Screening Rule Engine Report",
        "",
        "## Summary",
        f"- Total products processed: `{result.total_products}`",
        f"- Passed products: `{result.passed_products}`",
        f"- Manual review products: `{result.manual_review_products}`",
        f"- Rejected products: `{result.rejected_products}`",
        "",
        "## Top Rejection Reasons",
    ]
    if result.top_rejection_reasons:
        lines.extend(
            f"- `{reason}`: `{count}`"
            for reason, count in sorted(
                result.top_rejection_reasons.items(),
                key=lambda item: (-item[1], item[0]),
            )
        )
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def _write_rule_report(result: RuleEngineBatchResult) -> str:
    RULE_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RULE_REPORT_PATH.write_text(_build_rule_report(result), encoding="utf-8")
    return str(RULE_REPORT_PATH.resolve())


def run_rule_engine(
    screening_inputs: list[ScreeningInput],
    repository: ProductScreeningRepository,
) -> RuleEngineBatchResult:
    rejection_counter: Counter[str] = Counter()
    results: list[RuleEngineResult] = []
    pre_filtered_products: list[ScreeningInput] = []

    for screening_input in screening_inputs:
        result = _evaluate_rules(screening_input)
        repository.save_rule_engine_result(result)
        results.append(result)
        if result.status in {"passed", "manual_review"}:
            repository.save_pre_filtered_product(screening_input)
            pre_filtered_products.append(screening_input)
        if result.status == "rejected":
            rejection_counter.update(
                reason
                for reason in result.reason_codes
                if reason not in {"warehouse_missing", "review_count_zero"}
            )

    batch = RuleEngineBatchResult(
        total_products=len(screening_inputs),
        passed_products=sum(1 for item in results if item.status == "passed"),
        manual_review_products=sum(1 for item in results if item.status == "manual_review"),
        rejected_products=sum(1 for item in results if item.status == "rejected"),
        rule_engine_results=results,
        pre_filtered_products=pre_filtered_products,
        top_rejection_reasons=dict(rejection_counter.most_common()),
    )
    batch.report_path = _write_rule_report(batch)
    return batch


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def calculate_overall_score(score) -> float:
    weighted = (
        score.trend_score * 0.20
        + score.season_score * 0.10
        + score.profit_score * 0.20
        + score.price_score * 0.10
        + score.inventory_score * 0.10
        + score.seller_score * 0.10
        + score.fulfillment_score * 0.05
        + score.review_score * 0.05
        + score.shipping_score * 0.05
        + (100 - score.return_risk_score) * 0.03
        + (100 - score.compliance_risk_score) * 0.02
    )
    return round(max(0, min(100, weighted)), 2)


def _build_product_score(request: DeepSeekScoreRequest, score_response, *, model_name: str) -> ProductScore:
    return ProductScore(
        supplier_sku=request.product.supplier_sku,
        model_name=model_name,
        scored_at=_now_iso(),
        trend_score=score_response.trend_score,
        season_score=score_response.season_score,
        profit_score=score_response.profit_score,
        price_score=score_response.price_score,
        inventory_score=score_response.inventory_score,
        seller_score=score_response.seller_score,
        fulfillment_score=score_response.fulfillment_score,
        review_score=score_response.review_score,
        shipping_score=score_response.shipping_score,
        return_risk_score=score_response.return_risk_score,
        compliance_risk_score=score_response.compliance_risk_score,
        overall_score=0,
        reasoning=score_response.reasoning,
        risk_notes=list(score_response.risk_notes),
        input_source="pre_filtered_products",
        fallback_reason=score_response.fallback_reason,
    )


def _build_deepseek_report(result: ProductScoreBatchResult) -> str:
    lines = [
        "# DeepSeek Product Scoring Report",
        "",
        "## Summary",
        f"- Total pre_filtered_products processed: `{result.total_pre_filtered_products}`",
        f"- Total scored products: `{result.total_scored_products}`",
        f"- Scoring mode: `{result.scoring_mode}`",
        f"- Average overall_score: `{result.average_overall_score}`",
        f"- Fallback count: `{result.fallback_count}`",
        f"- No listing_candidates created: `{str(result.no_listing_candidates_created).lower()}`",
        "",
        "## Top Scoring Products",
    ]
    if result.top_scoring_products:
        lines.extend(
            f"- `{item.supplier_sku}` overall=`{item.overall_score}` model=`{item.model_name}`"
            for item in result.top_scoring_products
        )
    else:
        lines.append("- None")
    lines.extend(["", "## High Return Risk Products"])
    if result.high_return_risk_products:
        lines.extend(
            f"- `{item.supplier_sku}` return_risk=`{item.return_risk_score}` overall=`{item.overall_score}`"
            for item in result.high_return_risk_products
        )
    else:
        lines.append("- None")
    lines.extend(["", "## High Compliance Risk Products"])
    if result.high_compliance_risk_products:
        lines.extend(
            f"- `{item.supplier_sku}` compliance_risk=`{item.compliance_risk_score}` overall=`{item.overall_score}`"
            for item in result.high_compliance_risk_products
        )
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def _write_deepseek_report(result: ProductScoreBatchResult) -> str:
    DEEPSEEK_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    DEEPSEEK_REPORT_PATH.write_text(_build_deepseek_report(result), encoding="utf-8")
    return str(DEEPSEEK_REPORT_PATH.resolve())


def run_deepseek_scoring(
    pre_filtered_products: list[ScreeningInput],
    repository: ProductScreeningRepository,
    scoring_service: ProductScoringService | None = None,
) -> ProductScoreBatchResult:
    service = scoring_service or get_product_scoring_service()
    scores: list[ProductScore] = []
    fallback_count = 0

    for product in pre_filtered_products:
        request = DeepSeekScoreRequest(product=product, prompt=build_deepseek_prompt(product))
        score_response = service.score(request)
        score = _build_product_score(request, score_response, model_name=service.model_name)
        score.overall_score = calculate_overall_score(score)
        repository.save_ai_product_score(score)
        scores.append(score)
        if score.fallback_reason:
            fallback_count += 1

    average_overall_score = round(
        sum(item.overall_score for item in scores) / len(scores),
        2,
    ) if scores else 0
    batch = ProductScoreBatchResult(
        total_pre_filtered_products=len(pre_filtered_products),
        total_scored_products=len(scores),
        scoring_mode=service.mode,
        average_overall_score=average_overall_score,
        top_scoring_products=sorted(scores, key=lambda item: item.overall_score, reverse=True)[:5],
        high_return_risk_products=[item for item in scores if item.return_risk_score >= 70],
        high_compliance_risk_products=[item for item in scores if item.compliance_risk_score >= 70],
        fallback_count=fallback_count,
        no_listing_candidates_created=True,
        ai_product_scores=scores,
    )
    repository.save_product_score_batch_result(batch)
    batch.report_path = _write_deepseek_report(batch)
    return batch


def _score_snapshot(score: ProductScore) -> dict[str, int | float | str | list[str]]:
    return {
        "trend_score": score.trend_score,
        "season_score": score.season_score,
        "profit_score": score.profit_score,
        "price_score": score.price_score,
        "inventory_score": score.inventory_score,
        "seller_score": score.seller_score,
        "fulfillment_score": score.fulfillment_score,
        "review_score": score.review_score,
        "shipping_score": score.shipping_score,
        "return_risk_score": score.return_risk_score,
        "compliance_risk_score": score.compliance_risk_score,
        "overall_score": score.overall_score,
        "risk_notes": list(score.risk_notes),
        "reasoning": score.reasoning,
    }


def _has_no_critical_risk(score: ProductScore) -> bool:
    return score.compliance_risk_score <= 40 and score.return_risk_score <= 50


def _build_listing_candidate(score: ProductScore):
    reason_codes: list[str] = []

    reject_reasons: list[str] = []
    if score.overall_score < 60:
        reject_reasons.append("rejected_low_overall_score")
    if score.compliance_risk_score > 60:
        reject_reasons.append("rejected_high_compliance_risk")
    if score.profit_score < 50:
        reject_reasons.append("rejected_low_profit_score")
    if score.return_risk_score > 70:
        reject_reasons.append("rejected_high_return_risk")
    if reject_reasons:
        return {
            "status": "rejected",
            "reason_codes": reject_reasons,
        }

    approved_reasons: list[str] = []
    is_approved = all(
        [
            score.overall_score >= 80,
            score.profit_score >= 70,
            score.inventory_score >= 60,
            score.seller_score >= 60,
            score.compliance_risk_score <= 40,
            score.return_risk_score <= 50,
        ]
    )
    if is_approved:
        approved_reasons.extend(
            [
                "approved_high_overall_score",
                "approved_profit_ok",
                "approved_inventory_ok",
            ]
        )
        return {
            "status": "approved_for_listing",
            "reason_codes": approved_reasons,
        }

    watchlist_reasons: list[str] = []
    watchlist_triggered = False
    explicit_watchlist_override = False
    if score.trend_score >= 80 and score.overall_score >= 55 and score.inventory_score < 60:
        watchlist_reasons.append("watchlist_high_trend_low_inventory")
        watchlist_triggered = True
    if score.season_score >= 80 and score.overall_score < 80:
        watchlist_reasons.append("watchlist_seasonal_opportunity")
        watchlist_triggered = True
    if score.trend_score >= 90 and _has_no_critical_risk(score):
        watchlist_reasons.append("watchlist_high_trend_low_inventory")
        watchlist_triggered = True
        explicit_watchlist_override = True

    manual_review_reasons: list[str] = []
    if 60 <= score.overall_score < 80:
        manual_review_reasons.append("manual_review_mid_score")
    if score.seller_score < 60:
        manual_review_reasons.append("manual_review_low_seller_score")
    if score.fulfillment_score < 60:
        manual_review_reasons.append("manual_review_low_fulfillment_score")
    if score.review_score < 50:
        manual_review_reasons.append("manual_review_low_review_score")

    if manual_review_reasons and not explicit_watchlist_override:
        return {
            "status": "manual_review",
            "reason_codes": manual_review_reasons,
        }

    if watchlist_triggered:
        return {
            "status": "watchlist",
            "reason_codes": watchlist_reasons or ["watchlist_seasonal_opportunity"],
        }

    return {
        "status": "manual_review",
        "reason_codes": ["default_manual_review"],
    }


def _build_candidate_pool_report(result: CandidatePoolBatchResult) -> str:
    lines = [
        "# Candidate Pool Report",
        "",
        "## Summary",
        f"- Total scored products processed: `{result.total_scored_products_processed}`",
        f"- Approved for listing count: `{result.approved_for_listing_count}`",
        f"- Manual review count: `{result.manual_review_count}`",
        f"- Watchlist count: `{result.watchlist_count}`",
        f"- Rejected count: `{result.rejected_count}`",
        "",
        "## Top Approved Products",
    ]
    if result.top_approved_products:
        lines.extend(
            f"- `{candidate.supplier_sku}` overall=`{candidate.overall_score}`"
            for candidate in result.top_approved_products
        )
    else:
        lines.append("- None")
    lines.extend(["", "## Top Rejection Reasons"])
    if result.top_rejection_reasons:
        lines.extend(
            f"- `{reason}`: `{count}`"
            for reason, count in sorted(result.top_rejection_reasons.items(), key=lambda item: (-item[1], item[0]))
        )
    else:
        lines.append("- None")
    lines.extend(["", "## Average Score By Status"])
    if result.average_score_by_status:
        lines.extend(
            f"- `{status}`: `{score}`"
            for status, score in sorted(result.average_score_by_status.items())
        )
    else:
        lines.append("- None")
    lines.extend(["", "## Candidate Status Distribution"])
    lines.extend(
        f"- `{status}`: `{count}`"
        for status, count in sorted(result.candidate_status_distribution.items())
    )
    lines.extend(
        [
            "",
            "## Safety Checks",
            f"- No Shopify writes occurred: `{str(result.no_shopify_writes_occurred).lower()}`",
            f"- No DeepSeek call occurred: `{str(result.no_deepseek_call_occurred).lower()}`",
            f"- No Doba API call occurred: `{str(result.no_doba_api_call_occurred).lower()}`",
            f"- No inventory sync occurred: `{str(result.no_inventory_sync_occurred).lower()}`",
            f"- No price sync occurred: `{str(result.no_price_sync_occurred).lower()}`",
            f"- No governance implementation occurred: `{str(result.no_governance_implementation_occurred).lower()}`",
        ]
    )
    return "\n".join(lines) + "\n"


def _write_candidate_pool_report(result: CandidatePoolBatchResult) -> str:
    CANDIDATE_POOL_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    CANDIDATE_POOL_REPORT_PATH.write_text(_build_candidate_pool_report(result), encoding="utf-8")
    return str(CANDIDATE_POOL_REPORT_PATH.resolve())


def run_candidate_pool(
    ai_product_scores: list[ProductScore],
    repository: ProductScreeningRepository,
) -> CandidatePoolBatchResult:
    candidates = []
    rejection_counter: Counter[str] = Counter()
    scores_by_status: dict[str, list[float]] = {
        "approved_for_listing": [],
        "manual_review": [],
        "watchlist": [],
        "rejected": [],
    }

    for score in ai_product_scores:
        decision = _build_listing_candidate(score)
        candidate = ListingCandidate(
            supplier_sku=score.supplier_sku,
            status=decision["status"],
            overall_score=score.overall_score,
            reason_codes=decision["reason_codes"],
            score_snapshot=_score_snapshot(score),
            created_at=_now_iso(),
            source="ai_product_scores",
        )
        repository.save_listing_candidate(candidate)
        candidates.append(candidate)
        scores_by_status[candidate.status].append(candidate.overall_score)
        if candidate.status == "rejected":
            rejection_counter.update(candidate.reason_codes)

    status_distribution = Counter(candidate.status for candidate in candidates)
    average_score_by_status = {
        status: round(sum(values) / len(values), 2)
        for status, values in scores_by_status.items()
        if values
    }
    batch = CandidatePoolBatchResult(
        total_scored_products_processed=len(ai_product_scores),
        approved_for_listing_count=status_distribution.get("approved_for_listing", 0),
        manual_review_count=status_distribution.get("manual_review", 0),
        watchlist_count=status_distribution.get("watchlist", 0),
        rejected_count=status_distribution.get("rejected", 0),
        top_approved_products=sorted(
            [candidate for candidate in candidates if candidate.status == "approved_for_listing"],
            key=lambda candidate: candidate.overall_score,
            reverse=True,
        )[:5],
        top_rejection_reasons=dict(rejection_counter.most_common()),
        average_score_by_status=average_score_by_status,
        candidate_status_distribution=dict(status_distribution),
        listing_candidates=candidates,
    )
    repository.save_candidate_pool_batch_result(batch)
    batch.report_path = _write_candidate_pool_report(batch)
    return batch
