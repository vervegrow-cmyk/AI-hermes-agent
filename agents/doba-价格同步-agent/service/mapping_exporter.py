from __future__ import annotations

from service.mapping_repository import MappingRepository


class MappingExporter:
    def __init__(self, repository: MappingRepository | None = None) -> None:
        self.repository = repository or MappingRepository()

    def export_review(self, *, store_name: str) -> dict:
        records = [
            item.model_dump(mode="json")
            for item in self.repository.load_variant_records()
            if item.store_name == store_name and item.mapping_status != "active"
        ]
        path = self.repository.save_review_rows(records)
        return {"ok": True, "path": path, "items": len(records)}
