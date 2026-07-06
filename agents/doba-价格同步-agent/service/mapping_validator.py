from __future__ import annotations

from models.variant_mapping import VariantMappingRecord


VALID_STATUSES = {
    "active",
    "candidate",
    "manual_review",
    "unmatched_doba",
    "unmatched_shopify",
    "duplicate_source",
    "duplicate_target",
    "disabled",
}


class MappingValidator:
    def validate(self, *, store_name: str, records: list[VariantMappingRecord]) -> dict:
        scoped = [item for item in records if item.store_name == store_name]
        duplicate_source = 0
        duplicate_target = 0
        missing_required_fields = 0
        invalid_shopify_variant_id = 0
        source_map: dict[str, list[VariantMappingRecord]] = {}
        target_map: dict[str, list[VariantMappingRecord]] = {}

        for item in scoped:
            if item.mapping_status not in VALID_STATUSES:
                missing_required_fields += 1
            if item.mapping_status == "active":
                if not item.doba_sku or not item.shopify_product_id or not item.shopify_variant_id:
                    missing_required_fields += 1
                if item.shopify_variant_id and not item.shopify_variant_id.startswith("gid://shopify/ProductVariant/"):
                    invalid_shopify_variant_id += 1
            source_map.setdefault(item.doba_sku, []).append(item)
            if item.shopify_variant_id:
                target_map.setdefault(item.shopify_variant_id, []).append(item)

        for values in source_map.values():
            if len([item for item in values if item.mapping_status == "active"]) > 1:
                duplicate_source += 1
        for values in target_map.values():
            if len([item for item in values if item.mapping_status == "active"]) > 1:
                duplicate_target += 1

        passed = duplicate_source == 0 and duplicate_target == 0 and missing_required_fields == 0 and invalid_shopify_variant_id == 0
        return {
            "store_name": store_name,
            "mappings_total": len(scoped),
            "active_total": sum(1 for item in scoped if item.mapping_status == "active"),
            "duplicate_source": duplicate_source,
            "duplicate_target": duplicate_target,
            "missing_required_fields": missing_required_fields,
            "invalid_shopify_variant_id": invalid_shopify_variant_id,
            "result": "pass" if passed else "fail",
        }

