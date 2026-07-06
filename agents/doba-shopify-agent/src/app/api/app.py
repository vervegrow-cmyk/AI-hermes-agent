from __future__ import annotations

import bootstrap
from fastapi import APIRouter
from pydantic import BaseModel, Field

from shared.agent_runtime import create_agent_app
from shared.registry import registry
from src.app.executor import execute_task
from src.app.runners.tasks import evaluate_product_decision, maybe_publish_decision
from src.modules.doba_pipeline import run_doba_pipeline
from src.modules.shopify_listing import create_draft_listing, query_shop_connection
from src.shared.contracts.listing import CreateDraftListingCommand
from src.shared.contracts.product import DobaProductInput
from src.shared.contracts.screening import ScreeningDecision
from src.shared.repositories import InMemoryListingRepository

_definition = registry.get_agent("doba-shopify-agent") or {}
_publish_route_listing_repository = InMemoryListingRepository()

app = create_agent_app(
    agent_name="doba-shopify-agent",
    description="Evaluates Doba catalog products and creates Shopify draft listings.",
    executor=execute_task,
    capabilities=_definition.get("capabilities", []),
)

router = APIRouter()


@router.get("/shopify/shop-info")
def shopify_shop_info_route() -> dict:
    return query_shop_connection()


class EvaluateProductRequest(BaseModel):
    product: DobaProductInput
    target_market: str = "US"
    publish_to_shopify: bool = False


class EvaluateBatchRequest(BaseModel):
    products: list[DobaProductInput] = Field(default_factory=list)
    target_market: str = "US"
    publish_to_shopify: bool = False


class PublishApprovedRequest(BaseModel):
    decisions: list[ScreeningDecision] = Field(default_factory=list)
    target_market: str = "US"


class PipelineRunRequest(BaseModel):
    mode: str = "archive-and-publish"
    archive_report_path: str = "docs/audits/doba-online-archive-us-focus-report.json"
    archive_checkpoint_path: str = "data/runtime/supplier_archive/doba_online_archive_us_focus_checkpoint.json"
    publish_report_path: str = "docs/audits/doba-shopify-live-publish-candidate-only-report.json"
    candidate_pool_path: str = "data/runtime/shopify_listing/doba_publish_candidates.json"
    target_country: str = "US"
    inventory_threshold: int = 10
    list_min_inventory: int = 11
    eligible_inventory_threshold: int = 10
    page_size: int = 20
    max_pages: int | None = None
    max_successes: int | None = None
    channels: list[str] = Field(default_factory=lambda: ["Inbox", "Shop", "Pinterest", "Facebook & Instagram"])
    incremental: bool = True
    no_resume: bool = False
    no_candidate_pool: bool = False
    refresh_candidate_pool: bool = False
    archive_eligible_only: bool = True


@router.post("/evaluate-product")
def evaluate_product_route(request: EvaluateProductRequest) -> ScreeningDecision:
    decision = evaluate_product_decision(request.product, target_market=request.target_market)
    if request.publish_to_shopify and decision.status == "approved":
        decision = maybe_publish_decision(decision, request.target_market)
    return decision


@router.post("/evaluate-batch")
def evaluate_batch_route(request: EvaluateBatchRequest) -> dict:
    decisions = []
    for product in request.products:
        decision = evaluate_product_decision(product, target_market=request.target_market)
        if request.publish_to_shopify and decision.status == "approved":
            decision = maybe_publish_decision(decision, request.target_market)
        decisions.append(decision)
    return {
        "count": len(decisions),
        "approved": sum(1 for item in decisions if item.status == "approved"),
        "manual_review": sum(1 for item in decisions if item.status == "manual_review"),
        "rejected": sum(1 for item in decisions if item.status == "rejected"),
        "decisions": decisions,
    }


@router.post("/publish-approved")
def publish_approved_route(request: PublishApprovedRequest) -> dict:
    published: list[dict] = []
    skipped: list[dict] = []
    for decision in request.decisions:
        listing = create_draft_listing(
            CreateDraftListingCommand(decision=decision, target_market=request.target_market),
            listing_repository=_publish_route_listing_repository,
        )
        if listing.action not in {"draft_created", "already_created"}:
            skipped.append(
                {
                    "product_id": decision.product_id,
                    "sku": decision.sku,
                    "status": decision.status,
                    "reasons": decision.reasons or listing.reasons,
                }
            )
            continue
        published.append(
            {
                "product_id": decision.product_id,
                "sku": decision.sku,
                "target_market": request.target_market.upper(),
                "draft_id": listing.draft_id,
                "status": listing.action,
            }
        )
    return {
        "published_count": len(published),
        "skipped_count": len(skipped),
        "published": published,
        "skipped": skipped,
    }


@router.post("/pipeline/run")
def pipeline_run_route(request: PipelineRunRequest) -> dict:
    return run_doba_pipeline(request.model_dump())


app.include_router(router)
