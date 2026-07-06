import pytest

from shared.config.settings import get_settings
from src.modules.product_screening import normalize_product
from src.modules.shopify_listing import create_draft_listing
from src.shared.contracts.listing import CreateDraftListingCommand
from src.shared.contracts.product import DobaProductInput
from src.shared.contracts.screening import ScreeningDecision
from src.shared.repositories import InMemoryListingRepository
from tests.conftest import load_fixture


@pytest.fixture(autouse=True)
def _shopify_test_env(monkeypatch):
    monkeypatch.setenv("SHOPIFY_STORE", "unit-test-store.myshopify.com")
    monkeypatch.setenv("SHOPIFY_TOKEN", "test-admin-token")
    monkeypatch.setenv("SHOPIFY_ADMIN_ACCESS_TOKEN", "")
    monkeypatch.setenv("SHOPIFY_AUTH_MODE", "custom_admin_token")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _approved_decision() -> ScreeningDecision:
    product = DobaProductInput.model_validate(load_fixture("approved_product.json"))
    normalized = normalize_product(product)
    return ScreeningDecision(
        status="approved",
        product_id=normalized.product_id,
        sku=normalized.sku,
        normalized_title=normalized.normalized_title,
        target_market="US",
        reasons=["approved"],
        expected_profit=20,
        margin_rate=0.3,
        shipping_ratio=0.2,
        score=92,
        normalized_product=normalized,
    )


def test_shopify_listing_only_creates_draft_once():
    repository = InMemoryListingRepository()
    decision = _approved_decision()
    first = create_draft_listing(CreateDraftListingCommand(decision=decision, target_market="US"), repository)
    second = create_draft_listing(CreateDraftListingCommand(decision=decision, target_market="US"), repository)
    assert first.action == "draft_created"
    assert second.action == "already_created"
    assert first.draft_id == second.draft_id


def test_shopify_listing_skips_non_approved_decision():
    repository = InMemoryListingRepository()
    decision = _approved_decision()
    decision.status = "manual_review"
    result = create_draft_listing(CreateDraftListingCommand(decision=decision, target_market="US"), repository)
    assert result.action == "skipped"
