from __future__ import annotations

from models.variant_mapping import VariantMappingRecord
from service.mapping_repository import MappingRepository


class MappingImporter:
    def __init__(self, repository: MappingRepository | None = None) -> None:
        self.repository = repository or MappingRepository()

    def import_reviewed(self, *, store_name: str, file_path: str) -> dict:
        existing = {
            (item.store_name, item.doba_sku): item
            for item in self.repository.load_variant_records()
        }
        rows = self.repository.read_review_file(file_path)
        imported = 0
        for row in rows:
            if str(row.get("store_name") or store_name) != store_name:
                continue
            doba_sku = str(row.get("doba_sku") or "").strip()
            if not doba_sku:
                continue
            record = VariantMappingRecord.model_validate(
                {
                    "store_name": store_name,
                    "supplier": row.get("supplier", "doba"),
                    "doba_product_id": row.get("doba_product_id", ""),
                    "doba_sku": doba_sku,
                    "doba_title": row.get("doba_title", ""),
                    "shopify_product_id": row.get("shopify_product_id", ""),
                    "shopify_variant_id": row.get("shopify_variant_id", ""),
                    "shopify_sku": row.get("shopify_sku", ""),
                    "shopify_product_title": row.get("shopify_product_title", ""),
                    "shopify_variant_title": row.get("shopify_variant_title", ""),
                    "match_type": row.get("match_type", "manual_import"),
                    "match_confidence": int(row.get("match_confidence", 100) or 100),
                    "mapping_status": row.get("mapping_status", "active"),
                    "reason_code": row.get("reason_code", "matched_by_manual_import"),
                    "manual_note": row.get("manual_note", ""),
                }
            )
            existing[(store_name, doba_sku)] = record
            imported += 1
        path = self.repository.save_variant_records(list(existing.values()))
        return {"ok": True, "imported": imported, "path": path}

