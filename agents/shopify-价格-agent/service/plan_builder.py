from __future__ import annotations

from models.price_sync import GigaPriceSnapshot, PriceSyncItem, ShopifyPriceState, SkuMappingRecord
from service.mapping_repository import MappingRepository
from service.pricing_rules import calculate_price, round_delta, round_money
from service.sync_repository import SyncRepository
from shared.config import get_settings

REASON_MISSING_MAPPING = "missing_mapping"
REASON_DUPLICATE_SOURCE_MAPPING = "duplicate_source_mapping"
REASON_DUPLICATE_TARGET_MAPPING = "duplicate_target_mapping"
REASON_VARIANT_NOT_FOUND = "variant_not_found"
REASON_INVALID_SUPPLIER_COST = "invalid_supplier_cost"
REASON_PRICE_DELTA_TOO_SMALL = "price_delta_too_small"
REASON_PRICE_RAISED_TO_FORMULA = "price_raised_to_formula_floor"
REASON_SOURCE_PRICE_CHANGED = "source_price_changed"
REASON_SOURCE_SHIPPING_CHANGED = "source_shipping_changed"
REASON_SOURCE_HASH_UNCHANGED = "source_hash_unchanged"


def _state_key(store_name: str, giga_sku: str, variant_id: str) -> str:
    return f"{store_name}::{giga_sku}::{variant_id}"


def build_plan(
    *,
    store_name: str,
    snapshots: list[GigaPriceSnapshot],
    mappings: list[SkuMappingRecord],
    shopify_states: list[ShopifyPriceState],
    sync_scope: str,
    force_recalculate: bool,
    mapping_repository: MappingRepository | None = None,
    sync_repository: SyncRepository | None = None,
) -> list[PriceSyncItem]:
    settings = get_settings()
    mapping_repo = mapping_repository or MappingRepository()
    sync_repo = sync_repository or SyncRepository()
    state_by_key = sync_repo.list_states()
    shopify_by_variant = {item.shopify_variant_id: item for item in shopify_states}

    items: list[PriceSyncItem] = []
    for snapshot in snapshots:
        mapping, mapping_error = mapping_repo.find_unique_mapping(
            store_name=store_name,
            giga_sku=snapshot.giga_sku,
            records=mappings,
        )
        if mapping is None:
            mapping_reason = {
                "missing_target": REASON_MISSING_MAPPING,
                "duplicated_source": REASON_DUPLICATE_SOURCE_MAPPING,
                "duplicated_target": REASON_DUPLICATE_TARGET_MAPPING,
            }.get(mapping_error or "", REASON_MISSING_MAPPING)
            decision = "manual_review" if mapping_error == "duplicated_source" else "skip"
            items.append(
                PriceSyncItem(
                    store_name=store_name,
                    giga_sku=snapshot.giga_sku,
                    old_price=0,
                    supplier_cost=snapshot.supplier_cost,
                    target_price=0,
                    delta=0,
                    decision=decision,
                    reason_codes=[mapping_reason],
                    status="manual_review" if decision == "manual_review" else "skipped",
                )
            )
            continue

        state_key = _state_key(store_name, snapshot.giga_sku, mapping.shopify_variant_id)
        previous_state = state_by_key.get(state_key, {})
        if (
            sync_scope != "full"
            and not force_recalculate
            and previous_state.get("last_source_hash") == snapshot.raw_hash
            and not (
                previous_state.get("last_target_price") != previous_state.get("last_shopify_price")
                and previous_state.get("last_sync_status") != "synced"
            )
        ):
            continue

        shopify_state = shopify_by_variant.get(mapping.shopify_variant_id)
        if shopify_state is None:
            items.append(
                PriceSyncItem(
                    store_name=store_name,
                    giga_sku=snapshot.giga_sku,
                    shopify_product_id=mapping.shopify_product_id,
                    shopify_variant_id=mapping.shopify_variant_id,
                    old_price=0,
                    supplier_cost=snapshot.supplier_cost,
                    target_price=0,
                    delta=0,
                    decision="manual_review",
                    reason_codes=[REASON_VARIANT_NOT_FOUND],
                    status="manual_review",
                )
            )
            continue

        calculation = calculate_price(snapshot, shopify_state.current_price)
        old_price = round_money(shopify_state.current_price)
        target_price = round_money(calculation.target_price)
        delta = round_delta(target_price - old_price)
        decision = "keep_price"
        reason_codes: list[str] = []
        status = "skipped"

        if snapshot.supplier_cost <= 0:
            decision = "manual_review"
            status = "manual_review"
            reason_codes.append(REASON_INVALID_SUPPLIER_COST)
        else:
            if target_price < calculation.minimum_safe_price:
                target_price = round_money(calculation.minimum_safe_price)
                delta = round_delta(target_price - old_price)
                reason_codes.append(REASON_PRICE_RAISED_TO_FORMULA)
            if abs(delta) < settings.price_sync_min_delta_amount:
                decision = "keep_price"
                status = "skipped"
                reason_codes.append(REASON_PRICE_DELTA_TOO_SMALL)
            elif delta > 0:
                decision = "increase_price"
                status = "planned"
                if previous_state.get("last_source_hash") != snapshot.raw_hash:
                    if previous_state.get("last_target_price") != target_price:
                        if previous_state.get("last_source_updated_at") != snapshot.source_updated_at:
                            if previous_state.get("last_target_price") not in (None, ""):
                                previous_source_state = previous_state.get("last_source_snapshot", {})
                                if previous_source_state.get("supplier_cost") != snapshot.supplier_cost:
                                    reason_codes.append(REASON_SOURCE_PRICE_CHANGED)
                                if previous_source_state.get("shipping_cost") != snapshot.shipping_cost:
                                    reason_codes.append(REASON_SOURCE_SHIPPING_CHANGED)
                if not reason_codes:
                    reason_codes.append(REASON_SOURCE_PRICE_CHANGED)
            elif delta < 0:
                decision = "decrease_price"
                status = "planned"
                if previous_state.get("last_source_hash") != snapshot.raw_hash:
                    previous_source_state = previous_state.get("last_source_snapshot", {})
                    if previous_source_state.get("supplier_cost") != snapshot.supplier_cost:
                        reason_codes.append(REASON_SOURCE_PRICE_CHANGED)
                    if previous_source_state.get("shipping_cost") != snapshot.shipping_cost:
                        reason_codes.append(REASON_SOURCE_SHIPPING_CHANGED)
                if not reason_codes:
                    reason_codes.append(REASON_SOURCE_PRICE_CHANGED)

        items.append(
            PriceSyncItem(
                store_name=store_name,
                giga_sku=snapshot.giga_sku,
                shopify_product_id=mapping.shopify_product_id,
                shopify_variant_id=mapping.shopify_variant_id,
                old_price=old_price,
                supplier_cost=snapshot.supplier_cost,
                target_price=target_price,
                delta=delta,
                decision=decision,
                reason_codes=reason_codes,
                status=status,
            )
        )
    return items
