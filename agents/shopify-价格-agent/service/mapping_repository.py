from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from models.price_sync import SkuMappingRecord


class MappingRepository:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (Path(__file__).resolve().parents[1] / "runtime" / "mappings.json")

    def load_records(self, overrides: list[SkuMappingRecord] | list[dict] | None = None) -> list[SkuMappingRecord]:
        if overrides is not None:
            return [item if isinstance(item, SkuMappingRecord) else SkuMappingRecord.model_validate(item) for item in overrides]
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return [SkuMappingRecord.model_validate(item) for item in payload]

    def save_records(self, records: list[SkuMappingRecord] | list[dict]) -> str:
        payload = [
            item.model_dump(mode="json") if isinstance(item, SkuMappingRecord) else SkuMappingRecord.model_validate(item).model_dump(mode="json")
            for item in records
        ]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        return str(self.path.resolve())

    def find_unique_mapping(
        self,
        *,
        store_name: str,
        giga_sku: str,
        records: list[SkuMappingRecord],
    ) -> tuple[SkuMappingRecord | None, str | None]:
        candidates = [
            item
            for item in records
            if item.store_name == store_name and item.giga_sku == giga_sku and item.mapping_status == "active"
        ]
        if not candidates:
            return None, "missing_target"
        if len(candidates) > 1:
            return None, "duplicated_source"
        mapping = candidates[0]
        duplicates = [
            item
            for item in records
            if item.store_name == store_name
            and item.shopify_variant_id == mapping.shopify_variant_id
            and item.giga_sku != giga_sku
            and item.mapping_status == "active"
        ]
        if duplicates:
            return None, "duplicated_target"
        return mapping, None

    def build_validation_report(
        self,
        *,
        store_name: str,
        records: list[SkuMappingRecord],
    ) -> dict[str, Any]:
        scoped = [item for item in records if item.store_name == store_name]
        missing_target = [
            item.giga_sku
            for item in scoped
            if item.mapping_status != "active" or not item.shopify_variant_id or not item.shopify_product_id
        ]

        source_counts: dict[str, list[SkuMappingRecord]] = {}
        target_counts: dict[str, list[SkuMappingRecord]] = {}
        for item in scoped:
            source_counts.setdefault(item.giga_sku, []).append(item)
            if item.shopify_variant_id:
                target_counts.setdefault(item.shopify_variant_id, []).append(item)

        duplicate_sources = {
            key: [row.shopify_variant_id for row in value]
            for key, value in source_counts.items()
            if len([row for row in value if row.mapping_status == "active"]) > 1
        }
        duplicate_targets = {
            key: [row.giga_sku for row in value]
            for key, value in target_counts.items()
            if len([row for row in value if row.mapping_status == "active"]) > 1
        }
        return {
            "store_name": store_name,
            "record_count": len(scoped),
            "missing_mapping_count": len(missing_target),
            "duplicate_source_count": len(duplicate_sources),
            "duplicate_target_count": len(duplicate_targets),
            "missing_mapping_skus": sorted(set(missing_target)),
            "duplicate_sources": duplicate_sources,
            "duplicate_targets": duplicate_targets,
        }

    def write_template(self, destination: Path | None = None) -> str:
        target = destination or self.path.with_name("mapping_template.json")
        payload = [
            {
                "store_name": "demo-store",
                "giga_sku": "GIGA-SKU-001",
                "shopify_product_id": "gid://shopify/Product/1234567890",
                "shopify_variant_id": "gid://shopify/ProductVariant/1234567890",
                "shopify_sku": "SHOPIFY-SKU-001",
                "mapping_status": "active",
                "updated_at": "",
            }
        ]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        return str(target.resolve())
