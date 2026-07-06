from __future__ import annotations

from src.modules.doba_pipeline import run_doba_pipeline
from src.modules.inventory_sync import run_inventory_sync
from src.modules.price_sync import run_price_sync
from src.modules.product_screening import normalize_product, screen_product
from src.modules.risk_control import assess_risk
from src.modules.shopify_listing import create_draft_listing
from src.shared.contracts.inventory import InventorySyncCommand
from src.shared.contracts.listing import CreateDraftListingCommand
from src.shared.contracts.pricing import PriceSyncCommand
from src.shared.contracts.product import DobaProductInput
from src.shared.contracts.risk import RiskAssessmentCommand
from src.shared.contracts.screening import ScreenProductCommand, ScreeningDecision
from src.shared.repositories import (
    InMemoryDecisionLogRepository,
    InMemoryListingRepository,
    InMemoryProductStateRepository,
    InMemorySkuMappingRepository,
)


DECISION_LOG_REPOSITORY = InMemoryDecisionLogRepository()
LISTING_REPOSITORY = InMemoryListingRepository()
PRODUCT_STATE_REPOSITORY = InMemoryProductStateRepository()
SKU_MAPPING_REPOSITORY = InMemorySkuMappingRepository()


def evaluate_product_decision(product: DobaProductInput, target_market: str) -> ScreeningDecision:
    normalized = normalize_product(product)
    risk_result = assess_risk(RiskAssessmentCommand(normalized_product=normalized, target_market=target_market))
    decision = screen_product(
        ScreenProductCommand(
            product=product,
            normalized_product=normalized,
            risk_assessment=risk_result,
            target_market=target_market,
        )
    )
    DECISION_LOG_REPOSITORY.save(decision)
    return decision


def maybe_publish_decision(decision: ScreeningDecision, target_market: str) -> ScreeningDecision:
    listing = create_draft_listing(
        CreateDraftListingCommand(decision=decision, target_market=target_market),
        listing_repository=LISTING_REPOSITORY,
    )
    decision.publish_action = listing.action
    decision.shopify_draft_id = listing.draft_id
    return decision


def evaluate_product_task(payload: dict) -> dict:
    target_market = payload.get("target_market", "US")
    product = DobaProductInput.model_validate(payload.get("product", {}))
    decision = evaluate_product_decision(product, target_market=target_market)
    if payload.get("publish_to_shopify", False) and decision.status == "approved":
        decision = maybe_publish_decision(decision, target_market)
    return {"summary": f"Evaluated product {decision.product_id or decision.sku}", "data": decision.model_dump()}


def evaluate_batch_task(payload: dict) -> dict:
    target_market = payload.get("target_market", "US")
    decisions: list[ScreeningDecision] = []
    for item in payload.get("products", []):
        decision = evaluate_product_decision(DobaProductInput.model_validate(item), target_market=target_market)
        if payload.get("publish_to_shopify", False) and decision.status == "approved":
            decision = maybe_publish_decision(decision, target_market)
        decisions.append(decision)
    return {
        "summary": f"Evaluated {len(decisions)} Doba products",
        "data": {
            "count": len(decisions),
            "approved": sum(1 for item in decisions if item.status == "approved"),
            "manual_review": sum(1 for item in decisions if item.status == "manual_review"),
            "rejected": sum(1 for item in decisions if item.status == "rejected"),
            "decisions": [item.model_dump() for item in decisions],
        },
    }


def sync_candidates_task(payload: dict) -> dict:
    return evaluate_batch_task(payload)


def doba_pipeline_task(payload: dict) -> dict:
    result = run_doba_pipeline(payload)
    return {"summary": f"Executed Doba pipeline mode {payload.get('mode', 'archive-and-publish')}", "data": result}


def publish_approved_task(payload: dict) -> dict:
    target_market = payload.get("target_market", "US")
    published: list[dict] = []
    skipped: list[dict] = []
    for item in payload.get("products", []):
        decision = evaluate_product_decision(DobaProductInput.model_validate(item), target_market=target_market)
        if decision.status != "approved":
            skipped.append(
                {
                    "product_id": decision.product_id,
                    "sku": decision.sku,
                    "status": decision.status,
                    "reasons": decision.reasons,
                }
            )
            continue
        decision = maybe_publish_decision(decision, target_market)
        published.append(
            {
                "product_id": decision.product_id,
                "sku": decision.sku,
                "target_market": target_market.upper(),
                "draft_id": decision.shopify_draft_id,
                "status": decision.publish_action,
            }
        )
    return {
        "summary": f"Processed publish for {len(published) + len(skipped)} products",
        "data": {
            "published_count": len(published),
            "skipped_count": len(skipped),
            "published": published,
            "skipped": skipped,
        },
    }


def sync_inventory_task(payload: dict) -> dict:
    result = run_inventory_sync(InventorySyncCommand.model_validate(payload))
    return {"summary": f"Processed inventory sync for {len(result.items)} items", "data": result.model_dump()}


def sync_prices_task(payload: dict) -> dict:
    result = run_price_sync(PriceSyncCommand.model_validate(payload))
    return {"summary": f"Processed price sync for {len(result.items)} items", "data": result.model_dump()}
