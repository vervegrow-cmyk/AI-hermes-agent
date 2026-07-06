from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from models.price_sync import SkuMappingRecord
from models.variant_mapping import VariantMappingRecord


class MappingRepository:
    def __init__(self, root: Path | None = None, path: Path | None = None) -> None:
        resolved_path = path
        self.root = root or (resolved_path.parent if resolved_path is not None else Path(__file__).resolve().parents[1] / "runtime")
        self.path = resolved_path or (self.root / "mappings.json")
        self.template_path = self.root / "mapping_template.json"
        self.candidates_path = self.root / "mapping_candidates.json"
        self.review_csv_path = self.root / "mapping_review.csv"
        self.unmatched_doba_path = self.root / "mapping_unmatched_doba.json"
        self.unmatched_shopify_path = self.root / "mapping_unmatched_shopify.json"
        self.duplicates_path = self.root / "mapping_duplicates.json"

    def ensure_layout(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        for file_path, default in (
            (self.path, "[]\n"),
            (self.template_path, "[]\n"),
            (self.candidates_path, "[]\n"),
            (self.unmatched_doba_path, "[]\n"),
            (self.unmatched_shopify_path, "[]\n"),
            (self.duplicates_path, "{}\n"),
        ):
            if not file_path.exists():
                file_path.write_text(default, encoding="utf-8")

    def load_records(self, overrides: list[SkuMappingRecord] | list[dict] | None = None) -> list[SkuMappingRecord]:
        if overrides is not None:
            return [item if isinstance(item, SkuMappingRecord) else SkuMappingRecord.model_validate(item) for item in overrides]
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8") or "[]")
        return [SkuMappingRecord.model_validate(item) for item in payload]

    def load_variant_records(self) -> list[VariantMappingRecord]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8") or "[]")
        return [VariantMappingRecord.model_validate(item) for item in payload]

    def save_records(self, records: list[SkuMappingRecord] | list[dict]) -> str:
        payload = [
            item.model_dump(mode="json") if isinstance(item, SkuMappingRecord) else SkuMappingRecord.model_validate(item).model_dump(mode="json")
            for item in records
        ]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        return str(self.path.resolve())

    def save_variant_records(self, records: list[VariantMappingRecord] | list[dict]) -> str:
        payload = [
            item.model_dump(mode="json") if isinstance(item, VariantMappingRecord) else VariantMappingRecord.model_validate(item).model_dump(mode="json")
            for item in records
        ]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        return str(self.path.resolve())

    def save_candidates(self, payload: list[dict[str, Any]]) -> str:
        self.candidates_path.parent.mkdir(parents=True, exist_ok=True)
        self.candidates_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        return str(self.candidates_path.resolve())

    def save_unmatched_doba(self, payload: list[dict[str, Any]]) -> str:
        self.unmatched_doba_path.parent.mkdir(parents=True, exist_ok=True)
        self.unmatched_doba_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        return str(self.unmatched_doba_path.resolve())

    def save_unmatched_shopify(self, payload: list[dict[str, Any]]) -> str:
        self.unmatched_shopify_path.parent.mkdir(parents=True, exist_ok=True)
        self.unmatched_shopify_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        return str(self.unmatched_shopify_path.resolve())

    def save_duplicates(self, payload: dict[str, Any]) -> str:
        self.duplicates_path.parent.mkdir(parents=True, exist_ok=True)
        self.duplicates_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        return str(self.duplicates_path.resolve())

    def save_review_rows(self, rows: list[dict[str, Any]]) -> str:
        self.review_csv_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            "store_name",
            "supplier",
            "doba_product_id",
            "doba_sku",
            "doba_title",
            "shopify_product_id",
            "shopify_variant_id",
            "shopify_sku",
            "shopify_product_title",
            "shopify_variant_title",
            "match_type",
            "match_confidence",
            "mapping_status",
            "reason_code",
            "manual_note",
        ]
        with self.review_csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow({key: row.get(key, "") for key in fieldnames})
        return str(self.review_csv_path.resolve())

    def read_review_file(self, file_path: str) -> list[dict[str, Any]]:
        target = Path(file_path)
        if not target.is_absolute():
            target = self.root.parent / file_path
        if target.suffix.lower() == ".json":
            return list(json.loads(target.read_text(encoding="utf-8") or "[]"))
        with target.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def find_unique_mapping(
        self,
        *,
        store_name: str,
        doba_sku: str,
        records: list[SkuMappingRecord],
    ) -> tuple[SkuMappingRecord | None, str | None]:
        candidates = [
            item
            for item in records
            if item.store_name == store_name and item.doba_sku == doba_sku and item.mapping_status == "active"
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
            and item.doba_sku != doba_sku
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
            item.doba_sku
            for item in scoped
            if item.mapping_status != "active" or not item.shopify_variant_id or not item.shopify_product_id
        ]
        source_counts: dict[str, list[SkuMappingRecord]] = {}
        target_counts: dict[str, list[SkuMappingRecord]] = {}
        for item in scoped:
            source_counts.setdefault(item.doba_sku, []).append(item)
            if item.shopify_variant_id:
                target_counts.setdefault(item.shopify_variant_id, []).append(item)

        duplicate_sources = {
            key: [row.shopify_variant_id for row in value]
            for key, value in source_counts.items()
            if len([row for row in value if row.mapping_status == "active"]) > 1
        }
        duplicate_targets = {
            key: [row.doba_sku for row in value]
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

    def build_mapping_stats(self, *, store_name: str, records: list[VariantMappingRecord], total_shopify_variants: int = 0, total_doba_skus: int = 0) -> dict[str, Any]:
        scoped = [item for item in records if item.store_name == store_name]
        return {
            "store_name": store_name,
            "total_doba_skus": total_doba_skus or len({item.doba_sku for item in scoped if item.doba_sku}),
            "total_shopify_variants": total_shopify_variants or len({item.shopify_variant_id for item in scoped if item.shopify_variant_id}),
            "active_mappings": sum(1 for item in scoped if item.mapping_status == "active"),
            "candidate_mappings": sum(1 for item in scoped if item.mapping_status == "candidate"),
            "manual_review": sum(1 for item in scoped if item.mapping_status == "manual_review"),
            "unmatched_doba": sum(1 for item in scoped if item.mapping_status == "unmatched_doba"),
            "unmatched_shopify": sum(1 for item in scoped if item.mapping_status == "unmatched_shopify"),
            "duplicate_source": sum(1 for item in scoped if item.mapping_status == "duplicate_source"),
            "duplicate_target": sum(1 for item in scoped if item.mapping_status == "duplicate_target"),
            "disabled": sum(1 for item in scoped if item.mapping_status == "disabled"),
        }

    def write_template(self, destination: Path | None = None) -> str:
        target = destination or self.template_path
        payload = [
            {
                "store_name": "4ea863-98.myshopify.com",
                "supplier": "doba",
                "doba_product_id": "DOBA-PRODUCT-ID",
                "doba_sku": "DOBA-SKU-001",
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
