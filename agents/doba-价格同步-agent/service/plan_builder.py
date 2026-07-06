from __future__ import annotations

from models.price_sync import DobaPriceSnapshot, PriceSyncItem, ShopifyPriceState, SkuMappingRecord
from service.mapping_repository import MappingRepository
from service.pricing_rules import calculate_price, round_delta, round_money
from service.sync_repository import SyncRepository
from shared.config import get_settings

REASON_MISSING_MAPPING = "missing_mapping"
REASON_DUPLICATE_SOURCE_MAPPING = "duplicate_source_mapping"
REASON_DUPLICATE_TARGET_MAPPING = "duplicate_target_mapping"
REASON_VARIANT_NOT_FOUND = "variant_not_found"
REASON_MISSING_SUPPLIER_COST = "missing_supplier_cost"
REASON_INVALID_SUPPLIER_COST = "invalid_supplier_cost"
REASON_MISSING_SHIPPING_COST = "missing_shipping_cost"
REASON_SOURCE_UNCHANGED = "source_unchanged"
REASON_TARGET_PRICE_UNCHANGED = "target_price_unchanged"
REASON_SHOPIFY_PRICE_ALREADY_CORRECT = "shopify_price_already_correct"
REASON_MARGIN_BELOW_MINIMUM = "margin_below_minimum"
REASON_TARGET_PRICE_BELOW_COST = "target_price_below_cost"
REASON_PRICE_INCREASE_TOO_LARGE = "price_increase_too_large"
REASON_PRICE_DECREASE_TOO_LARGE = "price_decrease_too_large"


def _state_key(store_name: str, doba_sku: str, variant_id: str) -> str:
    return f"{store_name}::{doba_sku}::{variant_id}"


def build_plan(
    *,
    store_name: str,
    snapshots: list[DobaPriceSnapshot],
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
            doba_sku=snapshot.doba_sku,
            records=mappings,
        )
        if mapping is None:
            mapping_reason = {
                "missing_target": REASON_MISSING_MAPPING,
                "duplicated_source": REASON_DUPLICATE_SOURCE_MAPPING,
                "duplicated_target": REASON_DUPLICATE_TARGET_MAPPING,
            }.get(mapping_error or "", REASON_MISSING_MAPPING)
            items.append(
                PriceSyncItem(
                    store_name=store_name,
                    doba_product_id=snapshot.doba_product_id,
                    doba_sku=snapshot.doba_sku,
                    supplier_cost=float(snapshot.supplier_cost or 0.0),
                    shipping_cost=float(snapshot.shipping_cost or 0.0),
                    estimated_total_cost=float(snapshot.estimated_total_cost or 0.0),
                    decision="manual_review" if mapping_error in {"duplicated_source", "duplicated_target"} else "skip",
                    reason_codes=[mapping_reason],
                    status="manual_review" if mapping_error in {"duplicated_source", "duplicated_target"} else "skipped",
                )
            )
            continue

        if snapshot.supplier_cost is None:
            items.append(_manual_review_item(store_name, snapshot, mapping, REASON_MISSING_SUPPLIER_COST))
            continue
        if snapshot.supplier_cost <= 0:
            items.append(_manual_review_item(store_name, snapshot, mapping, REASON_INVALID_SUPPLIER_COST))
            continue
        if snapshot.shipping_cost is None:
            items.append(_manual_review_item(store_name, snapshot, mapping, REASON_MISSING_SHIPPING_COST))
            continue

        state_key = _state_key(store_name, snapshot.doba_sku, mapping.shopify_variant_id)
        previous_state = state_by_key.get(state_key, {})
        source_changed = force_recalculate or sync_scope == "full" or previous_state.get("last_source_hash") != snapshot.raw_hash

        shopify_state = shopify_by_variant.get(mapping.shopify_variant_id)
        if shopify_state is None:
            items.append(_manual_review_item(store_name, snapshot, mapping, REASON_VARIANT_NOT_FOUND))
            continue

        calculation = calculate_price(snapshot, shopify_state.current_price)
        old_price = round_money(shopify_state.current_price)
        target_price = round_money(calculation.target_price)
        delta = round_delta(target_price - old_price)
        previous_target_price = round_money(float(previous_state.get("last_target_price", 0) or 0))
        target_price_changed = force_recalculate or sync_scope == "full" or previous_target_price != target_price
        shopify_price_changed = abs(delta) >= settings.price_sync_min_delta_amount

        base_item = PriceSyncItem(
            store_name=store_name,
            doba_product_id=snapshot.doba_product_id,
            doba_sku=snapshot.doba_sku,
            shopify_product_id=mapping.shopify_product_id,
            shopify_variant_id=mapping.shopify_variant_id,
            shopify_sku=mapping.shopify_sku,
            old_price=old_price,
            supplier_cost=float(snapshot.supplier_cost or 0.0),
            shipping_cost=float(snapshot.shipping_cost or 0.0),
            estimated_total_cost=calculation.estimated_total_cost,
            target_price=target_price,
            delta=delta,
            will_update_shopify=False,
            source_changed=source_changed,
            target_price_changed=target_price_changed,
            shopify_price_changed=shopify_price_changed,
            decision="keep_price",
            status="skipped",
        )

        if target_price < calculation.estimated_total_cost:
            items.append(base_item.model_copy(update={"decision": "manual_review", "status": "manual_review", "reason_codes": [REASON_TARGET_PRICE_BELOW_COST]}))
            continue

        if old_price > 0:
            increase_percent = ((target_price - old_price) / old_price) * 100
            if increase_percent > settings.price_sync_max_increase_percent_without_review:
                items.append(base_item.model_copy(update={"decision": "manual_review", "status": "manual_review", "reason_codes": [REASON_PRICE_INCREASE_TOO_LARGE]}))
                continue
            if abs(increase_percent) > settings.price_sync_max_decrease_percent_without_review and increase_percent < 0:
                items.append(base_item.model_copy(update={"decision": "manual_review", "status": "manual_review", "reason_codes": [REASON_PRICE_DECREASE_TOO_LARGE]}))
                continue

        if not source_changed:
            items.append(base_item.model_copy(update={"reason_codes": [REASON_SOURCE_UNCHANGED]}))
            continue
        if not target_price_changed:
            items.append(base_item.model_copy(update={"reason_codes": [REASON_TARGET_PRICE_UNCHANGED]}))
            continue
        if not shopify_price_changed:
            items.append(base_item.model_copy(update={"reason_codes": [REASON_SHOPIFY_PRICE_ALREADY_CORRECT]}))
            continue

        decision = "increase_price" if delta > 0 else "decrease_price"
        items.append(base_item.model_copy(update={"decision": decision, "status": "planned", "reason_codes": ["price_changed"], "will_update_shopify": True}))

    return items


def _manual_review_item(
    store_name: str,
    snapshot: DobaPriceSnapshot,
    mapping: SkuMappingRecord,
    reason_code: str,
) -> PriceSyncItem:
    return PriceSyncItem(
        store_name=store_name,
        doba_product_id=snapshot.doba_product_id,
        doba_sku=snapshot.doba_sku,
        shopify_product_id=mapping.shopify_product_id,
        shopify_variant_id=mapping.shopify_variant_id,
        shopify_sku=mapping.shopify_sku,
        supplier_cost=float(snapshot.supplier_cost or 0.0),
        shipping_cost=float(snapshot.shipping_cost or 0.0),
        estimated_total_cost=float(snapshot.estimated_total_cost or 0.0),
        decision="manual_review",
        reason_codes=[reason_code],
        status="manual_review",
    )
