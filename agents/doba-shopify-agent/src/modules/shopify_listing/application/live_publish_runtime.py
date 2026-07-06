from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import math
import os
import re
import time
from typing import Any

import bootstrap
from shared.clients import DobaClient, ShopifyAuthClient, ShopifyGraphQLError
from shared.config import get_settings
from src.modules.supplier_archive.application.ship_from_resolver import (
    normalize_ship_from_country,
    resolve_ship_from,
)
from src.modules.shopify_listing.application.content_enrichment import (
    build_candidate_enrichment,
    build_post_publish_review,
    summarize_enrichment,
)
from src.modules.supplier_archive.application.service import archive_supplier_products
from src.modules.shopify_listing.runners.publish_vendor_catalog import (
    CategoryResolution,
    _hydrate_resolution,
    _resolve_category,
    _search_taxonomy_category_id,
)
from src.shared.contracts.publish_mapping import ShopifyPublishMappingRecord
from src.shared.contracts.product import DobaProductInput
from src.shared.repositories import (
    LocalJsonPublishMappingRepository,
    LocalJsonSupplierArchiveRepository,
    SQLiteCandidatePoolRepository,
    SQLitePublishMappingRepository,
    SQLiteSupplierArchiveRepository,
)


NEW_ARRIVALS_COLLECTION_TITLE = "NEW ARRIVALS"
SHOPIFY_PLATFORM_NAME = "Shopify"
DEFAULT_PAGE_SIZE = 20
DEFAULT_TARGET_COUNTRY = "US"
DEFAULT_CHANNELS = ("Inbox", "Shop", "Pinterest", "Facebook & Instagram")
DEFAULT_INVENTORY_THRESHOLD = 10
DEFAULT_LIST_MIN_INVENTORY = 11
SOURCE_VENDOR_NAME = "DOBA"
DEFAULT_CANDIDATE_POOL_PATH = Path("data/runtime/shopify_listing/doba_publish_candidates.json")
DEFAULT_TEMPORARY_SELLER_BLOCKLIST = {"green market"}
DEFAULT_TEMPORARY_CATEGORY_BLOCKLIST = {"tracking devices"}


SPU_LIST_QUERY_PATH = "/api/goods/doba/spu/list"
SPU_DETAIL_QUERY_PATH = "/api/goods/doba/spu/detail"
STOCK_QUERY_PATH = "/api/goods/doba/stock"
SHIPPING_COST_QUERY_PATH = "/api/shipping/doba/cost/goods"
PLATFORM_LIST_QUERY_PATH = "/api/platform/list"
SUPPLIER_LIST_QUERY_PATH = "/api/supplier/doba/list"


PRODUCT_CREATE = """
mutation CreateProduct($input: ProductCreateInput!) {
  productCreate(product: $input) {
    product {
      id
      title
      status
      handle
      options {
        id
        name
        optionValues {
          id
          name
        }
      }
      variants(first: 50) {
        edges {
          node {
            id
            sku
            price
            inventoryItem {
              id
            }
            selectedOptions {
              name
              value
            }
          }
        }
      }
    }
    userErrors {
      field
      message
    }
  }
}
"""

PRODUCT_UPDATE = """
mutation UpdateProduct($product: ProductUpdateInput!) {
  productUpdate(product: $product) {
    product {
      id
      title
      status
      handle
      variants(first: 50) {
        edges {
          node {
            id
            sku
            price
            inventoryItem {
              id
            }
            selectedOptions {
              name
              value
            }
          }
        }
      }
      options {
        id
        name
      }
    }
    userErrors {
      field
      message
    }
  }
}
"""

PRODUCT_BY_ID = """
query ProductById($id: ID!) {
  product(id: $id) {
    id
    title
    status
    handle
    vendor
    productType
    category {
      id
      name
      fullName
    }
    tags
    options {
      id
      name
      optionValues {
        id
        name
      }
    }
    variants(first: 100) {
      edges {
        node {
          id
          sku
          price
          inventoryItem {
            id
          }
          selectedOptions {
            name
            value
          }
        }
      }
    }
    resourcePublicationsV2(first: 20, onlyPublished: true) {
      edges {
        node {
          publication {
            id
            name
          }
        }
      }
    }
  }
}
"""

PRODUCTS_BY_TAG = """
query ProductsByTag($query: String!) {
  products(first: 10, query: $query) {
    edges {
      node {
        id
        title
        status
        handle
      }
    }
  }
}
"""

PRODUCT_OPTIONS_CREATE = """
mutation ProductOptionsCreate(
  $productId: ID!,
  $options: [OptionCreateInput!]!,
  $variantStrategy: ProductOptionCreateVariantStrategy
) {
  productOptionsCreate(productId: $productId, options: $options, variantStrategy: $variantStrategy) {
    product {
      id
      options {
        id
        name
        optionValues {
          id
          name
        }
      }
    }
    userErrors {
      field
      message
      code
    }
  }
}
"""

PRODUCT_VARIANTS_BULK_UPDATE = """
mutation ProductVariantsBulkUpdate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
  productVariantsBulkUpdate(productId: $productId, variants: $variants) {
    productVariants {
      id
      sku
      price
      inventoryItem {
        id
      }
      selectedOptions {
        name
        value
      }
    }
    userErrors {
      field
      message
    }
  }
}
"""

PRODUCT_VARIANTS_BULK_CREATE = """
mutation ProductVariantsBulkCreate(
  $productId: ID!,
  $variants: [ProductVariantsBulkInput!]!,
  $strategy: ProductVariantsBulkCreateStrategy
) {
  productVariantsBulkCreate(productId: $productId, variants: $variants, strategy: $strategy) {
    productVariants {
      id
      sku
      price
      inventoryItem {
        id
      }
      selectedOptions {
        name
        value
      }
    }
    userErrors {
      field
      message
    }
  }
}
"""

PRODUCT_CREATE_MEDIA = """
mutation ProductCreateMedia($productId: ID!, $media: [CreateMediaInput!]!) {
  productCreateMedia(productId: $productId, media: $media) {
    media {
      alt
      mediaContentType
      status
    }
    mediaUserErrors {
      field
      message
    }
  }
}
"""

PUBLICATIONS_QUERY = """
query PublicationsList {
  publications(first: 50) {
    edges {
      node {
        id
        name
      }
    }
  }
}
"""

COLLECTIONS_QUERY = """
query CollectionByTitle($query: String!) {
  collections(first: 10, query: $query) {
    edges {
      node {
        id
        title
        handle
      }
    }
  }
}
"""

COLLECTION_CREATE = """
mutation CreateCollection($input: CollectionInput!) {
  collectionCreate(input: $input) {
    collection {
      id
      title
      handle
    }
    userErrors {
      field
      message
    }
  }
}
"""

COLLECTION_ADD_PRODUCTS = """
mutation AddProductsToCollection($id: ID!, $productIds: [ID!]!) {
  collectionAddProducts(id: $id, productIds: $productIds) {
    collection {
      id
      title
    }
    userErrors {
      field
      message
    }
  }
}
"""

PUBLISH_PRODUCT = """
mutation PublishProduct($id: ID!, $input: [PublicationInput!]!) {
  publishablePublish(id: $id, input: $input) {
    publishable {
      resourcePublicationsCount {
        count
      }
    }
    userErrors {
      field
      message
    }
  }
}
"""

UNPUBLISH_PRODUCT = """
mutation UnpublishProduct($id: ID!, $input: [PublicationInput!]!) {
  publishableUnpublish(id: $id, input: $input) {
    userErrors {
      field
      message
    }
  }
}
"""

UPSERT_PRODUCT_METAFIELDS = """
mutation UpsertProductMetafields($metafields: [MetafieldsSetInput!]!) {
  metafieldsSet(metafields: $metafields) {
    metafields {
      namespace
      key
    }
    userErrors {
      field
      message
      code
    }
  }
}
"""


@dataclass(slots=True)
class DobaVariantCandidate:
    sku: str
    sku_code: str
    sku_id: str
    option_values: dict[str, str]
    inventory: int
    source_price: float
    shipping_cost: float
    cost_price: float
    sale_price: float
    compare_at_price: float
    ship_time_days: int
    item_no: str
    ship_name: str
    warehouse: str
    image_urls: list[str]
    warehouse_name: str = ""
    ship_from_raw: str = ""
    ship_from_source: str = ""
    ship_from_confidence: str = ""


@dataclass(slots=True)
class DobaProductCandidate:
    spu_id: str
    spu_no: str
    supplier_id: str
    category_id: str
    merge_key: str
    seller_name: str
    seller_info: dict[str, Any]
    title: str
    category_name: str
    description_html: str
    brand: str
    ship_from_country: str
    ship_from_source: str = "unknown"
    ship_from_confidence: str = "low"
    processing_time: int = 0
    store_url: str = ""
    image_urls: list[str] = field(default_factory=list)
    variants: list[DobaVariantCandidate] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    category_metafields: dict[str, Any] = field(default_factory=dict)
    content_enrichment: dict[str, Any] = field(default_factory=dict)
    source_vendor: str = SOURCE_VENDOR_NAME
    source_channels: list[str] = field(default_factory=lambda: list(DEFAULT_CHANNELS))


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")
    return slug[:255] or "doba-product"


def _candidate_to_summary(candidate: DobaProductCandidate) -> dict[str, Any]:
    return {
        "spuId": candidate.spu_id,
        "spuNo": candidate.spu_no,
        "title": candidate.title,
        "sellerName": candidate.seller_name,
        "cateId": candidate.category_id,
        "cateName": candidate.category_name,
    }


def _candidate_to_detail(candidate: DobaProductCandidate) -> dict[str, Any]:
    return {
        "spuId": candidate.spu_id,
        "spuNo": candidate.spu_no,
        "busiId": candidate.supplier_id,
        "sellerName": candidate.seller_name,
        "title": candidate.title,
        "cateId": candidate.category_id,
        "cateName": candidate.category_name,
        "goodsDesc": candidate.description_html,
        "brand": candidate.brand,
        "shipFromCountry": candidate.ship_from_country,
        "shipFromSource": candidate.ship_from_source,
        "shipFromConfidence": candidate.ship_from_confidence,
        "pictureUrl": candidate.image_urls[0] if candidate.image_urls else "",
        "children": [
            {
                "skuId": variant.sku_id,
                "skuCode": variant.sku_code,
                "itemNo": variant.item_no,
                "shipFrom": variant.ship_from_raw,
                "shipFromSource": variant.ship_from_source,
                "shipFromConfidence": variant.ship_from_confidence,
                "skuPicList": list(variant.image_urls),
                "variantProps": [
                    {"propName": option_name, "propValue": option_value}
                    for option_name, option_value in variant.option_values.items()
                ],
                "stocks": [
                    {
                        "itemNo": variant.item_no,
                        "availableNum": variant.inventory,
                        "regionName": variant.warehouse,
                        "regionId": "US" if variant.warehouse == "United States" else variant.warehouse,
                    }
                ],
            }
            for variant in candidate.variants
        ],
    }


def _serialize_candidate(candidate: DobaProductCandidate) -> dict[str, Any]:
    return {
        "spu_id": candidate.spu_id,
        "spu_no": candidate.spu_no,
        "supplier_id": candidate.supplier_id,
        "category_id": candidate.category_id,
        "merge_key": candidate.merge_key,
        "seller_name": candidate.seller_name,
        "seller_info": dict(candidate.seller_info),
        "title": candidate.title,
        "category_name": candidate.category_name,
        "description_html": candidate.description_html,
        "brand": candidate.brand,
        "ship_from_country": candidate.ship_from_country,
        "ship_from_source": candidate.ship_from_source,
        "ship_from_confidence": candidate.ship_from_confidence,
        "processing_time": candidate.processing_time,
        "store_url": candidate.store_url,
        "image_urls": list(candidate.image_urls),
        "tags": list(candidate.tags),
        "category_metafields": dict(candidate.category_metafields),
        "content_enrichment": dict(candidate.content_enrichment),
        "source_vendor": candidate.source_vendor,
        "source_channels": list(candidate.source_channels),
        "variants": [
            {
                "sku": variant.sku,
                "sku_code": variant.sku_code,
                "sku_id": variant.sku_id,
                "option_values": dict(variant.option_values),
                "inventory": variant.inventory,
                "source_price": variant.source_price,
                "shipping_cost": variant.shipping_cost,
                "cost_price": variant.cost_price,
                "sale_price": variant.sale_price,
                "compare_at_price": variant.compare_at_price,
                "ship_time_days": variant.ship_time_days,
                "item_no": variant.item_no,
                "ship_name": variant.ship_name,
                "warehouse": variant.warehouse,
                "image_urls": list(variant.image_urls),
                "warehouse_name": variant.warehouse_name,
                "ship_from_raw": variant.ship_from_raw,
                "ship_from_source": variant.ship_from_source,
                "ship_from_confidence": variant.ship_from_confidence,
            }
            for variant in candidate.variants
        ],
    }


def _deserialize_candidate(payload: dict[str, Any]) -> DobaProductCandidate:
    candidate = DobaProductCandidate(
        spu_id=str(payload.get("spu_id") or ""),
        spu_no=str(payload.get("spu_no") or ""),
        supplier_id=str(payload.get("supplier_id") or ""),
        category_id=str(payload.get("category_id") or ""),
        merge_key=str(payload.get("merge_key") or ""),
        seller_name=str(payload.get("seller_name") or ""),
        seller_info=dict(payload.get("seller_info") or {}),
        title=str(payload.get("title") or ""),
        category_name=str(payload.get("category_name") or ""),
        description_html=str(payload.get("description_html") or ""),
        brand=str(payload.get("brand") or ""),
        ship_from_country=str(payload.get("ship_from_country") or "UNKNOWN"),
        ship_from_source=str(payload.get("ship_from_source") or "unknown"),
        ship_from_confidence=str(payload.get("ship_from_confidence") or "low"),
        processing_time=_safe_int(payload.get("processing_time"), 0),
        store_url=str(payload.get("store_url") or ""),
        image_urls=_unique_strings(payload.get("image_urls") or []),
        variants=[
            DobaVariantCandidate(
                sku=str(variant.get("sku") or ""),
                sku_code=str(variant.get("sku_code") or ""),
                sku_id=str(variant.get("sku_id") or ""),
                option_values={str(key): str(value) for key, value in dict(variant.get("option_values") or {}).items() if str(key).strip()},
                inventory=_safe_int(variant.get("inventory"), 0),
                source_price=_safe_float(variant.get("source_price")),
                shipping_cost=_safe_float(variant.get("shipping_cost")),
                cost_price=_safe_float(variant.get("cost_price")),
                sale_price=_safe_float(variant.get("sale_price")),
                compare_at_price=_safe_float(variant.get("compare_at_price")),
                ship_time_days=_safe_int(variant.get("ship_time_days"), 0),
                item_no=str(variant.get("item_no") or ""),
                ship_name=str(variant.get("ship_name") or ""),
                warehouse=str(variant.get("warehouse") or ""),
                image_urls=_unique_strings(variant.get("image_urls") or []),
                warehouse_name=str(variant.get("warehouse_name") or ""),
                ship_from_raw=str(variant.get("ship_from_raw") or ""),
                ship_from_source=str(variant.get("ship_from_source") or "unknown"),
                ship_from_confidence=str(variant.get("ship_from_confidence") or "low"),
            )
            for variant in (payload.get("variants") or [])
        ],
        tags=_unique_strings(payload.get("tags") or []),
        category_metafields=dict(payload.get("category_metafields") or {}),
        content_enrichment=dict(payload.get("content_enrichment") or {}),
        source_vendor=str(payload.get("source_vendor") or SOURCE_VENDOR_NAME),
        source_channels=_unique_strings(payload.get("source_channels") or list(DEFAULT_CHANNELS)),
    )
    if not candidate.content_enrichment:
        _apply_candidate_enrichment(candidate)
    return candidate


def _normalize_merge_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", (value or "").lower())).strip()


def _build_merge_title_key(title: str) -> str:
    normalized = str(title or "").strip().lower()
    normalized = re.sub(r'(\d+(?:\.\d+)?"(?:x\d+(?:\.\d+)?"?)+)', " ", normalized)
    normalized = re.sub(r"\b\d+(?:\.\d+)?\s*(?:cm|in|inch|ft|lb|lbs|pcs)\b", " ", normalized)
    normalized = re.sub(r"^\s*\d+\s*piece[s]?\s+", "", normalized)
    normalized = re.sub(r"\bcushions\b", "cushion", normalized)
    phrase_patterns = [
        "poly rattan",
        "solid acacia wood",
        "acacia wood",
        "solid teak wood",
        "solid wood teak",
        "teak wood",
        "cast aluminum",
        "galvanized steel",
        "stainless steel",
        "firwood",
        "hot tub",
        "spa surround",
        "storage box",
    ]
    color_patterns = [
        "light gray",
        "cream white",
        "anthracite",
        "bronze",
        "beige",
        "black",
        "white",
        "brown",
        "green",
        "cream",
        "gray",
        "grey",
        "red",
        "blue",
        "khaki",
    ]
    for phrase in [*phrase_patterns, *color_patterns]:
        normalized = re.sub(rf"\b{re.escape(phrase)}\b", " ", normalized)
    normalized = re.sub(r"\bsolid\b", " ", normalized)
    normalized = re.sub(r"\bwith cushion\b", "with cushion", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return _normalize_merge_text(normalized)


def _extract_title_variant_attributes(title: str) -> dict[str, str]:
    text = str(title or "").strip()
    lower = text.lower()
    values: dict[str, str] = {}

    piece_match = re.search(r"\b(\d+)\s*piece[s]?\b", lower)
    if piece_match:
        values["Set Size"] = f"{piece_match.group(1)} Piece"

    color_patterns = [
        ("Light Gray", "light gray"),
        ("Cream White", "cream white"),
        ("Anthracite", "anthracite"),
        ("Bronze", "bronze"),
        ("Beige", "beige"),
        ("Black", "black"),
        ("White", "white"),
        ("Brown", "brown"),
        ("Green", "green"),
        ("Cream", "cream"),
        ("Gray", "gray"),
        ("Grey", "grey"),
        ("Red", "red"),
        ("Blue", "blue"),
        ("Khaki", "khaki"),
    ]
    for label, pattern in color_patterns:
        if re.search(rf"\b{re.escape(pattern)}\b", lower):
            values["Color"] = label
            break

    material_patterns = [
        ("Poly Rattan", "poly rattan"),
        ("Solid Acacia Wood", "solid acacia wood"),
        ("Acacia Wood", "acacia wood"),
        ("Solid Teak Wood", "solid teak wood"),
        ("Solid Wood Teak", "solid wood teak"),
        ("Teak Wood", "teak wood"),
        ("Cast Aluminum", "cast aluminum"),
        ("Galvanized Steel", "galvanized steel"),
        ("Stainless Steel", "stainless steel"),
        ("Firwood", "firwood"),
        ("Granite", "granite"),
    ]
    for label, pattern in material_patterns:
        if re.search(rf"\b{re.escape(pattern)}\b", lower):
            values["Material"] = label
            break

    if not values:
        values["Variant"] = text[:100]
    return values


def _normalize_option_name(name: str) -> str:
    raw = str(name or "").strip()
    if not raw:
        return ""
    if raw.lower() == "variant":
        return "Variant"
    normalized = re.sub(r"\s+", " ", raw.replace("_", " ").replace("-", " ")).strip()
    if not normalized:
        return ""
    return " ".join(part[:1].upper() + part[1:].lower() for part in normalized.split(" "))


def _normalize_option_values(option_values: dict[str, str]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for raw_name, raw_value in dict(option_values or {}).items():
        option_name = _normalize_option_name(str(raw_name or ""))
        if not option_name:
            continue
        option_value = str(raw_value or "").strip() or "Default"
        existing_value = str(normalized.get(option_name) or "").strip()
        if not existing_value:
            normalized[option_name] = option_value
            continue
        if existing_value == "Default" and option_value != "Default":
            normalized[option_name] = option_value
            continue
        if existing_value.lower() == option_value.lower():
            continue
    return normalized


def _build_merge_key(*, title: str, category_id: str, supplier_id: str, seller_name: str) -> str:
    raw = "|".join(
        [
            _build_merge_title_key(title),
            str(category_id or "").strip().lower(),
            str(supplier_id or "").strip().lower(),
            _normalize_merge_text(seller_name),
        ]
    )
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
    return digest


def _clean_html(value: str) -> str:
    return str(value or "").strip() or "<p>No product description provided by Doba.</p>"


def _parse_runtime_list_env(name: str) -> set[str]:
    raw = str(os.getenv(name, "") or "").strip()
    if not raw:
        return set()
    return {item.strip().lower() for item in raw.split(",") if item.strip()}


def _get_shopify_price_multiplier() -> float:
    value = _safe_float(os.getenv("SHOPIFY_PRICE_MULTIPLIER", "1.15"), 1.15)
    return max(value, 0.0)


def _derive_shopify_sale_price(source_price: float, shipping_cost: float = 0.0) -> float:
    return round(max((source_price * _get_shopify_price_multiplier()) + shipping_cost, 0.0), 2)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _candidate_runtime_policy_reason(*, seller_name: str, category_name: str) -> str | None:
    normalized_seller = str(seller_name or "").strip().lower()
    normalized_category = str(category_name or "").strip().lower()
    seller_allowlist = _parse_runtime_list_env("DOBA_SELLER_ALLOWLIST")
    seller_blocklist = _parse_runtime_list_env("DOBA_SELLER_BLOCKLIST") | set(DEFAULT_TEMPORARY_SELLER_BLOCKLIST)
    category_allowlist = _parse_runtime_list_env("DOBA_CATEGORY_ALLOWLIST")
    category_blocklist = _parse_runtime_list_env("DOBA_CATEGORY_BLOCKLIST") | set(DEFAULT_TEMPORARY_CATEGORY_BLOCKLIST)
    if seller_allowlist and normalized_seller and normalized_seller not in seller_allowlist:
        return "seller_not_in_allowlist"
    if normalized_seller and normalized_seller in seller_blocklist:
        return "seller_in_blocklist"
    if category_allowlist and normalized_category and normalized_category not in category_allowlist:
        return "category_not_in_allowlist"
    if normalized_category and normalized_category in category_blocklist:
        return "category_in_blocklist"
    return None


def _normalize_ship_from_label(value: Any) -> str:
    return normalize_ship_from_country(value)


def _build_category_metafields(*, category_id: str, category_name: str) -> dict[str, Any]:
    return {
        "doba_category_id": str(category_id or "").strip(),
        "doba_category_name": str(category_name or "").strip(),
    }


def _is_allowed_ship_from(value: str) -> bool:
    normalized = _normalize_ship_from_label(value)
    return normalized == "United States"


def _parse_ship_time_days(value: Any, fallback: int = 0) -> int:
    text = str(value or "").strip()
    if not text:
        return fallback
    numbers = [int(match) for match in re.findall(r"\d+", text)]
    if not numbers:
        return fallback
    return max(numbers)


def _unique_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = str(value or "").strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        result.append(cleaned)
    return result


def _next_cursor(page_number: int, page_size: int, index_in_page: int, page_count: int) -> tuple[int, int]:
    if index_in_page + 1 < page_count:
        return page_number, index_in_page + 1
    return page_number + 1, 0


def _candidate_pool_flat_index(page_number: int, page_size: int, index_in_page: int) -> int:
    return max(page_number - 1, 0) * max(page_size, 1) + max(index_in_page, 0)


def _candidate_pool_cursor_anchor_from_serialized(candidate: dict[str, Any] | None) -> dict[str, str]:
    if not isinstance(candidate, dict):
        return {}
    anchor = {
        "spu_no": str(candidate.get("spu_no") or "").strip(),
        "spu_id": str(candidate.get("spu_id") or "").strip(),
    }
    return {key: value for key, value in anchor.items() if value}


def _find_candidate_pool_anchor_index(
    serialized_candidates: list[dict[str, Any]],
    anchor: dict[str, Any] | None,
) -> int | None:
    if not isinstance(anchor, dict):
        return None
    anchor_spu_no = str(anchor.get("spu_no") or "").strip()
    anchor_spu_id = str(anchor.get("spu_id") or "").strip()
    if not anchor_spu_no and not anchor_spu_id:
        return None
    for index, item in enumerate(serialized_candidates):
        if not isinstance(item, dict):
            continue
        item_spu_no = str(item.get("spu_no") or "").strip()
        item_spu_id = str(item.get("spu_id") or "").strip()
        if anchor_spu_no and item_spu_no == anchor_spu_no:
            return index
        if anchor_spu_id and item_spu_id == anchor_spu_id:
            return index
    return None


def _set_candidate_pool_cursor_checkpoint(
    checkpoint: dict[str, Any],
    *,
    serialized_candidates: list[dict[str, Any]],
    page_size: int,
    next_page: int,
    next_index: int,
) -> None:
    checkpoint["cursor"] = {"next_page": next_page, "next_index": next_index}
    flat_index = _candidate_pool_flat_index(next_page, page_size, next_index)
    next_candidate = serialized_candidates[flat_index] if 0 <= flat_index < len(serialized_candidates) else None
    anchor = _candidate_pool_cursor_anchor_from_serialized(next_candidate)
    if anchor:
        checkpoint["cursor_anchor"] = anchor
    else:
        checkpoint.pop("cursor_anchor", None)


def _log(event: str, **payload: Any) -> None:
    body = " ".join(f"{key}={json.dumps(value, ensure_ascii=False)}" for key, value in payload.items())
    chinese_line = _format_chinese_log(event, payload)
    if chinese_line:
        print(chinese_line, flush=True)
    print(f"[doba_shopify_live_publish] {event} {body}".rstrip(), flush=True)


def _translate_reason(reason: str) -> str:
    mapping = {
        "seller_not_in_allowlist": "卖家不在允许名单中",
        "seller_in_blocklist": "卖家在屏蔽名单中",
        "category_not_in_allowlist": "类目不在允许名单中",
        "category_in_blocklist": "类目在屏蔽名单中",
        "ship_from_not_us_or_unknown": "发货地不是美国或发货地未知",
        "all_variants_inventory_below_threshold": "所有变体库存都未达到门槛",
        "missing_variant_stock_data": "缺少变体库存数据",
        "missing_variants": "缺少变体数据",
        "already_successfully_published": "该商品之前已经成功发布",
        "missing_shopify_category": "缺少 Shopify 类目映射",
        "active_product_exists": "Shopify 已存在 ACTIVE 商品",
        "interrupted_by_user": "用户手动中断",
        "not_us_or_inventory_below_threshold": "发货地不是美国或库存未达到门槛",
    }
    normalized = str(reason or "").strip()
    return mapping.get(normalized, normalized or "无")


def _format_chinese_log(event: str, payload: dict[str, Any]) -> str:
    if event == "candidate_pool_start":
        return (
            f"候选池生成开始：归档分组总数 {payload.get('total_groups', '?')}，"
            f"完整归档组数 {payload.get('full_archive_groups', '?')}，"
            f"目标国家 {payload.get('target_country', '')}，"
            f"库存门槛 {payload.get('inventory_threshold', '')}。"
        )
    if event == "candidate_pool_result":
        action = str(payload.get("action") or "")
        title = str(payload.get("title") or "")
        spu_no = str(payload.get("doba_spu_no") or "")
        if action == "qualified":
            return (
                f"候选池命中：SPU {spu_no}，标题《{title}》，"
                f"变体数 {payload.get('variant_count', 0)}，"
                f"发货地 {payload.get('ship_from_country', 'UNKNOWN')}，"
                f"库存 {payload.get('inventories', [])}。"
            )
        return f"候选池跳过：SPU {spu_no}，标题《{title}》，原因 {_translate_reason(str(payload.get('reason') or ''))}。"
    if event == "candidate_pool_summary":
        return (
            f"候选池完成：归档组数 {payload.get('total_groups', 0)}，"
            f"合格数量 {payload.get('qualified_count', 0)}，"
            f"发货地统计 {payload.get('ship_from_summary', {})}。"
        )
    if event == "scan_start":
        return (
            f"开始发布扫描：当前第 {payload.get('current_index', '?')} / {payload.get('total', '?')} 个，"
            f"SPU {payload.get('doba_spu_no', '')}，标题《{payload.get('title', '')}》。"
        )
    if event == "scan_result":
        action = str(payload.get("action") or "")
        title = str(payload.get("title") or "")
        spu_no = str(payload.get("doba_spu_no") or "")
        if action == "published":
            return (
                f"发布成功：SPU {spu_no}，标题《{title}》，"
                f"Shopify 商品 {payload.get('shopify_product_id', '')}，"
                f"变体数 {payload.get('variant_count', 0)}，"
                f"发货地 {payload.get('ship_from_country', 'UNKNOWN')}。"
            )
        if action == "skipped":
            return f"发布跳过：SPU {spu_no}，标题《{title}》，原因 {_translate_reason(str(payload.get('reason') or ''))}。"
        if action == "failed":
            return f"发布失败：SPU {spu_no}，标题《{title}》，原因 {_translate_reason(str(payload.get('reason') or ''))}。"
        if action == "interrupted":
            return f"发布中断：SPU {spu_no}，标题《{title}》，原因 用户手动中断。"
    return ""


def _doba_trust_env_enabled() -> bool:
    value = str(os.getenv("DOBA_TRUST_ENV", "true") or "").strip().lower()
    return value not in {"0", "false", "no", "off"}


def _configure_doba_client(client: DobaClient) -> DobaClient:
    try:
        client.trust_env = _doba_trust_env_enabled()
    except AttributeError:
        return client
    return client


def _load_checkpoint(report_path: str) -> dict[str, Any]:
    path = Path(report_path)
    if not path.exists():
        return {
            "started_at": _now_iso(),
            "updated_at": _now_iso(),
            "cursor": {"next_page": 1, "next_index": 0},
            "successful_spu_nos": [],
            "results": [],
            "summary": {
                "total_candidates": 0,
                "scanned_count": 0,
                "published_count": 0,
                "skipped_count": 0,
                "failed_count": 0,
            },
        }
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {
            "started_at": _now_iso(),
            "updated_at": _now_iso(),
            "cursor": {"next_page": 1, "next_index": 0},
            "successful_spu_nos": [],
            "results": [],
            "summary": {
                "total_candidates": 0,
                "scanned_count": 0,
                "published_count": 0,
                "skipped_count": 0,
                "failed_count": 0,
            },
        }


def _write_checkpoint(report_path: str, checkpoint: dict[str, Any]) -> str:
    checkpoint["updated_at"] = _now_iso()
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path.resolve())


def _build_resume_command(report_path: str) -> str:
    return f'python -m src.app.runners.run_doba_shopify_live_publish --report-path "{report_path}"'


def _empty_summary(total_candidates: int = 0) -> dict[str, int]:
    return {
        "total_candidates": total_candidates,
        "scanned_count": 0,
        "published_count": 0,
        "skipped_count": 0,
        "failed_count": 0,
    }


def _normalize_successful_spu_no(value: Any) -> str:
    spu_no = str(value or "").strip()
    if not spu_no:
        return ""
    upper_spu_no = spu_no.upper()
    if upper_spu_no.startswith("SPU-"):
        return ""
    return spu_no


def _load_published_spu_nos(repository: LocalJsonPublishMappingRepository) -> set[str]:
    return {
        normalized_spu_no
        for record in repository.list_publish_mappings()
        for normalized_spu_no in [_normalize_successful_spu_no(record.supplier_spu_no)]
        if normalized_spu_no
        and str(record.status or "").strip().lower() == "published"
    }


def _prepare_candidate_pool_checkpoint(
    *,
    checkpoint: dict[str, Any],
    candidate_payload: dict[str, Any],
    refresh_candidate_pool: bool,
    published_spu_nos: set[str],
    page_size: int,
) -> tuple[dict[str, Any], bool]:
    qualified_candidates = list(candidate_payload.get("qualified_candidates") or [])
    pool_generation = str(candidate_payload.get("generated_at") or "").strip()
    prior_generation = str(checkpoint.get("candidate_pool_generation") or "").strip()
    should_reset = (
        refresh_candidate_pool
        or str(checkpoint.get("source_mode") or "").strip() != "candidate_pool"
        or (pool_generation and pool_generation != prior_generation)
    )
    merged_successful_spu_nos = {
        normalized_spu_no
        for item in (checkpoint.get("successful_spu_nos") or [])
        for normalized_spu_no in [_normalize_successful_spu_no(item)]
        if normalized_spu_no
    }
    merged_successful_spu_nos.update(published_spu_nos)

    checkpoint["source_mode"] = "candidate_pool"
    checkpoint["candidate_pool_generation"] = pool_generation
    checkpoint["candidate_pool_summary"] = dict(candidate_payload.get("summary") or {})
    checkpoint["successful_spu_nos"] = sorted(merged_successful_spu_nos)
    checkpoint["summary"]["total_candidates"] = len(qualified_candidates)

    if should_reset:
        anchor_index: int | None = None
        can_preserve_cursor = (
            not refresh_candidate_pool
            and str(checkpoint.get("source_mode") or "").strip() == "candidate_pool"
            and bool(qualified_candidates)
        )
        if can_preserve_cursor:
            anchor_index = _find_candidate_pool_anchor_index(
                qualified_candidates,
                checkpoint.get("cursor_anchor"),
            )
            if anchor_index is None:
                fallback_index = _candidate_pool_flat_index(
                    _safe_int((checkpoint.get("cursor") or {}).get("next_page"), 1),
                    page_size,
                    _safe_int((checkpoint.get("cursor") or {}).get("next_index"), 0),
                )
                if 0 <= fallback_index < len(qualified_candidates):
                    anchor_index = fallback_index
        if anchor_index is not None:
            next_page = (anchor_index // max(page_size, 1)) + 1
            next_index = anchor_index % max(page_size, 1)
            _set_candidate_pool_cursor_checkpoint(
                checkpoint,
                serialized_candidates=qualified_candidates,
                page_size=page_size,
                next_page=next_page,
                next_index=next_index,
            )
            checkpoint["completed"] = False
            checkpoint.pop("stopped_reason", None)
            checkpoint.pop("last_failure", None)
        else:
            checkpoint["results"] = []
            checkpoint["summary"] = _empty_summary(len(qualified_candidates))
            checkpoint.pop("last_failure", None)
            checkpoint["completed"] = False
            checkpoint.pop("stopped_reason", None)
            _set_candidate_pool_cursor_checkpoint(
                checkpoint,
                serialized_candidates=qualified_candidates,
                page_size=page_size,
                next_page=1,
                next_index=0,
            )

    return checkpoint, should_reset


def _extract_detail_sku_rows(detail: dict[str, Any] | None) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for child in list((detail or {}).get("children") or []):
        child_stocks = list((child or {}).get("stocks") or [])
        stock_hint = child_stocks[0] if child_stocks else {}
        item_no = _extract_item_no(child=child or {}, stock_hint=stock_hint or {}, stock={})
        ship_from_resolution = resolve_ship_from(
            detail=detail or {},
            child=child or {},
            shipping_cost={},
            stock={},
            stock_hint=stock_hint or {},
        )
        rows.append(
            {
                "sku": item_no,
                "sku_code": str((child or {}).get("skuCode") or "").strip(),
                "sku_id": str((child or {}).get("skuId") or "").strip(),
                "item_no": item_no,
                "warehouse": ship_from_resolution.country,
                "warehouse_name": ship_from_resolution.warehouse_name,
                "ship_from_raw": ship_from_resolution.raw,
                "ship_from_source": ship_from_resolution.source,
                "ship_from_confidence": ship_from_resolution.confidence,
            }
        )
    return rows


def _unwrap_doba_payload(response_json: dict[str, Any]) -> Any:
    business_data = response_json.get("businessData")
    if isinstance(business_data, dict):
        if business_data.get("businessStatus") not in (None, "", "000000"):
            raise RuntimeError(str(business_data.get("businessMessage") or business_data.get("businessStatus")))
        return business_data.get("data")
    if isinstance(business_data, list):
        return business_data
    return business_data


def _fetch_platform_id(doba_client: DobaClient, platform_name: str = SHOPIFY_PLATFORM_NAME) -> str:
    response = doba_client.get(PLATFORM_LIST_QUERY_PATH)
    response.raise_for_status()
    platforms = _unwrap_doba_payload(response.json()) or []
    for item in platforms:
        if str((item or {}).get("platformName") or "").strip().lower() == platform_name.lower():
            return str((item or {}).get("platformId") or "")
    raise RuntimeError(f"Missing Doba platform id for {platform_name}.")


def _fetch_spu_page(
    doba_client: DobaClient,
    *,
    page_number: int,
    page_size: int,
    ship_to_country: str,
    min_inventory: int | None = None,
) -> tuple[int, list[dict[str, Any]]]:
    params: dict[str, Any] = {
        "pageNumber": page_number,
        "pageSize": page_size,
        "shipTo": ship_to_country,
    }
    if min_inventory is not None:
        params["minInventory"] = max(int(min_inventory), 0)
    response = doba_client.get(
        SPU_LIST_QUERY_PATH,
        params=params,
    )
    response.raise_for_status()
    payload = _unwrap_doba_payload(response.json()) or {}
    total = _safe_int(payload.get("totalQuantity"))
    goods_list = list(payload.get("goodsList") or [])
    return total, goods_list


def _fetch_spu_details(doba_client: DobaClient, spu_nos: list[str]) -> dict[str, dict[str, Any]]:
    if not spu_nos:
        return {}
    response = doba_client.get(
        SPU_DETAIL_QUERY_PATH,
        params={"spuNo": ",".join(spu_nos[:20])},
    )
    response.raise_for_status()
    details = _unwrap_doba_payload(response.json()) or []
    return {
        str((item or {}).get("spuNo") or ""): item
        for item in details
        if str((item or {}).get("spuNo") or "").strip()
    }


def _fetch_stock_map(doba_client: DobaClient, item_nos: list[str]) -> dict[str, dict[str, Any]]:
    if not item_nos:
        return {}
    response = doba_client.get(
        STOCK_QUERY_PATH,
        params={"itemNo": ",".join(item_nos[:20])},
    )
    response.raise_for_status()
    rows = _unwrap_doba_payload(response.json()) or []
    return {
        str((item or {}).get("itemNo") or ""): item
        for item in rows
        if str((item or {}).get("itemNo") or "").strip()
    }


def _fetch_shipping_map(
    doba_client: DobaClient,
    *,
    item_nos: list[str],
    ship_to_country: str,
    platform_id: str,
) -> dict[str, dict[str, Any]]:
    if not item_nos:
        return {}
    response = doba_client.post(
        SHIPPING_COST_QUERY_PATH,
        json_body={
            "shipToCountry": ship_to_country,
            "platformId": platform_id,
            "goods": [{"itemNo": item_no, "quantity": 1} for item_no in item_nos[:20]],
        },
    )
    response.raise_for_status()
    rows = _unwrap_doba_payload(response.json()) or []
    result: dict[str, dict[str, Any]] = {}
    for item in rows:
        data = (item or {}).get("data") or {}
        item_no = str(data.get("itemNo") or "").strip()
        costs = list(data.get("costs") or [])
        if not item_no:
            continue
        costs.sort(key=lambda cost: _safe_float((cost or {}).get("shipFee"), math.inf))
        result[item_no] = {
            "itemNo": item_no,
            "quantity": _safe_int(data.get("quantity"), 1),
            "cost": costs[0] if costs else None,
            "successful": bool((item or {}).get("successful")),
            "message": str((item or {}).get("businessMessage") or ""),
        }
    return result


def _fetch_seller_info(
    doba_client: DobaClient,
    *,
    supplier_id: str,
    seller_cache: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    key = supplier_id.strip()
    if not key:
        return {}
    if key in seller_cache:
        return seller_cache[key]
    response = doba_client.get(
        SUPPLIER_LIST_QUERY_PATH,
        params={"supplierId": key, "pageNumber": 1, "pageSize": 1},
    )
    response.raise_for_status()
    payload = _unwrap_doba_payload(response.json()) or []
    if isinstance(payload, dict):
        rows = list(payload.get("supplierList") or payload.get("data") or [])
    else:
        rows = list(payload or [])
    seller_cache[key] = rows[0] if rows else {}
    return seller_cache[key]


def _build_option_schema(variants: list[dict[str, Any]]) -> list[str]:
    option_names: list[str] = []
    for child in variants:
        variant_props = list((child or {}).get("variantProps") or [])
        if not variant_props and len(variants) > 1:
            if "Variant" not in option_names:
                option_names.append("Variant")
            continue
        for prop in variant_props:
            prop_name = _normalize_option_name(str((prop or {}).get("propName") or ""))
            if prop_name and prop_name not in option_names:
                option_names.append(prop_name)
    return option_names


def _build_option_values_map(child: dict[str, Any], option_names: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    variant_props = list((child or {}).get("variantProps") or [])
    for prop in variant_props:
        prop_name = _normalize_option_name(str((prop or {}).get("propName") or ""))
        prop_value = str((prop or {}).get("propValue") or "").strip()
        if prop_name:
            if prop_name not in values or values[prop_name] == "Default":
                values[prop_name] = prop_value or "Default"
    if not variant_props and option_names == ["Variant"]:
        values["Variant"] = str((child or {}).get("skuCode") or (child or {}).get("skuId") or "Default").strip()
    values = _normalize_option_values(values)
    for option_name in option_names:
        values.setdefault(option_name, "Default")
    return _normalize_option_values(values)


def _resolve_ship_from_label(
    *,
    detail: dict[str, Any],
    child: dict[str, Any],
    shipping_cost: dict[str, Any],
    stock: dict[str, Any],
    stock_hint: dict[str, Any],
) -> str:
    return resolve_ship_from(
        detail=detail,
        child=child,
        shipping_cost=shipping_cost,
        stock=stock,
        stock_hint=stock_hint,
    ).country


def _extract_item_no(*, child: dict[str, Any], stock_hint: dict[str, Any], stock: dict[str, Any]) -> str:
    candidates = [
        (stock_hint or {}).get("itemNo"),
        (child or {}).get("itemNo"),
        (child or {}).get("item_no"),
        (stock or {}).get("itemNo"),
        (stock or {}).get("item_no"),
    ]
    for candidate in candidates:
        text = str(candidate or "").strip()
        if text:
            return text
    return ""


def _extract_available_num(*, child: dict[str, Any], stock_hint: dict[str, Any], stock: dict[str, Any]) -> int:
    candidates = [
        (stock or {}).get("availableNum"),
        (stock or {}).get("inventoryNum"),
        (stock or {}).get("quantity"),
        (stock or {}).get("qty"),
        (stock_hint or {}).get("availableNum"),
        (stock_hint or {}).get("inventoryNum"),
        (stock_hint or {}).get("quantity"),
        (stock_hint or {}).get("qty"),
        (child or {}).get("availableNum"),
        (child or {}).get("inventoryNum"),
        (child or {}).get("quantity"),
        (child or {}).get("qty"),
    ]
    for candidate in candidates:
        value = _safe_int(candidate, -1)
        if value >= 0:
            return value
    return 0


def _build_product_candidate(
    *,
    detail: dict[str, Any],
    stock_map: dict[str, dict[str, Any]],
    shipping_map: dict[str, dict[str, Any]],
    seller_info: dict[str, Any],
    inventory_threshold: int,
    target_country: str,
) -> tuple[DobaProductCandidate | None, str | None]:
    children = list(detail.get("children") or [])
    if not children:
        return None, "missing_variants"

    title_variant_attributes = _extract_title_variant_attributes(str(detail.get("title") or "").strip())
    option_names = _build_option_schema(children)
    for option_name in title_variant_attributes:
        if option_name not in option_names:
            option_names.append(option_name)
    qualifying_variants: list[DobaVariantCandidate] = []
    collected_images: list[str] = []
    ship_from_country = "UNKNOWN"
    missing_variant_data = False
    missing_variant_pricing = False
    blocked_by_ship_from = False

    for child in children:
        child_stocks = list(child.get("stocks") or [])
        stock_hint = None
        for row in child_stocks:
            if str((row or {}).get("regionId") or "").strip().upper() == target_country.upper():
                stock_hint = row
                break
        stock_hint = stock_hint or (child_stocks[0] if child_stocks else {})
        item_no = _extract_item_no(child=child, stock_hint=stock_hint or {}, stock={})
        if not item_no:
            missing_variant_data = True
            continue
        stock = stock_map.get(item_no) or {}
        shipping = shipping_map.get(item_no) or {}
        shipping_cost_row = ((shipping.get("cost") or {}) if shipping else {})
        shipping_cost = _safe_float(shipping_cost_row.get("shipFee"))
        available_num = _extract_available_num(child=child, stock_hint=stock_hint or {}, stock=stock)
        ship_from_resolution = resolve_ship_from(
            detail=detail,
            child=child,
            shipping_cost=shipping_cost_row,
            stock=stock,
            stock_hint=stock_hint or {},
        )
        resolved_ship_from = ship_from_resolution.country
        if not _is_allowed_ship_from(resolved_ship_from):
            blocked_by_ship_from = True
            continue
        if available_num <= inventory_threshold:
            continue
        source_price = _safe_float(stock.get("sellingPrice"))
        msrp = _safe_float(stock.get("msrpPrice") or child.get("marketPrice"))
        total_cost = round(source_price + shipping_cost, 2)
        item_images = _unique_strings([*(child.get("skuPicList") or []), *(detail.get("skuPicList") or []), detail.get("pictureUrl") or ""])
        collected_images.extend(item_images)
        if ship_from_country == "UNKNOWN":
            ship_from_country = resolved_ship_from
        option_values = _build_option_values_map(child, option_names)
        for option_name, option_value in title_variant_attributes.items():
            normalized_option_name = _normalize_option_name(option_name)
            if not str(option_values.get(normalized_option_name) or "").strip() or option_values.get(normalized_option_name) == "Default":
                option_values[normalized_option_name] = option_value
        option_values = _normalize_option_values(option_values)
        doba_input = DobaProductInput(
            supplier_id=str(detail.get("busiId") or ""),
            supplier_spu_no=str(detail.get("spuNo") or ""),
            product_id=str(detail.get("spuId") or ""),
            sku=item_no,
            sku_code=str(child.get("skuCode") or ""),
            sku_id=str(child.get("skuId") or ""),
            item_no=item_no,
            title=str(detail.get("title") or ""),
            brand=str(detail.get("brand") or ""),
            category_id=str(detail.get("cateId") or ""),
            category_name=str(detail.get("cateName") or ""),
            category_path=str(detail.get("cateName") or ""),
            supplier_status="active",
            source_vendor=SOURCE_VENDOR_NAME,
            source_channels=list(DEFAULT_CHANNELS),
            cost=total_cost,
            msrp=msrp,
            inventory=available_num,
            ship_from_country=ship_from_country,
            ship_from_raw=ship_from_resolution.raw,
            ship_from_source=ship_from_resolution.source,
            ship_from_confidence=ship_from_resolution.confidence,
            warehouse_name=str(
                ship_from_resolution.warehouse_name
                or resolved_ship_from
            ),
            ships_to_countries=[country.get("regionId", "") for country in (detail.get("availableRegions") or [])],
            shipping_cost=shipping_cost,
            delivery_days=_parse_ship_time_days(((shipping.get("cost") or {}) if shipping else {}).get("shipTime"), _safe_int(detail.get("processingTime"))),
            description=re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(detail.get("goodsDesc") or ""))).strip(),
            image_urls=item_images,
            variant_attributes=option_values,
            category_metafields=_build_category_metafields(
                category_id=str(detail.get("cateId") or ""),
                category_name=str(detail.get("cateName") or ""),
            ),
            seller_name=str(detail.get("sellerName") or ""),
            seller_info=dict(seller_info or {}),
            warehouse_info={
                "warehouse_name": str(
                    ship_from_resolution.warehouse_name
                    or resolved_ship_from
                ),
                "ship_name": str(shipping_cost_row.get("shipName") or ""),
                "region_id": ship_from_resolution.region_id,
                "ship_from_source": ship_from_resolution.source,
                "ship_from_confidence": ship_from_resolution.confidence,
            },
            attributes={
                "sellerName": str(detail.get("sellerName") or ""),
                "vendor": SOURCE_VENDOR_NAME,
            },
        )
        sale_price = _derive_shopify_sale_price(source_price, shipping_cost)
        if total_cost <= 0 or source_price <= 0 or sale_price <= 0:
            missing_variant_pricing = True
            continue
        delivery_days = _parse_ship_time_days(
            ((shipping.get("cost") or {}) if shipping else {}).get("shipTime"),
            _safe_int(detail.get("processingTime")),
        )
        qualifying_variants.append(
            DobaVariantCandidate(
                sku=item_no,
                sku_code=str(child.get("skuCode") or ""),
                sku_id=str(child.get("skuId") or ""),
                option_values=option_values,
                inventory=available_num,
                source_price=source_price,
                shipping_cost=shipping_cost,
                cost_price=total_cost,
                sale_price=sale_price,
                compare_at_price=round(max(msrp, sale_price), 2) if msrp > 0 else 0.0,
                ship_time_days=delivery_days,
                item_no=item_no,
                ship_name=str(shipping_cost_row.get("shipName") or ""),
                warehouse=resolved_ship_from,
                warehouse_name=str(
                    ship_from_resolution.warehouse_name
                    or resolved_ship_from
                ),
                ship_from_raw=ship_from_resolution.raw,
                ship_from_source=ship_from_resolution.source,
                ship_from_confidence=ship_from_resolution.confidence,
                image_urls=item_images,
            )
        )

    if not qualifying_variants:
        if blocked_by_ship_from:
            return None, "ship_from_not_us_or_unknown"
        if missing_variant_data:
            return None, "missing_variant_stock_data"
        if missing_variant_pricing:
            return None, "missing_variant_pricing_data"
        return None, "all_variants_inventory_below_threshold"

    image_urls = _unique_strings(collected_images)
    if not image_urls:
        return None, "missing_images"

    category_name = str(detail.get("cateName") or "").strip() or "General"
    spu_no = str(detail.get("spuNo") or "").strip()
    merge_key = _build_merge_key(
        title=str(detail.get("title") or "").strip(),
        category_id=str(detail.get("cateId") or ""),
        supplier_id=str(detail.get("busiId") or ""),
        seller_name=str(detail.get("sellerName") or ""),
    )
    tags = _unique_strings(
        [
            "doba-import",
            "doba-live-publish",
            f"doba-spu-id:{detail.get('spuId') or ''}",
            f"doba-spu-no:{spu_no}",
            f"doba-supplier:{detail.get('busiId') or ''}",
            f"doba-merge-key:{merge_key}",
            _slugify(category_name),
        ]
    )
    return (
        _apply_candidate_enrichment(
            DobaProductCandidate(
            spu_id=str(detail.get("spuId") or ""),
            spu_no=spu_no,
            supplier_id=str(detail.get("busiId") or ""),
            category_id=str(detail.get("cateId") or ""),
            merge_key=merge_key,
            seller_name=str(detail.get("sellerName") or ""),
            seller_info=seller_info,
            title=str(detail.get("title") or "").strip(),
            category_metafields=_build_category_metafields(
                category_id=str(detail.get("cateId") or ""),
                category_name=category_name,
            ),
            category_name=category_name,
            description_html=_clean_html(detail.get("goodsDesc") or ""),
            brand=str(detail.get("brand") or "").strip(),
            source_vendor=SOURCE_VENDOR_NAME,
            source_channels=list(DEFAULT_CHANNELS),
            ship_from_country=ship_from_country,
            ship_from_source=qualifying_variants[0].ship_from_source if qualifying_variants else "unknown",
            ship_from_confidence=qualifying_variants[0].ship_from_confidence if qualifying_variants else "low",
            processing_time=_safe_int(detail.get("processingTime")),
            store_url=str(detail.get("storeUrl") or ""),
            image_urls=image_urls,
            variants=qualifying_variants,
            tags=tags,
        )
        ),
        None,
    )


def _build_archive_product_candidate(
    products: list[Any],
    *,
    inventory_threshold: int,
) -> tuple[DobaProductCandidate | None, str | None]:
    if not products:
        return None, "missing_variants"

    base = products[0]
    grouped_products = sorted(
        list(products),
        key=lambda item: (
            str(getattr(item, "sku_code", "") or ""),
            str(getattr(item, "sku", "") or ""),
        ),
    )
    qualifying_variants: list[DobaVariantCandidate] = []
    blocked_by_ship_from = False
    missing_variant_data = False
    missing_variant_pricing = False
    ship_from_country = "UNKNOWN"
    ship_from_source = "unknown"
    ship_from_confidence = "low"
    collected_images: list[str] = []

    for product in grouped_products:
        item_no = str(getattr(product, "item_no", "") or getattr(product, "sku", "") or "").strip()
        if not item_no:
            missing_variant_data = True
            continue
        resolved_ship_from = _normalize_ship_from_label(
            getattr(product, "ship_from_country", "") or getattr(product, "ship_from_raw", "")
        )
        if not _is_allowed_ship_from(resolved_ship_from):
            blocked_by_ship_from = True
            continue
        inventory = _safe_int(getattr(product, "inventory", 0), 0)
        if inventory <= inventory_threshold:
            continue
        shipping_cost = _safe_float(getattr(product, "shipping_cost", 0))
        cost_price = round(_safe_float(getattr(product, "cost", 0)), 2)
        source_price = round(max(cost_price - shipping_cost, 0.0), 2)
        sale_price = _derive_shopify_sale_price(source_price, shipping_cost)
        if cost_price <= 0 or source_price <= 0 or sale_price <= 0:
            missing_variant_pricing = True
            continue
        compare_at_price = round(max(_safe_float(getattr(product, "msrp", 0)), sale_price), 2)
        option_values = {
            str(key): str(value)
            for key, value in dict(getattr(product, "variant_attributes", {}) or {}).items()
            if str(key).strip()
        }
        option_values = _normalize_option_values(option_values)
        if not option_values:
            option_values["Variant"] = (
                str(getattr(product, "sku_code", "") or getattr(product, "sku", "") or "Default").strip() or "Default"
            )
        image_urls = _unique_strings(getattr(product, "image_urls", []) or [])
        collected_images.extend(image_urls)
        if ship_from_country == "UNKNOWN":
            ship_from_country = resolved_ship_from
            ship_from_source = str(getattr(product, "ship_from_source", "") or "archive")
            ship_from_confidence = str(getattr(product, "ship_from_confidence", "") or "medium")
        qualifying_variants.append(
            DobaVariantCandidate(
                sku=str(getattr(product, "sku", "") or item_no),
                sku_code=str(getattr(product, "sku_code", "") or ""),
                sku_id=str(getattr(product, "sku_id", "") or ""),
                option_values=option_values,
                inventory=inventory,
                source_price=source_price,
                shipping_cost=shipping_cost,
                cost_price=cost_price,
                sale_price=sale_price,
                compare_at_price=compare_at_price,
                ship_time_days=_safe_int(getattr(product, "delivery_days", 0), 0),
                item_no=item_no,
                ship_name="Standard",
                warehouse=resolved_ship_from,
                image_urls=image_urls,
                warehouse_name=str(getattr(product, "warehouse_name", "") or resolved_ship_from),
                ship_from_raw=str(getattr(product, "ship_from_raw", "") or resolved_ship_from),
                ship_from_source=str(getattr(product, "ship_from_source", "") or "archive"),
                ship_from_confidence=str(getattr(product, "ship_from_confidence", "") or "medium"),
            )
        )

    if not qualifying_variants:
        if missing_variant_data:
            return None, "missing_variants"
        if blocked_by_ship_from:
            return None, "ship_from_not_us_or_unknown"
        if missing_variant_pricing:
            return None, "missing_variant_pricing_data"
        return None, "all_variants_inventory_below_threshold"

    title = str(getattr(base, "title", "") or "").strip()
    category_id = str(getattr(base, "category_id", "") or "")
    supplier_id = str(getattr(base, "supplier_id", "") or "")
    seller_name = str(getattr(base, "seller_name", "") or "")
    merge_key = _build_merge_key(
        title=title,
        category_id=category_id,
        supplier_id=supplier_id,
        seller_name=seller_name,
    )
    category_name = str(getattr(base, "category_name", "") or "").strip() or "General"
    spu_no = str(getattr(base, "supplier_spu_no", "") or "").strip()
    tags = _unique_strings(
        [
            "doba-import",
            "doba-live-publish",
            f"doba-spu-id:{getattr(base, 'product_id', '') or ''}",
            f"doba-spu-no:{spu_no}",
            f"doba-supplier:{supplier_id}",
            f"doba-merge-key:{merge_key}",
            _slugify(category_name),
        ]
    )
    category_metafields = {
        "doba_category_id": category_id,
        "doba_category_name": category_name,
    }
    return (
        _apply_candidate_enrichment(
            DobaProductCandidate(
            spu_id=str(getattr(base, "product_id", "") or ""),
            spu_no=spu_no,
            supplier_id=supplier_id,
            category_id=category_id,
            merge_key=merge_key,
            seller_name=seller_name,
            seller_info=dict(getattr(base, "seller_info", {}) or {}),
            title=title,
            category_name=category_name,
            description_html=_clean_html(getattr(base, "description", "")),
            brand=str(getattr(base, "brand", "") or ""),
            ship_from_country=ship_from_country,
            ship_from_source=ship_from_source,
            ship_from_confidence=ship_from_confidence,
            processing_time=_safe_int(getattr(base, "delivery_days", 0), 0),
            store_url="",
            image_urls=_unique_strings(collected_images),
            variants=qualifying_variants,
            tags=tags,
            category_metafields=category_metafields,
            source_vendor=str(getattr(base, "source_vendor", "") or SOURCE_VENDOR_NAME),
            source_channels=_unique_strings(getattr(base, "source_channels", []) or list(DEFAULT_CHANNELS)),
        )
        ),
        None,
    )


def _build_archive_groups_from_products(products: list[Any]) -> list[list[Any]]:
    grouped: dict[str, list[Any]] = {}
    for product in products:
        key = str(product.supplier_spu_no or product.product_id or "").strip()
        if not key:
            key = f"{product.supplier_id}:{product.sku}"
        grouped.setdefault(key, []).append(product)
    return list(grouped.values())


def _group_archive_products(archive_repository: Any) -> list[list[Any]]:
    return _build_archive_groups_from_products(archive_repository.list_supplier_products())


def _apply_candidate_enrichment(candidate: DobaProductCandidate) -> DobaProductCandidate:
    candidate.content_enrichment = build_candidate_enrichment(candidate).model_dump()
    return candidate


def _load_candidate_pool(path: str | Path) -> dict[str, Any]:
    candidate_path = Path(path)
    if not candidate_path.exists():
        return {}
    try:
        payload = json.loads(candidate_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_candidate_pool(path: str | Path, payload: dict[str, Any]) -> str:
    candidate_path = Path(path)
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    candidate_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(candidate_path)


def _diversify_candidate_pool_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    remaining = [item for item in candidates if isinstance(item, dict)]
    diversified: list[dict[str, Any]] = []
    last_category = ""
    last_seller = ""

    while remaining:
        preferred_index: int | None = None
        fallback_seller_index: int | None = None
        fallback_category_index: int | None = None

        for index, item in enumerate(remaining):
            category_name = str(item.get("category_name") or "").strip().lower()
            seller_name = str(item.get("seller_name") or "").strip().lower()

            if category_name != last_category and seller_name != last_seller:
                preferred_index = index
                break
            if fallback_seller_index is None and seller_name != last_seller:
                fallback_seller_index = index
            if fallback_category_index is None and category_name != last_category:
                fallback_category_index = index

        selected_index = preferred_index
        if selected_index is None:
            selected_index = fallback_seller_index
        if selected_index is None:
            selected_index = fallback_category_index
        if selected_index is None:
            selected_index = 0

        selected = remaining.pop(selected_index)
        diversified.append(selected)
        last_category = str(selected.get("category_name") or "").strip().lower()
        last_seller = str(selected.get("seller_name") or "").strip().lower()

    return diversified


def _candidate_pool_matches_config(
    payload: dict[str, Any],
    *,
    target_country: str,
    inventory_threshold: int,
    archive_groups: int,
) -> bool:
    return (
        str(payload.get("source_mode") or "").strip() == "archive_candidate_pool"
        and str(payload.get("target_country") or "").strip().upper() == str(target_country).strip().upper()
        and _safe_int(payload.get("inventory_threshold"), inventory_threshold) == inventory_threshold
        and _safe_int((payload.get("summary") or {}).get("archive_groups"), archive_groups) == archive_groups
    )


def _build_candidate_pool_payload(
    *,
    target_country: str,
    inventory_threshold: int,
    archive_groups: int,
    qualified_candidates: list[dict[str, Any]],
    skipped_by_reason: dict[str, int],
    missing_category_examples: list[dict[str, Any]],
    ship_from_summary: dict[str, int],
    current_index: int,
    completed: bool,
) -> dict[str, Any]:
    return {
        "generated_at": _now_iso() if completed else "",
        "updated_at": _now_iso(),
        "source_mode": "archive_candidate_pool",
        "target_country": target_country,
        "inventory_threshold": inventory_threshold,
        "summary": {
            "archive_groups": archive_groups,
            "qualified_count": len(qualified_candidates),
            "skipped_by_reason": dict(skipped_by_reason),
            "missing_category_examples": list(missing_category_examples),
            "ship_from_summary": dict(ship_from_summary),
        },
        "progress": {
            "total_groups": archive_groups,
            "current_index": current_index,
            "next_index": current_index,
            "completed": completed,
        },
        "qualified_candidates": qualified_candidates,
    }


def build_doba_publish_candidate_pool(
    *,
    candidate_pool_path: str = str(DEFAULT_CANDIDATE_POOL_PATH),
    target_country: str = DEFAULT_TARGET_COUNTRY,
    inventory_threshold: int = DEFAULT_INVENTORY_THRESHOLD,
    incremental: bool = True,
    incremental_spu_nos: list[str] | None = None,
) -> dict[str, Any]:
    archive_repository = SQLiteSupplierArchiveRepository()
    publish_mapping_repository = SQLitePublishMappingRepository()
    candidate_repository = SQLiteCandidatePoolRepository()
    shopify_client = ShopifyAuthClient.from_settings(get_settings())
    changed_spu_nos = (
        _unique_strings(incremental_spu_nos or [])
        if incremental_spu_nos is not None
        else (archive_repository.consume_changed_supplier_spu_nos() if incremental else [])
    )
    can_incremental_refresh = incremental and bool(changed_spu_nos)
    existing_payload = _load_candidate_pool(candidate_pool_path)
    grouped_products = (
        _build_archive_groups_from_products(archive_repository.list_supplier_products_by_spu_nos(changed_spu_nos))
        if can_incremental_refresh
        else _group_archive_products(archive_repository)
    )
    taxonomy_cache: dict[str, str | None] = {}
    successful_spu_nos = {
        normalized_spu_no
        for record in publish_mapping_repository.list_publish_mappings()
        for normalized_spu_no in [_normalize_successful_spu_no(record.supplier_spu_no)]
        if normalized_spu_no
        if str(record.status or "").strip().lower() == "published"
    }
    full_archive_groups = _safe_int(
        archive_repository.count_supplier_product_groups(),
        _safe_int((existing_payload.get("summary") or {}).get("archive_groups"), len(grouped_products)),
    )
    archive_groups = len(grouped_products)
    can_resume = (not can_incremental_refresh) and _candidate_pool_matches_config(
        existing_payload,
        target_country=target_country,
        inventory_threshold=inventory_threshold,
        archive_groups=full_archive_groups,
    ) and not bool((existing_payload.get("progress") or {}).get("completed"))
    skipped_by_reason: dict[str, int] = dict((existing_payload.get("summary") or {}).get("skipped_by_reason") or {}) if can_resume else {}
    qualified_candidates: list[dict[str, Any]] = list(existing_payload.get("qualified_candidates") or []) if can_resume else []
    missing_category_examples: list[dict[str, Any]] = list((existing_payload.get("summary") or {}).get("missing_category_examples") or []) if can_resume else []
    start_index = _safe_int((existing_payload.get("progress") or {}).get("next_index"), 0) if can_resume else 0
    _log(
        "candidate_pool_start",
        total_groups=archive_groups,
        full_archive_groups=full_archive_groups,
        target_country=target_country,
        inventory_threshold=inventory_threshold,
        candidate_pool_path=candidate_pool_path,
        incremental=can_incremental_refresh,
        resume_from_index=start_index + 1 if start_index else 1,
    )
    if can_resume:
        candidate_repository.clear_all()
        for item in qualified_candidates:
            if not isinstance(item, dict):
                continue
            candidate_repository.upsert_entry(
                supplier_spu_no=str(item.get("spu_no") or ""),
                supplier_product_id=str(item.get("spu_id") or ""),
                title=str(item.get("title") or ""),
                seller_name=str(item.get("seller_name") or ""),
                category_name=str(item.get("category_name") or ""),
                status="qualified",
                skip_reason="",
                source_hash=json.dumps(item, ensure_ascii=False, sort_keys=True),
                payload=item,
                updated_at=_now_iso(),
            )
    elif can_incremental_refresh:
        candidate_repository.delete_entries_by_spu_nos(changed_spu_nos)
    else:
        candidate_repository.clear_all()

    for group_index, group in enumerate(grouped_products[start_index:], start=start_index + 1):
        raw_sku_list = [
            str(getattr(product, "sku", "") or getattr(product, "item_no", "") or "").strip()
            for product in group
            if str(getattr(product, "sku", "") or getattr(product, "item_no", "") or "").strip()
        ]
        group_spu_no = str(getattr(group[0], "supplier_spu_no", "") or getattr(group[0], "product_id", "") or "")
        group_product_id = str(getattr(group[0], "product_id", "") or "")
        group_title = str(getattr(group[0], "title", "") or "")
        group_category_name = str(getattr(group[0], "category_name", "") or "")
        group_seller_name = str(getattr(group[0], "seller_name", "") or "")
        runtime_policy_reason = _candidate_runtime_policy_reason(
            seller_name=group_seller_name,
            category_name=group_category_name,
        )
        group_ship_from_country = _unique_strings(
            [
                _normalize_ship_from_label(
                    getattr(product, "ship_from_country", "") or getattr(product, "ship_from_raw", "")
                )
                for product in group
            ]
        )
        try:
            if runtime_policy_reason:
                record_payload = {
                    "spu_id": group_product_id,
                    "spu_no": group_spu_no,
                    "title": group_title,
                    "sku_list": raw_sku_list,
                    "seller_name": group_seller_name,
                    "category_name": group_category_name,
                    "ship_from_country": group_ship_from_country[0] if group_ship_from_country else "UNKNOWN",
                }
                candidate_repository.upsert_entry(
                    supplier_spu_no=group_spu_no,
                    supplier_product_id=group_product_id,
                    title=group_title,
                    seller_name=group_seller_name,
                    category_name=group_category_name,
                    status="skipped",
                    skip_reason=runtime_policy_reason,
                    source_hash=json.dumps(record_payload, ensure_ascii=False, sort_keys=True),
                    payload=record_payload,
                    updated_at=_now_iso(),
                )
                _log(
                    "candidate_pool_result",
                    progress={"total": archive_groups, "current_index": group_index},
                    doba_product_id=group_product_id,
                    doba_spu_no=group_spu_no,
                    title=group_title,
                    sku_list=raw_sku_list,
                    seller_name=group_seller_name,
                    category_name=group_category_name,
                    action="skipped",
                    reason=runtime_policy_reason,
                )
                continue
            candidate, skip_reason = _build_archive_product_candidate(
                group,
                inventory_threshold=inventory_threshold,
            )
            record_payload: dict[str, Any] = {
                "spu_id": group_product_id,
                "spu_no": group_spu_no,
                "title": group_title,
                "sku_list": raw_sku_list,
                "seller_name": group_seller_name,
                "category_name": group_category_name,
                "ship_from_country": group_ship_from_country[0] if group_ship_from_country else "UNKNOWN",
            }
            if candidate is None:
                reason = str(skip_reason or "unknown")
                candidate_repository.upsert_entry(
                    supplier_spu_no=group_spu_no,
                    supplier_product_id=group_product_id,
                    title=group_title,
                    seller_name=group_seller_name,
                    category_name=group_category_name,
                    status="skipped",
                    skip_reason=reason,
                    source_hash=json.dumps(record_payload, ensure_ascii=False, sort_keys=True),
                    payload=record_payload,
                    updated_at=_now_iso(),
                )
                _log(
                    "candidate_pool_result",
                    progress={"total": archive_groups, "current_index": group_index},
                    doba_product_id=group_product_id,
                    doba_spu_no=group_spu_no,
                    title=group_title,
                    sku_list=raw_sku_list,
                    seller_name=group_seller_name,
                    category_name=group_category_name,
                    action="skipped",
                    reason=reason,
                )
            elif candidate.ship_from_country not in {"United States"}:
                record_payload = {
                    **record_payload,
                    "ship_from_country": candidate.ship_from_country,
                    "sku_list": [variant.sku for variant in candidate.variants],
                }
                candidate_repository.upsert_entry(
                    supplier_spu_no=candidate.spu_no,
                    supplier_product_id=candidate.spu_id,
                    title=candidate.title,
                    seller_name=candidate.seller_name,
                    category_name=candidate.category_name,
                    status="skipped",
                    skip_reason="ship_from_not_us_or_unknown",
                    source_hash=json.dumps(record_payload, ensure_ascii=False, sort_keys=True),
                    payload=record_payload,
                    updated_at=_now_iso(),
                )
                _log(
                    "candidate_pool_result",
                    progress={"total": archive_groups, "current_index": group_index},
                    doba_product_id=candidate.spu_id,
                    doba_spu_no=candidate.spu_no,
                    title=candidate.title,
                    sku_list=[variant.sku for variant in candidate.variants],
                    seller_name=candidate.seller_name,
                    category_name=candidate.category_name,
                    ship_from_country=candidate.ship_from_country,
                    action="skipped",
                    reason="ship_from_not_us_or_unknown",
                )
            elif candidate.spu_no in successful_spu_nos:
                record_payload = {
                    **record_payload,
                    "ship_from_country": candidate.ship_from_country,
                    "sku_list": [variant.sku for variant in candidate.variants],
                }
                candidate_repository.upsert_entry(
                    supplier_spu_no=candidate.spu_no,
                    supplier_product_id=candidate.spu_id,
                    title=candidate.title,
                    seller_name=candidate.seller_name,
                    category_name=candidate.category_name,
                    status="skipped",
                    skip_reason="already_successfully_published",
                    source_hash=json.dumps(record_payload, ensure_ascii=False, sort_keys=True),
                    payload=record_payload,
                    updated_at=_now_iso(),
                )
                _log(
                    "candidate_pool_result",
                    progress={"total": archive_groups, "current_index": group_index},
                    doba_product_id=candidate.spu_id,
                    doba_spu_no=candidate.spu_no,
                    title=candidate.title,
                    sku_list=[variant.sku for variant in candidate.variants],
                    seller_name=candidate.seller_name,
                    category_name=candidate.category_name,
                    action="skipped",
                    reason="already_successfully_published",
                )
            else:
                category_resolution = _resolve_shopify_category(
                    shopify_client,
                    candidate=candidate,
                    taxonomy_cache=taxonomy_cache,
                )
                if category_resolution is None or not category_resolution.category_id:
                    example = {
                        "spu_id": candidate.spu_id,
                        "spu_no": candidate.spu_no,
                        "title": candidate.title,
                        "category_name": candidate.category_name,
                        "sku_list": [variant.sku for variant in candidate.variants],
                    }
                    candidate_repository.upsert_entry(
                        supplier_spu_no=candidate.spu_no,
                        supplier_product_id=candidate.spu_id,
                        title=candidate.title,
                        seller_name=candidate.seller_name,
                        category_name=candidate.category_name,
                        status="skipped",
                        skip_reason="missing_shopify_category",
                        source_hash=json.dumps(example, ensure_ascii=False, sort_keys=True),
                        payload=example,
                        updated_at=_now_iso(),
                    )
                    _log(
                        "candidate_pool_result",
                        progress={"total": archive_groups, "current_index": group_index},
                        doba_product_id=candidate.spu_id,
                        doba_spu_no=candidate.spu_no,
                        title=candidate.title,
                        sku_list=[variant.sku for variant in candidate.variants],
                        seller_name=candidate.seller_name,
                        category_name=candidate.category_name,
                        action="skipped",
                        reason="missing_shopify_category",
                    )
                else:
                    candidate.category_metafields = {
                        **dict(candidate.category_metafields),
                            "shopify_category_id": category_resolution.category_id,
                            "shopify_category_name": category_resolution.taxonomy_search,
                        }
                    _apply_candidate_enrichment(candidate)
                    existing_product = _find_existing_product_by_merge_key(shopify_client, candidate.merge_key)
                    if not existing_product:
                        existing_product, _ = _find_existing_product_by_spu_no(shopify_client, candidate.spu_no)
                    if existing_product and str(existing_product.get("status") or "").upper() == "ACTIVE":
                        record_payload = _serialize_candidate(candidate)
                        candidate_repository.upsert_entry(
                            supplier_spu_no=candidate.spu_no,
                            supplier_product_id=candidate.spu_id,
                            title=candidate.title,
                            seller_name=candidate.seller_name,
                            category_name=candidate.category_name,
                            status="skipped",
                            skip_reason="active_product_exists",
                            source_hash=json.dumps(record_payload, ensure_ascii=False, sort_keys=True),
                            payload=record_payload,
                            updated_at=_now_iso(),
                        )
                        _log(
                            "candidate_pool_result",
                            progress={"total": archive_groups, "current_index": group_index},
                            doba_product_id=candidate.spu_id,
                            doba_spu_no=candidate.spu_no,
                            title=candidate.title,
                            sku_list=[variant.sku for variant in candidate.variants],
                            seller_name=candidate.seller_name,
                            category_name=candidate.category_name,
                            action="skipped",
                            reason="active_product_exists",
                        )
                    else:
                        record_payload = _serialize_candidate(candidate)
                        candidate_repository.upsert_entry(
                            supplier_spu_no=candidate.spu_no,
                            supplier_product_id=candidate.spu_id,
                            title=candidate.title,
                            seller_name=candidate.seller_name,
                            category_name=candidate.category_name,
                            status="qualified",
                            skip_reason="",
                            source_hash=json.dumps(record_payload, ensure_ascii=False, sort_keys=True),
                            payload=record_payload,
                            updated_at=_now_iso(),
                        )
                        _log(
                            "candidate_pool_result",
                            progress={"total": archive_groups, "current_index": group_index},
                            doba_product_id=candidate.spu_id,
                            doba_spu_no=candidate.spu_no,
                            title=candidate.title,
                            sku_list=[variant.sku for variant in candidate.variants],
                            seller_name=candidate.seller_name,
                            category_name=candidate.category_name,
                            category_metafields=candidate.category_metafields,
                            ship_from_country=candidate.ship_from_country,
                            variant_count=len(candidate.variants),
                            cost_prices=[round(variant.cost_price, 2) for variant in candidate.variants],
                            sale_prices=[round(variant.sale_price, 2) for variant in candidate.variants],
                            inventories=[variant.inventory for variant in candidate.variants],
                            action="qualified",
                            reason="",
                        )
        except KeyboardInterrupt:
            summary = candidate_repository.build_summary()
            payload = _build_candidate_pool_payload(
                target_country=target_country,
                inventory_threshold=inventory_threshold,
                archive_groups=full_archive_groups,
                qualified_candidates=candidate_repository.list_qualified_candidates(),
                skipped_by_reason=dict(summary.get("skipped_by_reason") or {}),
                missing_category_examples=list(summary.get("missing_category_examples") or []),
                ship_from_summary=dict(summary.get("ship_from_summary") or {}),
                current_index=group_index - 1,
                completed=False,
            )
            payload["candidate_pool_path"] = _write_candidate_pool(candidate_pool_path, payload)
            raise
    summary = candidate_repository.build_summary()
    payload = _build_candidate_pool_payload(
        target_country=target_country,
        inventory_threshold=inventory_threshold,
        archive_groups=full_archive_groups,
        qualified_candidates=candidate_repository.list_qualified_candidates(),
        skipped_by_reason=dict(summary.get("skipped_by_reason") or {}),
        missing_category_examples=list(summary.get("missing_category_examples") or []),
        ship_from_summary=dict(summary.get("ship_from_summary") or {}),
        current_index=archive_groups,
        completed=True,
    )
    payload["candidate_pool_path"] = _write_candidate_pool(candidate_pool_path, payload)
    _log(
        "candidate_pool_summary",
        total_groups=payload["summary"]["archive_groups"],
        qualified_count=payload["summary"]["qualified_count"],
        skipped_by_reason=payload["summary"]["skipped_by_reason"],
        missing_category_examples=payload["summary"]["missing_category_examples"],
        ship_from_summary=payload["summary"]["ship_from_summary"],
        incremental=can_incremental_refresh,
        candidate_pool_path=payload["candidate_pool_path"],
    )
    return payload


def _build_archive_inputs_from_detail(
    *,
    detail: dict[str, Any],
    stock_map: dict[str, dict[str, Any]],
    shipping_map: dict[str, dict[str, Any]],
    target_country: str,
) -> list[DobaProductInput]:
    children = list(detail.get("children") or [])
    if not children:
        return []

    title_variant_attributes = _extract_title_variant_attributes(str(detail.get("title") or "").strip())
    option_names = _build_option_schema(children)
    for option_name in title_variant_attributes:
        if option_name not in option_names:
            option_names.append(option_name)

    archive_inputs: list[DobaProductInput] = []
    for child in children:
        child_stocks = list(child.get("stocks") or [])
        stock_hint = None
        for row in child_stocks:
            if str((row or {}).get("regionId") or "").strip().upper() == target_country.upper():
                stock_hint = row
                break
        stock_hint = stock_hint or (child_stocks[0] if child_stocks else {})
        item_no = _extract_item_no(child=child, stock_hint=stock_hint or {}, stock={})
        if not item_no:
            continue
        stock = stock_map.get(item_no) or {}
        shipping = shipping_map.get(item_no) or {}
        shipping_cost_row = ((shipping.get("cost") or {}) if shipping else {})
        ship_from_resolution = resolve_ship_from(
            detail=detail,
            child=child,
            shipping_cost=shipping_cost_row,
            stock=stock,
            stock_hint=stock_hint or {},
        )
        shipping_cost = _safe_float(shipping_cost_row.get("shipFee"))
        source_price = _safe_float(stock.get("sellingPrice"))
        msrp = _safe_float(stock.get("msrpPrice") or child.get("marketPrice"))
        available_num = _extract_available_num(child=child, stock_hint=stock_hint or {}, stock=stock)
        option_values = _build_option_values_map(child, option_names)
        for option_name, option_value in title_variant_attributes.items():
            normalized_option_name = _normalize_option_name(option_name)
            if not str(option_values.get(normalized_option_name) or "").strip() or option_values.get(normalized_option_name) == "Default":
                option_values[normalized_option_name] = option_value
        option_values = _normalize_option_values(option_values)
        archive_inputs.append(
            DobaProductInput(
                supplier_id=str(detail.get("busiId") or ""),
                supplier_spu_no=str(detail.get("spuNo") or ""),
                product_id=str(detail.get("spuId") or ""),
                sku=item_no,
                sku_code=str(child.get("skuCode") or ""),
                sku_id=str(child.get("skuId") or ""),
                item_no=item_no,
                title=str(detail.get("title") or ""),
                brand=str(detail.get("brand") or ""),
                category_id=str(detail.get("cateId") or ""),
                category_name=str(detail.get("cateName") or ""),
                category_path=str(detail.get("cateName") or ""),
                supplier_status="active",
                source_vendor=SOURCE_VENDOR_NAME,
                source_channels=list(DEFAULT_CHANNELS),
                cost=round(source_price + shipping_cost, 2),
                msrp=msrp,
                inventory=available_num,
                ship_from_country=ship_from_resolution.country,
                ship_from_raw=ship_from_resolution.raw,
                ship_from_source=ship_from_resolution.source,
                ship_from_confidence=ship_from_resolution.confidence,
                warehouse_name=str(
                    ship_from_resolution.warehouse_name
                    or ship_from_resolution.country
                ),
                ships_to_countries=[country.get("regionId", "") for country in (detail.get("availableRegions") or [])],
                shipping_cost=shipping_cost,
                delivery_days=_parse_ship_time_days(
                    ((shipping.get("cost") or {}) if shipping else {}).get("shipTime"),
                    _safe_int(detail.get("processingTime")),
                ),
                description=re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(detail.get("goodsDesc") or ""))).strip(),
                image_urls=_unique_strings(
                    [*(child.get("skuPicList") or []), *(detail.get("skuPicList") or []), detail.get("pictureUrl") or ""]
                ),
                variant_attributes=option_values,
                category_metafields=_build_category_metafields(
                    category_id=str(detail.get("cateId") or ""),
                    category_name=str(detail.get("cateName") or ""),
                ),
                seller_name=str(detail.get("sellerName") or ""),
                seller_info={
                    "supplier_id": str(detail.get("busiId") or ""),
                },
                warehouse_info={
                    "warehouse_name": str(
                        ship_from_resolution.warehouse_name
                        or ""
                    ),
                    "ship_name": str(shipping_cost_row.get("shipName") or ""),
                    "ship_time": str(shipping_cost_row.get("shipTime") or ""),
                    "region_id": ship_from_resolution.region_id,
                    "ship_from_source": ship_from_resolution.source,
                    "ship_from_confidence": ship_from_resolution.confidence,
                },
                attributes={
                    "sellerName": str(detail.get("sellerName") or ""),
                    "categoryId": str(detail.get("cateId") or ""),
                    "vendor": SOURCE_VENDOR_NAME,
                },
            )
        )
    return archive_inputs


def _get_publication_map(client: ShopifyAuthClient) -> dict[str, dict[str, Any]]:
    data = client.graphql(PUBLICATIONS_QUERY)
    return {
        str(((edge or {}).get("node") or {}).get("name") or ""): ((edge or {}).get("node") or {})
        for edge in (data.get("publications") or {}).get("edges", [])
        if str((((edge or {}).get("node") or {}).get("name") or "")).strip()
    }


def _ensure_collection(client: ShopifyAuthClient, title: str) -> dict[str, Any] | None:
    data = client.graphql(COLLECTIONS_QUERY, {"query": f'title:"{title}"'})
    for edge in (data.get("collections") or {}).get("edges", []):
        node = (edge or {}).get("node") or {}
        if str(node.get("title") or "").strip().lower() == title.lower():
            return node
    created = client.graphql(COLLECTION_CREATE, {"input": {"title": title}}).get("collectionCreate") or {}
    user_errors = created.get("userErrors") or []
    if user_errors:
        raise ShopifyGraphQLError(str(user_errors))
    return created.get("collection")


def _add_product_to_collection(client: ShopifyAuthClient, *, collection_id: str, product_id: str) -> None:
    result = client.graphql(
        COLLECTION_ADD_PRODUCTS,
        {"id": collection_id, "productIds": [product_id]},
    ).get("collectionAddProducts") or {}
    user_errors = result.get("userErrors") or []
    fatal_errors = []
    for error in user_errors:
        message = str((error or {}).get("message") or "").lower()
        if "already exists" in message or "already in collection" in message:
            continue
        fatal_errors.append(error)
    if fatal_errors:
        raise ShopifyGraphQLError(str(fatal_errors))


def _publish_product(client: ShopifyAuthClient, *, product_id: str, publication_inputs: list[dict[str, str]]) -> None:
    result = client.graphql(
        PUBLISH_PRODUCT,
        {"id": product_id, "input": publication_inputs},
    ).get("publishablePublish") or {}
    user_errors = result.get("userErrors") or []
    if user_errors:
        raise ShopifyGraphQLError(str(user_errors))


def _unpublish_product(client: ShopifyAuthClient, *, product_id: str, publication_inputs: list[dict[str, str]]) -> None:
    result = client.graphql(
        UNPUBLISH_PRODUCT,
        {"id": product_id, "input": publication_inputs},
    ).get("publishableUnpublish") or {}
    user_errors = result.get("userErrors") or []
    if user_errors:
        raise ShopifyGraphQLError(str(user_errors))


def _load_shopify_product(client: ShopifyAuthClient, product_id: str) -> dict[str, Any]:
    data = client.graphql(PRODUCT_BY_ID, {"id": product_id})
    return data.get("product") or {}


def _extract_variants(product: dict[str, Any]) -> list[dict[str, Any]]:
    return [((edge or {}).get("node") or {}) for edge in ((product.get("variants") or {}).get("edges") or [])]


def _load_shopify_product_variants_until_ready(
    client: ShopifyAuthClient,
    *,
    product_id: str,
    expected_skus: list[str],
    max_attempts: int = 5,
    delay_seconds: float = 0.5,
) -> list[dict[str, Any]]:
    target_skus = {str(sku or "").strip() for sku in expected_skus if str(sku or "").strip()}
    latest_variants: list[dict[str, Any]] = []
    for attempt in range(max_attempts):
        refreshed = _load_shopify_product(client, product_id)
        latest_variants = _extract_variants(refreshed)
        loaded_skus = {
            str((variant or {}).get("sku") or "").strip()
            for variant in latest_variants
            if str((variant or {}).get("sku") or "").strip()
        }
        if target_skus.issubset(loaded_skus):
            return latest_variants
        if attempt + 1 < max_attempts:
            time.sleep(delay_seconds)
    return latest_variants


def _find_existing_product_by_variant_skus(
    client: ShopifyAuthClient,
    sku_values: list[str],
) -> tuple[dict[str, Any] | None, str | None]:
    seen_products: dict[str, dict[str, Any]] = {}
    for sku in sku_values:
        variant = client.find_variant_by_sku(sku)
        if not variant:
            continue
        product = variant.get("product") or {}
        product_id = str(product.get("id") or "")
        if not product_id:
            continue
        seen_products[product_id] = product
        if str(product.get("status") or "").strip().upper() == "ACTIVE":
            return product, "active_product_exists"
    if len(seen_products) > 1:
        raise RuntimeError("Incoming Doba variants map to multiple Shopify products.")
    return (next(iter(seen_products.values())), None) if seen_products else (None, None)


def _find_existing_product_by_spu_no(client: ShopifyAuthClient, spu_no: str) -> tuple[dict[str, Any] | None, str | None]:
    if not spu_no.strip():
        return None, None
    query_string = f'tag:"doba-spu-no:{spu_no}"'
    data = client.graphql(PRODUCTS_BY_TAG, {"query": query_string})
    edges = (data.get("products") or {}).get("edges") or []
    if not edges:
        return None, None
    product = ((edges[0] or {}).get("node") or {})
    if str(product.get("status") or "").strip().upper() == "ACTIVE":
        return product, "active_product_exists"
    return product, None


def _find_existing_product_by_merge_key(client: ShopifyAuthClient, merge_key: str) -> dict[str, Any] | None:
    if not merge_key.strip():
        return None
    query_string = f'tag:"doba-merge-key:{merge_key}"'
    data = client.graphql(PRODUCTS_BY_TAG, {"query": query_string})
    edges = (data.get("products") or {}).get("edges") or []
    if not edges:
        return None
    return ((edges[0] or {}).get("node") or {})


def _build_category_search_tokens(category_name: str) -> tuple[str, ...]:
    return tuple(token for token in re.split(r"[^a-z0-9]+", str(category_name or "").lower()) if token)


def _build_category_search_candidates(candidate: DobaProductCandidate) -> list[str]:
    category_name = str(candidate.category_name or "").strip()
    title = str(candidate.title or "").strip()
    searches: list[str] = []
    for value in (category_name, re.sub(r"^(other|misc|general)\s+", "", category_name, flags=re.IGNORECASE).strip()):
        if value and value not in searches:
            searches.append(value)
    title_lower = title.lower()
    if "patio lounge set" in title_lower:
        for value in ("patio lounge sets", "patio furniture sets"):
            if value not in searches:
                searches.append(value)
    if "patio chairs" in title_lower:
        for value in ("patio chairs", "outdoor chairs"):
            if value not in searches:
                searches.append(value)
    if "parasol base" in title_lower or "umbrella base" in title_lower:
        for value in ("parasol base", "umbrella base", "patio umbrellas"):
            if value not in searches:
                searches.append(value)
    if "parasol" in title_lower or "umbrella" in title_lower:
        for value in ("patio umbrellas", "outdoor umbrellas"):
            if value not in searches:
                searches.append(value)
    if "pool cover" in title_lower or "air pillows" in title_lower:
        for value in (
            "pool cover air pillows",
            "pool cover pillows",
            "winter pool cover pillows",
            "pool covers",
        ):
            if value not in searches:
                searches.append(value)
    if "pool filter ball" in title_lower or "pool filter balls" in title_lower:
        for value in (
            "pool filter balls",
            "pool filter media",
            "pool filters",
        ):
            if value not in searches:
                searches.append(value)
    if "raised garden bed" in title_lower or "garden bed" in title_lower:
        for value in (
            "raised garden beds",
            "garden raised beds",
            "planter boxes",
            "planters",
        ):
            if value not in searches:
                searches.append(value)
    if "log storage shed" in title_lower or "storage shed" in title_lower:
        for value in (
            "outdoor storage sheds",
            "garden storage sheds",
            "storage sheds",
            "firewood racks",
        ):
            if value not in searches:
                searches.append(value)
    if "mannequin" in title_lower or "dress form" in title_lower:
        for value in (
            "mannequins",
            "dress forms",
            "tailors dummies",
            "retail display mannequins",
        ):
            if value not in searches:
                searches.append(value)
    if "patio storage box" in title_lower or "deck box" in title_lower or "storage box" in title_lower:
        for value in (
            "outdoor storage boxes",
            "deck boxes",
            "patio storage boxes",
            "outdoor storage benches",
        ):
            if value not in searches:
                searches.append(value)
    if "spa surround" in title_lower or "hot tub surround" in title_lower or "spa step" in title_lower:
        for value in (
            "hot tub surrounds",
            "spa surrounds",
            "hot tub accessories",
            "spa accessories",
        ):
            if value not in searches:
                searches.append(value)
    if "strainer set" in title_lower or "above ground strainer" in title_lower:
        for value in (
            "pool skimmer accessories",
            "pool strainer baskets",
            "above ground pool accessories",
            "pool pump accessories",
        ):
            if value not in searches:
                searches.append(value)
    if "home office furniture" in category_name.lower():
        if any(token in title_lower for token in ("portable folding table", "folding table with fan", "multifunctional portable folding table", "folding table")):
            for value in (
                "laptop stands",
                "lap desks",
                "bed trays",
            ):
                if value not in searches:
                    searches.append(value)
        if any(token in title_lower for token in ("desk", "writing desk", "computer desk")):
            for value in (
                "desks",
                "computer desks",
                "writing desks",
                "home office desks",
            ):
                if value not in searches:
                    searches.append(value)
        if any(token in title_lower for token in ("printer stand", "printer table", "work cart", "laptop cart", "end table", "corner table")):
            for value in (
                "printer stands",
                "office carts",
                "laptop carts",
                "office storage carts",
            ):
                if value not in searches:
                    searches.append(value)
        if any(token in title_lower for token in ("filing cabinet", "hutch", "shelf")):
            for value in (
                "filing cabinets",
                "bookcases",
                "office storage cabinets",
                "office hutches",
            ):
                if value not in searches:
                    searches.append(value)
    if "home storage & organization" in category_name.lower():
        if any(token in title_lower for token in ("laundry hamper", "laundry sorter", "hamper sorter")):
            for value in (
                "laundry hampers",
                "laundry sorters",
                "hamper sorters",
            ):
                if value not in searches:
                    searches.append(value)
        if any(token in title_lower for token in ("wardrobe", "closet")):
            for value in (
                "portable closets",
                "wardrobes",
                "clothes closets",
            ):
                if value not in searches:
                    searches.append(value)
        if any(token in title_lower for token in ("storage shelf", "storage rack", "compartment")):
            for value in (
                "storage shelves",
                "storage racks",
                "cube storage organizers",
                "shelving units",
            ):
                if value not in searches:
                    searches.append(value)
    if "home audio & theater" in category_name.lower():
        if any(token in title_lower for token in ("home theater", "sound system", "multimedia")):
            for value in (
                "home theater systems",
                "surround sound systems",
                "speaker systems",
                "stereo systems",
            ):
                if value not in searches:
                    searches.append(value)
        if "megaphone" in title_lower:
            for value in (
                "megaphones",
                "pa speakers",
                "bullhorns",
            ):
                if value not in searches:
                    searches.append(value)
    if "other lab & scientific products" in category_name.lower():
        if any(token in title_lower for token in ("storage shelf", "shelf")):
            for value in (
                "storage shelves",
                "bookcases",
                "shelving units",
                "display shelves",
            ):
                if value not in searches:
                    searches.append(value)
    if "conversation sets" in category_name.lower() or "conversation set" in title_lower:
        for value in (
            "patio conversation sets",
            "outdoor conversation sets",
            "patio furniture sets",
        ):
            if value not in searches:
                searches.append(value)
    if "power station" in title_lower or "solar generator" in title_lower:
        for value in (
            "portable power stations",
            "solar generators",
            "backup power supplies",
        ):
            if value not in searches:
                searches.append(value)
    if "pots, planters & container accessories" in category_name.lower():
        if any(token in title_lower for token in ("planter", "planting box", "plant box", "container")):
            for value in (
                "planters",
                "plant pots",
                "planter boxes",
                "garden planters",
            ):
                if value not in searches:
                    searches.append(value)
    if "fire pit" in title_lower:
        for value in (
            "fire pits",
            "outdoor fire pits",
            "patio fire pits",
            "wood burning fire pits",
        ):
            if value not in searches:
                searches.append(value)
    if "bat house" in title_lower or "bat shelter" in title_lower:
        for value in (
            "bat houses",
            "bat shelters",
            "bird and wildlife houses",
            "wildlife houses",
        ):
            if value not in searches:
                searches.append(value)
        if "plant stand" in title_lower:
            for value in (
                "plant stands",
                "planters",
            ):
                if value not in searches:
                    searches.append(value)
    if "other patio, lawn & garden supplies" in category_name.lower():
        if any(token in title_lower for token in ("chair mat", "floor mat")):
            for value in (
                "chair mats",
                "floor mats",
            ):
                if value not in searches:
                    searches.append(value)
        if "waterfall" in title_lower:
            for value in (
                "garden waterfalls",
                "pond waterfalls",
                "waterfalls",
                "outdoor fountains",
            ):
                if value not in searches:
                    searches.append(value)
    if "other home improvement supplies" in category_name.lower():
        if any(token in title_lower for token in ("vertical garden", "planter", "planter box", "raised bed", "container")):
            for value in (
                "vertical planters",
                "garden planters",
                "planter boxes",
            ):
                if value not in searches:
                    searches.append(value)
    if "office & school chairs and accessories" in category_name.lower():
        if "bench cushion" in title_lower:
            for value in (
                "bench cushions",
                "outdoor bench cushions",
                "chair cushions",
            ):
                if value not in searches:
                    searches.append(value)
    return searches


def _resolve_shopify_category(
    client: ShopifyAuthClient,
    *,
    candidate: DobaProductCandidate,
    taxonomy_cache: dict[str, str | None],
) -> CategoryResolution | None:
    product_context = {
        "title": candidate.title,
        "productType": candidate.category_name,
        "tags": candidate.tags,
        "descriptionHtml": candidate.description_html,
        "vendor": SOURCE_VENDOR_NAME,
    }
    resolution = _resolve_category(product_context)
    if resolution is not None:
        hydrated = _hydrate_resolution(client, resolution, taxonomy_cache)
        if hydrated.category_id:
            return hydrated

    category_name = str(candidate.category_name or "").strip()
    if not category_name:
        return None

    resolved_category_id: str | None = None
    resolved_search = category_name
    resolved_tokens = _build_category_search_tokens(category_name)
    for search in _build_category_search_candidates(candidate):
        cache_key = f"doba-category:{search.lower()}"
        if cache_key not in taxonomy_cache:
            taxonomy_cache[cache_key] = _search_taxonomy_category_id(
                client=client,
                category_label=_slugify(category_name),
                search=search,
                path_tokens=_build_category_search_tokens(search),
            )
        resolved_category_id = taxonomy_cache[cache_key]
        if resolved_category_id:
            resolved_search = search
            resolved_tokens = _build_category_search_tokens(search)
            break
    return CategoryResolution(
        category_id=resolved_category_id,
        product_type=category_name[:255],
        category_label=_slugify(category_name),
        tags=(),
        matched_rule="doba_category_name",
        taxonomy_search=resolved_search,
        taxonomy_path_tokens=resolved_tokens,
        allow_category_update=bool(resolved_category_id),
    )


def _extract_publication_names(product: dict[str, Any]) -> list[str]:
    return [
        str(((((edge or {}).get("node") or {}).get("publication") or {}).get("name") or "")).strip()
        for edge in ((product.get("resourcePublicationsV2") or {}).get("edges") or [])
        if str(((((edge or {}).get("node") or {}).get("publication") or {}).get("name") or "")).strip()
    ]


def _build_product_input(
    candidate: DobaProductCandidate,
    *,
    category_resolution: CategoryResolution | None = None,
    include_product_options: bool = True,
) -> dict[str, Any]:
    normalized_option_maps = [_normalize_option_values(dict(variant.option_values)) for variant in candidate.variants]
    option_names = list(normalized_option_maps[0].keys()) if normalized_option_maps else []
    product_input: dict[str, Any] = {
        "title": candidate.title[:255],
        "descriptionHtml": candidate.description_html,
        "productType": candidate.category_name[:255],
        "vendor": SOURCE_VENDOR_NAME,
        "status": "DRAFT",
        "handle": _slugify(f"{candidate.title}-{candidate.spu_no}"),
        "tags": candidate.tags[:250],
        "seo": {
            "title": candidate.title[:70],
            "description": re.sub(r"<[^>]+>", " ", candidate.description_html)[:320],
        },
    }
    if category_resolution and category_resolution.category_id:
        product_input["category"] = category_resolution.category_id
    if include_product_options and option_names:
        product_input["productOptions"] = [
            {
                "name": option_name,
                "values": [
                    {"name": value}
                    for value in _unique_strings(
                        [option_map.get(option_name, "Default") for option_map in normalized_option_maps]
                    )
                ],
            }
            for option_name in option_names
        ]
    return product_input


def _create_product(
    client: ShopifyAuthClient,
    candidate: DobaProductCandidate,
    *,
    category_resolution: CategoryResolution | None = None,
) -> dict[str, Any]:
    result = client.graphql(
        PRODUCT_CREATE,
        {"input": _build_product_input(candidate, category_resolution=category_resolution)},
    ).get("productCreate") or {}
    user_errors = result.get("userErrors") or []
    if user_errors:
        raise ShopifyGraphQLError(str(user_errors))
    return result.get("product") or {}


def _update_product_basics(
    client: ShopifyAuthClient,
    *,
    product_id: str,
    candidate: DobaProductCandidate,
    category_resolution: CategoryResolution | None = None,
) -> dict[str, Any]:
    payload = _build_product_input(
        candidate,
        category_resolution=category_resolution,
        include_product_options=False,
    )
    payload["id"] = product_id
    result = client.graphql(PRODUCT_UPDATE, {"product": payload}).get("productUpdate") or {}
    user_errors = result.get("userErrors") or []
    if user_errors:
        raise ShopifyGraphQLError(str(user_errors))
    return result.get("product") or {}


def _ensure_product_options(client: ShopifyAuthClient, *, product: dict[str, Any], candidate: DobaProductCandidate) -> dict[str, Any]:
    normalized_variants = [_normalize_option_values(dict(variant.option_values)) for variant in candidate.variants]
    wanted_option_names = list(normalized_variants[0].keys()) if normalized_variants else []
    if not wanted_option_names:
        return product
    existing_option_names = [_normalize_option_name(str((option or {}).get("name") or "")) for option in (product.get("options") or [])]
    missing_options = [name for name in wanted_option_names if name not in existing_option_names]
    if not missing_options:
        return product
    option_payload = []
    for option_name in missing_options:
        values = _unique_strings([variant.get(option_name, "Default") for variant in normalized_variants])
        option_payload.append({"name": option_name, "values": [{"name": value} for value in values]})
    result = client.graphql(
        PRODUCT_OPTIONS_CREATE,
        {
            "productId": product["id"],
            "options": option_payload,
            "variantStrategy": "LEAVE_AS_IS",
        },
    ).get("productOptionsCreate") or {}
    user_errors = result.get("userErrors") or []
    if user_errors:
        raise ShopifyGraphQLError(str(user_errors))
    return result.get("product") or product


def _variant_option_payload(variant: DobaVariantCandidate) -> list[dict[str, str]]:
    normalized_option_values = _normalize_option_values(dict(variant.option_values))
    return [
        {"optionName": option_name, "name": option_value}
        for option_name, option_value in normalized_option_values.items()
    ]


def _build_shopify_variant_payload(variant: DobaVariantCandidate) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "price": round(variant.sale_price, 2),
        "inventoryItem": {
            "sku": variant.sku,
            "cost": round(variant.cost_price, 2),
            "tracked": True,
            "requiresShipping": True,
        },
    }
    if variant.compare_at_price > 0:
        payload["compareAtPrice"] = round(variant.compare_at_price, 2)
    option_payload = _variant_option_payload(variant)
    if option_payload:
        payload["optionValues"] = option_payload
    return payload


def _extract_missing_candidate_variants(
    loaded_variants: list[dict[str, Any]],
    candidate: DobaProductCandidate,
) -> list[DobaVariantCandidate]:
    loaded_skus = {
        str((variant or {}).get("sku") or "").strip()
        for variant in loaded_variants
        if str((variant or {}).get("sku") or "").strip()
    }
    return [variant for variant in candidate.variants if variant.sku not in loaded_skus]


def _bulk_create_single_variant(
    client: ShopifyAuthClient,
    *,
    product_id: str,
    variant: DobaVariantCandidate,
) -> None:
    result = client.graphql(
        PRODUCT_VARIANTS_BULK_CREATE,
        {
            "productId": product_id,
            "variants": [_build_shopify_variant_payload(variant)],
            "strategy": "DEFAULT",
        },
    ).get("productVariantsBulkCreate") or {}
    user_errors = result.get("userErrors") or []
    if user_errors:
        raise ShopifyGraphQLError(str(user_errors))


def _load_or_repair_shopify_variants(
    client: ShopifyAuthClient,
    *,
    product_id: str,
    candidate: DobaProductCandidate,
    initial_attempts: int = 8,
    repair_rounds: int = 2,
) -> list[dict[str, Any]]:
    variants = _load_shopify_product_variants_until_ready(
        client,
        product_id=product_id,
        expected_skus=[variant.sku for variant in candidate.variants],
        max_attempts=initial_attempts,
        delay_seconds=0.75,
    )
    missing_variants = _extract_missing_candidate_variants(variants, candidate)
    for _ in range(repair_rounds):
        if not missing_variants:
            break
        for missing_variant in missing_variants:
            _bulk_create_single_variant(
                client,
                product_id=product_id,
                variant=missing_variant,
            )
        variants = _load_shopify_product_variants_until_ready(
            client,
            product_id=product_id,
            expected_skus=[variant.sku for variant in candidate.variants],
            max_attempts=6,
            delay_seconds=0.75,
        )
        missing_variants = _extract_missing_candidate_variants(variants, candidate)
    if missing_variants:
        missing_skus = [variant.sku for variant in missing_variants]
        raise RuntimeError(f"Missing Shopify variants after retries for SKUs {missing_skus}.")
    return variants


def _update_or_create_variants(
    client: ShopifyAuthClient,
    *,
    product: dict[str, Any],
    candidate: DobaProductCandidate,
) -> list[dict[str, Any]]:
    existing_variants = _extract_variants(product)
    is_new_standalone_product = (
        len(existing_variants) == 1
        and not str((existing_variants[0] or {}).get("sku") or "").strip()
    )
    existing_by_sku = {
        str((variant or {}).get("sku") or "").strip(): variant
        for variant in existing_variants
        if str((variant or {}).get("sku") or "").strip()
    }
    existing_without_sku = []
    if not (is_new_standalone_product and len(candidate.variants) > 1):
        existing_without_sku = [variant for variant in existing_variants if not str((variant or {}).get("sku") or "").strip()]
    updates: list[dict[str, Any]] = []
    creates: list[dict[str, Any]] = []
    pending_without_sku = list(existing_without_sku)

    for index, variant in enumerate(candidate.variants):
        target_existing = existing_by_sku.get(variant.sku)
        if target_existing is None and pending_without_sku:
            target_existing = pending_without_sku.pop(0)
        payload = _build_shopify_variant_payload(variant)
        if target_existing:
            payload["id"] = target_existing["id"]
            updates.append(payload)
        elif index == 0 and is_new_standalone_product and len(candidate.variants) == 1:
            payload["id"] = existing_variants[0]["id"]
            updates.append(payload)
        else:
            creates.append(payload)

    updated_variants: list[dict[str, Any]] = []
    if updates:
        result = client.graphql(
            PRODUCT_VARIANTS_BULK_UPDATE,
            {"productId": product["id"], "variants": updates},
        ).get("productVariantsBulkUpdate") or {}
        user_errors = result.get("userErrors") or []
        if user_errors:
            raise ShopifyGraphQLError(str(user_errors))
        updated_variants.extend(result.get("productVariants") or [])

    if creates:
        result = client.graphql(
            PRODUCT_VARIANTS_BULK_CREATE,
            {
                "productId": product["id"],
                "variants": creates,
                "strategy": "REMOVE_STANDALONE_VARIANT",
            },
        ).get("productVariantsBulkCreate") or {}
        user_errors = result.get("userErrors") or []
        if user_errors:
            raise ShopifyGraphQLError(str(user_errors))
        updated_variants.extend(result.get("productVariants") or [])

    return _load_or_repair_shopify_variants(
        client,
        product_id=product["id"],
        candidate=candidate,
    )


def _set_variant_inventory(
    client: ShopifyAuthClient,
    *,
    variants: list[dict[str, Any]],
    candidate: DobaProductCandidate,
) -> None:
    location = client.get_primary_location()
    if not location or not location.get("id"):
        raise RuntimeError("Missing Shopify primary location.")
    variant_by_sku = {str((variant or {}).get("sku") or "").strip(): variant for variant in variants}
    for source_variant in candidate.variants:
        shopify_variant = variant_by_sku.get(source_variant.sku)
        if not shopify_variant:
            raise RuntimeError(f"Missing Shopify variant for SKU {source_variant.sku}.")
        inventory_item_id = ((shopify_variant.get("inventoryItem") or {}).get("id") or "")
        if not inventory_item_id:
            raise RuntimeError(f"Missing inventory item id for SKU {source_variant.sku}.")
        client.set_inventory_quantity(
            inventory_item_id=inventory_item_id,
            location_id=location["id"],
            quantity=source_variant.inventory,
            change_from_quantity=None,
            reference_document_uri=f"hermes://doba-live-publish/{candidate.spu_no}/{source_variant.sku}",
        )


def _attach_product_media(client: ShopifyAuthClient, *, product_id: str, image_urls: list[str], title: str) -> None:
    if not image_urls:
        return
    media = [
        {
            "originalSource": url,
            "mediaContentType": "IMAGE",
            "alt": f"{title[:120]} image {index}",
        }
        for index, url in enumerate(image_urls[:20], start=1)
    ]
    result = client.graphql(
        PRODUCT_CREATE_MEDIA,
        {"productId": product_id, "media": media},
    ).get("productCreateMedia") or {}
    media_errors = result.get("mediaUserErrors") or []
    if media_errors:
        raise ShopifyGraphQLError(str(media_errors))


def _set_product_metafields(
    client: ShopifyAuthClient,
    *,
    product_id: str,
    candidate: DobaProductCandidate,
    category_resolution: CategoryResolution | None = None,
) -> None:
    metafields = [
        {
            "ownerId": product_id,
            "namespace": "hermes",
            "key": "doba_spu_id",
            "type": "single_line_text_field",
            "value": candidate.spu_id,
        },
        {
            "ownerId": product_id,
            "namespace": "hermes",
            "key": "doba_spu_no",
            "type": "single_line_text_field",
            "value": candidate.spu_no,
        },
        {
            "ownerId": product_id,
            "namespace": "hermes",
            "key": "doba_category_id",
            "type": "single_line_text_field",
            "value": candidate.category_id,
        },
        {
            "ownerId": product_id,
            "namespace": "hermes",
            "key": "doba_category_name",
            "type": "single_line_text_field",
            "value": candidate.category_name,
        },
        {
            "ownerId": product_id,
            "namespace": "hermes",
            "key": "shopify_category_id",
            "type": "single_line_text_field",
            "value": str((category_resolution.category_id if category_resolution else "") or ""),
        },
        {
            "ownerId": product_id,
            "namespace": "hermes",
            "key": "shopify_category_rule",
            "type": "single_line_text_field",
            "value": str((category_resolution.matched_rule if category_resolution else "") or "")[:255],
        },
        {
            "ownerId": product_id,
            "namespace": "hermes",
            "key": "source_vendor",
            "type": "single_line_text_field",
            "value": SOURCE_VENDOR_NAME,
        },
        {
            "ownerId": product_id,
            "namespace": "hermes",
            "key": "doba_seller_name",
            "type": "single_line_text_field",
            "value": candidate.seller_name,
        },
        {
            "ownerId": product_id,
            "namespace": "hermes",
            "key": "variant_item_nos",
            "type": "json",
            "value": json.dumps([variant.item_no for variant in candidate.variants], ensure_ascii=False),
        },
        {
            "ownerId": product_id,
            "namespace": "hermes",
            "key": "ship_from_country",
            "type": "single_line_text_field",
            "value": candidate.ship_from_country,
        },
        {
            "ownerId": product_id,
            "namespace": "hermes",
            "key": "source_channels",
            "type": "json",
            "value": json.dumps(list(candidate.source_channels), ensure_ascii=False),
        },
    ]
    metafields = [item for item in metafields if str(item.get("value") or "").strip()]
    result = client.graphql(
        UPSERT_PRODUCT_METAFIELDS,
        {"metafields": metafields},
    ).get("metafieldsSet") or {}
    user_errors = result.get("userErrors") or []
    if user_errors:
        raise ShopifyGraphQLError(str(user_errors))


def _set_product_status(client: ShopifyAuthClient, *, product_id: str, status: str) -> None:
    result = client.graphql(
        PRODUCT_UPDATE,
        {"product": {"id": product_id, "status": status}},
    ).get("productUpdate") or {}
    user_errors = result.get("userErrors") or []
    if user_errors:
        raise ShopifyGraphQLError(str(user_errors))


def rollback_shopify_product_publications(*, product_id: str, channels: list[str] | None = None, set_draft: bool = True) -> dict[str, Any]:
    settings = get_settings()
    shopify_client = ShopifyAuthClient.from_settings(settings)
    target_channels = channels or list(DEFAULT_CHANNELS)
    publication_map = _get_publication_map(shopify_client)
    publication_inputs = [
        {"publicationId": publication_map[name]["id"]}
        for name in target_channels
        if name in publication_map
    ]
    unpublished_channels: list[str] = []
    if publication_inputs:
        _unpublish_product(shopify_client, product_id=product_id, publication_inputs=publication_inputs)
        unpublished_channels = [name for name in target_channels if name in publication_map]
    if set_draft:
        _set_product_status(shopify_client, product_id=product_id, status="DRAFT")
    product = _load_shopify_product(shopify_client, product_id)
    return {
        "shopify_product_id": product_id,
        "unpublished_channels": unpublished_channels,
        "shopify_status": str(product.get("status") or ""),
        "published_channels": _extract_publication_names(product),
    }


def _publish_candidate_to_shopify(
    shopify_client: ShopifyAuthClient,
    *,
    candidate: DobaProductCandidate,
    publication_inputs: list[dict[str, str]],
    collection_id: str | None,
    target_channel_names: list[str],
) -> dict[str, Any]:
    taxonomy_cache: dict[str, str | None] = {}
    category_resolution = _resolve_shopify_category(
        shopify_client,
        candidate=candidate,
        taxonomy_cache=taxonomy_cache,
    )
    if category_resolution is None or not category_resolution.category_id:
        raise RuntimeError(
            f"missing_shopify_category doba_category={candidate.category_name!r} title={candidate.title!r}"
        )
    existing_product = _find_existing_product_by_merge_key(shopify_client, candidate.merge_key)
    skip_reason = None
    if existing_product:
        existing_product = _load_shopify_product(shopify_client, str(existing_product.get("id") or ""))
        if str(existing_product.get("status") or "").strip().upper() == "ACTIVE":
            skip_reason = "active_product_exists"
    if existing_product is None:
        existing_product, skip_reason = _find_existing_product_by_spu_no(shopify_client, candidate.spu_no)
    if existing_product is None:
        existing_product, skip_reason = _find_existing_product_by_variant_skus(
            shopify_client,
            [variant.sku for variant in candidate.variants],
        )
    if skip_reason == "active_product_exists":
        existing_product_id = str((existing_product or {}).get("id") or "")
        if existing_product_id:
            existing_product = _load_shopify_product(shopify_client, existing_product_id)
        return {
            "action": "skipped",
            "reason": "active_product_exists",
            "shopify_product_id": str((existing_product or {}).get("id") or ""),
            "variant_count": 0,
            "shopify_status": str((existing_product or {}).get("status") or "ACTIVE"),
            "published_to": _extract_publication_names(existing_product or {}),
            "shopify_category_id": str((((existing_product or {}).get("category") or {}).get("id") or "")),
            "shopify_category_name": str(
                (((existing_product or {}).get("category") or {}).get("fullName") or ((existing_product or {}).get("category") or {}).get("name") or "")
            ),
        }

    if existing_product:
        product = _update_product_basics(
            shopify_client,
            product_id=str(existing_product.get("id") or ""),
            candidate=candidate,
            category_resolution=category_resolution,
        )
    else:
        product = _create_product(
            shopify_client,
            candidate,
            category_resolution=category_resolution,
        )

    product = _ensure_product_options(shopify_client, product=product, candidate=candidate)
    final_variants = _update_or_create_variants(shopify_client, product=product, candidate=candidate)
    _set_variant_inventory(shopify_client, variants=final_variants, candidate=candidate)
    _attach_product_media(shopify_client, product_id=product["id"], image_urls=candidate.image_urls, title=candidate.title)
    _set_product_metafields(
        shopify_client,
        product_id=product["id"],
        candidate=candidate,
        category_resolution=category_resolution,
    )
    if collection_id:
        _add_product_to_collection(shopify_client, collection_id=collection_id, product_id=product["id"])
    _set_product_status(shopify_client, product_id=product["id"], status="ACTIVE")
    _publish_product(shopify_client, product_id=product["id"], publication_inputs=publication_inputs)
    refreshed = _load_shopify_product(shopify_client, product["id"])
    refreshed_category = refreshed.get("category") or {}
    if not str(refreshed_category.get("id") or "").strip():
        raise RuntimeError(
            f"category_not_applied shopify_product_id={product['id']} doba_category={candidate.category_name!r}"
        )
    published_to = _extract_publication_names(refreshed)
    missing_channels = [name for name in target_channel_names if name not in published_to]
    if missing_channels:
        raise RuntimeError(
            f"missing_publications shopify_product_id={product['id']} missing={missing_channels}"
        )
    return {
        "action": "published",
        "reason": "",
        "shopify_product_id": product["id"],
        "shopify_handle": str(refreshed.get("handle") or ""),
        "variant_count": len(_extract_variants(refreshed)),
        "variants": _extract_variants(refreshed),
        "published_to": published_to,
        "shopify_category_id": str(refreshed_category.get("id") or ""),
        "shopify_category_name": str(refreshed_category.get("fullName") or refreshed_category.get("name") or ""),
        "shopify_status": str(refreshed.get("status") or ""),
    }


def _is_retryable_publish_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return any(
        token in message
        for token in (
            "throttle",
            "rate limit",
            "too many requests",
            "timeout",
            "temporarily unavailable",
            "connection reset",
            "connection aborted",
        )
    )


def _publish_candidate_to_shopify_with_retry(
    shopify_client: ShopifyAuthClient,
    *,
    candidate: DobaProductCandidate,
    publication_inputs: list[dict[str, str]],
    collection_id: str | None,
    target_channel_names: list[str],
    retry_attempts: int = 3,
) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(1, retry_attempts + 1):
        try:
            return _publish_candidate_to_shopify(
                shopify_client,
                candidate=candidate,
                publication_inputs=publication_inputs,
                collection_id=collection_id,
                target_channel_names=target_channel_names,
            )
        except Exception as exc:
            last_error = exc
            if attempt >= retry_attempts or not _is_retryable_publish_error(exc):
                raise
            time.sleep(min(6.0, float(attempt * 1.5)))
    if last_error is not None:
        raise last_error
    raise RuntimeError("publish_retry_failed_without_error")


def _build_result_payload(
    *,
    total_candidates: int,
    global_index: int,
    page_number: int,
    index_in_page: int,
    summary: dict[str, Any],
    detail: dict[str, Any] | None,
    candidate: DobaProductCandidate | None,
    action: str,
    reason: str,
    channels: list[str] | None = None,
    shopify_product_id: str = "",
    variant_count: int = 0,
    publish_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    variant_rows = candidate.variants if candidate else []
    category_metafields = dict(candidate.category_metafields) if candidate else {}
    published_channels = list((publish_result or {}).get("published_to") or [])
    post_publish_review_payload: dict[str, Any] = {}
    if candidate and publish_result:
        post_publish_review_payload = build_post_publish_review(candidate, publish_result).model_dump()
    enrichment_summary = summarize_enrichment(
        dict(candidate.content_enrichment) if candidate else {},
        post_publish_review_payload or None,
    )
    detail_sku_rows = _extract_detail_sku_rows(detail or summary)
    fallback_sku_list = [row["sku"] for row in detail_sku_rows if row["sku"]]
    fallback_sku_code_list = [row["sku_code"] for row in detail_sku_rows if row["sku_code"]]
    fallback_ship_from_list = _unique_strings([row["warehouse"] for row in detail_sku_rows if row["warehouse"]]) or ["UNKNOWN"]
    fallback_warehouse_list = _unique_strings([row["warehouse"] for row in detail_sku_rows if row["warehouse"] and row["warehouse"] != "UNKNOWN"])
    return {
        "timestamp": _now_iso(),
        "progress": {
            "total": total_candidates,
            "current_index": global_index,
            "page_number": page_number,
            "index_in_page": index_in_page,
        },
        "doba_product_id": str((detail or summary).get("spuId") or ""),
        "doba_spu_no": str((detail or summary).get("spuNo") or ""),
        "title": str((detail or summary).get("title") or ""),
        "source_vendor": candidate.source_vendor if candidate else SOURCE_VENDOR_NAME,
        "target_channels": list(channels or []),
        "published_channels": published_channels,
        "sku_list": ([variant.sku for variant in variant_rows] or fallback_sku_list),
        "sku_code_list": ([variant.sku_code for variant in variant_rows] or fallback_sku_code_list),
        "shopify_product_id": shopify_product_id,
        "shopify_status": str((publish_result or {}).get("shopify_status") or ""),
        "variant_count": variant_count or len(variant_rows),
        "variant_details": (
            [
                {
                    "sku": variant.sku,
                    "sku_code": variant.sku_code,
                    "sku_id": variant.sku_id,
                    "item_no": variant.item_no,
                    "options": dict(variant.option_values),
                    "inventory": variant.inventory,
                    "cost_price": round(variant.cost_price, 2),
                    "sale_price": round(variant.sale_price, 2),
                    "shipping_cost": round(variant.shipping_cost, 2),
                "warehouse": variant.warehouse,
                "warehouse_name": variant.warehouse_name,
                "ship_from_raw": variant.ship_from_raw or "UNKNOWN",
                "ship_from_source": variant.ship_from_source or "unknown",
                "ship_from_confidence": variant.ship_from_confidence or "low",
                }
                for variant in variant_rows
            ]
            or detail_sku_rows
        ),
        "cost_prices": [round(variant.cost_price, 2) for variant in variant_rows],
        "sale_prices": [round(variant.sale_price, 2) for variant in variant_rows],
        "inventories": [variant.inventory for variant in variant_rows],
        "category_id": candidate.category_id if candidate else str((detail or {}).get("cateId") or ""),
        "category_name": candidate.category_name if candidate else str((detail or {}).get("cateName") or ""),
        "category_metafields": {
            **category_metafields,
            "shopify_category_id": str((publish_result or {}).get("shopify_category_id") or ""),
            "shopify_category_name": str((publish_result or {}).get("shopify_category_name") or ""),
        },
        "ship_from_country": candidate.ship_from_country if candidate else (fallback_ship_from_list[0] if fallback_ship_from_list else "UNKNOWN"),
        "ship_from_source": candidate.ship_from_source if candidate else "unknown",
        "ship_from_confidence": candidate.ship_from_confidence if candidate else "low",
        "ship_from_list": _unique_strings([variant.warehouse for variant in variant_rows]) or fallback_ship_from_list,
        "warehouse_list": _unique_strings([variant.warehouse for variant in variant_rows]) or fallback_warehouse_list,
        "seller_name": candidate.seller_name if candidate else str((detail or {}).get("sellerName") or ""),
        "content_enrichment_summary": enrichment_summary,
        "post_publish_review": post_publish_review_payload,
        "action": action,
        "reason": reason,
    }


def _persist_publish_mappings(
    *,
    repository: LocalJsonPublishMappingRepository,
    candidate: DobaProductCandidate,
    publish_result: dict[str, Any],
    timestamp: str,
) -> None:
    published_variants = {
        str((variant or {}).get("sku") or "").strip(): (variant or {})
        for variant in (publish_result.get("variants") or [])
        if str((variant or {}).get("sku") or "").strip()
    }
    for variant in candidate.variants:
        published_variant = published_variants.get(variant.sku) or {}
        repository.save_publish_mapping(
            ShopifyPublishMappingRecord(
                supplier_name="doba",
                supplier_id=candidate.supplier_id,
                supplier_product_id=candidate.spu_id,
                supplier_spu_no=candidate.spu_no,
                supplier_sku=variant.sku,
                sku_code=variant.sku_code,
                merge_key=candidate.merge_key,
                shopify_product_id=str(publish_result.get("shopify_product_id") or ""),
                shopify_variant_id=str(published_variant.get("id") or ""),
                shopify_handle=str(publish_result.get("shopify_handle") or ""),
                shopify_category_id=str(publish_result.get("shopify_category_id") or ""),
                shopify_category_name=str(publish_result.get("shopify_category_name") or ""),
                doba_category_id=candidate.category_id,
                doba_category_name=candidate.category_name,
                ship_from_country=candidate.ship_from_country,
                ship_from_raw=variant.ship_from_raw,
                ship_from_source=variant.ship_from_source,
                ship_from_confidence=variant.ship_from_confidence,
                warehouse=variant.warehouse,
                inventory=variant.inventory,
                cost_price=round(variant.cost_price, 2),
                sale_price=round(variant.sale_price, 2),
                compare_at_price=round(variant.compare_at_price, 2),
                target_channels=list(candidate.source_channels),
                published_channels=list(publish_result.get("published_to") or []),
                status=str(publish_result.get("action") or "published"),
                last_error=str(publish_result.get("reason") or ""),
                published_at=timestamp,
                updated_at=timestamp,
            )
        )


def _publish_candidate_pool(
    *,
    checkpoint: dict[str, Any],
    report_path: str,
    candidate_pool_path: str,
    page_size: int,
    target_channels: list[str],
    publication_inputs: list[dict[str, str]],
    collection: dict[str, Any],
    shopify_client: ShopifyAuthClient,
    publish_mapping_repository: LocalJsonPublishMappingRepository,
    payload: dict[str, Any] | None = None,
    max_successes: int | None = None,
) -> dict[str, Any]:
    payload = payload or _load_candidate_pool(candidate_pool_path)
    serialized_candidates = _diversify_candidate_pool_candidates(list(payload.get("qualified_candidates") or []))
    candidates = [_deserialize_candidate(item) for item in serialized_candidates if isinstance(item, dict)]
    checkpoint["source_mode"] = "candidate_pool"
    checkpoint["candidate_pool_path"] = candidate_pool_path
    checkpoint["candidate_pool_generation"] = str(payload.get("generated_at") or "")
    checkpoint["summary"]["total_candidates"] = len(candidates)
    checkpoint["candidate_pool_summary"] = dict(payload.get("summary") or {})

    current_page = _safe_int((checkpoint.get("cursor") or {}).get("next_page"), 1)
    current_index = _safe_int((checkpoint.get("cursor") or {}).get("next_index"), 0)
    successful_spu_nos = {
        normalized_spu_no
        for item in (checkpoint.get("successful_spu_nos") or [])
        for normalized_spu_no in [_normalize_successful_spu_no(item)]
        if normalized_spu_no
    }
    published_this_run = 0

    while True:
        page_start = (current_page - 1) * page_size
        page_candidates = candidates[page_start : page_start + page_size]
        if not page_candidates:
            break
        start_index = current_index if current_index < len(page_candidates) else 0
        for index_in_page in range(start_index, len(page_candidates)):
            candidate = page_candidates[index_in_page]
            summary = _candidate_to_summary(candidate)
            detail = _candidate_to_detail(candidate)
            global_index = page_start + index_in_page + 1
            current_cursor = {"next_page": current_page, "next_index": index_in_page}
            _log(
                "scan_start",
                total=len(candidates),
                current_index=global_index,
                doba_product_id=candidate.spu_id,
                doba_spu_no=candidate.spu_no,
                title=candidate.title[:120],
            )

            if candidate.spu_no in successful_spu_nos:
                result = _build_result_payload(
                    total_candidates=len(candidates),
                    global_index=global_index,
                    page_number=current_page,
                    index_in_page=index_in_page,
                    summary=summary,
                    detail=detail,
                    candidate=candidate,
                    action="skipped",
                    reason="already_successfully_published",
                    channels=target_channels,
                )
                checkpoint["results"].append(result)
                checkpoint["summary"]["scanned_count"] += 1
                checkpoint["summary"]["skipped_count"] += 1
                next_page, next_index = _next_cursor(current_page, page_size, index_in_page, len(page_candidates))
                _set_candidate_pool_cursor_checkpoint(
                    checkpoint,
                    serialized_candidates=serialized_candidates,
                    page_size=page_size,
                    next_page=next_page,
                    next_index=next_index,
                )
                checkpoint["report_path"] = _write_checkpoint(report_path, checkpoint)
                _log("scan_result", **result)
                continue

            try:
                publish_result = _publish_candidate_to_shopify_with_retry(
                    shopify_client,
                    candidate=candidate,
                    publication_inputs=publication_inputs,
                    collection_id=str((collection or {}).get("id") or ""),
                    target_channel_names=target_channels,
                )
                result = _build_result_payload(
                    total_candidates=len(candidates),
                    global_index=global_index,
                    page_number=current_page,
                    index_in_page=index_in_page,
                    summary=summary,
                    detail=detail,
                    candidate=candidate,
                    action=publish_result["action"],
                    reason=publish_result["reason"],
                    channels=target_channels,
                    shopify_product_id=publish_result["shopify_product_id"],
                    variant_count=publish_result["variant_count"],
                    publish_result=publish_result,
                )
                checkpoint["results"].append(result)
                checkpoint["summary"]["scanned_count"] += 1
                if publish_result["action"] == "published":
                    _persist_publish_mappings(
                        repository=publish_mapping_repository,
                        candidate=candidate,
                        publish_result=publish_result,
                        timestamp=str(result.get("timestamp") or _now_iso()),
                    )
                    checkpoint["summary"]["published_count"] += 1
                    published_this_run += 1
                    successful_spu_nos.add(candidate.spu_no)
                    checkpoint["successful_spu_nos"] = sorted(successful_spu_nos)
                else:
                    checkpoint["summary"]["skipped_count"] += 1
                next_page, next_index = _next_cursor(current_page, page_size, index_in_page, len(page_candidates))
                _set_candidate_pool_cursor_checkpoint(
                    checkpoint,
                    serialized_candidates=serialized_candidates,
                    page_size=page_size,
                    next_page=next_page,
                    next_index=next_index,
                )
                checkpoint["report_path"] = _write_checkpoint(report_path, checkpoint)
                _log("scan_result", **result)
                if max_successes is not None and published_this_run >= max_successes:
                    checkpoint["stopped_reason"] = "max_successes_reached"
                    checkpoint["report_path"] = _write_checkpoint(report_path, checkpoint)
                    return checkpoint
            except KeyboardInterrupt:
                interrupted_result = _build_result_payload(
                    total_candidates=len(candidates),
                    global_index=global_index,
                    page_number=current_page,
                    index_in_page=index_in_page,
                    summary=summary,
                    detail=detail,
                    candidate=candidate,
                    action="interrupted",
                    reason="interrupted_by_user",
                    channels=target_channels,
                )
                checkpoint["results"].append(interrupted_result)
                checkpoint["last_failure"] = {
                    "failed_spu_no": interrupted_result["doba_spu_no"],
                    "failed_doba_product_id": interrupted_result["doba_product_id"],
                    "failed_sku": (interrupted_result["sku_list"][0] if interrupted_result["sku_list"] else ""),
                    "failed_sku_list": interrupted_result["sku_list"],
                    "failed_reason": "interrupted_by_user",
                    "completed_count": checkpoint["summary"]["published_count"],
                    "resume_from_command": _build_resume_command(report_path),
                    "resume_position": current_cursor,
                }
                _set_candidate_pool_cursor_checkpoint(
                    checkpoint,
                    serialized_candidates=serialized_candidates,
                    page_size=page_size,
                    next_page=current_page,
                    next_index=index_in_page,
                )
                checkpoint["stopped_reason"] = "interrupted_by_user"
                checkpoint["report_path"] = _write_checkpoint(report_path, checkpoint)
                _log("scan_result", **interrupted_result)
                return checkpoint
            except Exception as exc:
                failure_result = _build_result_payload(
                    total_candidates=len(candidates),
                    global_index=global_index,
                    page_number=current_page,
                    index_in_page=index_in_page,
                    summary=summary,
                    detail=detail,
                    candidate=candidate,
                    action="failed",
                    reason=str(exc),
                    channels=target_channels,
                )
                checkpoint["results"].append(failure_result)
                checkpoint["summary"]["scanned_count"] += 1
                checkpoint["summary"]["failed_count"] += 1
                checkpoint["last_failure"] = {
                    "failed_spu_no": failure_result["doba_spu_no"],
                    "failed_doba_product_id": failure_result["doba_product_id"],
                    "failed_sku": (failure_result["sku_list"][0] if failure_result["sku_list"] else ""),
                    "failed_sku_list": failure_result["sku_list"],
                    "failed_reason": str(exc),
                    "completed_count": checkpoint["summary"]["published_count"],
                    "resume_from_command": _build_resume_command(report_path),
                    "resume_position": current_cursor,
                }
                next_page, next_index = _next_cursor(current_page, page_size, index_in_page, len(page_candidates))
                _set_candidate_pool_cursor_checkpoint(
                    checkpoint,
                    serialized_candidates=serialized_candidates,
                    page_size=page_size,
                    next_page=next_page,
                    next_index=next_index,
                )
                checkpoint["report_path"] = _write_checkpoint(report_path, checkpoint)
                _log("scan_result", **failure_result)
                continue
        current_page += 1
        current_index = 0
        _set_candidate_pool_cursor_checkpoint(
            checkpoint,
            serialized_candidates=serialized_candidates,
            page_size=page_size,
            next_page=current_page,
            next_index=0,
        )
        checkpoint["report_path"] = _write_checkpoint(report_path, checkpoint)

    checkpoint["completed"] = True
    checkpoint.pop("stopped_reason", None)
    checkpoint.pop("last_failure", None)
    checkpoint["report_path"] = _write_checkpoint(report_path, checkpoint)
    return checkpoint


def publish_doba_products_live(
    *,
    report_path: str = "docs/audits/doba-shopify-live-publish-report.json",
    target_country: str = DEFAULT_TARGET_COUNTRY,
    channels: list[str] | None = None,
    page_size: int = DEFAULT_PAGE_SIZE,
    inventory_threshold: int = DEFAULT_INVENTORY_THRESHOLD,
    list_min_inventory: int | None = DEFAULT_LIST_MIN_INVENTORY,
    candidate_pool_path: str = str(DEFAULT_CANDIDATE_POOL_PATH),
    prefer_candidate_pool: bool = True,
    refresh_candidate_pool: bool = False,
    resume: bool = True,
    candidate_spu_nos: list[str] | None = None,
    max_successes: int | None = None,
) -> dict[str, Any]:
    publish_mapping_repository = SQLitePublishMappingRepository()
    checkpoint = _load_checkpoint(report_path) if resume else _load_checkpoint("__new__")
    if not resume:
        checkpoint["cursor"] = {"next_page": 1, "next_index": 0}
        checkpoint["successful_spu_nos"] = []
        checkpoint["results"] = []
        checkpoint["summary"] = _empty_summary()
    checkpoint.pop("stopped_reason", None)
    checkpoint["resume_command"] = _build_resume_command(report_path)
    checkpoint["candidate_pool_path"] = candidate_pool_path

    use_candidate_pool = prefer_candidate_pool
    candidate_payload: dict[str, Any] = {}
    targeted_candidate_spu_nos = _unique_strings(candidate_spu_nos or [])
    targeted_candidate_publish = bool(targeted_candidate_spu_nos)
    if use_candidate_pool:
        published_spu_nos = _load_published_spu_nos(publish_mapping_repository)
        if refresh_candidate_pool:
            try:
                candidate_payload = build_doba_publish_candidate_pool(
                    candidate_pool_path=candidate_pool_path,
                    target_country=target_country,
                    inventory_threshold=inventory_threshold,
                )
            except KeyboardInterrupt:
                partial_candidate_payload = _load_candidate_pool(candidate_pool_path)
                checkpoint["source_mode"] = "candidate_pool"
                checkpoint["candidate_pool_path"] = candidate_pool_path
                checkpoint["candidate_pool_summary"] = dict(partial_candidate_payload.get("summary") or {})
                checkpoint["stopped_reason"] = "interrupted_by_user"
                checkpoint["last_failure"] = {
                    "failed_spu_no": "",
                    "failed_doba_product_id": "",
                    "failed_sku": "",
                    "failed_sku_list": [],
                    "failed_reason": "interrupted_by_user",
                    "completed_count": checkpoint["summary"]["published_count"],
                    "resume_from_command": _build_resume_command(report_path),
                    "resume_position": {
                        "candidate_pool_path": candidate_pool_path,
                        "candidate_pool_progress": dict(partial_candidate_payload.get("progress") or {}),
                    },
                }
                checkpoint["report_path"] = _write_checkpoint(report_path, checkpoint)
                return checkpoint
        else:
            candidate_payload = _load_candidate_pool(candidate_pool_path)
        if not candidate_payload:
            raise RuntimeError(
                f"Candidate pool not found or invalid: {candidate_pool_path}. "
                "Run again with --refresh-candidate-pool to rebuild it."
            )
        qualified_candidates = list(candidate_payload.get("qualified_candidates") or [])
        if targeted_candidate_publish:
            filtered_candidates = [
                item
                for item in qualified_candidates
                if str((item or {}).get("spu_no") or "").strip() in targeted_candidate_spu_nos
            ]
            candidate_payload = {
                **candidate_payload,
                "summary": {
                    **dict(candidate_payload.get("summary") or {}),
                    "qualified_count": len(filtered_candidates),
                },
                "qualified_candidates": filtered_candidates,
            }
            qualified_candidates = filtered_candidates
            checkpoint["source_mode"] = "candidate_pool"
            checkpoint["candidate_pool_generation"] = str(candidate_payload.get("generated_at") or "")
            checkpoint["candidate_pool_summary"] = dict(candidate_payload.get("summary") or {})
            checkpoint["cursor"] = {"next_page": 1, "next_index": 0}
            checkpoint["results"] = []
            checkpoint["summary"] = _empty_summary(len(qualified_candidates))
            checkpoint["completed"] = False
            checkpoint.pop("last_failure", None)
            checkpoint.pop("stopped_reason", None)
        else:
            checkpoint, _ = _prepare_candidate_pool_checkpoint(
                checkpoint=checkpoint,
                candidate_payload=candidate_payload,
                refresh_candidate_pool=refresh_candidate_pool,
                published_spu_nos=published_spu_nos,
                page_size=page_size,
            )
        if not qualified_candidates:
            checkpoint["completed"] = True
            checkpoint.pop("stopped_reason", None)
            checkpoint.pop("last_failure", None)
            checkpoint["report_path"] = _write_checkpoint(report_path, checkpoint)
            _log(
                "candidate_pool_publish_empty",
                qualified_count=0,
                candidate_pool_path=candidate_pool_path,
                candidate_spu_nos=targeted_candidate_spu_nos,
                skipped_by_reason=(candidate_payload.get("summary") or {}).get("skipped_by_reason", {}),
            )
            return checkpoint

    settings = get_settings()
    shopify_client = ShopifyAuthClient.from_settings(settings)
    archive_repository = SQLiteSupplierArchiveRepository()
    target_channels = channels or list(DEFAULT_CHANNELS)
    publication_map = _get_publication_map(shopify_client)
    publication_inputs = [
        {"publicationId": publication_map[name]["id"]}
        for name in target_channels
        if name in publication_map
    ]
    if not publication_inputs:
        raise RuntimeError(f"No Shopify publications found for channels: {target_channels}")

    collection = _ensure_collection(shopify_client, NEW_ARRIVALS_COLLECTION_TITLE)

    if use_candidate_pool:
        return _publish_candidate_pool(
            checkpoint=checkpoint,
            report_path=report_path,
            candidate_pool_path=candidate_pool_path,
            page_size=page_size,
            target_channels=target_channels,
            publication_inputs=publication_inputs,
            collection=collection,
            shopify_client=shopify_client,
            publish_mapping_repository=publish_mapping_repository,
            payload=candidate_payload,
            max_successes=max_successes,
        )

    doba_client = _configure_doba_client(DobaClient.from_settings())
    platform_id = _fetch_platform_id(doba_client, SHOPIFY_PLATFORM_NAME)
    seller_cache: dict[str, dict[str, Any]] = {}

    current_page = _safe_int((checkpoint.get("cursor") or {}).get("next_page"), 1)
    current_index = _safe_int((checkpoint.get("cursor") or {}).get("next_index"), 0)
    successful_spu_nos = {
        normalized_spu_no
        for item in (checkpoint.get("successful_spu_nos") or [])
        for normalized_spu_no in [_normalize_successful_spu_no(item)]
        if normalized_spu_no
    }

    published_this_run = 0
    effective_list_min_inventory = list_min_inventory
    if effective_list_min_inventory is None:
        checkpoint["list_filter"] = {"min_inventory": None}
    else:
        checkpoint["list_filter"] = {"min_inventory": max(int(effective_list_min_inventory), 0)}
    while True:
        total_candidates, goods_list = _fetch_spu_page(
            doba_client,
            page_number=current_page,
            page_size=page_size,
            ship_to_country=target_country,
            min_inventory=effective_list_min_inventory,
        )
        checkpoint["summary"]["total_candidates"] = total_candidates
        if not goods_list:
            break
        detail_map = _fetch_spu_details(
            doba_client,
            [str((item or {}).get("spuNo") or "") for item in goods_list if str((item or {}).get("spuNo") or "").strip()],
        )
        start_index = current_index if current_index < len(goods_list) else 0
        for index_in_page in range(start_index, len(goods_list)):
            summary = goods_list[index_in_page]
            detail = detail_map.get(str(summary.get("spuNo") or "").strip()) or {}
            candidate: DobaProductCandidate | None = None
            global_index = ((current_page - 1) * page_size) + index_in_page + 1
            current_cursor = {"next_page": current_page, "next_index": index_in_page}
            _log(
                "scan_start",
                total=total_candidates,
                current_index=global_index,
                doba_product_id=str(summary.get("spuId") or ""),
                doba_spu_no=str(summary.get("spuNo") or ""),
                title=str(summary.get("title") or "")[:120],
            )

            if str(summary.get("spuNo") or "").strip() in successful_spu_nos:
                result = _build_result_payload(
                    total_candidates=total_candidates,
                    global_index=global_index,
                    page_number=current_page,
                    index_in_page=index_in_page,
                    summary=summary,
                    detail=detail,
                    candidate=None,
                    action="skipped",
                    reason="already_successfully_published",
                    channels=target_channels,
                )
                checkpoint["results"].append(result)
                checkpoint["summary"]["scanned_count"] += 1
                checkpoint["summary"]["skipped_count"] += 1
                checkpoint["cursor"] = dict(zip(("next_page", "next_index"), _next_cursor(current_page, page_size, index_in_page, len(goods_list))))
                checkpoint["report_path"] = _write_checkpoint(report_path, checkpoint)
                _log("scan_result", **result)
                continue

            try:
                children = list(detail.get("children") or [])
                item_nos = _unique_strings(
                    [
                        str((stock or {}).get("itemNo") or "").strip()
                        for child in children
                        for stock in (child.get("stocks") or [])
                    ]
                )
                stock_map = _fetch_stock_map(doba_client, item_nos)
                shipping_map = _fetch_shipping_map(
                    doba_client,
                    item_nos=item_nos,
                    ship_to_country=target_country,
                    platform_id=platform_id,
                )
                seller_info = _fetch_seller_info(
                    doba_client,
                    supplier_id=str(detail.get("busiId") or summary.get("busiId") or ""),
                    seller_cache=seller_cache,
                )
                archive_supplier_products(
                    _build_archive_inputs_from_detail(
                        detail=detail or summary,
                        stock_map=stock_map,
                        shipping_map=shipping_map,
                        target_country=target_country,
                    ),
                    archive_repository,
                )
                candidate, skip_reason = _build_product_candidate(
                    detail=detail or summary,
                    stock_map=stock_map,
                    shipping_map=shipping_map,
                    seller_info=seller_info,
                    inventory_threshold=inventory_threshold,
                    target_country=target_country,
                )
                if candidate is None:
                    result = _build_result_payload(
                        total_candidates=total_candidates,
                        global_index=global_index,
                        page_number=current_page,
                        index_in_page=index_in_page,
                        summary=summary,
                        detail=detail,
                        candidate=None,
                        action="skipped",
                        reason=skip_reason or "not_publishable",
                        channels=target_channels,
                    )
                    checkpoint["results"].append(result)
                    checkpoint["summary"]["scanned_count"] += 1
                    checkpoint["summary"]["skipped_count"] += 1
                    checkpoint["cursor"] = dict(zip(("next_page", "next_index"), _next_cursor(current_page, page_size, index_in_page, len(goods_list))))
                    checkpoint["report_path"] = _write_checkpoint(report_path, checkpoint)
                    _log("scan_result", **result)
                    continue

                publish_result = _publish_candidate_to_shopify_with_retry(
                    shopify_client,
                    candidate=candidate,
                    publication_inputs=publication_inputs,
                    collection_id=str((collection or {}).get("id") or ""),
                    target_channel_names=target_channels,
                )
                result = _build_result_payload(
                    total_candidates=total_candidates,
                    global_index=global_index,
                    page_number=current_page,
                    index_in_page=index_in_page,
                    summary=summary,
                    detail=detail,
                    candidate=candidate,
                    action=publish_result["action"],
                    reason=publish_result["reason"],
                    channels=target_channels,
                    shopify_product_id=publish_result["shopify_product_id"],
                    variant_count=publish_result["variant_count"],
                    publish_result=publish_result,
                )
                checkpoint["results"].append(result)
                checkpoint["summary"]["scanned_count"] += 1
                if publish_result["action"] == "published":
                    _persist_publish_mappings(
                        repository=publish_mapping_repository,
                        candidate=candidate,
                        publish_result=publish_result,
                        timestamp=str(result.get("timestamp") or _now_iso()),
                    )
                    checkpoint["summary"]["published_count"] += 1
                    published_this_run += 1
                    successful_spu_nos.add(candidate.spu_no)
                    checkpoint["successful_spu_nos"] = sorted(successful_spu_nos)
                else:
                    checkpoint["summary"]["skipped_count"] += 1
                checkpoint["cursor"] = dict(zip(("next_page", "next_index"), _next_cursor(current_page, page_size, index_in_page, len(goods_list))))
                checkpoint["report_path"] = _write_checkpoint(report_path, checkpoint)
                _log("scan_result", **result)
                if max_successes is not None and published_this_run >= max_successes:
                    checkpoint["stopped_reason"] = "max_successes_reached"
                    checkpoint["report_path"] = _write_checkpoint(report_path, checkpoint)
                    return checkpoint
            except KeyboardInterrupt:
                interrupted_result = _build_result_payload(
                    total_candidates=total_candidates,
                    global_index=global_index,
                    page_number=current_page,
                    index_in_page=index_in_page,
                    summary=summary,
                    detail=detail,
                    candidate=candidate,
                    action="interrupted",
                    reason="interrupted_by_user",
                    channels=target_channels,
                )
                checkpoint["results"].append(interrupted_result)
                checkpoint["last_failure"] = {
                    "failed_spu_no": interrupted_result["doba_spu_no"],
                    "failed_doba_product_id": interrupted_result["doba_product_id"],
                    "failed_sku": (interrupted_result["sku_list"][0] if interrupted_result["sku_list"] else ""),
                    "failed_sku_list": interrupted_result["sku_list"],
                    "failed_reason": "interrupted_by_user",
                    "completed_count": checkpoint["summary"]["published_count"],
                    "resume_from_command": _build_resume_command(report_path),
                    "resume_position": current_cursor,
                }
                checkpoint["cursor"] = current_cursor
                checkpoint["stopped_reason"] = "interrupted_by_user"
                checkpoint["report_path"] = _write_checkpoint(report_path, checkpoint)
                _log("scan_result", **interrupted_result)
                return checkpoint
            except Exception as exc:
                failure_result = _build_result_payload(
                    total_candidates=total_candidates,
                    global_index=global_index,
                    page_number=current_page,
                    index_in_page=index_in_page,
                    summary=summary,
                    detail=detail,
                    candidate=candidate,
                    action="failed",
                    reason=str(exc),
                    channels=target_channels,
                )
                checkpoint["results"].append(failure_result)
                checkpoint["summary"]["scanned_count"] += 1
                checkpoint["summary"]["failed_count"] += 1
                checkpoint["last_failure"] = {
                    "failed_spu_no": failure_result["doba_spu_no"],
                    "failed_doba_product_id": failure_result["doba_product_id"],
                    "failed_sku": (failure_result["sku_list"][0] if failure_result["sku_list"] else ""),
                    "failed_sku_list": failure_result["sku_list"],
                    "failed_reason": str(exc),
                    "completed_count": checkpoint["summary"]["published_count"],
                    "resume_from_command": _build_resume_command(report_path),
                    "resume_position": current_cursor,
                }
                checkpoint["cursor"] = dict(zip(("next_page", "next_index"), _next_cursor(current_page, page_size, index_in_page, len(goods_list))))
                checkpoint["report_path"] = _write_checkpoint(report_path, checkpoint)
                _log("scan_result", **failure_result)
                continue

        current_page += 1
        current_index = 0
        checkpoint["cursor"] = {"next_page": current_page, "next_index": 0}
        checkpoint["report_path"] = _write_checkpoint(report_path, checkpoint)

    checkpoint["completed"] = True
    checkpoint.pop("stopped_reason", None)
    checkpoint["report_path"] = _write_checkpoint(report_path, checkpoint)
    return checkpoint
