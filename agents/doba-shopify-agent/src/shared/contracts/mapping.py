from __future__ import annotations

from pydantic import BaseModel, model_validator


class ResolveSkuCommand(BaseModel):
    supplier_product_id: str = ""
    sku: str = ""


class SkuMapping(BaseModel):
    supplier_product_id: str = ""
    supplier_sku: str = ""
    sku: str = ""
    shopify_product_id: str = ""
    shopify_variant_id: str = ""
    handle: str = ""
    product_hash: str = ""
    created_at: str = ""

    @model_validator(mode="after")
    def _sync_supplier_sku(self) -> "SkuMapping":
        if not self.supplier_sku and self.sku:
            self.supplier_sku = self.sku
        if not self.sku and self.supplier_sku:
            self.sku = self.supplier_sku
        return self


class SkuMappingRecord(SkuMapping):
    pass
