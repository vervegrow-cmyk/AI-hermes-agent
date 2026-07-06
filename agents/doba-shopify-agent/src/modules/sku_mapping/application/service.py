from __future__ import annotations

from src.shared.contracts.mapping import ResolveSkuCommand, SkuMappingRecord
from src.shared.repositories.protocols import SkuMappingRepository


def resolve_sku_mapping(command: ResolveSkuCommand, repository: SkuMappingRepository) -> SkuMappingRecord:
    if command.sku:
        existing = repository.get_by_sku(command.sku)
        if existing:
            return existing
    if command.supplier_product_id:
        existing = repository.get_by_supplier_product_id(command.supplier_product_id)
        if existing:
            return existing
    return SkuMappingRecord(
        supplier_product_id=command.supplier_product_id,
        sku=command.sku,
        shopify_product_id="",
        shopify_variant_id="",
    )

