from __future__ import annotations

from src.shared.contracts.listing import CreateDraftListingCommand, ListingResult


def prepare_listing(command: CreateDraftListingCommand) -> ListingResult:
    decision = command.decision
    if decision.status != "approved":
        return ListingResult(
            product_id=decision.product_id,
            sku=decision.sku,
            target_market=command.target_market.upper(),
            action="skipped",
            reasons=[f"Decision status {decision.status} is not publishable."],
        )
    return ListingResult(
        product_id=decision.product_id,
        sku=decision.sku,
        target_market=command.target_market.upper(),
        action="ready",
        reasons=[],
    )

