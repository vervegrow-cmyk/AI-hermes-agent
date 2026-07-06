from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from models.price_sync import utc_now_iso


MappingStatus = Literal[
    "active",
    "candidate",
    "manual_review",
    "unmatched_doba",
    "unmatched_shopify",
    "duplicate_source",
    "duplicate_target",
    "disabled",
]

MatchType = Literal[
    "exact_sku",
    "exact_supplier_sku",
    "metafield_doba_sku",
    "metafield_doba_product_id",
    "manual_import",
    "previous_mapping",
    "unmatched",
    "duplicate",
    "unknown",
]


class ShopifyVariantSnapshot(BaseModel):
    store_name: str = ""
    shopify_product_id: str
    shopify_variant_id: str
    shopify_sku: str = ""
    shopify_product_title: str = ""
    shopify_variant_title: str = ""
    shopify_vendor: str = ""
    doba_sku_metafield: str = ""
    doba_product_id_metafield: str = ""
    status: str = ""


class VariantMappingRecord(BaseModel):
    store_name: str = ""
    supplier: str = "doba"
    doba_product_id: str = ""
    doba_sku: str = ""
    doba_title: str = ""
    shopify_product_id: str = ""
    shopify_variant_id: str = ""
    shopify_sku: str = ""
    shopify_product_title: str = ""
    shopify_variant_title: str = ""
    match_type: MatchType = "unknown"
    match_confidence: int = 0
    mapping_status: MappingStatus = "candidate"
    reason_code: str = ""
    last_price_hash: str = ""
    last_doba_updated_at: str = ""
    last_shopify_synced_at: str = ""
    manual_note: str = ""
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class VariantMappingBuildRequest(BaseModel):
    store_name: str = ""
    sync_scope: str = "full"
    print_detail: bool = True
    doba_snapshots: list[dict] = Field(default_factory=list)
    shopify_variants: list[dict] = Field(default_factory=list)


class VariantMappingValidateRequest(BaseModel):
    store_name: str = ""


class VariantMappingImportRequest(BaseModel):
    store_name: str = ""
    file_path: str
