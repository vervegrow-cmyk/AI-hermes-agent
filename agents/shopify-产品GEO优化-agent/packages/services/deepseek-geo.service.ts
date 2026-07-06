import {
  AgenticUXAudit,
  BeforeAfterScoreModule,
  DeepSeekContentOptimizationResult,
  DeepSeekGeoAnalysis,
  DeepSeekGeoInput,
  DeepSeekPolicyCompliance,
  ImageAltRecommendation,
  MetafieldRecommendation,
  ProductDetailContent,
  ProductFAQEntry,
  ProductGeoAuditModule,
  ProductGeoRecommendations,
  ProductOptimizationResult,
  ProductSemanticProfile,
  SafeWritebackPlanOutput,
  SearchIntentProjection,
  SeoMetadataRecommendation,
} from "../agents/product-agentic-geo-agent/product-agentic-geo.types.js";
import {
  DEEPSEEK_SAFE_WRITEBACK_CONTENT_FIELDS,
} from "../config/deepseek-content-optimization-fields.js";
import { fetchWithRetry } from "./fetch-retry.service.js";

function asString(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

function asNumber(value: unknown, fallback = 0): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function asBoolean(value: unknown, fallback = false): boolean {
  return typeof value === "boolean" ? value : fallback;
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === "string");
}

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function truncate(value: string | undefined, maxLength: number): string {
  if (!value) {
    return "";
  }
  return value.length > maxLength ? `${value.slice(0, maxLength)}...` : value;
}

function compactJsonLikeValue(
  value: unknown,
  options: {
    maxDepth?: number;
    maxKeys?: number;
    maxItems?: number;
    maxStringLength?: number;
  } = {},
): unknown {
  const maxDepth = options.maxDepth ?? 4;
  const maxKeys = options.maxKeys ?? 20;
  const maxItems = options.maxItems ?? 20;
  const maxStringLength = options.maxStringLength ?? 300;
  const seen = new WeakSet<object>();

  const visit = (input: unknown, depth: number): unknown => {
    if (input == null) {
      return input;
    }

    if (typeof input === "string") {
      return truncate(normalizeText(input), maxStringLength);
    }

    if (typeof input === "number" || typeof input === "boolean") {
      return input;
    }

    if (depth >= maxDepth) {
      if (Array.isArray(input)) {
        return input.length > 0 ? ["[truncated]"] : [];
      }
      return "[truncated]";
    }

    if (Array.isArray(input)) {
      return input.slice(0, maxItems).map((item) => visit(item, depth + 1));
    }

    if (typeof input === "object") {
      if (seen.has(input)) {
        return "[circular]";
      }
      seen.add(input);

      const entries = Object.entries(input).slice(0, maxKeys);
      return Object.fromEntries(
        entries.map(([key, nested]) => [key, visit(nested, depth + 1)]),
      );
    }

    return String(input);
  };

  return visit(value, 0);
}

function normalizeText(value: string): string {
  return value.replace(/\s+/g, " ").trim();
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function resolveOptimizationResult(value: string): ProductOptimizationResult {
  if (
    value === "PASS" ||
    value === "PARTIAL_PASS" ||
    value === "WEAK_PASS" ||
    value === "FAILED" ||
    value === "RISK_BLOCKED" ||
    value === "NEED_MANUAL_DATA" ||
    value === "MAX_REOPTIMIZE_REACHED" ||
    value === "UNQUALIFIED_SKIPPED" ||
    value === "MODEL_REPEATED_WEAK_OUTPUT"
  ) {
    return value;
  }
  return "FAILED";
}

function normalizeSafeField(field: string): string {
  const normalized = normalizeText(field).toLowerCase();
  const aliasMap: Record<string, string> = {
    descriptionhtml: "description_html",
    "product_detail_content.description_html": "description_html",
    "product_detail_content": "description_html",
    seotitle: "seo_title",
    "seo_metadata.seo_title": "seo_title",
    seodescription: "seo_description",
    "seo_metadata.seo_description": "seo_description",
    imagealt: "image_alt",
    "image_alt_text": "image_alt",
    "image_alt_texts": "image_alt",
    "image_alt_suggestions": "image_alt",
    "seo_metadata.image_alt_suggestions": "image_alt",
    "handle_suggestion": "handle",
    "seo_metadata.handle_suggestion": "handle",
    "faq_metafields": "metafields",
    "semantic_profile_metafields": "metafields",
    "geo_custom_metafields": "metafields",
    "geo_metafields": "metafields",
    "schema_metafields": "metafields",
    "google_merchant_metafields": "metafields",
    "openai_feed_metafields": "metafields",
  };
  return aliasMap[normalized] ?? normalized;
}

function uniqueNormalizedFields(fields: string[]): string[] {
  const values = new Set(
    fields.map(normalizeSafeField).filter(Boolean),
  );
  return [...values];
}

function asFaqArray(value: unknown): ProductFAQEntry[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((item) => {
      const record = asRecord(item);
      return {
        question: normalizeText(asString(record.question)),
        answer: normalizeText(asString(record.answer)),
      };
    })
    .filter((item) => item.question.length > 0 && item.answer.length > 0);
}

function asImageAltArray(value: unknown): ImageAltRecommendation[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((item) => {
      const record = asRecord(item);
      return {
        image_id: asString(record.image_id),
        alt: normalizeText(asString(record.alt)),
      };
    })
    .filter((item) => item.image_id.length > 0 && item.alt.length > 0);
}

function parseSemanticProfile(raw: unknown): ProductSemanticProfile {
  const record = asRecord(raw);
  return {
    what_is_it: normalizeText(asString(record.what_is_it)),
    primary_use_case: normalizeText(asString(record.primary_use_case)),
    target_buyers: asStringArray(record.target_buyers).map(normalizeText).filter(Boolean),
    shopping_scenarios: asStringArray(record.shopping_scenarios).map(normalizeText).filter(Boolean),
    recommendation_triggers: asStringArray(record.recommendation_triggers)
      .map(normalizeText)
      .filter(Boolean),
    not_suitable_for: asStringArray(record.not_suitable_for).map(normalizeText).filter(Boolean),
    key_attributes: asStringArray(record.key_attributes).map(normalizeText).filter(Boolean),
  };
}

function parseSearchIntentProjection(raw: unknown): SearchIntentProjection {
  const record = asRecord(raw);
  return {
    core_queries: asStringArray(record.core_queries).map(normalizeText).filter(Boolean),
    problem_queries: asStringArray(record.problem_queries).map(normalizeText).filter(Boolean),
    comparison_queries: asStringArray(record.comparison_queries).map(normalizeText).filter(Boolean),
    gift_queries: asStringArray(record.gift_queries).map(normalizeText).filter(Boolean),
    agent_recommendation_triggers: asStringArray(record.agent_recommendation_triggers)
      .map(normalizeText)
      .filter(Boolean),
  };
}

function parseProductDetailContent(raw: unknown): ProductDetailContent {
  const record = asRecord(raw);
  return {
    summary: normalizeText(asString(record.summary)),
    key_selling_points: asStringArray(record.key_selling_points).map(normalizeText).filter(Boolean),
    use_cases: asStringArray(record.use_cases).map(normalizeText).filter(Boolean),
    specifications: asStringArray(record.specifications).map(normalizeText).filter(Boolean),
    package_includes: asStringArray(record.package_includes).map(normalizeText).filter(Boolean),
    how_to_use: asStringArray(record.how_to_use).map(normalizeText).filter(Boolean),
    suitable_for: asStringArray(record.suitable_for).map(normalizeText).filter(Boolean),
    caution_notes: asStringArray(record.caution_notes).map(normalizeText).filter(Boolean),
    description_html: normalizeText(asString(record.description_html)),
  };
}

function parseSeoMetadata(raw: unknown): SeoMetadataRecommendation {
  const record = asRecord(raw);
  return {
    seo_title: normalizeText(asString(record.seo_title)),
    seo_description: normalizeText(asString(record.seo_description)),
    handle_suggestion: normalizeText(asString(record.handle_suggestion)),
    image_alt_suggestions: asImageAltArray(record.image_alt_suggestions),
    internal_link_suggestions: asStringArray(record.internal_link_suggestions)
      .map(normalizeText)
      .filter(Boolean),
  };
}

function parseAgenticUXAudit(raw: unknown): AgenticUXAudit {
  const record = asRecord(raw);
  return {
    can_identify_title: asBoolean(record.can_identify_title, true),
    can_identify_price: asBoolean(record.can_identify_price, true),
    can_select_variant: asBoolean(record.can_select_variant, true),
    can_add_to_cart: asBoolean(record.can_add_to_cart, true),
    can_enter_checkout: asBoolean(record.can_enter_checkout, false),
    can_read_shipping_return: asBoolean(record.can_read_shipping_return, false),
    issues: asStringArray(record.issues).map(normalizeText).filter(Boolean),
  };
}

function parsePolicyCompliance(raw: unknown): DeepSeekPolicyCompliance {
  const record = asRecord(raw);
  return {
    source_truth_used: asBoolean(record.source_truth_used, false),
    business_policy_used: asBoolean(record.business_policy_used, false),
    locked_policy_fields_modified: asBoolean(record.locked_policy_fields_modified, false),
    real_fields_invented: asBoolean(record.real_fields_invented, false),
    gtin_invented: asBoolean(record.gtin_invented, false),
    warehouse_city_invented: asBoolean(record.warehouse_city_invented, false),
    sku_used_as_gtin: asBoolean(record.sku_used_as_gtin, false),
    notes: asStringArray(record.notes).map(normalizeText).filter(Boolean),
  };
}

function parseSafeWritebackPlan(raw: unknown): SafeWritebackPlanOutput {
  const record = asRecord(raw);
  return {
    safe_fields: asStringArray(record.safe_fields).map(normalizeText).filter(Boolean),
    approval_required_fields: asStringArray(record.approval_required_fields)
      .map(normalizeText)
      .filter(Boolean),
    forbidden_fields: asStringArray(record.forbidden_fields).map(normalizeText).filter(Boolean),
  };
}

function parseGeoAuditModule(raw: unknown): ProductGeoAuditModule {
  const record = asRecord(raw);
  return {
    before_geo_score: asNumber(record.before_geo_score),
    missing_fields: asStringArray(record.missing_fields).map(normalizeText).filter(Boolean),
    risk_flags: asStringArray(record.risk_flags).map(normalizeText).filter(Boolean),
    catalog_gaps: asStringArray(record.catalog_gaps).map(normalizeText).filter(Boolean),
    google_merchant_gaps: asStringArray(record.google_merchant_gaps).map(normalizeText).filter(Boolean),
    openai_feed_gaps: asStringArray(record.openai_feed_gaps).map(normalizeText).filter(Boolean),
    schema_gaps: asStringArray(record.schema_gaps).map(normalizeText).filter(Boolean),
    agentic_ux_gaps: asStringArray(record.agentic_ux_gaps).map(normalizeText).filter(Boolean),
  };
}

function parseBeforeAfterScoreModule(raw: unknown): BeforeAfterScoreModule {
  const record = asRecord(raw);
  return {
    before_geo_score: asNumber(record.before_geo_score),
    after_geo_score: asNumber(record.after_geo_score),
    score_delta: asNumber(record.score_delta),
    optimization_result: resolveOptimizationResult(asString(record.optimization_result)),
    writeback_allowed: asBoolean(record.writeback_allowed),
  };
}

function buildDescriptionHtml(content: ProductDetailContent): string {
  if (content.description_html) {
    return content.description_html;
  }

  const sections: string[] = [];
  if (content.summary) {
    sections.push(`<p>${escapeHtml(content.summary)}</p>`);
  }

  const mappings: Array<[string, string[]]> = [
    ["Key Selling Points", content.key_selling_points],
    ["Use Cases", content.use_cases],
    ["Specifications", content.specifications],
    ["Package Includes", content.package_includes],
    ["How To Use", content.how_to_use],
    ["Suitable For", content.suitable_for],
    ["Caution Notes", content.caution_notes],
  ];

  for (const [title, items] of mappings) {
    if (items.length === 0) {
      continue;
    }

    sections.push(
      `<h3>${escapeHtml(title)}</h3><ul>${items
        .map((item) => `<li>${escapeHtml(item)}</li>`)
        .join("")}</ul>`,
    );
  }

  return sections.join("");
}

function buildFallbackSearchIntents(semanticProfile: ProductSemanticProfile): SearchIntentProjection {
  return {
    core_queries: semanticProfile.shopping_scenarios.slice(0, 4),
    problem_queries: [semanticProfile.primary_use_case].filter(Boolean),
    comparison_queries: [],
    gift_queries: semanticProfile.target_buyers.slice(0, 2).map((buyer) => `gift for ${buyer}`),
    agent_recommendation_triggers: semanticProfile.recommendation_triggers,
  };
}

function slugifyHandle(value: string): string {
  return normalizeText(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 120);
}

function buildFallbackFaqContent(
  input: DeepSeekGeoInput | undefined,
  semanticProfile: ProductSemanticProfile,
  productDetailContent: ProductDetailContent,
): ProductFAQEntry[] {
  const title = normalizeText(input?.title ?? semanticProfile.what_is_it);
  const productType = normalizeText(input?.productType ?? semanticProfile.what_is_it);
  const primaryUse = normalizeText(
    semanticProfile.primary_use_case || productDetailContent.use_cases[0] || "everyday use",
  );
  const summary = normalizeText(productDetailContent.summary || title);
  const firstSpec = normalizeText(productDetailContent.specifications[0] ?? "");
  const firstPackageItem = normalizeText(productDetailContent.package_includes[0] ?? "");
  const firstHowTo = normalizeText(productDetailContent.how_to_use[0] ?? "");

  return [
    {
      question: `What is this ${productType || "product"} used for?`,
      answer: primaryUse || summary || title,
    },
    {
      question: `Who is ${title || "this product"} best for?`,
      answer:
        semanticProfile.target_buyers.slice(0, 3).join(", ") ||
        semanticProfile.shopping_scenarios[0] ||
        "buyers looking for a practical, ready-to-use solution.",
    },
    {
      question: `What are the key features of ${title || "this product"}?`,
      answer:
        productDetailContent.key_selling_points.slice(0, 3).join("; ") ||
        summary ||
        "See the product detail section for the main benefits and specifications.",
    },
    {
      question: `What comes in the package?`,
      answer:
        productDetailContent.package_includes.join("; ") ||
        firstPackageItem ||
        "Please review the package contents listed in the product details.",
    },
    {
      question: `How do I use or set up this product?`,
      answer:
        productDetailContent.how_to_use.join("; ") ||
        firstHowTo ||
        "Follow the product instructions and use it as intended for the best results.",
    },
    {
      question: `Are there any important specifications or notes?`,
      answer:
        [firstSpec, ...productDetailContent.caution_notes.slice(0, 2)].filter(Boolean).join("; ") ||
        "Check the specification and notes sections for dimensions, materials, and care guidance.",
    },
  ].filter((item) => item.question && item.answer);
}

function buildFallbackImageAltSuggestions(
  input: DeepSeekGeoInput | undefined,
  semanticProfile: ProductSemanticProfile,
): ImageAltRecommendation[] {
  const productLabel = normalizeText(input?.productType || semanticProfile.what_is_it || input?.title || "product");
  const useCase = normalizeText(semanticProfile.primary_use_case || semanticProfile.shopping_scenarios[0] || "");
  return (input?.images ?? []).slice(0, 12).map((image, index) => ({
    image_id: image.id,
    alt: [productLabel, useCase, `image ${index + 1}`].filter(Boolean).join(" - "),
  }));
}

function buildFallbackSchemaProjection(
  input: DeepSeekGeoInput | undefined,
  semanticProfile: ProductSemanticProfile,
  productDetailContent: ProductDetailContent,
  faqContent: ProductFAQEntry[],
): Record<string, unknown> {
  const firstVariant = input?.variants?.[0];
  const firstImage = input?.images?.[0];
  const title = normalizeText(input?.title || semanticProfile.what_is_it);
  const description = normalizeText(productDetailContent.summary || input?.descriptionHtml || title);
  const vendor = normalizeText(input?.vendor ?? "");
  const price = typeof firstVariant?.price === "number" ? String(firstVariant.price) : "";
  const availability = firstVariant?.availableForSale ? "https://schema.org/InStock" : "https://schema.org/OutOfStock";
  const handle = slugifyHandle(title);

  return {
    Product: {
      "@context": "https://schema.org",
      "@type": "Product",
      name: title,
      description,
      sku: firstVariant?.sku || "",
      brand: vendor ? { "@type": "Brand", name: vendor } : undefined,
      image: firstImage?.url || "",
    },
    Offer: {
      "@type": "Offer",
      priceCurrency: "USD",
      price,
      availability,
      itemCondition: "https://schema.org/NewCondition",
      url: handle ? `/products/${handle}` : "",
    },
    FAQPage: {
      "@type": "FAQPage",
      mainEntity: faqContent.slice(0, 8).map((item) => ({
        "@type": "Question",
        name: item.question,
        acceptedAnswer: { "@type": "Answer", text: item.answer },
      })),
    },
    BreadcrumbList: {
      "@type": "BreadcrumbList",
      itemListElement: [
        { "@type": "ListItem", position: 1, name: "Home", item: "/" },
        { "@type": "ListItem", position: 2, name: input?.productType || "Products", item: "/collections/all" },
        { "@type": "ListItem", position: 3, name: title, item: handle ? `/products/${handle}` : "" },
      ],
    },
  };
}

function buildFallbackGoogleMerchantProjection(
  input: DeepSeekGeoInput | undefined,
  semanticProfile: ProductSemanticProfile,
  productDetailContent: ProductDetailContent,
): Record<string, unknown> {
  const firstVariant = input?.variants?.[0];
  const firstImage = input?.images?.[0];
  const title = normalizeText(input?.title || semanticProfile.what_is_it);
  const description = normalizeText(productDetailContent.summary || input?.descriptionHtml || title);
  const handle = slugifyHandle(title);
  const hasGtin = Boolean(firstVariant?.barcode?.trim());
  return {
    id: input?.productId || firstVariant?.id || title,
    title,
    description,
    product_type: normalizeText(input?.productType || semanticProfile.what_is_it),
    google_product_category: "",
    link: handle ? `/products/${handle}` : "",
    image_link: firstImage?.url || "",
    additional_image_link: (input?.images ?? []).slice(1, 10).map((image) => image.url),
    availability: firstVariant?.availableForSale ? "in_stock" : "out_of_stock",
    price: typeof firstVariant?.price === "number" ? `${firstVariant.price} USD` : "",
    condition: "new",
    brand: normalizeText(input?.vendor ?? ""),
    mpn: firstVariant?.sku || "",
    gtin: hasGtin ? firstVariant?.barcode || "" : "",
    custom_product: hasGtin ? false : true,
  };
}

function buildFallbackOpenAiProductFeedProjection(
  input: DeepSeekGeoInput | undefined,
  semanticProfile: ProductSemanticProfile,
  productDetailContent: ProductDetailContent,
): Record<string, unknown> {
  const firstVariant = input?.variants?.[0];
  const firstImage = input?.images?.[0];
  const title = normalizeText(input?.title || semanticProfile.what_is_it);
  const description = normalizeText(productDetailContent.summary || input?.descriptionHtml || title);
  const handle = slugifyHandle(title);
  return {
    item_id: input?.productId || firstVariant?.id || title,
    title,
    description,
    url: handle ? `/products/${handle}` : "",
    image_url: firstImage?.url || "",
    price: typeof firstVariant?.price === "number" ? `${firstVariant.price} USD` : "",
    availability: firstVariant?.availableForSale ? "in_stock" : "out_of_stock",
    seller_name: normalizeText(input?.vendor ?? ""),
    seller_url: "",
    return_policy: "",
    target_countries: ["US"],
    store_country: "US",
    product_type: normalizeText(input?.productType || semanticProfile.what_is_it),
    use_cases: productDetailContent.use_cases.slice(0, 6),
    key_attributes: semanticProfile.key_attributes?.slice(0, 8) ?? [],
    variants: (input?.variants ?? []).slice(0, 10).map((variant) => ({
      id: variant.id,
      title: variant.title,
      sku: variant.sku,
      price: variant.price,
      availability: variant.availableForSale ? "in_stock" : "out_of_stock",
    })),
    shipping: "",
    related_products: [],
    geo_availability: ["US"],
  };
}

function buildStructuredMetafields(input: {
  semanticProfile: ProductSemanticProfile;
  faqContent: ProductFAQEntry[];
  schemaProjection: Record<string, unknown>;
  googleMerchantProjection: Record<string, unknown>;
  openaiProductFeedProjection: Record<string, unknown>;
  searchIntents: SearchIntentProjection;
  geoAudit: ProductGeoAuditModule;
}): MetafieldRecommendation[] {
  return [
    {
      namespace: "product_geo",
      key: "semantic_profile",
      type: "json",
      value: JSON.stringify(input.semanticProfile),
    },
    {
      namespace: "product_geo",
      key: "faq_content",
      type: "json",
      value: JSON.stringify(input.faqContent),
    },
    {
      namespace: "product_geo",
      key: "schema_projection",
      type: "json",
      value: JSON.stringify(input.schemaProjection),
    },
    {
      namespace: "product_geo",
      key: "google_merchant_projection",
      type: "json",
      value: JSON.stringify(input.googleMerchantProjection),
    },
    {
      namespace: "product_geo",
      key: "openai_product_feed_projection",
      type: "json",
      value: JSON.stringify(input.openaiProductFeedProjection),
    },
    {
      namespace: "product_geo",
      key: "search_intents",
      type: "json",
      value: JSON.stringify(input.searchIntents),
    },
    {
      namespace: "product_geo",
      key: "geo_audit",
      type: "json",
      value: JSON.stringify(input.geoAudit),
    },
  ];
}

function buildRecommendations(input: {
  semanticProfile: ProductSemanticProfile;
  productDetailContent: ProductDetailContent;
  seoMetadata: SeoMetadataRecommendation;
  faqContent: ProductFAQEntry[];
  schemaProjection: Record<string, unknown>;
  googleMerchantProjection: Record<string, unknown>;
  openaiProductFeedProjection: Record<string, unknown>;
  searchIntents: SearchIntentProjection;
  geoAudit: ProductGeoAuditModule;
}): ProductGeoRecommendations {
  return {
    title: input.seoMetadata.seo_title || input.semanticProfile.what_is_it,
    description_html: buildDescriptionHtml(input.productDetailContent),
    seo_title: input.seoMetadata.seo_title,
    seo_description: input.seoMetadata.seo_description,
    handle_suggestion: input.seoMetadata.handle_suggestion,
    description_outline: [
      input.productDetailContent.summary,
      ...input.productDetailContent.key_selling_points,
      ...input.productDetailContent.use_cases,
      ...input.productDetailContent.specifications,
      ...input.productDetailContent.how_to_use,
    ].filter(Boolean),
    tags: [
      ...input.semanticProfile.target_buyers,
      ...input.semanticProfile.shopping_scenarios,
      ...input.productDetailContent.use_cases,
    ]
      .map(normalizeText)
      .filter(Boolean)
      .slice(0, 12),
    faq: input.faqContent,
    image_alt: input.seoMetadata.image_alt_suggestions,
    metafields: buildStructuredMetafields({
      semanticProfile: input.semanticProfile,
      faqContent: input.faqContent,
      schemaProjection: input.schemaProjection,
      googleMerchantProjection: input.googleMerchantProjection,
      openaiProductFeedProjection: input.openaiProductFeedProjection,
      searchIntents: input.searchIntents,
      geoAudit: input.geoAudit,
    }),
    search_intents: input.searchIntents,
    openai_feed_projection: input.openaiProductFeedProjection,
    google_merchant_projection: input.googleMerchantProjection,
    schema_projection: input.schemaProjection,
  };
}

function buildDefaultSafeWritebackFields(input: {
  productDetailContent: ProductDetailContent;
  seoMetadata: SeoMetadataRecommendation;
  faqContent: ProductFAQEntry[];
  imageAltSuggestions: ImageAltRecommendation[];
  metafields: MetafieldRecommendation[];
  recommendationTitle?: string;
  recommendationTags?: string[];
}): string[] {
  const fields: string[] = [];

  if (input.recommendationTitle) {
    fields.push("title");
  }
  if (input.seoMetadata.handle_suggestion) {
    fields.push("handle");
  }
  if (input.productDetailContent.description_html || input.productDetailContent.summary) {
    fields.push("description_html");
  }
  if (input.seoMetadata.seo_title) {
    fields.push("seo_title");
  }
  if (input.seoMetadata.seo_description) {
    fields.push("seo_description");
  }
  if (input.imageAltSuggestions.length > 0) {
    fields.push("image_alt");
  }
  if ((input.recommendationTags ?? []).length > 0) {
    fields.push("tags");
  }
  if (input.faqContent.length > 0 || input.metafields.length > 0) {
    fields.push("metafields");
  }

  return uniqueNormalizedFields(fields);
}

function buildContentOptimizationResult(
  parsed: DeepSeekGeoAnalysis,
): DeepSeekContentOptimizationResult {
  return {
    title: parsed.recommendations.title,
    handle: parsed.seo_metadata.handle_suggestion,
    seo_title: parsed.seo_metadata.seo_title,
    seo_description: parsed.seo_metadata.seo_description,
    description_html: parsed.recommendations.description_html,
    tags: parsed.recommendations.tags,
    summary: parsed.product_detail_content.summary,
    key_selling_points: parsed.product_detail_content.key_selling_points,
    use_cases: parsed.product_detail_content.use_cases,
    suitable_for: parsed.product_detail_content.suitable_for,
    package_includes: parsed.product_detail_content.package_includes,
    how_to_use: parsed.product_detail_content.how_to_use,
    caution_notes: parsed.product_detail_content.caution_notes,
    faq_content: parsed.faq_content,
    image_alt: parsed.seo_metadata.image_alt_suggestions,
    schema_projection: parsed.schema_projection,
    google_merchant_projection: parsed.google_merchant_projection,
    openai_product_feed_projection: parsed.openai_product_feed_projection,
    semantic_profile: parsed.semantic_profile,
    search_intents: parsed.search_intents,
    agentic_ux_audit: parsed.agentic_ux_audit,
  };
}

export class DeepSeekGeoService {
  private readonly apiKey: string;
  private readonly baseUrl: string;
  private readonly model: string;

  constructor(config?: { apiKey?: string; baseUrl?: string; model?: string }) {
    this.apiKey = config?.apiKey ?? process.env.DEEPSEEK_API_KEY ?? "";
    this.baseUrl = config?.baseUrl ?? process.env.DEEPSEEK_BASE_URL ?? "https://api.deepseek.com";
    this.model = config?.model ?? process.env.DEEPSEEK_MODEL ?? "deepseek-chat";
  }

  async analyzeProductGEO(input: DeepSeekGeoInput): Promise<DeepSeekGeoAnalysis> {
    if (!this.apiKey) {
      throw new Error("DEEPSEEK_API_KEY is required");
    }

    const compactInput = this.compactInput(input);
    let lastError: Error | null = null;

    for (let attempt = 1; attempt <= 3; attempt += 1) {
      try {
        const content = await this.requestCompletion(compactInput, attempt);
        return this.parseAndValidate(content, compactInput);
      } catch (error) {
        const currentError = error instanceof Error ? error : new Error(String(error));
        lastError = currentError;

        if (this.isJsonParseLikeError(currentError)) {
          try {
            const repaired = await this.repairMalformedJson(currentError.message, compactInput, attempt);
            return this.parseAndValidate(repaired, compactInput);
          } catch (repairError) {
            lastError =
              repairError instanceof Error ? repairError : new Error(String(repairError));
          }
        }
      }
    }

    throw new Error(`DeepSeek 结果解析失败: ${lastError?.message ?? "unknown error"}`);
  }

  parseAndValidate(content: string, input?: DeepSeekGeoInput): DeepSeekGeoAnalysis {
    const raw = this.parseJsonObjectContent(content);
    const record = asRecord(raw);

    const geoAudit = parseGeoAuditModule(record.geo_audit);
    const semanticProfile = parseSemanticProfile(record.semantic_profile);
    const parsedSearchIntents = parseSearchIntentProjection(record.search_intents);
    const productDetailContent = parseProductDetailContent(record.product_detail_content);
    const seoMetadata = parseSeoMetadata(record.seo_metadata);
    const faqContent = asFaqArray(record.faq_content);
    const schemaProjection = asRecord(record.schema_projection);
    const googleMerchantProjection = asRecord(record.google_merchant_projection);
    const openaiProductFeedProjection = asRecord(record.openai_product_feed_projection);
    const agenticUxAudit = parseAgenticUXAudit(record.agentic_ux_audit);
    const beforeAfterScore = parseBeforeAfterScoreModule(record.before_after_score);
    const safeWritebackPlan = parseSafeWritebackPlan(record.safe_writeback_plan);
    const policyCompliance = parsePolicyCompliance(record.policy_compliance);
    const fallbackSearchIntents = buildFallbackSearchIntents(semanticProfile);
    const searchIntents =
      parsedSearchIntents.core_queries.length > 0 ||
      parsedSearchIntents.problem_queries.length > 0 ||
      parsedSearchIntents.comparison_queries.length > 0 ||
      parsedSearchIntents.gift_queries.length > 0 ||
      parsedSearchIntents.agent_recommendation_triggers.length > 0
        ? parsedSearchIntents
        : fallbackSearchIntents;

    const normalizedGeoAudit: ProductGeoAuditModule = {
      before_geo_score: geoAudit.before_geo_score || asNumber(record.geo_score),
      missing_fields:
        geoAudit.missing_fields.length > 0
          ? geoAudit.missing_fields
          : asStringArray(record.missing_fields).map(normalizeText).filter(Boolean),
      risk_flags:
        geoAudit.risk_flags.length > 0
          ? geoAudit.risk_flags
          : asStringArray(record.risk_flags).map(normalizeText).filter(Boolean),
      catalog_gaps: geoAudit.catalog_gaps,
      google_merchant_gaps: geoAudit.google_merchant_gaps,
      openai_feed_gaps: geoAudit.openai_feed_gaps,
      schema_gaps: geoAudit.schema_gaps,
      agentic_ux_gaps: geoAudit.agentic_ux_gaps,
    };

    const normalizedBeforeAfter: BeforeAfterScoreModule = {
      before_geo_score:
        beforeAfterScore.before_geo_score || normalizedGeoAudit.before_geo_score,
      after_geo_score: beforeAfterScore.after_geo_score,
      score_delta: beforeAfterScore.score_delta,
      optimization_result: beforeAfterScore.optimization_result,
      writeback_allowed: beforeAfterScore.writeback_allowed,
    };

    const recommendationDraft = buildRecommendations({
      semanticProfile,
      productDetailContent,
      seoMetadata,
      faqContent,
      schemaProjection,
      googleMerchantProjection,
      openaiProductFeedProjection,
      searchIntents,
      geoAudit: normalizedGeoAudit,
    });

    const normalizedSafeWritebackFields = uniqueNormalizedFields(
      safeWritebackPlan.safe_fields.length > 0
        ? safeWritebackPlan.safe_fields
        : asStringArray(record.safe_writeback_fields),
    );

    const fallbackSafeWritebackFields = buildDefaultSafeWritebackFields({
      productDetailContent,
      seoMetadata,
      faqContent,
      imageAltSuggestions: seoMetadata.image_alt_suggestions,
      metafields: recommendationDraft.metafields,
      recommendationTitle: recommendationDraft.title,
      recommendationTags: recommendationDraft.tags,
    });

    const parsed: DeepSeekGeoAnalysis = {
      geo_audit: normalizedGeoAudit,
      geo_score: normalizedGeoAudit.before_geo_score,
      catalog_score: asNumber(record.catalog_score),
      google_merchant_score: asNumber(record.google_merchant_score),
      openai_feed_score: asNumber(record.openai_feed_score),
      schema_score: asNumber(record.schema_score),
      faq_score: asNumber(record.faq_score, this.deriveFaqScore(faqContent)),
      image_alt_score: asNumber(
        record.image_alt_score,
        this.deriveImageAltScore(seoMetadata.image_alt_suggestions),
      ),
      agentic_ux_score: asNumber(record.agentic_ux_score),
      missing_fields: normalizedGeoAudit.missing_fields,
      risk_flags: normalizedGeoAudit.risk_flags,
      semantic_profile: semanticProfile,
      search_intents: searchIntents,
      product_detail_content: productDetailContent,
      seo_metadata: seoMetadata,
      faq_content: faqContent,
      schema_projection: schemaProjection,
      google_merchant_projection: googleMerchantProjection,
      openai_product_feed_projection: openaiProductFeedProjection,
      agentic_ux_audit: agenticUxAudit,
      before_after_score: normalizedBeforeAfter,
      safe_writeback_plan: safeWritebackPlan,
      policy_compliance: policyCompliance,
      content_optimization_result: {
        title: "",
        handle: "",
        seo_title: "",
        seo_description: "",
        description_html: "",
        tags: [],
        summary: "",
        key_selling_points: [],
        use_cases: [],
        suitable_for: [],
        package_includes: [],
        how_to_use: [],
        caution_notes: [],
        faq_content: [],
        image_alt: [],
        schema_projection: {},
        google_merchant_projection: {},
        openai_product_feed_projection: {},
        semantic_profile: semanticProfile,
        search_intents: searchIntents,
        agentic_ux_audit: agenticUxAudit,
      },
      recommendations: recommendationDraft,
      safe_writeback_fields: uniqueNormalizedFields([
        ...normalizedSafeWritebackFields,
        ...fallbackSafeWritebackFields,
      ]),
      approval_required_fields:
        safeWritebackPlan.approval_required_fields.length > 0
          ? safeWritebackPlan.approval_required_fields
          : asStringArray(record.approval_required_fields).map(normalizeText).filter(Boolean),
      forbidden_fields:
        safeWritebackPlan.forbidden_fields.length > 0
          ? safeWritebackPlan.forbidden_fields
          : asStringArray(record.forbidden_fields).map(normalizeText).filter(Boolean),
    };

    this.applyLayeredFallbacks(parsed, input);
    this.applyContentOptimizationGuard(parsed, input);
    parsed.content_optimization_result = buildContentOptimizationResult(parsed);
    this.assertValid(parsed);
    return parsed;
  }

  private async requestCompletion(input: DeepSeekGeoInput, attempt: number): Promise<string> {
    const response = await fetchWithRetry(`${this.baseUrl}/chat/completions`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${this.apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: this.model,
        messages: [
          {
            role: "system",
            content: [
              "You are ProductAgenticGEOAgent.",
              "Analyze Shopify ACTIVE products for AI shopping, catalog readiness, Google Merchant readiness, and agentic commerce readiness.",
              "Your optimization target is preview_after_geo_score >= 75 whenever product data allows it.",
              "Aggressively fill missing structured modules using available Shopify data and supplier source data.",
              "If aggressive_geo_optimization is enabled, treat target_geo_score as the working goal and push toward 85+ where possible.",
              "Return one valid JSON object only.",
              "Do not include markdown, prose, explanations, or code fences.",
              "Keep strings concise and escape all quotes correctly.",
              "You must return structured top-level modules first, not a flat blob.",
              "Keep each output module separate. Do not mix FAQ, schema, feed, or SEO into descriptionHtml.",
              "Do not modify SKU, price, inventory, barcode, GTIN, or variant_id.",
              "If fields are missing but can be safely inferred from provided product data, generate them in FAQ, schema_projection, google_merchant_projection, openai_product_feed_projection, seo_metadata, and image_alt_suggestions.",
              "If GTIN, barcode, material, dimensions, or weight are not present in input or supplier data, leave them blank instead of inventing values.",
            ].join("\n"),
          },
          {
            role: "user",
            content: this.buildPrompt(input, attempt),
          },
        ],
        response_format: { type: "json_object" },
        temperature: attempt >= 2 ? 0 : 0.1,
      }),
    }, { attempts: 3, baseDelayMs: 1200 });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`DeepSeek API failed: ${response.status} ${text}`);
    }

    const payload = (await response.json()) as {
      choices?: Array<{ message?: { content?: string } }>;
    };
    const content = payload.choices?.[0]?.message?.content;
    if (!content) {
      throw new Error("DeepSeek returned empty content");
    }

    return content;
  }

  private async repairMalformedJson(
    rawErrorMessage: string,
    input: DeepSeekGeoInput,
    attempt: number,
  ): Promise<string> {
    const response = await fetchWithRetry(`${this.baseUrl}/chat/completions`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${this.apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: this.model,
        messages: [
          {
            role: "system",
            content: [
              "You repair malformed JSON for ProductAgenticGEOAgent.",
              "Return one valid JSON object only.",
              "Preserve the required top-level module structure.",
              "Do not return markdown or prose.",
            ].join("\n"),
          },
          {
            role: "user",
            content: JSON.stringify({
              task: "Regenerate a valid JSON object for the same product because the previous response was malformed.",
              attempt,
              previous_error: rawErrorMessage,
              product: input,
              required_top_level_modules: [
                "geo_audit",
                "semantic_profile",
                "search_intents",
                "catalog_score",
                "google_merchant_score",
                "openai_feed_score",
                "schema_score",
                "faq_score",
                "image_alt_score",
                "agentic_ux_score",
                "product_detail_content",
                "seo_metadata",
                "faq_content",
                "schema_projection",
                "google_merchant_projection",
                "openai_product_feed_projection",
                "agentic_ux_audit",
                "before_after_score",
                "safe_writeback_plan",
              ],
            }),
          },
        ],
        response_format: { type: "json_object" },
        temperature: 0,
      }),
    }, { attempts: 3, baseDelayMs: 1200 });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`DeepSeek JSON 修复失败: ${response.status} ${text}`);
    }

    const payload = (await response.json()) as {
      choices?: Array<{ message?: { content?: string } }>;
    };
    const content = payload.choices?.[0]?.message?.content;
    if (!content) {
      throw new Error("DeepSeek JSON 修复返回为空");
    }

    return content;
  }

  private parseJsonObjectContent(content: string): unknown {
    const cleaned = this.sanitizeJsonEnvelope(content);

    try {
      return JSON.parse(cleaned) as unknown;
    } catch (error) {
      const parseMessage = error instanceof Error ? error.message : String(error);
      const extracted = this.extractFirstJsonObject(cleaned);
      if (extracted) {
        try {
          return JSON.parse(extracted) as unknown;
        } catch (nestedError) {
          const nestedMessage =
            nestedError instanceof Error ? nestedError.message : String(nestedError);
          throw new Error(`${nestedMessage}; 原始解析错误: ${parseMessage}`);
        }
      }

      throw new Error(parseMessage);
    }
  }

  private sanitizeJsonEnvelope(content: string): string {
    return content
      .trim()
      .replace(/^```json\s*/i, "")
      .replace(/^```\s*/i, "")
      .replace(/```$/i, "")
      .replace(/\u0000/g, "")
      .trim();
  }

  private extractFirstJsonObject(content: string): string | null {
    const start = content.indexOf("{");
    if (start < 0) {
      return null;
    }

    let depth = 0;
    let inString = false;
    let escaped = false;

    for (let index = start; index < content.length; index += 1) {
      const char = content[index];

      if (escaped) {
        escaped = false;
        continue;
      }

      if (char === "\\") {
        escaped = true;
        continue;
      }

      if (char === "\"") {
        inString = !inString;
        continue;
      }

      if (inString) {
        continue;
      }

      if (char === "{") {
        depth += 1;
      } else if (char === "}") {
        depth -= 1;
        if (depth === 0) {
          return content.slice(start, index + 1);
        }
      }
    }

    return null;
  }

  private isJsonParseLikeError(error: Error): boolean {
    const message = error.message.toLowerCase();
    return (
      message.includes("malformed json") ||
      message.includes("expected ','") ||
      message.includes("expected property name") ||
      message.includes("unexpected token") ||
      message.includes("unterminated string") ||
      message.includes("json")
    );
  }

  private assertValid(parsed: DeepSeekGeoAnalysis): void {
    const scores = [
      parsed.geo_score,
      parsed.catalog_score,
      parsed.google_merchant_score,
      parsed.openai_feed_score,
      parsed.schema_score,
      parsed.faq_score,
      parsed.image_alt_score,
      parsed.agentic_ux_score,
    ];

    if (scores.some((score) => score < 0 || score > 100)) {
      throw new Error("DeepSeek GEO response contains invalid score values");
    }

    if (!parsed.semantic_profile.what_is_it || !parsed.seo_metadata.seo_title) {
      throw new Error("DeepSeek GEO response is missing required layered modules");
    }
  }

  private applyLayeredFallbacks(parsed: DeepSeekGeoAnalysis, input?: DeepSeekGeoInput): void {
    const titleFallback = normalizeText(input?.title ?? "");
    const productTypeFallback = normalizeText(input?.productType ?? "");
    const vendorFallback = normalizeText(input?.vendor ?? "");
    const descriptionFallback = normalizeText(input?.descriptionHtml ?? "");

    if (!parsed.semantic_profile.what_is_it) {
      parsed.semantic_profile.what_is_it = productTypeFallback || titleFallback;
    }

    if (!parsed.semantic_profile.primary_use_case) {
      parsed.semantic_profile.primary_use_case =
        parsed.product_detail_content.summary || titleFallback;
    }

    if (parsed.semantic_profile.target_buyers.length === 0 && vendorFallback) {
      parsed.semantic_profile.target_buyers = [vendorFallback];
    }

    if (!parsed.product_detail_content.summary) {
      parsed.product_detail_content.summary =
        descriptionFallback || parsed.semantic_profile.what_is_it || titleFallback;
    }

    if (!parsed.seo_metadata.seo_title) {
      parsed.seo_metadata.seo_title =
        parsed.recommendations.seo_title || titleFallback || parsed.semantic_profile.what_is_it;
    }

    if (!parsed.seo_metadata.seo_description) {
      parsed.seo_metadata.seo_description =
        parsed.recommendations.seo_description ||
        parsed.product_detail_content.summary ||
        descriptionFallback;
    }

    if (!parsed.recommendations.title) {
      parsed.recommendations.title = titleFallback || parsed.semantic_profile.what_is_it;
    }

    if (!parsed.recommendations.seo_title) {
      parsed.recommendations.seo_title = parsed.seo_metadata.seo_title;
    }

    if (!parsed.recommendations.seo_description) {
      parsed.recommendations.seo_description = parsed.seo_metadata.seo_description;
    }

    if (!parsed.recommendations.description_html) {
      parsed.recommendations.description_html =
        parsed.product_detail_content.description_html || buildDescriptionHtml(parsed.product_detail_content);
    }

    if (!parsed.seo_metadata.handle_suggestion) {
      parsed.seo_metadata.handle_suggestion = slugifyHandle(parsed.recommendations.title || titleFallback);
    }

    if (parsed.faq_content.length === 0) {
      parsed.faq_content = buildFallbackFaqContent(input, parsed.semantic_profile, parsed.product_detail_content);
    }

    if (parsed.seo_metadata.image_alt_suggestions.length === 0) {
      parsed.seo_metadata.image_alt_suggestions = buildFallbackImageAltSuggestions(
        input,
        parsed.semantic_profile,
      );
    }

    if (Object.keys(parsed.schema_projection).length === 0) {
      parsed.schema_projection = buildFallbackSchemaProjection(
        input,
        parsed.semantic_profile,
        parsed.product_detail_content,
        parsed.faq_content,
      );
    }

    if (Object.keys(parsed.google_merchant_projection).length === 0) {
      parsed.google_merchant_projection = buildFallbackGoogleMerchantProjection(
        input,
        parsed.semantic_profile,
        parsed.product_detail_content,
      );
    }

    if (Object.keys(parsed.openai_product_feed_projection).length === 0) {
      parsed.openai_product_feed_projection = buildFallbackOpenAiProductFeedProjection(
        input,
        parsed.semantic_profile,
        parsed.product_detail_content,
      );
    }

    parsed.faq_score = Math.max(parsed.faq_score, this.deriveFaqScore(parsed.faq_content));
    parsed.image_alt_score = Math.max(
      parsed.image_alt_score,
      this.deriveImageAltScore(parsed.seo_metadata.image_alt_suggestions),
    );

    parsed.recommendations = buildRecommendations({
      semanticProfile: parsed.semantic_profile,
      productDetailContent: parsed.product_detail_content,
      seoMetadata: parsed.seo_metadata,
      faqContent: parsed.faq_content,
      schemaProjection: parsed.schema_projection,
      googleMerchantProjection: parsed.google_merchant_projection,
      openaiProductFeedProjection: parsed.openai_product_feed_projection,
      searchIntents: parsed.search_intents,
      geoAudit: parsed.geo_audit,
    });

    parsed.safe_writeback_fields = uniqueNormalizedFields([
      ...parsed.safe_writeback_fields,
      ...buildDefaultSafeWritebackFields({
        productDetailContent: parsed.product_detail_content,
        seoMetadata: parsed.seo_metadata,
        faqContent: parsed.faq_content,
        imageAltSuggestions: parsed.seo_metadata.image_alt_suggestions,
        metafields: parsed.recommendations.metafields,
        recommendationTitle: parsed.recommendations.title,
        recommendationTags: parsed.recommendations.tags,
      }),
    ]);
  }

  private applyContentOptimizationGuard(
    parsed: DeepSeekGeoAnalysis,
    input?: DeepSeekGeoInput,
  ): void {
    if (!input?.deepseekContentOnly) {
      return;
    }

    const allowedSafeFields = new Set<string>(DEEPSEEK_SAFE_WRITEBACK_CONTENT_FIELDS);
    const originalSafeFields = [...parsed.safe_writeback_fields];
    parsed.safe_writeback_fields = parsed.safe_writeback_fields.filter((field) =>
      allowedSafeFields.has(normalizeSafeField(field)),
    );
    parsed.safe_writeback_plan.safe_fields = parsed.safe_writeback_plan.safe_fields.filter((field) =>
      allowedSafeFields.has(normalizeSafeField(field)),
    );
    parsed.safe_writeback_plan.approval_required_fields = [];
    parsed.approval_required_fields = [];

    const removedSafeFields = originalSafeFields.filter(
      (field) => !parsed.safe_writeback_fields.includes(field),
    );
    if (removedSafeFields.length > 0) {
      parsed.risk_flags = [...new Set([...parsed.risk_flags, "deepseek_non_content_field_removed"])];
      parsed.policy_compliance.notes = [
        ...parsed.policy_compliance.notes,
        `已移除非内容层写回字段: ${removedSafeFields.join(", ")}`,
      ];
    }

    parsed.recommendations = buildRecommendations({
      semanticProfile: parsed.semantic_profile,
      productDetailContent: parsed.product_detail_content,
      seoMetadata: parsed.seo_metadata,
      faqContent: parsed.faq_content,
      schemaProjection: parsed.schema_projection,
      googleMerchantProjection: parsed.google_merchant_projection,
      openaiProductFeedProjection: parsed.openai_product_feed_projection,
      searchIntents: parsed.search_intents,
      geoAudit: parsed.geo_audit,
    });
  }

  private compactInput(input: DeepSeekGeoInput): DeepSeekGeoInput {
    return {
      productId: input.productId,
      auditMode: input.auditMode,
      aggressiveGeoOptimization: input.aggressiveGeoOptimization,
      autoFillMissingFields: input.autoFillMissingFields,
      targetGeoScore: input.targetGeoScore,
      minimumPassScore: input.minimumPassScore,
      deepseekContentOnly: input.deepseekContentOnly,
      lockSourceTruthFields: input.lockSourceTruthFields,
      lockBusinessPolicyFields: input.lockBusinessPolicyFields,
      title: truncate(input.title, 200),
      descriptionHtml: truncate(input.descriptionHtml, 4000),
      productType: truncate(input.productType, 120),
      vendor: truncate(input.vendor, 120),
      tags: (input.tags ?? []).slice(0, 25).map((tag) => truncate(tag, 60)),
      options: (input.options ?? []).slice(0, 10).map((option) => ({
        id: option.id,
        name: truncate(option.name, 80),
        position: option.position,
        values: option.values.slice(0, 20).map((value) => ({
          id: value.id,
          name: truncate(value.name, 80),
        })),
      })),
      variants: (input.variants ?? []).slice(0, 20).map((variant) => ({
        id: variant.id,
        title: truncate(variant.title, 160),
        sku: truncate(variant.sku, 80),
        barcode: truncate(variant.barcode, 80),
        price: variant.price,
        compareAtPrice: variant.compareAtPrice,
        inventoryQuantity: variant.inventoryQuantity,
        availableForSale: variant.availableForSale,
        selectedOptions: variant.selectedOptions.slice(0, 10).map((option) => ({
          name: truncate(option.name, 80),
          value: truncate(option.value, 80),
        })),
      })),
      images: (input.images ?? []).slice(0, 12).map((image) => ({
        id: image.id,
        url: image.url,
        altText: truncate(image.altText, 200),
        mediaContentType: image.mediaContentType,
        position: image.position,
      })),
      metafields: (input.metafields ?? []).slice(0, 30).map((field) => ({
        namespace: truncate(field.namespace, 80),
        key: truncate(field.key, 80),
        type: truncate(field.type, 80),
        value: truncate(field.value, 600),
      })),
      sourceEnrichmentContext: input.sourceEnrichmentContext
        ? {
            sourceType: input.sourceEnrichmentContext.sourceType,
            supplierProductId: truncate(input.sourceEnrichmentContext.supplierProductId, 120),
            supplierSku: truncate(input.sourceEnrichmentContext.supplierSku, 120),
            enrichedFields: (input.sourceEnrichmentContext.enrichedFields ?? []).slice(0, 30),
            unresolvedFields: (input.sourceEnrichmentContext.unresolvedFields ?? []).slice(0, 30),
            supplierData: compactJsonLikeValue(input.sourceEnrichmentContext.supplierData ?? {}, {
              maxDepth: 4,
              maxKeys: 25,
              maxItems: 15,
              maxStringLength: 240,
            }) as Record<string, unknown>,
          }
        : undefined,
      businessDefaults: compactJsonLikeValue(input.businessDefaults ?? {}, {
        maxDepth: 3,
        maxKeys: 20,
        maxItems: 10,
        maxStringLength: 200,
      }) as Record<string, unknown>,
      warehousePolicy: compactJsonLikeValue(input.warehousePolicy ?? {}, {
        maxDepth: 3,
        maxKeys: 20,
        maxItems: 10,
        maxStringLength: 200,
      }) as Record<string, unknown>,
      lockedPolicyFields: input.lockedPolicyFields ?? [],
      contentFieldsDeepseekCanOptimize: input.contentFieldsDeepseekCanOptimize ?? [],
      truthFieldsDeepseekCannotGenerate: input.truthFieldsDeepseekCannotGenerate ?? [],
      reoptimizeContext: compactJsonLikeValue(input.reoptimizeContext, {
        maxDepth: 3,
        maxKeys: 20,
        maxItems: 15,
        maxStringLength: 200,
      }) as DeepSeekGeoInput["reoptimizeContext"],
    };
  }

  private buildPrompt(input: DeepSeekGeoInput, attempt: number): string {
    const promptPayload = this.createPromptPayload(input, attempt);

    try {
      const prompt = JSON.stringify(promptPayload);
      if (prompt.length <= 120_000) {
        return prompt;
      }
    } catch (error) {
      if (!(error instanceof RangeError) && !String(error).includes("Invalid string length")) {
        throw error;
      }
    }

    return JSON.stringify(this.createPromptPayload(this.buildEmergencyPromptInput(input), attempt));
  }

  private createPromptPayload(input: DeepSeekGeoInput, attempt: number): Record<string, unknown> {
    return {
      task: "Analyze this Shopify ACTIVE product for ProductAgenticGEO optimization.",
      attempt,
      audit_mode: input.auditMode ?? "before",
      optimization_mode: input.aggressiveGeoOptimization ? "aggressive_geo_optimization" : "standard",
      pipeline_mode:
        input.deepseekContentOnly || input.lockSourceTruthFields || input.lockBusinessPolicyFields
          ? "source_first_policy_second_deepseek_last"
          : "standard",
      auto_fill_missing_fields: input.autoFillMissingFields ?? false,
      target_geo_score: input.targetGeoScore ?? 85,
      minimum_pass_score: input.minimumPassScore ?? 75,
      reoptimize_context: input.reoptimizeContext ?? null,
      rules: [
        "Return one valid JSON object only.",
        "Use the exact top-level modules requested in required_output_schema.",
        "Separate outputs by module.",
        "Aim for a realistic optimization plan that can achieve preview_after_geo_score >= 75 when enough product data exists.",
        "Actively fill missing FAQ, image alt, schema, Google Merchant projection, OpenAI product feed projection, search intents, and SEO metadata from available product data.",
        "Do not put FAQ into product_detail_content.description_html.",
        "Do not put schema, feed fields, or SEO metadata into product_detail_content.description_html.",
        "Do not suggest direct updates to SKU, variant_id, price, inventory, barcode, GTIN, checkout, shipping rate, or live theme code.",
        "Keep product_detail_content focused on product detail body content only.",
        "Escape every inner quote in strings correctly.",
        "If reoptimize_context is present, focus on fixing low-score modules and do not repeat weak prior output.",
        "If sourceEnrichmentContext is present, use supplier source data to fix taxonomy, product type, merchant feed, schema, FAQ, and attribute completeness.",
        "Do not invent GTIN, barcode, material, dimensions, or weight if sourceEnrichmentContext does not provide them.",
        "If businessDefaults or warehousePolicy are present, treat them as locked system policy inputs.",
        "If deepseekContentOnly is true, only optimize content, structure, SEO, FAQ, image alt, schema text, Google Merchant text, and OpenAI product feed text.",
        "If deepseekContentOnly is true, safe_writeback_plan.safe_fields must only include title, handle, description_html, tags, seo_title, seo_description, image_alt, and metafields.",
        "Do not modify lockedPolicyFields.",
        "Do not invent warehouse city or warehouse state.",
        "Use truthFieldsDeepseekCannotGenerate as a hard blacklist for generated real-world facts.",
        "If a field cannot be safely known, leave it blank and compensate by strengthening other allowed structured modules.",
      ],
      product: input,
      required_output_schema: {
        geo_audit: {
          before_geo_score: "number 0-100",
          missing_fields: ["string"],
          risk_flags: ["string"],
          catalog_gaps: ["string"],
          google_merchant_gaps: ["string"],
          openai_feed_gaps: ["string"],
          schema_gaps: ["string"],
          agentic_ux_gaps: ["string"],
        },
        semantic_profile: {
          what_is_it: "string",
          primary_use_case: "string",
          target_buyers: ["string"],
          shopping_scenarios: ["string"],
          recommendation_triggers: ["string"],
          not_suitable_for: ["string"],
          key_attributes: ["string"],
        },
        search_intents: {
          core_queries: ["string"],
          problem_queries: ["string"],
          comparison_queries: ["string"],
          gift_queries: ["string"],
          agent_recommendation_triggers: ["string"],
        },
        catalog_score: "number 0-100",
        google_merchant_score: "number 0-100",
        openai_feed_score: "number 0-100",
        schema_score: "number 0-100",
        faq_score: "number 0-100",
        image_alt_score: "number 0-100",
        agentic_ux_score: "number 0-100",
        product_detail_content: {
          summary: "string",
          key_selling_points: ["string"],
          use_cases: ["string"],
          specifications: ["string"],
          package_includes: ["string"],
          how_to_use: ["string"],
          suitable_for: ["string"],
          caution_notes: ["string"],
          description_html: "string",
        },
        seo_metadata: {
          seo_title: "string",
          seo_description: "string",
          handle_suggestion: "string",
          image_alt_suggestions: [{ image_id: "string", alt: "string" }],
          internal_link_suggestions: ["string"],
        },
        faq_content: [{ question: "string", answer: "string" }],
        schema_projection: "object",
        google_merchant_projection: "object",
        openai_product_feed_projection: "object",
        agentic_ux_audit: {
          can_identify_title: "boolean",
          can_identify_price: "boolean",
          can_select_variant: "boolean",
          can_add_to_cart: "boolean",
          can_enter_checkout: "boolean",
          can_read_shipping_return: "boolean",
          issues: ["string"],
        },
        before_after_score: {
          before_geo_score: "number 0-100",
          after_geo_score: "number 0-100",
          score_delta: "number",
          optimization_result: "PASS | WEAK_PASS | FAILED | RISK_BLOCKED",
          writeback_allowed: "boolean",
        },
        policy_compliance: {
          source_truth_used: "boolean",
          business_policy_used: "boolean",
          locked_policy_fields_modified: "boolean",
          real_fields_invented: "boolean",
          gtin_invented: "boolean",
          warehouse_city_invented: "boolean",
          sku_used_as_gtin: "boolean",
          notes: ["string"],
        },
        safe_writeback_plan: {
          safe_fields: ["string"],
          approval_required_fields: ["string"],
          forbidden_fields: [
            "sku",
            "variant_id",
            "price",
            "inventory",
            "barcode",
            "gtin",
            "checkout",
            "shipping rate",
            "live theme code",
          ],
        },
      },
    };
  }

  private buildEmergencyPromptInput(input: DeepSeekGeoInput): DeepSeekGeoInput {
    return {
      ...input,
      title: truncate(input.title, 160),
      descriptionHtml: truncate(input.descriptionHtml, 1500),
      tags: (input.tags ?? []).slice(0, 10).map((tag) => truncate(tag, 40)),
      options: (input.options ?? []).slice(0, 5).map((option) => ({
        ...option,
        name: truncate(option.name, 60),
        values: option.values.slice(0, 10).map((value) => ({
          ...value,
          name: truncate(value.name, 60),
        })),
      })),
      variants: (input.variants ?? []).slice(0, 8).map((variant) => ({
        ...variant,
        title: truncate(variant.title, 100),
        sku: truncate(variant.sku, 40),
        barcode: truncate(variant.barcode, 40),
        selectedOptions: variant.selectedOptions.slice(0, 5).map((option) => ({
          name: truncate(option.name, 40),
          value: truncate(option.value, 40),
        })),
      })),
      images: (input.images ?? []).slice(0, 6).map((image) => ({
        ...image,
        altText: truncate(image.altText, 120),
      })),
      metafields: (input.metafields ?? []).slice(0, 12).map((field) => ({
        ...field,
        namespace: truncate(field.namespace, 50),
        key: truncate(field.key, 50),
        type: truncate(field.type, 50),
        value: truncate(field.value, 180),
      })),
      sourceEnrichmentContext: input.sourceEnrichmentContext
        ? {
            ...input.sourceEnrichmentContext,
            enrichedFields: (input.sourceEnrichmentContext.enrichedFields ?? []).slice(0, 15),
            unresolvedFields: (input.sourceEnrichmentContext.unresolvedFields ?? []).slice(0, 15),
            supplierData: compactJsonLikeValue(input.sourceEnrichmentContext.supplierData ?? {}, {
              maxDepth: 3,
              maxKeys: 15,
              maxItems: 8,
              maxStringLength: 120,
            }) as Record<string, unknown>,
          }
        : undefined,
      businessDefaults: compactJsonLikeValue(input.businessDefaults ?? {}, {
        maxDepth: 2,
        maxKeys: 12,
        maxItems: 6,
        maxStringLength: 100,
      }) as Record<string, unknown>,
      warehousePolicy: compactJsonLikeValue(input.warehousePolicy ?? {}, {
        maxDepth: 2,
        maxKeys: 12,
        maxItems: 6,
        maxStringLength: 100,
      }) as Record<string, unknown>,
      lockedPolicyFields: (input.lockedPolicyFields ?? []).slice(0, 20),
      contentFieldsDeepseekCanOptimize: (input.contentFieldsDeepseekCanOptimize ?? []).slice(0, 30),
      truthFieldsDeepseekCannotGenerate: (input.truthFieldsDeepseekCannotGenerate ?? []).slice(0, 30),
      reoptimizeContext: compactJsonLikeValue(input.reoptimizeContext, {
        maxDepth: 2,
        maxKeys: 10,
        maxItems: 8,
        maxStringLength: 100,
      }) as DeepSeekGeoInput["reoptimizeContext"],
    };
  }

  private deriveFaqScore(faqContent: ProductFAQEntry[]): number {
    return Math.min(100, faqContent.length * 18);
  }

  private deriveImageAltScore(imageAlt: ImageAltRecommendation[]): number {
    return Math.min(100, imageAlt.length * 12);
  }
}
