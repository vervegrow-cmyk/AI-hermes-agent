import {
  AgenticUXAudit,
  DeepSeekGeoAnalysis,
  DeepSeekGeoInput,
  ImageAltRecommendation,
  MetafieldRecommendation,
  ProductDetailContent,
  ProductFAQEntry,
  ProductGeoRecommendations,
  ProductSemanticProfile,
  SafeWritebackPlanOutput,
  SearchIntentProjection,
  SeoMetadataRecommendation,
} from "../agents/product-agentic-geo-agent/product-agentic-geo.types.js";

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

function asMetafieldArray(value: unknown): MetafieldRecommendation[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((item) => {
      const record = asRecord(item);
      return {
        namespace: asString(record.namespace),
        key: asString(record.key),
        type: asString(record.type),
        value: asString(record.value),
      };
    })
    .filter((item) => item.namespace.length > 0 && item.key.length > 0);
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

function buildRecommendations(input: {
  semanticProfile: ProductSemanticProfile;
  productDetailContent: ProductDetailContent;
  seoMetadata: SeoMetadataRecommendation;
  faqContent: ProductFAQEntry[];
  schemaProjection: Record<string, unknown>;
  googleMerchantProjection: Record<string, unknown>;
  openaiProductFeedProjection: Record<string, unknown>;
  safeWritebackPlan: SafeWritebackPlanOutput;
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
    metafields: [],
    search_intents: {
      core_queries: input.semanticProfile.shopping_scenarios.slice(0, 4),
      problem_queries: [input.semanticProfile.primary_use_case].filter(Boolean),
      comparison_queries: [],
      gift_queries: input.semanticProfile.target_buyers
        .slice(0, 2)
        .map((buyer) => `gift for ${buyer}`),
      agent_recommendation_triggers: input.semanticProfile.recommendation_triggers,
    },
    openai_feed_projection: input.openaiProductFeedProjection,
    google_merchant_projection: input.googleMerchantProjection,
    schema_projection: input.schemaProjection,
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

    for (let attempt = 1; attempt <= 2; attempt += 1) {
      try {
        const content = await this.requestCompletion(compactInput, attempt);
        return this.parseAndValidate(content);
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));
      }
    }

    throw new Error(`DeepSeek 结果解析失败: ${lastError?.message ?? "unknown error"}`);
  }

  parseAndValidate(content: string): DeepSeekGeoAnalysis {
    const raw = this.parseJsonObjectContent(content);
    const record = asRecord(raw);

    const semanticProfile = parseSemanticProfile(record.semantic_profile);
    const productDetailContent = parseProductDetailContent(record.product_detail_content);
    const seoMetadata = parseSeoMetadata(record.seo_metadata);
    const faqContent = asFaqArray(record.faq_content);
    const schemaProjection = asRecord(record.schema_projection);
    const googleMerchantProjection = asRecord(record.google_merchant_projection);
    const openaiProductFeedProjection = asRecord(record.openai_product_feed_projection);
    const agenticUxAudit = parseAgenticUXAudit(record.agentic_ux_audit);
    const safeWritebackPlan = parseSafeWritebackPlan(record.safe_writeback_plan);

    const parsed: DeepSeekGeoAnalysis = {
      geo_score: asNumber(record.geo_score),
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
      missing_fields: asStringArray(record.missing_fields).map(normalizeText).filter(Boolean),
      risk_flags: asStringArray(record.risk_flags).map(normalizeText).filter(Boolean),
      semantic_profile: semanticProfile,
      product_detail_content: productDetailContent,
      seo_metadata: seoMetadata,
      faq_content: faqContent,
      schema_projection: schemaProjection,
      google_merchant_projection: googleMerchantProjection,
      openai_product_feed_projection: openaiProductFeedProjection,
      agentic_ux_audit: agenticUxAudit,
      safe_writeback_plan: safeWritebackPlan,
      recommendations: buildRecommendations({
        semanticProfile,
        productDetailContent,
        seoMetadata,
        faqContent,
        schemaProjection,
        googleMerchantProjection,
        openaiProductFeedProjection,
        safeWritebackPlan,
      }),
      safe_writeback_fields:
        safeWritebackPlan.safe_fields.length > 0
          ? safeWritebackPlan.safe_fields
          : asStringArray(record.safe_writeback_fields).map(normalizeText).filter(Boolean),
      approval_required_fields:
        safeWritebackPlan.approval_required_fields.length > 0
          ? safeWritebackPlan.approval_required_fields
          : asStringArray(record.approval_required_fields)
              .map(normalizeText)
              .filter(Boolean),
      forbidden_fields:
        safeWritebackPlan.forbidden_fields.length > 0
          ? safeWritebackPlan.forbidden_fields
          : asStringArray(record.forbidden_fields).map(normalizeText).filter(Boolean),
    };

    this.assertValid(parsed);
    return parsed;
  }

  private async requestCompletion(input: DeepSeekGeoInput, attempt: number): Promise<string> {
    const response = await fetch(`${this.baseUrl}/chat/completions`, {
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
              "Return one valid JSON object only.",
              "Do not include markdown, prose, explanations, or code fences.",
              "Keep strings concise and escape all quotes correctly.",
              "Keep each output module separate. Do not mix FAQ, schema, feed, or SEO into descriptionHtml.",
              "Do not modify SKU, price, inventory, barcode, GTIN, or variant_id.",
            ].join("\n"),
          },
          {
            role: "user",
            content: this.buildPrompt(input, attempt),
          },
        ],
        response_format: { type: "json_object" },
        temperature: 0.1,
      }),
    });

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

  private parseJsonObjectContent(content: string): unknown {
    const cleaned = content.trim().replace(/^```json\s*/i, "").replace(/```$/i, "").trim();

    try {
      return JSON.parse(cleaned) as unknown;
    } catch {
      const firstBrace = cleaned.indexOf("{");
      const lastBrace = cleaned.lastIndexOf("}");
      if (firstBrace >= 0 && lastBrace > firstBrace) {
        return JSON.parse(cleaned.slice(firstBrace, lastBrace + 1)) as unknown;
      }
      throw new Error("DeepSeek returned malformed JSON");
    }
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

  private compactInput(input: DeepSeekGeoInput): DeepSeekGeoInput {
    return {
      productId: input.productId,
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
      metafields: (input.metafields ?? []).slice(0, 20).map((field) => ({
        namespace: truncate(field.namespace, 80),
        key: truncate(field.key, 80),
        type: truncate(field.type, 80),
        value: truncate(field.value, 400),
      })),
    };
  }

  private buildPrompt(input: DeepSeekGeoInput, attempt: number): string {
    return JSON.stringify({
      task: "Analyze this Shopify ACTIVE product for ProductAgenticGEO optimization.",
      attempt,
      audit_mode: input.auditMode ?? "before",
      rules: [
        "Return one valid JSON object only.",
        "Separate outputs by module.",
        "Do not put FAQ into product_detail_content.description_html.",
        "Do not put schema, feed fields, or SEO metadata into product_detail_content.description_html.",
        "Do not suggest direct updates to SKU, variant_id, price, inventory, barcode, GTIN, checkout, shipping rate, or live theme code.",
        "Keep product_detail_content focused on product detail body content only.",
      ],
      product: input,
      required_output_schema: {
        geo_score: "number 0-100",
        catalog_score: "number 0-100",
        google_merchant_score: "number 0-100",
        openai_feed_score: "number 0-100",
        schema_score: "number 0-100",
        faq_score: "number 0-100",
        image_alt_score: "number 0-100",
        agentic_ux_score: "number 0-100",
        missing_fields: ["string"],
        risk_flags: ["string"],
        semantic_profile: {
          what_is_it: "string",
          primary_use_case: "string",
          target_buyers: ["string"],
          shopping_scenarios: ["string"],
          recommendation_triggers: ["string"],
          not_suitable_for: ["string"],
          key_attributes: ["string"],
        },
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
    });
  }

  private deriveFaqScore(faqContent: ProductFAQEntry[]): number {
    return Math.min(100, faqContent.length * 18);
  }

  private deriveImageAltScore(imageAlt: ImageAltRecommendation[]): number {
    return Math.min(100, imageAlt.length * 12);
  }
}
