from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from src.modules.price_sync.infrastructure.shopify_price_sync_service import ShopifyPriceSyncService
from src.shared.contracts.mapping import SkuMappingRecord
from src.shared.contracts.pricing import (
    CompetitorPriceData,
    PlatformCost,
    PriceCalculation,
    PriceHealthScore,
    PricingDecision,
    PriceSyncBatchResult,
    PriceSyncCommand,
    PriceSyncItem,
    PriceSyncRecord,
    PriceSyncReport,
    ShopifyPriceState,
    ShippingCost,
    SupplierCost,
    WarehouseCost,
)
from src.shared.repositories import (
    InMemoryPlatformCostRepository,
    InMemoryPriceSyncBatchRepository,
    InMemoryPriceSyncLogRepository,
    InMemoryPricingDecisionRepository,
    InMemoryShippingCostRepository,
    InMemoryShopifyPriceRepository,
    InMemorySkuMappingRepository,
    InMemorySupplierCostRepository,
    InMemoryWarehouseCostRepository,
)
from src.shared.repositories.protocols import (
    PlatformCostRepository,
    PriceSyncBatchRepository,
    PriceSyncLogRepository,
    PricingDecisionRepository,
    ShippingCostRepository,
    ShopifyPriceRepository,
    SupplierArchiveRepository,
    SkuMappingRepository,
    SupplierCostRepository,
    WarehouseCostRepository,
)


REPORT_PATH = Path("docs/audits/price-sync-report.md")


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _round_money(value: float) -> float:
    return round(max(0.0, value), 2)


def _get_inventory_level(command: PriceSyncCommand, supplier_sku: str, fallback: int = 0) -> int:
    for snapshot in command.inventory_snapshots:
        if snapshot.sku.strip().lower() == supplier_sku.strip().lower():
            return snapshot.supplier_inventory
    for state in command.shopify_price_states:
        if state.supplier_sku.strip().lower() == supplier_sku.strip().lower():
            return state.inventory
    return fallback


def _default_competitor_price(calculation: PriceCalculation) -> CompetitorPriceData:
    return CompetitorPriceData(
        supplier_sku=calculation.supplier_sku,
        competitor_low=_round_money(calculation.recommended_price * 0.9),
        competitor_avg=_round_money(calculation.recommended_price),
        competitor_high=_round_money(calculation.recommended_price * 1.1),
    )


def calculate_price_metrics(
    *,
    supplier_cost: SupplierCost,
    shipping_cost: ShippingCost | None,
    warehouse_cost: WarehouseCost | None,
    platform_cost: PlatformCost | None,
    current_price: float,
) -> PriceCalculation:
    shipping = shipping_cost.cost if shipping_cost else 0
    warehouse = warehouse_cost.cost if warehouse_cost else 0
    platform = platform_cost.cost if platform_cost else 0
    true_cost = _round_money(supplier_cost.cost + shipping + warehouse + platform)
    break_even_price = _round_money(true_cost)
    minimum_safe_price = _round_money(true_cost / 0.8 if true_cost else 0)
    recommended_price = _round_money(true_cost / 0.6 if true_cost else 0)
    gross_margin = _round_money(current_price - supplier_cost.cost) if current_price else 0
    net_margin = round(((current_price - true_cost) / current_price), 4) if current_price else 0
    profit_amount = _round_money(current_price - true_cost) if current_price else 0
    roi = round(((profit_amount / true_cost) if true_cost else 0), 4)
    return PriceCalculation(
        supplier_sku=supplier_cost.supplier_sku,
        true_cost=true_cost,
        break_even_price=break_even_price,
        minimum_safe_price=minimum_safe_price,
        recommended_price=recommended_price,
        target_price=recommended_price,
        gross_margin=gross_margin,
        net_margin=net_margin,
        profit_amount=profit_amount,
        roi=roi,
    )


def _apply_inventory_strategy(base_price: float, inventory: int) -> tuple[float, list[str]]:
    reasons: list[str] = []
    target = base_price
    if inventory > 1000:
        target = _round_money(base_price * 0.95)
        reasons.append("inventory_high")
    elif inventory < 10:
        reasons.append("inventory_critical")
    elif inventory < 50:
        target = _round_money(base_price * 1.08)
        reasons.append("inventory_low")
    return target, reasons


def _apply_lifecycle_strategy(base_price: float, lifecycle_stage: str) -> tuple[float, list[str]]:
    stage = (lifecycle_stage or "growth").strip().lower()
    reasons: list[str] = []
    target = base_price
    if stage == "new_product":
        target = _round_money(base_price * 1.05)
        reasons.append("lifecycle_new_product")
    elif stage == "growth":
        reasons.append("lifecycle_growth")
    elif stage == "mature":
        target = _round_money(base_price * 0.98)
        reasons.append("lifecycle_mature")
    elif stage == "declining":
        target = _round_money(base_price * 0.92)
        reasons.append("lifecycle_declining")
    elif stage == "clearance":
        target = _round_money(base_price * 0.85)
        reasons.append("lifecycle_clearance")
    return target, reasons


def _apply_competitive_strategy(base_price: float, competitor: CompetitorPriceData) -> tuple[float, list[str]]:
    reasons: list[str] = []
    target = base_price
    if competitor.competitor_low and base_price > competitor.competitor_high > 0:
        target = _round_money(max(competitor.competitor_avg, competitor.competitor_high * 0.98))
        reasons.append("competitor_pressure")
    elif competitor.competitor_low and base_price < competitor.competitor_low:
        target = _round_money(min(competitor.competitor_avg, competitor.competitor_low * 1.02))
        reasons.append("competitive_headroom")
    return target, reasons


def calculate_price_health(
    *,
    supplier_sku: str,
    target_price: float,
    calculation: PriceCalculation,
    competitor: CompetitorPriceData,
    inventory: int,
) -> PriceHealthScore:
    margin_score = max(0.0, min(100.0, calculation.net_margin * 180))
    if competitor.competitor_avg:
        competitiveness_gap = abs(target_price - competitor.competitor_avg) / competitor.competitor_avg
    else:
        competitiveness_gap = 0
    competitiveness_score = max(0.0, min(100.0, 100 - competitiveness_gap * 120))
    stability_score = 100.0 if calculation.roi >= 0.4 else max(0.0, min(100.0, calculation.roi * 200))
    if inventory < 10:
        inventory_score = 55.0
    elif inventory < 50:
        inventory_score = 75.0
    elif inventory > 1000:
        inventory_score = 70.0
    else:
        inventory_score = 90.0
    score = round((margin_score * 0.4) + (competitiveness_score * 0.25) + (stability_score * 0.2) + (inventory_score * 0.15), 2)
    return PriceHealthScore(
        supplier_sku=supplier_sku,
        score=score,
        margin_score=round(margin_score, 2),
        competitiveness_score=round(competitiveness_score, 2),
        stability_score=round(stability_score, 2),
        inventory_score=round(inventory_score, 2),
    )


def build_pricing_decision(
    *,
    supplier_sku: str,
    current_price: float,
    calculation: PriceCalculation,
    competitor: CompetitorPriceData,
    inventory: int,
    lifecycle_stage: str,
) -> tuple[PricingDecision, PriceCalculation, PriceHealthScore]:
    target_price = calculation.recommended_price
    reason_codes: list[str] = []

    inventory_target, inventory_reasons = _apply_inventory_strategy(target_price, inventory)
    target_price = inventory_target
    reason_codes.extend(inventory_reasons)

    lifecycle_target, lifecycle_reasons = _apply_lifecycle_strategy(target_price, lifecycle_stage)
    target_price = lifecycle_target
    reason_codes.extend(lifecycle_reasons)

    competitor_target, competitor_reasons = _apply_competitive_strategy(target_price, competitor)
    target_price = competitor_target
    reason_codes.extend(competitor_reasons)

    target_price = max(calculation.minimum_safe_price, target_price)
    calculation.target_price = _round_money(target_price)
    profit_after = _round_money(calculation.target_price - calculation.true_cost)
    health = calculate_price_health(
        supplier_sku=supplier_sku,
        target_price=calculation.target_price,
        calculation=calculation,
        competitor=competitor,
        inventory=inventory,
    )

    price_gap = abs(calculation.target_price - current_price)
    tolerance = max(0.5, current_price * 0.03)
    if inventory < 10:
        decision_type = "manual_review"
        reason_codes.append("inventory_critical_manual_review")
    elif calculation.true_cost <= 0 or calculation.minimum_safe_price <= 0:
        decision_type = "manual_review"
        reason_codes.append("cost_anomaly")
    elif lifecycle_stage == "clearance" and inventory > 1000:
        decision_type = "clearance_price"
        reason_codes.append("clearance_lifecycle")
    elif price_gap <= tolerance:
        decision_type = "keep_price"
        reason_codes.append("price_within_tolerance")
    elif calculation.target_price > current_price + 0.01:
        decision_type = "increase_price"
        if calculation.net_margin < 0.2:
            reason_codes.append("margin_too_low")
    elif calculation.target_price < current_price - 0.01:
        decision_type = "decrease_price"
        if inventory > 1000:
            reason_codes.append("inventory_high_discount")
    else:
        decision_type = "keep_price"
        reason_codes.append("margin_healthy")

    decision = PricingDecision(
        supplier_sku=supplier_sku,
        decision=decision_type,
        old_price=_round_money(current_price),
        new_price=_round_money(calculation.target_price if decision_type != "keep_price" else current_price),
        reason_codes=reason_codes,
        profit_before=calculation.profit_amount,
        profit_after=profit_after if decision_type != "keep_price" else calculation.profit_amount,
        price_health_score=health.score,
    )
    return decision, calculation, health


def build_price_sync_plan(
    command: PriceSyncCommand,
    *,
    sku_mapping_repository: SkuMappingRepository | None = None,
) -> PriceSyncBatchResult:
    mapping_repository = sku_mapping_repository or InMemorySkuMappingRepository()
    calculations: list[PriceCalculation] = []
    decisions: list[PricingDecision] = []
    items: list[PriceSyncItem] = []

    shipping_by_sku = {item.supplier_sku.strip().lower(): item for item in command.shipping_costs}
    warehouse_by_sku = {item.supplier_sku.strip().lower(): item for item in command.warehouse_costs}
    platform_by_sku = {item.supplier_sku.strip().lower(): item for item in command.platform_costs}
    shopify_by_sku = {item.supplier_sku.strip().lower(): item for item in command.shopify_price_states}
    competitor_by_sku = {item.supplier_sku.strip().lower(): item for item in command.competitor_prices}

    for supplier_cost in command.supplier_costs:
        key = supplier_cost.supplier_sku.strip().lower()
        state = shopify_by_sku.get(key, ShopifyPriceState(supplier_sku=supplier_cost.supplier_sku))
        calculation = calculate_price_metrics(
            supplier_cost=supplier_cost,
            shipping_cost=shipping_by_sku.get(key),
            warehouse_cost=warehouse_by_sku.get(key),
            platform_cost=platform_by_sku.get(key),
            current_price=state.current_price,
        )
        inventory = _get_inventory_level(command, supplier_cost.supplier_sku, state.inventory)
        lifecycle_stage = command.lifecycle_stages.get(supplier_cost.supplier_sku, state.lifecycle_stage or "growth")
        competitor = competitor_by_sku.get(key, _default_competitor_price(calculation))
        decision, calculation, _ = build_pricing_decision(
            supplier_sku=supplier_cost.supplier_sku,
            current_price=state.current_price,
            calculation=calculation,
            competitor=competitor,
            inventory=inventory,
            lifecycle_stage=lifecycle_stage,
        )
        calculations.append(calculation)
        decisions.append(decision)
        mapping = mapping_repository.get_by_sku(supplier_cost.supplier_sku)
        action = "sync" if mapping and decision.decision in {"increase_price", "decrease_price", "clearance_price"} else "skip"
        if mapping is None:
            action = "sync_failed"
        if decision.decision in {"keep_price", "manual_review"}:
            action = "skip"
        items.append(
            PriceSyncItem(
                sku=supplier_cost.supplier_sku,
                current_price=state.current_price,
                target_price=decision.new_price,
                delta=_round_money(decision.new_price - state.current_price),
                action=action,
            )
        )

    return PriceSyncBatchResult(
        target_market=command.target_market.upper(),
        synced_count=sum(1 for item in items if item.action == "sync"),
        skipped_count=sum(1 for item in items if item.action != "sync"),
        items=items,
        calculations=calculations,
        decisions=decisions,
        mock_mode=True,
    )


def build_price_sync_command_from_archive(
    *,
    archive_repository: SupplierArchiveRepository,
    shopify_price_states: list[ShopifyPriceState] | None = None,
    sku_mappings: list[dict] | None = None,
    supplier_skus: list[str] | None = None,
    target_market: str = "US",
) -> PriceSyncCommand:
    allowed_skus = {sku.strip().lower() for sku in list(supplier_skus or []) if str(sku).strip()}
    latest_price_by_sku: dict[str, PriceSnapshot] = {}
    latest_inventory_by_sku: dict[str, InventorySnapshot] = {}
    for snapshot in archive_repository.list_price_snapshots():
        key = snapshot.sku.strip().lower()
        if allowed_skus and key not in allowed_skus:
            continue
        latest_price_by_sku[key] = snapshot
    for snapshot in archive_repository.list_inventory_snapshots():
        key = snapshot.sku.strip().lower()
        if allowed_skus and key not in allowed_skus:
            continue
        latest_inventory_by_sku[key] = snapshot
    return PriceSyncCommand(
        target_market=target_market,
        snapshots=list(latest_price_by_sku.values()),
        inventory_snapshots=list(latest_inventory_by_sku.values()),
        shopify_price_states=list(shopify_price_states or []),
        sku_mappings=list(sku_mappings or []),
    )


def _build_report(result: PriceSyncBatchResult) -> str:
    report = result.report
    lines = [
        "# Price Sync Report",
        "",
        "## Summary",
        f"- Products processed: `{report.products_processed}`",
        f"- Price changes detected: `{report.price_changes_detected}`",
        f"- Price increases: `{report.price_increases}`",
        f"- Price decreases: `{report.price_decreases}`",
        f"- Clearance pricing count: `{report.clearance_pricing_count}`",
        f"- Keep price count: `{report.keep_price_count}`",
        f"- Manual review count: `{report.manual_review_count}`",
        f"- Average margin: `{report.average_margin}`",
        f"- Lowest margin: `{report.lowest_margin}`",
        f"- Highest margin: `{report.highest_margin}`",
        f"- Average ROI: `{report.average_roi}`",
        f"- Price health score: `{report.price_health_score}`",
        f"- Successful syncs: `{report.successful_syncs}`",
        f"- Failed syncs: `{report.failed_syncs}`",
        f"- Mode: `{report.mode}`",
    ]
    return "\n".join(lines) + "\n"


def _write_report(result: PriceSyncBatchResult) -> str:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(_build_report(result), encoding="utf-8")
    return str(REPORT_PATH.resolve())


def run_price_sync_runtime(
    command: PriceSyncCommand,
    *,
    supplier_cost_repository: SupplierCostRepository | None = None,
    shipping_cost_repository: ShippingCostRepository | None = None,
    warehouse_cost_repository: WarehouseCostRepository | None = None,
    platform_cost_repository: PlatformCostRepository | None = None,
    shopify_price_repository: ShopifyPriceRepository | None = None,
    pricing_decision_repository: PricingDecisionRepository | None = None,
    price_sync_log_repository: PriceSyncLogRepository | None = None,
    price_sync_batch_repository: PriceSyncBatchRepository | None = None,
    sku_mapping_repository: SkuMappingRepository | None = None,
    sync_service: ShopifyPriceSyncService | None = None,
) -> PriceSyncBatchResult:
    supplier_repo = supplier_cost_repository or InMemorySupplierCostRepository()
    shipping_repo = shipping_cost_repository or InMemoryShippingCostRepository()
    warehouse_repo = warehouse_cost_repository or InMemoryWarehouseCostRepository()
    platform_repo = platform_cost_repository or InMemoryPlatformCostRepository()
    shopify_repo = shopify_price_repository or InMemoryShopifyPriceRepository()
    decision_repo = pricing_decision_repository or InMemoryPricingDecisionRepository()
    log_repo = price_sync_log_repository or InMemoryPriceSyncLogRepository()
    batch_repo = price_sync_batch_repository or InMemoryPriceSyncBatchRepository()
    mapping_repo = sku_mapping_repository or InMemorySkuMappingRepository()
    service = sync_service or ShopifyPriceSyncService()

    for mapping in command.sku_mappings:
        mapping_repo.save(SkuMappingRecord.model_validate(mapping))
    for item in command.supplier_costs:
        supplier_repo.save_supplier_cost(item)
    for item in command.shipping_costs:
        shipping_repo.save_shipping_cost(item)
    for item in command.warehouse_costs:
        warehouse_repo.save_warehouse_cost(item)
    for item in command.platform_costs:
        platform_repo.save_platform_cost(item)
    for item in command.shopify_price_states:
        shopify_repo.save_shopify_price_state(item)

    plan_result = build_price_sync_plan(
        PriceSyncCommand(
            target_market=command.target_market,
            supplier_costs=supplier_repo.list_supplier_costs(),
            shipping_costs=shipping_repo.list_shipping_costs(),
            warehouse_costs=warehouse_repo.list_warehouse_costs(),
            platform_costs=platform_repo.list_platform_costs(),
            shopify_price_states=shopify_repo.list_shopify_price_states(),
            competitor_prices=command.competitor_prices,
            inventory_snapshots=command.inventory_snapshots,
            lifecycle_stages=command.lifecycle_stages,
        ),
        sku_mapping_repository=mapping_repo,
    )

    records: list[PriceSyncRecord] = []
    successful_syncs = 0
    failed_syncs = 0
    health_scores: list[float] = []
    margin_values: list[float] = []
    roi_values: list[float] = []

    calc_by_sku = {item.supplier_sku: item for item in plan_result.calculations}
    item_by_sku = {item.sku: item for item in plan_result.items}
    for decision in plan_result.decisions:
        decision_repo.save_pricing_decision(decision)
        mapping = mapping_repo.get_by_sku(decision.supplier_sku)
        calc = calc_by_sku[decision.supplier_sku]
        health_scores.append(decision.price_health_score)
        margin_values.append(calc.net_margin)
        roi_values.append(calc.roi)

        if mapping is None and decision.decision != "keep_price":
            failed_syncs += 1
            record = PriceSyncRecord(
                supplier_sku=decision.supplier_sku,
                variant_id="",
                old_price=decision.old_price,
                new_price=decision.new_price,
                profit_before=decision.profit_before,
                profit_after=decision.profit_after,
                decision=decision.decision,
                timestamp=_now_iso(),
                status="missing_mapping",
                error_message="Missing SKU mapping for supplier_sku.",
            )
        elif decision.decision in {"keep_price", "manual_review"}:
            record = PriceSyncRecord(
                supplier_sku=decision.supplier_sku,
                variant_id=(mapping.shopify_variant_id if mapping else ""),
                old_price=decision.old_price,
                new_price=decision.new_price,
                profit_before=decision.profit_before,
                profit_after=decision.profit_after,
                decision=decision.decision,
                timestamp=_now_iso(),
                status="skipped" if decision.decision == "keep_price" else "manual_review",
            )
        else:
            try:
                service.sync_price(mapping.shopify_variant_id, decision.new_price, decision.supplier_sku)
                successful_syncs += 1
                record = PriceSyncRecord(
                    supplier_sku=decision.supplier_sku,
                    variant_id=mapping.shopify_variant_id,
                    old_price=decision.old_price,
                    new_price=decision.new_price,
                    profit_before=decision.profit_before,
                    profit_after=decision.profit_after,
                    decision=decision.decision,
                    timestamp=_now_iso(),
                    status="synced",
                )
                current = shopify_repo.get_shopify_price_state_by_sku(decision.supplier_sku) or ShopifyPriceState(supplier_sku=decision.supplier_sku, shopify_variant_id=mapping.shopify_variant_id)
                shopify_repo.save_shopify_price_state(
                    current.model_copy(update={"current_price": decision.new_price, "updated_at": record.timestamp})
                )
            except Exception as exc:
                failed_syncs += 1
                record = PriceSyncRecord(
                    supplier_sku=decision.supplier_sku,
                    variant_id=mapping.shopify_variant_id,
                    old_price=decision.old_price,
                    new_price=decision.new_price,
                    profit_before=decision.profit_before,
                    profit_after=decision.profit_after,
                    decision=decision.decision,
                    timestamp=_now_iso(),
                    status="sync_failed",
                    error_message=str(exc),
                )
        log_repo.save_price_sync_record(record)
        records.append(record)
        action = item_by_sku[decision.supplier_sku]
        action.action = record.status

    decision_counter = Counter(item.decision for item in plan_result.decisions)
    report = PriceSyncReport(
        products_processed=len(plan_result.decisions),
        price_changes_detected=sum(1 for item in plan_result.decisions if item.decision in {"increase_price", "decrease_price", "clearance_price"}),
        price_increases=decision_counter.get("increase_price", 0),
        price_decreases=decision_counter.get("decrease_price", 0),
        clearance_pricing_count=decision_counter.get("clearance_price", 0),
        keep_price_count=decision_counter.get("keep_price", 0),
        manual_review_count=decision_counter.get("manual_review", 0),
        average_margin=round(sum(margin_values) / len(margin_values), 4) if margin_values else 0,
        lowest_margin=round(min(margin_values), 4) if margin_values else 0,
        highest_margin=round(max(margin_values), 4) if margin_values else 0,
        average_roi=round(sum(roi_values) / len(roi_values), 4) if roi_values else 0,
        price_health_score=round(sum(health_scores) / len(health_scores), 2) if health_scores else 0,
        successful_syncs=successful_syncs,
        failed_syncs=failed_syncs,
        mode=service.mode,
    )

    result = PriceSyncBatchResult(
        target_market=command.target_market.upper(),
        synced_count=successful_syncs,
        skipped_count=len(plan_result.items) - successful_syncs,
        items=plan_result.items,
        calculations=plan_result.calculations,
        decisions=plan_result.decisions,
        records=records,
        report=report,
        mock_mode=service.mode == "mock",
        no_product_creation_occurred=True,
        no_publish_occurred=True,
        no_inventory_update_occurred=True,
        no_order_creation_occurred=True,
        no_fulfillment_occurred=True,
    )
    result.report_path = _write_report(result)
    batch_repo.save_price_sync_batch_result(result)
    return result
