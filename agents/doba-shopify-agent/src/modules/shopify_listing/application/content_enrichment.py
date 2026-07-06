from __future__ import annotations

from typing import Any
import re

from src.shared.contracts.enrichment import (
    GeoScoreProjection,
    GoogleMerchantProjection,
    OpenAIProductFeedProjection,
    PostPublishReviewProjection,
    ProductEnrichmentBundle,
    ProductFAQEntry,
    ProductImageAlt,
    ProductSemanticSummary,
    SchemaProjection,
    StructuredProductDetails,
)
from src.shared.contracts.listing import ShopifySEOContent


def _clean_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")
    return slug[:255] or "doba-product"


def _unique_strings(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for value in values:
        text = _clean_whitespace(str(value or ""))
        if not text or text in seen:
            continue
        seen.add(text)
        normalized.append(text)
    return normalized


def _clean_html_text(value: str) -> str:
    return _clean_whitespace(re.sub(r"<[^>]+>", " ", str(value or "")))


def _specs_from_candidate(candidate: Any) -> dict[str, str]:
    specs: dict[str, str] = {}
    if getattr(candidate, "brand", ""):
        specs["Brand"] = str(candidate.brand)
    if getattr(candidate, "category_name", ""):
        specs["Category"] = str(candidate.category_name)
    if getattr(candidate, "ship_from_country", ""):
        specs["Ship From"] = str(candidate.ship_from_country)
    variant_count = len(list(getattr(candidate, "variants", []) or []))
    if variant_count:
        specs["Variant Count"] = str(variant_count)
    inventories = [int(getattr(variant, "inventory", 0) or 0) for variant in list(getattr(candidate, "variants", []) or [])]
    if inventories:
        specs["Max Inventory"] = str(max(inventories))
    sale_prices = [float(getattr(variant, "sale_price", 0) or 0) for variant in list(getattr(candidate, "variants", []) or [])]
    if sale_prices:
        specs["Starting Price"] = f"{min(sale_prices):.2f} USD"
    return specs


def _semantic_summary(candidate: Any) -> ProductSemanticSummary:
    title = _clean_whitespace(str(getattr(candidate, "title", "") or ""))
    category_name = _clean_whitespace(str(getattr(candidate, "category_name", "") or "General"))
    brand = _clean_whitespace(str(getattr(candidate, "brand", "") or "DOBA"))
    product_type = category_name or "General"
    summary = _clean_whitespace(f"{brand} {title} for {category_name} catalogs.")
    confidence = 0.55
    if title and category_name:
        confidence += 0.2
    if len(list(getattr(candidate, "variants", []) or [])) > 0:
        confidence += 0.1
    if getattr(candidate, "description_html", ""):
        confidence += 0.1
    return ProductSemanticSummary(
        product_type=product_type[:80],
        category_label=_slugify(category_name),
        summary=summary[:240],
        confidence=round(min(confidence, 0.95), 2),
    )


def _build_seo(candidate: Any, semantic: ProductSemanticSummary) -> ShopifySEOContent:
    title = _clean_whitespace(str(getattr(candidate, "title", "") or ""))
    category_name = _clean_whitespace(str(getattr(candidate, "category_name", "") or "General"))
    description = _clean_html_text(str(getattr(candidate, "description_html", "") or ""))
    seo_description = description or f"{title} from DOBA, categorized under {category_name}."
    tags = _unique_strings(
        [
            "doba",
            "shopify-live-publish",
            category_name,
            semantic.product_type,
            *list(getattr(candidate, "tags", []) or []),
        ]
    )
    return ShopifySEOContent(
        seo_title=(title[:70] or semantic.summary[:70]),
        seo_description=seo_description[:160],
        handle=_slugify(title or semantic.summary),
        tags=[_slugify(tag) for tag in tags[:20]],
        collection_suggestions=["NEW ARRIVALS"],
    )


def _build_faq(candidate: Any) -> list[ProductFAQEntry]:
    title = _clean_whitespace(str(getattr(candidate, "title", "") or "this item"))
    category_name = _clean_whitespace(str(getattr(candidate, "category_name", "") or "this category")).lower()
    ship_from = _clean_whitespace(str(getattr(candidate, "ship_from_country", "") or "United States"))
    variants = list(getattr(candidate, "variants", []) or [])
    inventory = max([int(getattr(variant, "inventory", 0) or 0) for variant in variants] or [0])
    return [
        ProductFAQEntry(
            question=f"What kind of product is {title}?",
            answer=f"It is a {category_name} item supplied through DOBA and prepared for Shopify publishing.",
        ),
        ProductFAQEntry(
            question=f"Where does {title} ship from?",
            answer=f"The current supplier archive resolves ship-from as {ship_from}.",
        ),
        ProductFAQEntry(
            question=f"Is {title} currently in stock?",
            answer=f"The latest archive snapshot shows up to {inventory} units available across publishable variants.",
        ),
    ]


def _build_image_alts(candidate: Any) -> list[ProductImageAlt]:
    title = _clean_whitespace(str(getattr(candidate, "title", "") or "Doba product"))
    category_name = _clean_whitespace(str(getattr(candidate, "category_name", "") or "product"))
    image_urls = list(getattr(candidate, "image_urls", []) or [])
    variants = list(getattr(candidate, "variants", []) or [])
    primary_variant = variants[0] if variants else None
    option_hint = ""
    if primary_variant is not None:
        option_values = dict(getattr(primary_variant, "option_values", {}) or {})
        option_hint = _clean_whitespace(" ".join(str(value) for value in option_values.values()))
    return [
        ProductImageAlt(
            url=str(url),
            alt_text=_clean_whitespace(f"{title} {option_hint} {category_name} image {index}"),
            position=index,
            is_primary=index == 1,
        )
        for index, url in enumerate(image_urls, start=1)
    ]


def _build_structured_details(candidate: Any, semantic: ProductSemanticSummary) -> StructuredProductDetails:
    description = _clean_html_text(str(getattr(candidate, "description_html", "") or ""))
    title = _clean_whitespace(str(getattr(candidate, "title", "") or ""))
    specs = _specs_from_candidate(candidate)
    highlights = _unique_strings(
        [
            f"Prepared for {semantic.product_type.lower()} merchandising.",
            f"Ships from {specs.get('Ship From', 'United States')}.",
            f"Supports {specs.get('Variant Count', '1')} publishable variant(s).",
            f"Starting sale price {specs.get('Starting Price', '0.00 USD')}.",
        ]
    )
    return StructuredProductDetails(
        headline=title[:140],
        summary=(description[:240] or semantic.summary[:240]),
        highlights=highlights[:6],
        key_specs=specs,
        usage_scenarios=[
            f"Use on Shopify product pages for {semantic.product_type.lower()} discovery.",
            "Project to Google Merchant or feed exports after merchant review.",
        ],
        care_instructions=[
            "Verify variant-specific stock before promotion.",
            "Keep category and feed mapping aligned with the latest archive snapshot.",
        ],
    )


def _build_google_merchant(candidate: Any, seo: ShopifySEOContent, details: StructuredProductDetails) -> GoogleMerchantProjection:
    variants = list(getattr(candidate, "variants", []) or [])
    first_variant = variants[0] if variants else None
    sale_price = float(getattr(first_variant, "sale_price", 0) or 0)
    inventory = int(getattr(first_variant, "inventory", 0) or 0)
    category_name = _clean_whitespace(str(getattr(candidate, "category_name", "") or "General"))
    brand = _clean_whitespace(str(getattr(candidate, "brand", "") or "DOBA"))
    image_urls = list(getattr(candidate, "image_urls", []) or [])
    return GoogleMerchantProjection(
        title=seo.seo_title,
        description=seo.seo_description,
        google_product_category=category_name,
        product_type=category_name,
        brand=brand,
        availability=("in stock" if inventory > 0 else "out of stock"),
        price_amount=round(sale_price, 2),
        image_link=(image_urls[0] if image_urls else ""),
        additional_image_links=image_urls[1:10],
        custom_labels=_unique_strings(
            [
                f"ship-from:{getattr(candidate, 'ship_from_country', '') or 'UNKNOWN'}",
                f"seller:{getattr(candidate, 'seller_name', '') or 'unknown'}",
                details.key_specs.get("Variant Count", "1"),
            ]
        ),
    )


def _build_openai_feed(candidate: Any, semantic: ProductSemanticSummary, details: StructuredProductDetails, seo: ShopifySEOContent) -> OpenAIProductFeedProjection:
    attributes = dict(details.key_specs)
    category_tokens = [token for token in re.split(r"[>/]+", str(getattr(candidate, "category_name", "") or "")) if _clean_whitespace(token)]
    return OpenAIProductFeedProjection(
        title=_clean_whitespace(str(getattr(candidate, "title", "") or "")),
        description=_clean_html_text(str(getattr(candidate, "description_html", "") or ""))[:300],
        category_path=category_tokens or [semantic.product_type],
        tags=_unique_strings([semantic.category_label, *list(getattr(candidate, "tags", []) or []), *seo.tags])[:24],
        attributes={str(key): str(value) for key, value in attributes.items()},
        seo_keywords=_unique_strings([semantic.product_type, getattr(candidate, "category_name", ""), getattr(candidate, "brand", "")])[:12],
    )


def _build_schema(candidate: Any, merchant: GoogleMerchantProjection, details: StructuredProductDetails) -> SchemaProjection:
    variants = list(getattr(candidate, "variants", []) or [])
    first_variant = variants[0] if variants else None
    payload = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": getattr(candidate, "title", ""),
        "description": details.summary,
        "brand": {
            "@type": "Brand",
            "name": getattr(candidate, "brand", "") or "DOBA",
        },
        "sku": getattr(first_variant, "sku", "") if first_variant is not None else "",
        "category": merchant.product_type,
        "image": list(getattr(candidate, "image_urls", []) or []),
        "offers": {
            "@type": "Offer",
            "priceCurrency": merchant.price_currency,
            "price": merchant.price_amount,
            "availability": merchant.availability,
        },
    }
    return SchemaProjection(schema_type="Product", payload=payload)


def _build_geo_score(candidate: Any, details: StructuredProductDetails, image_alts: list[ProductImageAlt], seo: ShopifySEOContent) -> GeoScoreProjection:
    score = 45
    reasons: list[str] = []
    if str(getattr(candidate, "ship_from_country", "") or "") == "United States":
        score += 15
        reasons.append("US ship-from confirmed")
    if len(list(getattr(candidate, "variants", []) or [])) > 0:
        score += 10
        reasons.append("publishable variants available")
    if image_alts:
        score += 10
        reasons.append("image alt metadata prepared")
    if details.summary:
        score += 10
        reasons.append("structured description ready")
    if str(getattr(candidate, "category_metafields", {}) or {}).strip():
        score += 5
        reasons.append("category metadata present")
    if seo.seo_title and seo.seo_description:
        score += 5
        reasons.append("SEO fields prepared")
    return GeoScoreProjection(
        market="US",
        score=max(0, min(100, score)),
        eligible=score >= 70,
        reasons=reasons,
    )


def build_candidate_enrichment(candidate: Any) -> ProductEnrichmentBundle:
    semantic = _semantic_summary(candidate)
    seo = _build_seo(candidate, semantic)
    faq = _build_faq(candidate)
    image_alts = _build_image_alts(candidate)
    details = _build_structured_details(candidate, semantic)
    merchant = _build_google_merchant(candidate, seo, details)
    openai_feed = _build_openai_feed(candidate, semantic, details, seo)
    schema = _build_schema(candidate, merchant, details)
    geo_score = _build_geo_score(candidate, details, image_alts, seo)
    return ProductEnrichmentBundle(
        semantic=semantic,
        details=details,
        seo=seo,
        faq=faq,
        image_alts=image_alts,
        google_merchant=merchant,
        openai_feed=openai_feed,
        schema_projection=schema,
        geo_score=geo_score,
    )


def build_post_publish_review(candidate: Any, publish_result: dict[str, Any]) -> PostPublishReviewProjection:
    published_channels = list((publish_result or {}).get("published_to") or [])
    published_variants = list((publish_result or {}).get("variants") or [])
    expected_variant_count = len(list(getattr(candidate, "variants", []) or []))
    actual_variant_count = len(published_variants) or int((publish_result or {}).get("variant_count") or 0)
    category_written = bool(str((publish_result or {}).get("shopify_category_id") or "").strip())
    review_notes: list[str] = []
    if actual_variant_count == expected_variant_count:
        review_notes.append("Variant count matches expected publishable variants.")
    else:
        review_notes.append("Variant count does not match expected publishable variants.")
    if category_written:
        review_notes.append("Shopify category write confirmed.")
    else:
        review_notes.append("Shopify category write missing or unresolved.")
    if published_channels:
        review_notes.append("At least one target sales channel is published.")
    return PostPublishReviewProjection(
        shopify_product_id=str((publish_result or {}).get("shopify_product_id") or ""),
        published_channels=published_channels,
        variant_count_expected=expected_variant_count,
        variant_count_actual=actual_variant_count,
        category_written=category_written,
        publish_ready=(actual_variant_count == expected_variant_count and category_written and bool(published_channels)),
        review_notes=review_notes,
    )


def summarize_enrichment(bundle_payload: dict[str, Any], post_publish_review_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = dict(bundle_payload or {})
    semantic = dict(payload.get("semantic") or {})
    seo = dict(payload.get("seo") or {})
    schema = dict(payload.get("schema_projection") or {})
    google_merchant = dict(payload.get("google_merchant") or {})
    openai_feed = dict(payload.get("openai_feed") or {})
    geo_score = dict(payload.get("geo_score") or {})
    summary = {
        "semantic_product_type": str(semantic.get("product_type") or ""),
        "semantic_category_label": str(semantic.get("category_label") or ""),
        "seo_title": str(seo.get("seo_title") or ""),
        "faq_count": len(list(payload.get("faq") or [])),
        "image_alt_count": len(list(payload.get("image_alts") or [])),
        "schema_type": str(schema.get("schema_type") or ""),
        "google_product_category": str(google_merchant.get("google_product_category") or ""),
        "openai_feed_tag_count": len(list(openai_feed.get("tags") or [])),
        "geo_score": int(geo_score.get("score") or 0),
        "geo_eligible": bool(geo_score.get("eligible", False)),
    }
    if post_publish_review_payload:
        review = dict(post_publish_review_payload or {})
        summary["post_publish_ready"] = bool(review.get("publish_ready", False))
        summary["post_publish_variant_match"] = int(review.get("variant_count_expected") or 0) == int(review.get("variant_count_actual") or 0)
    return summary
