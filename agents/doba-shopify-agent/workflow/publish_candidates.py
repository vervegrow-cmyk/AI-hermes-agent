import bootstrap

from src.app.runners.tasks import evaluate_product_decision, maybe_publish_decision
from src.modules.shopify_listing import create_draft_listing
from src.shared.contracts.listing import CreateDraftListingCommand
from src.shared.contracts.product import DobaProductInput
from src.shared.contracts.screening import ScreeningDecision as PublishDecision
from src.shared.repositories import InMemoryListingRepository

_workflow_listing_repository = InMemoryListingRepository()


def evaluate_product(
    product: DobaProductInput,
    target_market: str,
    publish_to_shopify: bool = False,
) -> PublishDecision:
    decision = evaluate_product_decision(product, target_market=target_market)
    if publish_to_shopify and decision.status == "approved":
        decision = maybe_publish_decision(decision, target_market)
    return decision


def publish_approved_products(decisions: list[PublishDecision], target_market: str) -> dict:
    published: list[dict] = []
    skipped: list[dict] = []
    for decision in decisions:
        listing = create_draft_listing(
            CreateDraftListingCommand(decision=decision, target_market=target_market),
            listing_repository=_workflow_listing_repository,
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
                "target_market": target_market.upper(),
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
