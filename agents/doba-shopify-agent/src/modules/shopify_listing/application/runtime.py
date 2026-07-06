from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import re
from typing import Any

from src.modules.shopify_listing.infrastructure.draft_listing_service import ShopifyDraftListingService
from src.shared.contracts.listing import (
    ListingBatchResult,
    ShopifyDraftProduct,
    ShopifyImageAsset,
    ShopifyProductContent,
    ShopifyProductPayload,
    ShopifySEOContent,
)
from src.shared.contracts.mapping import SkuMappingRecord
from src.shared.contracts.screening import ListingCandidate
from src.shared.repositories import InMemorySkuMappingRepository
from src.shared.repositories.protocols import ListingRepository, SkuMappingRepository


REPORT_PATH = Path("docs/audits/shopify-listing-report.md")
VALID_IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".webp", ".gif")
COLLECTION_RULES = (
    ("Outdoor", ("outdoor", "garden", "patio", "camping", "yard")),
    ("Home", ("home", "kitchen", "bath", "bed", "decor", "storage", "furniture")),
    ("Tools", ("tool", "drill", "wrench", "saw", "hardware")),
    ("Electronics", ("electronic", "speaker", "headset", "antenna", "charger", "led")),
    ("Pet Supplies", ("pet", "dog", "cat", "grooming", "litter")),
    ("Fitness", ("fitness", "exercise", "gym", "yoga", "elliptical")),
    ("Automotive", ("car", "vehicle", "automotive", "truck", "motor")),
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:255] or "shopify-draft-product"


def _clean_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _optimize_title(title: str, brand: str = "") -> str:
    cleaned = re.sub(r"\[[^\]]+\]|\([^)]+\)", " ", title or "")
    cleaned = re.sub(r"[_|]+", " ", cleaned)
    cleaned = _clean_whitespace(cleaned)
    words = []
    for word in cleaned.split(" "):
        if not word:
            continue
        if word.isupper() and len(word) <= 5:
            words.append(word)
        elif any(char.isdigit() for char in word):
            words.append(word.upper() if len(word) <= 4 else word.capitalize())
        else:
            words.append(word.capitalize())
    optimized = _clean_whitespace(" ".join(words))
    if brand and brand.lower() not in optimized.lower():
        optimized = f"{brand.strip()} {optimized}".strip()
    return optimized[:150]


def _build_highlights(source: dict[str, Any], title: str) -> list[str]:
    highlights = [
        f"Designed for {source.get('category') or 'everyday'} use with a draft-ready merchandising structure.",
        f"Supplier SKU {source.get('supplier_sku') or source.get('sku') or 'N/A'} keeps catalog tracking simple.",
        f"Supports quick storefront setup with curated title, SEO, FAQ, and image metadata.",
    ]
    inventory = int(source.get("inventory") or 0)
    if inventory > 0:
        highlights.append(f"Current supplier inventory snapshot shows {inventory} units available.")
    attributes = source.get("attributes") or {}
    if attributes:
        first_key, first_value = next(iter(attributes.items()))
        highlights.append(f"{str(first_key).replace('_', ' ').title()}: {first_value}.")
    return [_clean_whitespace(item) for item in highlights[:5]]


def _build_faq(source: dict[str, Any], title: str) -> list[str]:
    category = source.get("category") or "this product"
    return [
        f"What makes {title} a good fit for {category.lower()} shoppers?",
        f"How should customers use and care for {title}?",
        f"Which product details should shoppers confirm before ordering {title}?",
    ]


def _build_description(source: dict[str, Any], title: str, highlights: list[str]) -> str:
    summary = source.get("description") or f"{title} is prepared as a Shopify draft with structured merchandising content."
    specs = []
    if source.get("brand"):
        specs.append(f"<li>Brand: {source['brand']}</li>")
    if source.get("category"):
        specs.append(f"<li>Category: {source['category']}</li>")
    if source.get("price"):
        specs.append(f"<li>Source price: ${float(source['price']):.2f}</li>")
    if source.get("inventory") is not None:
        specs.append(f"<li>Supplier inventory: {int(source.get('inventory') or 0)}</li>")
    feature_html = "".join(f"<li>{item}</li>" for item in highlights)
    specs_html = "".join(specs)
    return (
        f"<p>{summary}</p>"
        f"<h2>Key Features</h2><ul>{feature_html}</ul>"
        f"<h2>Specifications</h2><ul>{specs_html}</ul>"
        f"<h2>Usage</h2><p>Ideal for catalog-ready merchandising, customer education, and controlled Shopify draft review.</p>"
    )


def _map_collections(source: dict[str, Any]) -> list[str]:
    blob = _clean_whitespace(
        " ".join(
            [
                str(source.get("title") or ""),
                str(source.get("category") or ""),
                str(source.get("description") or ""),
            ]
        ).lower()
    )
    suggestions = [label for label, tokens in COLLECTION_RULES if any(token in blob for token in tokens)]
    return suggestions or ["General"]


def _process_images(source: dict[str, Any], title: str) -> list[ShopifyImageAsset]:
    raw_urls = list(source.get("image_urls") or [])
    seen: set[str] = set()
    valid_urls: list[str] = []
    for url in raw_urls:
        clean = str(url or "").strip()
        if not clean.startswith(("http://", "https://")):
            continue
        normalized = clean.split("?", 1)[0].lower()
        if "." in normalized.rsplit("/", 1)[-1] and not normalized.endswith(VALID_IMAGE_SUFFIXES):
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        valid_urls.append(clean)
    return [
        ShopifyImageAsset(
            url=url,
            alt_text=f"{title} image {index}",
            position=index,
            is_primary=index == 1,
        )
        for index, url in enumerate(valid_urls, start=1)
    ]


def _build_tags(source: dict[str, Any], collections: list[str]) -> list[str]:
    tags = [
        "doba-import",
        "shopify-draft",
        _slugify(source.get("category") or "general"),
        *(_slugify(collection) for collection in collections),
    ]
    brand = str(source.get("brand") or "").strip()
    if brand:
        tags.append(_slugify(brand))
    deduped: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        if not tag or tag in seen:
            continue
        seen.add(tag)
        deduped.append(tag[:255])
    return deduped[:20]


def _build_seo(title: str, source: dict[str, Any], collections: list[str]) -> ShopifySEOContent:
    seo_title = title[:70]
    base_description = _clean_whitespace(
        source.get("description")
        or f"{title} is a Shopify draft product prepared for controlled catalog review."
    )
    seo_description = base_description[:160]
    return ShopifySEOContent(
        seo_title=seo_title,
        seo_description=seo_description,
        handle=_slugify(title),
        tags=_build_tags(source, collections),
        collection_suggestions=collections,
    )


def _build_product_hash(source: dict[str, Any], title: str, handle: str) -> str:
    digest_source = "|".join(
        [
            str(source.get("brand") or ""),
            str(source.get("category") or ""),
            str(source.get("description") or ""),
            ",".join(source.get("image_urls") or []),
        ]
    )
    return sha256(digest_source.encode("utf-8")).hexdigest()


def _candidate_source(candidate: ListingCandidate) -> dict[str, Any]:
    source = dict(candidate.source_product)
    source.setdefault("supplier_sku", candidate.supplier_sku)
    source.setdefault("supplier_product_id", candidate.supplier_product_id)
    source.setdefault("title", candidate.source_title)
    source.setdefault("description", candidate.source_description)
    source.setdefault("brand", candidate.source_brand)
    source.setdefault("category", candidate.source_category)
    source.setdefault("price", candidate.source_price)
    source.setdefault("inventory", candidate.source_inventory)
    source.setdefault("image_urls", list(candidate.source_image_urls))
    source.setdefault("attributes", dict(candidate.source_attributes))
    source.setdefault("variant_attributes", dict(candidate.source_variant_attributes))
    source.setdefault("score_snapshot", dict(candidate.score_snapshot))
    return source


def _build_payload(candidate: ListingCandidate) -> ShopifyProductPayload:
    source = _candidate_source(candidate)
    title = _optimize_title(source.get("title") or candidate.supplier_sku, source.get("brand") or "")
    collections = _map_collections(source)
    highlights = _build_highlights(source, title)
    faq = _build_faq(source, title)
    description = _build_description(source, title, highlights)
    images = _process_images(source, title)
    seo = _build_seo(title, source, collections)
    product_hash = _build_product_hash(source, title, seo.handle)
    return ShopifyProductPayload(
        supplier_sku=candidate.supplier_sku,
        supplier_product_id=source.get("supplier_product_id") or "",
        product_type=source.get("category") or "General",
        vendor=source.get("brand") or "Doba",
        status="draft",
        product_hash=product_hash,
        content=ShopifyProductContent(
            title=title,
            description=description,
            highlights=highlights,
            faq=faq,
        ),
        seo=seo,
        images=images,
        source_data=source,
    )


def _duplicate_reason(
    payload: ShopifyProductPayload,
    listing_repository: ListingRepository,
    sku_mapping_repository: SkuMappingRepository,
) -> str | None:
    if sku_mapping_repository.get_by_sku(payload.supplier_sku):
        return "duplicate_supplier_sku"
    if listing_repository.handle_exists(payload.seo.handle):
        return "duplicate_handle"
    if listing_repository.product_hash_exists(payload.product_hash):
        return "duplicate_product_hash"
    return None


def _build_report(result: ListingBatchResult) -> str:
    lines = [
        "# Shopify Listing Report",
        "",
        "## Summary",
        f"- Total approved products: `{result.total_approved_products}`",
        f"- Draft products created: `{result.draft_products_created}`",
        f"- Duplicate products skipped: `{result.duplicate_products_skipped}`",
        f"- SKU mappings created: `{result.sku_mappings_created}`",
        f"- Failed products: `{result.failed_products}`",
        f"- Shopify mode: `{result.shopify_mode}`",
        f"- Publish count: `{result.publish_count}`",
        f"- Inventory update count: `{result.inventory_update_count}`",
        f"- Price update count: `{result.price_update_count}`",
        f"- Order create count: `{result.order_create_count}`",
        "",
        "## Failure Reasons",
    ]
    if result.failure_reasons:
        lines.extend(f"- `{reason}`: `{count}`" for reason, count in sorted(result.failure_reasons.items()))
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def _write_report(result: ListingBatchResult) -> str:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(_build_report(result), encoding="utf-8")
    return str(REPORT_PATH.resolve())


def run_shopify_listing(
    listing_candidates: list[ListingCandidate],
    repository: ListingRepository,
    sku_mapping_repository: SkuMappingRepository | None = None,
    shopify_service: ShopifyDraftListingService | None = None,
) -> ListingBatchResult:
    mapping_repository = sku_mapping_repository or InMemorySkuMappingRepository()
    service = shopify_service or ShopifyDraftListingService()
    approved_candidates = [item for item in listing_candidates if item.status == "approved_for_listing"]
    draft_products: list[ShopifyDraftProduct] = []
    skipped_products: list[dict[str, Any]] = []
    sku_mappings: list[SkuMappingRecord] = []
    failures: list[dict[str, str]] = []

    for candidate in approved_candidates:
        try:
            payload = _build_payload(candidate)
            if not payload.content.title or not payload.supplier_sku:
                failures.append({"supplier_sku": candidate.supplier_sku, "reason": "missing_required_source_fields"})
                continue
            duplicate_reason = _duplicate_reason(payload, repository, mapping_repository)
            if duplicate_reason:
                skipped_products.append({"supplier_sku": candidate.supplier_sku, "reason": duplicate_reason})
                continue

            created = service.create_draft_product(payload)
            draft = ShopifyDraftProduct(
                supplier_sku=payload.supplier_sku,
                shopify_product_id=created["shopify_product_id"],
                shopify_variant_id=created["shopify_variant_id"],
                title=payload.content.title,
                description=payload.content.description,
                highlights=payload.content.highlights,
                faq=payload.content.faq,
                seo_title=payload.seo.seo_title,
                seo_description=payload.seo.seo_description,
                handle=payload.seo.handle,
                tags=payload.seo.tags,
                images=payload.images,
                status="draft",
                created_at=_now_iso(),
                collection_suggestions=payload.seo.collection_suggestions,
                product_hash=payload.product_hash,
                source_supplier_product_id=payload.supplier_product_id,
                mock_mode=created["mock_mode"],
            )
            repository.save_shopify_product(draft)
            draft_products.append(draft)

            mapping = SkuMappingRecord(
                supplier_product_id=payload.supplier_product_id,
                supplier_sku=payload.supplier_sku,
                sku=payload.supplier_sku,
                shopify_product_id=draft.shopify_product_id,
                shopify_variant_id=draft.shopify_variant_id,
                handle=draft.handle,
                product_hash=draft.product_hash,
                created_at=draft.created_at,
            )
            mapping_repository.save(mapping)
            sku_mappings.append(mapping)
        except Exception as exc:
            failures.append({"supplier_sku": candidate.supplier_sku, "reason": str(exc)})

    failure_counter = Counter(item["reason"] for item in failures)
    result = ListingBatchResult(
        total_approved_products=len(approved_candidates),
        draft_products_created=len(draft_products),
        duplicate_products_skipped=len(skipped_products),
        sku_mappings_created=len(sku_mappings),
        failed_products=len(failures),
        failure_reasons=dict(failure_counter),
        shopify_mode=service.mode,
        publish_count=0,
        inventory_update_count=0,
        price_update_count=0,
        order_create_count=0,
        draft_products=draft_products,
        skipped_products=skipped_products + failures,
        sku_mappings=[mapping.model_dump() for mapping in sku_mappings],
    )
    repository.save_listing_batch_result(result)
    result.report_path = _write_report(result)
    return result
