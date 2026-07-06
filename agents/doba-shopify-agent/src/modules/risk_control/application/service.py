from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from src.modules.risk_control.domain.policy import (
    MANUAL_REVIEW_KEYWORDS,
    RESTRICTED_KEYWORDS,
    get_risk_config,
)
from src.modules.risk_control.infrastructure.ai_scoring_service import score_product_risk
from src.shared.contracts.risk import (
    ApprovalQueueItem,
    BlockedProduct,
    RiskAlert,
    RiskAssessmentCommand,
    RiskAssessmentResult,
    RiskBatchResult,
    RiskControlCommand,
    RiskEvent,
    RiskHealthSummary,
    RiskReport,
    RiskScore,
    SupplierRiskScore,
)
from src.shared.repositories import (
    InMemoryApprovalQueueRepository,
    InMemoryBlockedProductRepository,
    InMemoryRiskAlertRepository,
    InMemoryRiskBatchRepository,
    InMemoryRiskEventRepository,
    InMemoryRiskReportRepository,
    InMemoryRiskScoreRepository,
    InMemorySupplierRiskRepository,
)
from src.shared.repositories.protocols import (
    ApprovalQueueRepository,
    BlockedProductRepository,
    RiskAlertRepository,
    RiskBatchRepository,
    RiskEventRepository,
    RiskReportRepository,
    RiskScoreRepository,
    SupplierArchiveRepository,
    SupplierRiskRepository,
)


REPORT_PATH = Path("docs/audits/risk-control-report.md")
BRAND_RISK_KEYWORDS = {"apple", "dyson", "nintendo", "lego", "disney"}
REGULATED_KEYWORDS = {"fda", "fcc", "medical", "children", "baby", "hazmat"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _normalize_text(value: str) -> str:
    return " ".join((value or "").lower().split())


def _days_since(value: str) -> int | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return max(0, (now - dt).days)


def _score_to_level(score: float) -> str:
    if score <= 30:
        return "low"
    if score <= 60:
        return "medium"
    if score <= 80:
        return "high"
    return "critical"


def _make_event(
    *,
    risk_type: str,
    score: float,
    supplier_sku: str = "",
    shopify_variant_id: str = "",
    affected_entity: str = "",
    description: str = "",
    supplier_id: str = "",
) -> RiskEvent:
    return RiskEvent(
        risk_type=risk_type,
        risk_level=_score_to_level(score),
        supplier_sku=supplier_sku,
        shopify_variant_id=shopify_variant_id,
        affected_entity=affected_entity or supplier_sku or supplier_id,
        description=description,
        created_at=_now_iso(),
        status="open",
        risk_score=round(score, 2),
        supplier_id=supplier_id,
    )


def assess_risk(command: RiskAssessmentCommand) -> RiskAssessmentResult:
    config = get_risk_config()
    normalized = command.normalized_product
    category_tokens = {token.upper() for token in normalized.category_tokens}
    text_tokens = f"{normalized.category_path} {normalized.title} {normalized.description} {normalized.brand}".lower()
    ai_score, ai_summary = score_product_risk(normalized)

    blocked_reasons: list[str] = []
    review_reasons: list[str] = []

    if category_tokens & config.restricted_categories:
        blocked_reasons.append("Product category is restricted for phase one.")
    if any(keyword in text_tokens for keyword in RESTRICTED_KEYWORDS):
        blocked_reasons.append("Product matches a restricted policy-risk keyword.")
    if any(keyword in text_tokens for keyword in MANUAL_REVIEW_KEYWORDS):
        review_reasons.append("Product has a borderline compliance keyword and should be reviewed.")
    if category_tokens & config.manual_review_categories:
        review_reasons.append("Category requires manual review in phase one.")
    if normalized.brand:
        review_reasons.append("Branded product requires resale-rights review.")
    if ai_score >= 0.75:
        blocked_reasons.append("AI risk scoring marked the product as high risk.")
    elif ai_score >= 0.35:
        review_reasons.append("AI risk scoring requires manual review.")

    if blocked_reasons:
        return RiskAssessmentResult(
            level="high",
            blocked=True,
            review_required=False,
            reasons=blocked_reasons,
            ai_score=ai_score,
            ai_summary=ai_summary,
        )
    if review_reasons:
        return RiskAssessmentResult(
            level="medium",
            blocked=False,
            review_required=True,
            reasons=review_reasons,
            ai_score=ai_score,
            ai_summary=ai_summary,
        )
    return RiskAssessmentResult(
        level="low",
        blocked=False,
        review_required=False,
        reasons=[],
        ai_score=ai_score,
        ai_summary=ai_summary,
    )


def _inventory_risks(command: RiskControlCommand) -> list[RiskEvent]:
    events: list[RiskEvent] = []
    for snapshot in command.inventory_snapshots:
        if snapshot.shopify_inventory > 0 and snapshot.supplier_inventory == 0:
            events.append(
                _make_event(
                    risk_type="inventory_risk",
                    score=92,
                    supplier_sku=snapshot.sku,
                    affected_entity=snapshot.sku,
                    description="Inventory dropped to zero unexpectedly.",
                    supplier_id=snapshot.supplier_id,
                )
            )
        elif snapshot.shopify_inventory and snapshot.supplier_inventory <= max(1, int(snapshot.shopify_inventory * 0.2)):
            events.append(
                _make_event(
                    risk_type="inventory_risk",
                    score=72,
                    supplier_sku=snapshot.sku,
                    affected_entity=snapshot.sku,
                    description="Inventory dropped by more than 80%.",
                    supplier_id=snapshot.supplier_id,
                )
            )
        elif abs(snapshot.shopify_inventory - snapshot.supplier_inventory) >= 20:
            events.append(
                _make_event(
                    risk_type="inventory_risk",
                    score=68,
                    supplier_sku=snapshot.sku,
                    affected_entity=snapshot.sku,
                    description="Inventory mismatch indicates drift between supplier and Shopify.",
                    supplier_id=snapshot.supplier_id,
                )
            )

    failures = Counter(record.supplier_sku for record in command.inventory_sync_logs if record.status in {"sync_failed", "missing_mapping"})
    for sku, count in failures.items():
        score = 85 if count >= 5 else 70 if count >= 3 else 55
        events.append(
            _make_event(
                risk_type="inventory_risk",
                score=score,
                supplier_sku=sku,
                affected_entity=sku,
                description=f"Inventory sync failed {count} times.",
            )
        )
    return events


def _price_and_profit_risks(command: RiskControlCommand) -> list[RiskEvent]:
    events: list[RiskEvent] = []
    previous_costs: dict[str, float] = {}
    for snapshot in command.price_snapshots:
        key = snapshot.sku.strip().lower()
        if key in previous_costs and previous_costs[key] > 0:
            increase = (snapshot.supplier_cost - previous_costs[key]) / previous_costs[key]
            if increase > 0.2:
                events.append(
                    _make_event(
                        risk_type="price_risk",
                        score=75,
                        supplier_sku=snapshot.sku,
                        affected_entity=snapshot.sku,
                        description="Supplier cost increased by more than 20%.",
                        supplier_id=snapshot.supplier_id,
                    )
                )
        previous_costs[key] = snapshot.supplier_cost

    for decision in command.pricing_decisions:
        if decision.old_price > 0:
            change_ratio = abs(decision.new_price - decision.old_price) / decision.old_price
        else:
            change_ratio = 0
        if change_ratio > 0.5:
            events.append(
                _make_event(
                    risk_type="price_risk",
                    score=82,
                    supplier_sku=decision.supplier_sku,
                    affected_entity=decision.supplier_sku,
                    description="Price anomaly exceeds 50% change.",
                )
            )
        margin_after = (decision.profit_after / decision.new_price) if decision.new_price else 0
        if margin_after < 0.05:
            events.append(
                _make_event(
                    risk_type="profit_risk",
                    score=95,
                    supplier_sku=decision.supplier_sku,
                    affected_entity=decision.supplier_sku,
                    description="Projected margin fell below 5%.",
                )
            )
        elif margin_after < 0.10:
            events.append(
                _make_event(
                    risk_type="profit_risk",
                    score=75,
                    supplier_sku=decision.supplier_sku,
                    affected_entity=decision.supplier_sku,
                    description="Projected margin fell below 10%.",
                )
            )
    return events


def _seller_risks(command: RiskControlCommand) -> list[RiskEvent]:
    events: list[RiskEvent] = []
    by_supplier: dict[str, list] = defaultdict(list)
    for snapshot in command.seller_snapshots:
        by_supplier[snapshot.supplier_id or snapshot.seller_name or "unknown"].append(snapshot)

    for supplier_id, snapshots in by_supplier.items():
        latest = snapshots[-1]
        score = None
        description = ""
        if latest.rating < 3.5:
            score = 92
            description = "Seller rating dropped below 3.5."
        elif latest.rating < 4.0:
            score = 72
            description = "Seller rating dropped below 4.0."
        elif len(snapshots) >= 2 and snapshots[-1].fulfillment_speed_days > snapshots[0].fulfillment_speed_days + 2:
            score = 66
            description = "Fulfillment performance deteriorated."
        if score is not None:
            events.append(
                _make_event(
                    risk_type="seller_risk",
                    score=score,
                    affected_entity=supplier_id,
                    description=description,
                    supplier_id=supplier_id,
                )
            )
    return events


def _compliance_risks(command: RiskControlCommand) -> list[RiskEvent]:
    events: list[RiskEvent] = []
    products_by_sku = {product.sku.strip().lower(): product for product in command.supplier_products}
    for candidate in command.listing_candidates:
        source = candidate.source_product or {}
        text = _normalize_text(
            " ".join(
                [
                    candidate.source_title,
                    candidate.source_description,
                    candidate.source_brand,
                    candidate.source_category,
                    str(source),
                ]
            )
        )
        sku = candidate.supplier_sku
        if any(keyword in text for keyword in BRAND_RISK_KEYWORDS):
            events.append(
                _make_event(
                    risk_type="compliance_risk",
                    score=90,
                    supplier_sku=sku,
                    affected_entity=sku,
                    description="Trademark or brand violation risk detected.",
                    supplier_id=(products_by_sku.get(sku.lower()).supplier_id if products_by_sku.get(sku.lower()) else ""),
                )
            )
        elif any(keyword in text for keyword in REGULATED_KEYWORDS) or any(keyword in text for keyword in RESTRICTED_KEYWORDS):
            events.append(
                _make_event(
                    risk_type="compliance_risk",
                    score=78,
                    supplier_sku=sku,
                    affected_entity=sku,
                    description="Restricted, medical, children, or hazmat compliance risk detected.",
                    supplier_id=(products_by_sku.get(sku.lower()).supplier_id if products_by_sku.get(sku.lower()) else ""),
                )
            )
    return events


def _supplier_risks(command: RiskControlCommand) -> tuple[list[RiskEvent], list[SupplierRiskScore]]:
    events: list[RiskEvent] = []
    scores: list[SupplierRiskScore] = []
    by_supplier_products: dict[str, list] = defaultdict(list)
    by_supplier_inventory: dict[str, list] = defaultdict(list)
    by_supplier_price: dict[str, list] = defaultdict(list)
    by_supplier_seller: dict[str, list] = defaultdict(list)

    for product in command.supplier_products:
        by_supplier_products[product.supplier_id or "unknown"].append(product)
    for snapshot in command.inventory_snapshots:
        by_supplier_inventory[snapshot.supplier_id or "unknown"].append(snapshot)
    for snapshot in command.price_snapshots:
        by_supplier_price[snapshot.supplier_id or "unknown"].append(snapshot)
    for snapshot in command.seller_snapshots:
        by_supplier_seller[snapshot.supplier_id or "unknown"].append(snapshot)

    all_supplier_ids = set(by_supplier_products) | set(by_supplier_inventory) | set(by_supplier_price) | set(by_supplier_seller)
    for supplier_id in all_supplier_ids:
        inventory_days = [_days_since(item.snapshot_at) for item in by_supplier_inventory.get(supplier_id, []) if _days_since(item.snapshot_at) is not None]
        latest_inventory_age = max(inventory_days) if inventory_days else 0
        price_values = [item.supplier_cost for item in by_supplier_price.get(supplier_id, [])]
        stability_score = 100 - min(80, latest_inventory_age * 5)
        pricing_consistency_score = 100
        if len(price_values) >= 2:
            base = min(price_values) or 1
            spread = (max(price_values) - min(price_values)) / base
            pricing_consistency_score = max(20, 100 - spread * 100)
        inventory_consistency_score = max(20, 100 - latest_inventory_age * 5)
        seller_snapshots = by_supplier_seller.get(supplier_id, [])
        latest_rating = seller_snapshots[-1].rating if seller_snapshots else 5.0
        fulfillment_quality_score = max(20, min(100, latest_rating * 20))
        overall = round((stability_score * 0.3) + (pricing_consistency_score * 0.25) + (inventory_consistency_score * 0.25) + (fulfillment_quality_score * 0.2), 2)
        if overall >= 80:
            health = "healthy"
        elif overall >= 60:
            health = "watch"
        elif overall >= 40:
            health = "risky"
        else:
            health = "critical"
        score = SupplierRiskScore(
            supplier_id=supplier_id,
            stability_score=round(stability_score, 2),
            pricing_consistency_score=round(pricing_consistency_score, 2),
            inventory_consistency_score=round(inventory_consistency_score, 2),
            fulfillment_quality_score=round(fulfillment_quality_score, 2),
            overall_score=overall,
            health_classification=health,
        )
        scores.append(score)
        if latest_inventory_age > 14:
            events.append(
                _make_event(
                    risk_type="supplier_risk",
                    score=92,
                    affected_entity=supplier_id,
                    description="Supplier has no inventory updates for more than 14 days.",
                    supplier_id=supplier_id,
                )
            )
        elif latest_inventory_age > 7:
            events.append(
                _make_event(
                    risk_type="supplier_risk",
                    score=72,
                    affected_entity=supplier_id,
                    description="Supplier has no inventory updates for more than 7 days.",
                    supplier_id=supplier_id,
                )
            )
        if health in {"risky", "critical"}:
            events.append(
                _make_event(
                    risk_type="supplier_risk",
                    score=85 if health == "critical" else 65,
                    affected_entity=supplier_id,
                    description=f"Supplier health classified as {health}.",
                    supplier_id=supplier_id,
                )
            )
    return events, scores


def _shopify_and_sync_risks(command: RiskControlCommand) -> list[RiskEvent]:
    events: list[RiskEvent] = []
    for record in command.inventory_sync_logs:
        if record.status == "missing_mapping":
            events.append(
                _make_event(
                    risk_type="shopify_risk",
                    score=62,
                    supplier_sku=record.supplier_sku,
                    shopify_variant_id=record.shopify_variant_id,
                    affected_entity=record.supplier_sku,
                    description="SKU mapping failure detected during inventory sync.",
                )
            )
        elif record.status == "sync_failed":
            events.append(
                _make_event(
                    risk_type="sync_risk",
                    score=70,
                    supplier_sku=record.supplier_sku,
                    shopify_variant_id=record.shopify_variant_id,
                    affected_entity=record.supplier_sku,
                    description=f"Inventory sync failed: {record.error_message or 'unknown error'}.",
                )
            )
    for record in command.price_sync_logs:
        if record.status == "missing_mapping":
            events.append(
                _make_event(
                    risk_type="shopify_risk",
                    score=62,
                    supplier_sku=record.supplier_sku,
                    shopify_variant_id=record.variant_id,
                    affected_entity=record.supplier_sku,
                    description="SKU mapping failure detected during price sync.",
                )
            )
        elif record.status == "sync_failed":
            lowered = (record.error_message or "").lower()
            score = 88 if any(code in lowered for code in {"401", "403", "429"}) else 70
            category = "shopify_risk" if any(code in lowered for code in {"401", "403", "429"}) else "sync_risk"
            events.append(
                _make_event(
                    risk_type=category,
                    score=score,
                    supplier_sku=record.supplier_sku,
                    shopify_variant_id=record.variant_id,
                    affected_entity=record.supplier_sku,
                    description=f"Price sync failure detected: {record.error_message or 'unknown error'}.",
                )
            )
    return events


def _build_scores(events: list[RiskEvent]) -> list[RiskScore]:
    return [
        RiskScore(
            supplier_sku=event.supplier_sku,
            risk_type=event.risk_type,
            risk_score=event.risk_score,
            risk_level=event.risk_level,
            reasons=[event.description],
        )
        for event in events
    ]


def _build_alerts(events: list[RiskEvent]) -> list[RiskAlert]:
    alerts = []
    for event in events:
        if event.risk_level not in {"high", "critical"}:
            continue
        alerts.append(
            RiskAlert(
                risk_type=event.risk_type,
                risk_level=event.risk_level,
                supplier_sku=event.supplier_sku,
                alert_message=event.description,
                created_at=event.created_at,
                status="active",
            )
        )
    return alerts


def _build_approval_queue(events: list[RiskEvent], pricing_decisions) -> list[ApprovalQueueItem]:
    queue: list[ApprovalQueueItem] = []
    for event in events:
        if event.risk_type == "compliance_risk" or event.risk_level == "critical":
            queue.append(
                ApprovalQueueItem(
                    supplier_sku=event.supplier_sku,
                    trigger_type=event.risk_type,
                    risk_level=event.risk_level,
                    reason=event.description,
                    created_at=event.created_at,
                    status="pending",
                )
            )
    for decision in pricing_decisions:
        if decision.old_price <= 0:
            continue
        increase = (decision.new_price - decision.old_price) / decision.old_price
        decrease = (decision.old_price - decision.new_price) / decision.old_price
        if increase > 0.2 or decrease > 0.3:
            queue.append(
                ApprovalQueueItem(
                    supplier_sku=decision.supplier_sku,
                    trigger_type="price_risk",
                    risk_level="high",
                    reason="Pricing change exceeds approval threshold.",
                    created_at=_now_iso(),
                    status="pending",
                )
            )
    return queue


def _build_blocked_products(events: list[RiskEvent]) -> list[BlockedProduct]:
    blocked: list[BlockedProduct] = []
    for event in events:
        if event.risk_level != "critical":
            continue
        if event.risk_type not in {"compliance_risk", "profit_risk", "seller_risk", "inventory_risk"}:
            continue
        blocked.append(
            BlockedProduct(
                supplier_sku=event.supplier_sku,
                risk_type=event.risk_type,
                risk_level=event.risk_level,
                reason=event.description,
                blocked_at=event.created_at,
                status="blocked",
            )
        )
    return blocked


def _build_report(
    events: list[RiskEvent],
    supplier_scores: list[SupplierRiskScore],
    approval_queue: list[ApprovalQueueItem],
    blocked_products: list[BlockedProduct],
) -> RiskReport:
    level_counts = Counter(event.risk_level for event in events)
    category_counts = Counter(event.risk_type for event in events)
    supplier_summary = Counter(score.health_classification for score in supplier_scores)
    summary = RiskHealthSummary(
        total_events=len(events),
        low_count=level_counts.get("low", 0),
        medium_count=level_counts.get("medium", 0),
        high_count=level_counts.get("high", 0),
        critical_count=level_counts.get("critical", 0),
        affected_products=len({event.supplier_sku for event in events if event.supplier_sku}),
        affected_suppliers=len({event.supplier_id for event in events if event.supplier_id}),
        supplier_health_summary=dict(supplier_summary),
        approval_queue_count=len(approval_queue),
        blocked_product_count=len(blocked_products),
    )
    return RiskReport(
        health_summary=summary,
        category_counts=dict(category_counts),
        level_counts=dict(level_counts),
    )


def _write_report(report: RiskReport, events: list[RiskEvent]) -> str:
    lines = [
        "# Risk Control Report",
        "",
        "## Summary",
        f"- Total risk events: `{report.health_summary.total_events}`",
        f"- Low: `{report.health_summary.low_count}`",
        f"- Medium: `{report.health_summary.medium_count}`",
        f"- High: `{report.health_summary.high_count}`",
        f"- Critical: `{report.health_summary.critical_count}`",
        f"- Affected products: `{report.health_summary.affected_products}`",
        f"- Affected suppliers: `{report.health_summary.affected_suppliers}`",
        f"- Approval queue count: `{report.health_summary.approval_queue_count}`",
        f"- Blocked product count: `{report.health_summary.blocked_product_count}`",
        "",
        "## Category Counts",
    ]
    if report.category_counts:
        lines.extend(f"- `{key}`: `{value}`" for key, value in sorted(report.category_counts.items()))
    else:
        lines.append("- None")
    lines.extend(["", "## Supplier Health Summary"])
    if report.health_summary.supplier_health_summary:
        lines.extend(
            f"- `{key}`: `{value}`" for key, value in sorted(report.health_summary.supplier_health_summary.items())
        )
    else:
        lines.append("- None")
    lines.extend(["", "## Affected Products"])
    affected = sorted({event.supplier_sku for event in events if event.supplier_sku})
    lines.extend(f"- `{sku}`" for sku in affected) if affected else lines.append("- None")
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(REPORT_PATH.resolve())


def build_risk_control_command_from_archive(
    *,
    archive_repository: SupplierArchiveRepository,
    listing_candidates: list | None = None,
    inventory_sync_logs: list | None = None,
    price_sync_logs: list | None = None,
    pricing_decisions: list | None = None,
    shopify_products: list | None = None,
    sku_mappings: list | None = None,
    supplier_skus: list[str] | None = None,
) -> RiskControlCommand:
    allowed_skus = {sku.strip().lower() for sku in list(supplier_skus or []) if str(sku).strip()}
    supplier_products = archive_repository.list_supplier_products()
    if allowed_skus:
        supplier_products = [product for product in supplier_products if str(product.sku or "").strip().lower() in allowed_skus]
    allowed_supplier_ids = {str(product.supplier_id or "").strip() for product in supplier_products if str(product.supplier_id or "").strip()}
    inventory_snapshots = archive_repository.list_inventory_snapshots()
    price_snapshots = archive_repository.list_price_snapshots()
    seller_snapshots = archive_repository.list_seller_snapshots()
    if allowed_skus:
        inventory_snapshots = [snapshot for snapshot in inventory_snapshots if str(snapshot.sku or "").strip().lower() in allowed_skus]
        price_snapshots = [snapshot for snapshot in price_snapshots if str(snapshot.sku or "").strip().lower() in allowed_skus]
        seller_snapshots = [
            snapshot
            for snapshot in seller_snapshots
            if str(snapshot.supplier_id or "").strip() in allowed_supplier_ids
        ]
    return RiskControlCommand(
        supplier_products=supplier_products,
        inventory_snapshots=inventory_snapshots,
        price_snapshots=price_snapshots,
        seller_snapshots=seller_snapshots,
        listing_candidates=list(listing_candidates or []),
        inventory_sync_logs=list(inventory_sync_logs or []),
        price_sync_logs=list(price_sync_logs or []),
        pricing_decisions=list(pricing_decisions or []),
        shopify_products=list(shopify_products or []),
        sku_mappings=list(sku_mappings or []),
    )


def run_risk_control(
    command: RiskControlCommand,
    *,
    risk_event_repository: RiskEventRepository | None = None,
    risk_alert_repository: RiskAlertRepository | None = None,
    risk_report_repository: RiskReportRepository | None = None,
    approval_queue_repository: ApprovalQueueRepository | None = None,
    blocked_product_repository: BlockedProductRepository | None = None,
    supplier_risk_repository: SupplierRiskRepository | None = None,
    risk_score_repository: RiskScoreRepository | None = None,
    risk_batch_repository: RiskBatchRepository | None = None,
) -> RiskBatchResult:
    event_repo = risk_event_repository or InMemoryRiskEventRepository()
    alert_repo = risk_alert_repository or InMemoryRiskAlertRepository()
    report_repo = risk_report_repository or InMemoryRiskReportRepository()
    queue_repo = approval_queue_repository or InMemoryApprovalQueueRepository()
    blocked_repo = blocked_product_repository or InMemoryBlockedProductRepository()
    supplier_repo = supplier_risk_repository or InMemorySupplierRiskRepository()
    score_repo = risk_score_repository or InMemoryRiskScoreRepository()
    batch_repo = risk_batch_repository or InMemoryRiskBatchRepository()

    inventory_events = _inventory_risks(command)
    price_events = _price_and_profit_risks(command)
    seller_events = _seller_risks(command)
    compliance_events = _compliance_risks(command)
    supplier_events, supplier_scores = _supplier_risks(command)
    sync_events = _shopify_and_sync_risks(command)

    events = inventory_events + price_events + seller_events + compliance_events + supplier_events + sync_events
    for event in events:
        event_repo.save_risk_event(event)

    scores = _build_scores(events)
    for score in scores:
        score_repo.save_risk_score(score)

    alerts = _build_alerts(events)
    for alert in alerts:
        alert_repo.save_risk_alert(alert)

    approval_queue = _build_approval_queue(events, command.pricing_decisions)
    for item in approval_queue:
        queue_repo.save_approval_queue_item(item)

    blocked_products = _build_blocked_products(events)
    for product in blocked_products:
        blocked_repo.save_blocked_product(product)

    for score in supplier_scores:
        supplier_repo.save_supplier_risk_score(score)

    report = _build_report(events, supplier_scores, approval_queue, blocked_products)
    report.report_path = _write_report(report, events)
    report_repo.save_risk_report(report)

    result = RiskBatchResult(
        risk_events=events,
        risk_alerts=alerts,
        risk_scores=scores,
        approval_queue=approval_queue,
        blocked_products=blocked_products,
        supplier_risk_scores=supplier_scores,
        risk_report=report,
        mock_mode=True,
        no_inventory_modification_occurred=True,
        no_price_modification_occurred=True,
        no_product_creation_occurred=True,
        no_order_creation_occurred=True,
    )
    batch_repo.save_risk_batch_result(result)
    return result
