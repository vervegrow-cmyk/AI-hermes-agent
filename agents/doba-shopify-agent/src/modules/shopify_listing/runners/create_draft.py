from __future__ import annotations

from src.modules.shopify_listing.application.service import prepare_listing
from src.modules.shopify_listing.infrastructure.shopify_gateway import create_draft
from src.shared.contracts.listing import CreateDraftListingCommand, ListingResult
from src.shared.repositories.protocols import ListingRepository


def create_draft_listing(command: CreateDraftListingCommand, listing_repository: ListingRepository) -> ListingResult:
    prepared = prepare_listing(command)
    if prepared.action != "ready":
        return prepared

    duplicate_key = command.decision.normalized_product.duplicate_key
    existing_draft_id = listing_repository.get_draft_id(duplicate_key)
    if existing_draft_id:
        return ListingResult(
            product_id=command.decision.product_id,
            sku=command.decision.sku,
            target_market=command.target_market.upper(),
            action="already_created",
            draft_id=existing_draft_id,
            reasons=["Draft listing already exists for this duplicate key."],
        )

    draft = create_draft(command.decision)
    if draft.get("draft_id"):
        listing_repository.mark_created(duplicate_key, draft["draft_id"])
    return ListingResult(
        product_id=command.decision.product_id,
        sku=command.decision.sku,
        target_market=command.target_market.upper(),
        action=draft["status"],
        draft_id=draft["draft_id"],
        store=draft["store"],
        reasons=[] if draft["status"] != "already_exists_remote" else ["Remote Shopify product already exists for this SKU."],
    )
