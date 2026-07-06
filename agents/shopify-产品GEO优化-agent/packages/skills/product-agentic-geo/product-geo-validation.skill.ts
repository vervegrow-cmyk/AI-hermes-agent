import {
  DeepSeekGeoAnalysis,
  ImageAltRecommendation,
  MetafieldRecommendation,
  ProductAfterValidationResult,
  ProductGeoValidationResult,
  ProductSafeWritebackPlan,
  ShopifyProductSnapshot,
} from "../../agents/product-agentic-geo-agent/product-agentic-geo.types.js";

const FORBIDDEN_FIELDS = new Set([
  "sku",
  "variant_id",
  "price",
  "inventory",
  "barcode",
  "gtin",
  "checkout",
  "shipping_rate",
  "shipping rate",
  "live_theme_code",
  "live theme code",
]);

const SUPPORTED_METAFIELD_TYPES = new Set([
  "single_line_text_field",
  "multi_line_text_field",
  "json",
  "json_string",
  "number_integer",
  "number_decimal",
  "boolean",
  "url",
  "color",
  "date",
  "date_time",
]);

const PRODUCT_TITLE_MAX_LENGTH = 150;
const DESCRIPTION_HTML_MAX_LENGTH = 16000;
const SEO_TITLE_MAX_LENGTH = 70;
const SEO_DESCRIPTION_MAX_LENGTH = 320;
const IMAGE_ALT_MAX_LENGTH = 180;
const TAG_MAX_LENGTH = 40;
const HANDLE_MAX_LENGTH = 255;

const STRUCTURED_METAFIELD_KEYS = new Set([
  "product_geo.faq_content",
  "product_geo.semantic_profile",
  "product_geo.geo_audit",
  "product_geo.google_merchant_projection",
  "product_geo.openai_product_feed_projection",
  "product_geo.schema_projection",
  "product_geo.search_intents",
]);

function normalizeFieldAlias(field: string): string {
  const normalized = field.trim().toLowerCase();

  const aliasMap: Record<string, string> = {
    descriptionhtml: "description_html",
    "product_detail_content.description_html": "description_html",
    "product_detail_content": "description_html",
    seotitle: "seo_title",
    "seo_metadata.seo_title": "seo_title",
    seodescription: "seo_description",
    "seo_metadata.seo_description": "seo_description",
    "image_alt_text": "image_alt",
    imagealt: "image_alt",
    "image_alt_suggestions": "image_alt",
    "image_alt_texts": "image_alt",
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

function normalizeImageIdentifier(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) {
    return "";
  }
  const parts = trimmed.split("/");
  return parts[parts.length - 1] ?? trimmed;
}

export class ProductGEOValidationSkill {
  execute(analysis: DeepSeekGeoAnalysis): ProductGeoValidationResult {
    const errors: string[] = [];

    for (const field of analysis.forbidden_fields) {
      if (!FORBIDDEN_FIELDS.has(field.toLowerCase())) {
        errors.push(`模型返回了未支持的禁止字段标记: ${field}`);
      }
    }

    if (
      analysis.safe_writeback_fields.some((field) =>
        FORBIDDEN_FIELDS.has(normalizeFieldAlias(field)),
      )
    ) {
      errors.push("safe_writeback_fields 中包含禁止修改字段。");
    }

    return {
      ok: errors.length === 0,
      errors,
    };
  }

  buildSafeWritebackPlan(
    product: ShopifyProductSnapshot,
    analysis: DeepSeekGeoAnalysis,
  ): ProductSafeWritebackPlan {
    const imageAltUpdates = this.buildImageAltUpdates(
      product,
      analysis.seo_metadata.image_alt_suggestions,
    );
    const metafields = this.buildWritableMetafields(product, analysis);
    const normalizedTitle = this.normalizeText(
      analysis.recommendations.title,
      PRODUCT_TITLE_MAX_LENGTH,
    );
    const normalizedDescriptionHtml = this.normalizeText(
      analysis.recommendations.description_html,
      DESCRIPTION_HTML_MAX_LENGTH,
    );
    const normalizedTags = this.normalizeTags(analysis.recommendations.tags);
    const normalizedSeoTitle = this.normalizeText(
      analysis.seo_metadata.seo_title,
      SEO_TITLE_MAX_LENGTH,
    );
    const normalizedSeoDescription = this.normalizeText(
      analysis.seo_metadata.seo_description,
      SEO_DESCRIPTION_MAX_LENGTH,
    );
    const normalizedHandle = this.normalizeHandle(analysis.seo_metadata.handle_suggestion);

    const blockedFields = this.collectBlockedFields(analysis);
    const fieldsToWrite = [
      ...(this.allowsSafeWriteback(analysis, "title") && normalizedTitle ? ["title"] : []),
      ...(this.allowsSafeWriteback(analysis, "handle") && normalizedHandle ? ["handle"] : []),
      ...(this.allowsSafeWriteback(analysis, "description_html") && normalizedDescriptionHtml
        ? ["description_html"]
        : []),
      ...(this.allowsSafeWriteback(analysis, "tags") && normalizedTags.length > 0 ? ["tags"] : []),
      ...(this.allowsSafeWriteback(analysis, "seo_title") && normalizedSeoTitle
        ? ["seo_title"]
        : []),
      ...(this.allowsSafeWriteback(analysis, "seo_description") && normalizedSeoDescription
        ? ["seo_description"]
        : []),
      ...(this.allowsSafeWriteback(analysis, "image_alt") && imageAltUpdates.length > 0
        ? ["image_alt"]
        : []),
      ...(this.shouldWriteMetafields(analysis, metafields) ? ["metafields"] : []),
    ];

    return {
      title: fieldsToWrite.includes("title") ? normalizedTitle || undefined : undefined,
      descriptionHtml: fieldsToWrite.includes("description_html")
        ? normalizedDescriptionHtml || undefined
        : undefined,
      tags: fieldsToWrite.includes("tags") && normalizedTags.length > 0 ? normalizedTags : undefined,
      seoTitle: fieldsToWrite.includes("seo_title") ? normalizedSeoTitle || undefined : undefined,
      seoDescription: fieldsToWrite.includes("seo_description")
        ? normalizedSeoDescription || undefined
        : undefined,
      handle: fieldsToWrite.includes("handle") ? normalizedHandle || undefined : undefined,
      imageAltUpdates: fieldsToWrite.includes("image_alt") ? imageAltUpdates : [],
      metafields: fieldsToWrite.includes("metafields") ? metafields : [],
      fieldsToWrite: [...new Set(fieldsToWrite)],
      blockedFields,
      approvalRequiredFields: [],
      forbiddenFieldsConfirmed: [
        "SKU",
        "variant_id",
        "price",
        "inventory",
        "barcode",
        "GTIN",
        "checkout",
        "shipping rate",
        "live theme code",
      ],
      salesChannelsToPublish: product.salesChannels.filter((item) => !item.isPublished),
    };
  }

  validateAfterWriteback(
    productBefore: ShopifyProductSnapshot,
    productAfter: ShopifyProductSnapshot,
    plan: ProductSafeWritebackPlan,
    actuallyWrittenFields: string[],
    dryRun = false,
  ): ProductAfterValidationResult {
    if (dryRun) {
      return {
        ok: true,
        checkedFields: [...actuallyWrittenFields],
        mismatchedFields: [],
        message: "Dry Run 模式，已跳过真实写回校验。",
      };
    }

    const mismatchedFields: string[] = [];
    const checkedFields: string[] = [];

    if (actuallyWrittenFields.includes("title")) {
      checkedFields.push("title");
      if ((plan.title ?? "") !== productAfter.title) {
        mismatchedFields.push("title");
      }
    }

    if (actuallyWrittenFields.includes("description_html")) {
      checkedFields.push("description_html");
      if (!this.isEquivalentDescriptionHtml(plan.descriptionHtml ?? "", productAfter.descriptionHtml)) {
        mismatchedFields.push("description_html");
      }
    }

    if (actuallyWrittenFields.includes("tags")) {
      checkedFields.push("tags");
      if (!this.areTagsConsistent(plan.tags ?? [], productAfter.tags)) {
        mismatchedFields.push("tags");
      }
    }

    if (actuallyWrittenFields.includes("handle")) {
      checkedFields.push("handle");
      if ((plan.handle ?? "") !== productAfter.handle) {
        mismatchedFields.push("handle");
      }
    }

    if (actuallyWrittenFields.includes("seo_title")) {
      checkedFields.push("seo_title");
      if (
        !this.isEquivalentSeoText(
          plan.seoTitle ?? "",
          productAfter.seo.title,
          productAfter.title,
        )
      ) {
        mismatchedFields.push("seo_title");
      }
    }

    if (actuallyWrittenFields.includes("seo_description")) {
      checkedFields.push("seo_description");
      if (
        !this.isEquivalentSeoText(
          plan.seoDescription ?? "",
          productAfter.seo.description,
          this.stripHtml(productAfter.descriptionHtml),
        )
      ) {
        mismatchedFields.push("seo_description");
      }
    }

    if (actuallyWrittenFields.includes("image_alt")) {
      checkedFields.push("image_alt");
      const imageMap = new Map(
        productAfter.images.map((image) => [
          normalizeImageIdentifier(image.id),
          image.altText,
        ]),
      );
      for (const image of plan.imageAltUpdates) {
        if (imageMap.get(normalizeImageIdentifier(image.image_id)) !== image.alt) {
          mismatchedFields.push(`image_alt:${image.image_id}`);
        }
      }
    }

    if (actuallyWrittenFields.includes("metafields")) {
      checkedFields.push("metafields");
      const metafieldMap = new Map(
        productAfter.metafields.map((field) => [`${field.namespace}.${field.key}`, field.value]),
      );
      for (const field of plan.metafields) {
        const current = metafieldMap.get(`${field.namespace}.${field.key}`);
        if (current !== field.value) {
          mismatchedFields.push(`metafields:${field.namespace}.${field.key}`);
        }
      }
    }

    if (actuallyWrittenFields.includes("sales_channels")) {
      checkedFields.push("sales_channels");
      const unpublished = productAfter.salesChannels.filter(
        (item) => item.publicationAvailable !== false && !item.isPublished,
      );
      if (unpublished.length > 0) {
        mismatchedFields.push(
          `sales_channels:${unpublished
            .map((item) => item.name || item.catalogTitle || item.id)
            .join("|")}`,
        );
      }
    }

    const immutableMismatches = this.detectImmutableFieldChanges(productBefore, productAfter);
    mismatchedFields.push(...immutableMismatches);

    if (
      mismatchedFields.length > 0 &&
      this.isConcurrentImmutableDriftOnly(mismatchedFields)
    ) {
      return {
        ok: true,
        checkedFields,
        mismatchedFields,
        warningOnly: true,
        message: `写回后校验通过，但检测到并发外部变更字段: ${mismatchedFields.join(", ")}。本次内容写回未触及这些交易字段，已按外部漂移告警处理。`,
      };
    }

    return {
      ok: mismatchedFields.length === 0,
      checkedFields,
      mismatchedFields,
      message:
        mismatchedFields.length === 0
          ? "写回后校验通过"
          : `写回后校验失败，存在不一致字段: ${mismatchedFields.join(", ")}`,
    };
  }

  private shouldWriteMetafields(
    analysis: DeepSeekGeoAnalysis,
    metafields: MetafieldRecommendation[],
  ): boolean {
    if (metafields.length === 0) {
      return false;
    }

    const hasStructuredMetafields = metafields.some((field) =>
      STRUCTURED_METAFIELD_KEYS.has(`${field.namespace}.${field.key}`),
    );

    if (!hasStructuredMetafields) {
      return false;
    }

    if (analysis.safe_writeback_fields.length === 0) {
      return true;
    }

    if (this.allowsSafeWriteback(analysis, "metafields")) {
      return true;
    }

    const requested = new Set(
      analysis.safe_writeback_fields.map((field) => normalizeFieldAlias(field)),
    );

    return (
      requested.has("metafields") ||
      requested.has("faq_metafields") ||
      requested.has("semantic_profile_metafields") ||
      requested.has("geo_custom_metafields") ||
      requested.has("schema_metafields") ||
      requested.has("google_merchant_metafields") ||
      requested.has("openai_feed_metafields")
    );
  }

  private collectBlockedFields(analysis: DeepSeekGeoAnalysis): string[] {
    const blocked = new Set<string>();

    for (const field of analysis.safe_writeback_fields) {
      const normalized = normalizeFieldAlias(field);
      if (FORBIDDEN_FIELDS.has(normalized)) {
        blocked.add(field);
      }
    }

    for (const field of analysis.safe_writeback_plan.safe_fields) {
      const normalized = normalizeFieldAlias(field);
      if (FORBIDDEN_FIELDS.has(normalized)) {
        blocked.add(field);
      }
    }

    return [...blocked];
  }

  private detectImmutableFieldChanges(
    productBefore: ShopifyProductSnapshot,
    productAfter: ShopifyProductSnapshot,
  ): string[] {
    const mismatches: string[] = [];
    const beforeVariantMap = new Map(productBefore.variants.map((variant) => [variant.id, variant]));
    const afterVariantMap = new Map(productAfter.variants.map((variant) => [variant.id, variant]));

    for (const [variantId, beforeVariant] of beforeVariantMap) {
      const afterVariant = afterVariantMap.get(variantId);
      if (!afterVariant) {
        mismatches.push(`variant_id:${variantId}`);
        continue;
      }

      if (beforeVariant.sku !== afterVariant.sku) mismatches.push(`sku:${variantId}`);
      if (beforeVariant.price !== afterVariant.price) mismatches.push(`price:${variantId}`);
      if (beforeVariant.inventoryQuantity !== afterVariant.inventoryQuantity) {
        mismatches.push(`inventory:${variantId}`);
      }
      if (beforeVariant.barcode !== afterVariant.barcode) {
        mismatches.push(`barcode:${variantId}`);
      }
    }

    return mismatches;
  }

  private isConcurrentImmutableDriftOnly(fields: string[]): boolean {
    return fields.every((field) =>
      /^price:|^inventory:|^barcode:/.test(field),
    );
  }

  private buildImageAltUpdates(
    product: ShopifyProductSnapshot,
    recommendations: ImageAltRecommendation[],
  ): ImageAltRecommendation[] {
    const imageIdMap = new Map(
      product.images.map((image) => [normalizeImageIdentifier(image.id), image.id]),
    );

    return recommendations
      .map((image) => {
        const normalizedId = normalizeImageIdentifier(image.image_id);
        const matchedId = imageIdMap.get(normalizedId);
        return {
          image_id: matchedId ?? image.image_id,
          alt: this.normalizeText(image.alt, IMAGE_ALT_MAX_LENGTH),
        };
      })
      .filter((image) => imageIdMap.has(normalizeImageIdentifier(image.image_id)) && image.alt.length > 0);
  }

  private normalizeTags(tags: string[]): string[] {
    const deduped = new Map<string, string>();

    for (const tag of tags) {
      for (const part of tag.split(/[,|;\n\r]+/g)) {
        const normalized = this.normalizeText(part, TAG_MAX_LENGTH);
        if (!normalized) {
          continue;
        }

        const key = normalized.toLowerCase();
        if (!deduped.has(key)) {
          deduped.set(key, normalized);
        }
      }
    }

    return [...deduped.values()];
  }

  private normalizeHandle(value: string): string {
    const collapsed = value
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9-]+/g, "-")
      .replace(/-+/g, "-")
      .replace(/^-|-$/g, "");
    if (!collapsed) {
      return "";
    }
    return collapsed.length > HANDLE_MAX_LENGTH
      ? collapsed.slice(0, HANDLE_MAX_LENGTH).replace(/-+$/g, "")
      : collapsed;
  }

  private buildWritableMetafields(
    product: ShopifyProductSnapshot,
    analysis: DeepSeekGeoAnalysis,
  ): MetafieldRecommendation[] {
    const existingMetafields = new Map(
      product.metafields.map((field) => [`${field.namespace}.${field.key}`, field]),
    );

    const writable: MetafieldRecommendation[] = [];

    for (const recommendation of analysis.recommendations.metafields) {
      const existing = existingMetafields.get(`${recommendation.namespace}.${recommendation.key}`);
      const baseType = existing?.type ?? this.normalizeMetafieldType(recommendation.type, "");
      if (!SUPPORTED_METAFIELD_TYPES.has(baseType)) {
        continue;
      }

      const normalizedType = this.normalizeMetafieldType(recommendation.type, baseType);
      if (normalizedType !== baseType) {
        continue;
      }

      writable.push({
        namespace: existing?.namespace ?? recommendation.namespace,
        key: existing?.key ?? recommendation.key,
        type: existing?.type ?? normalizedType,
        value: recommendation.value,
      });
    }

    return this.uniqueMetafields(writable);
  }

  private uniqueMetafields(fields: MetafieldRecommendation[]): MetafieldRecommendation[] {
    const deduped = new Map<string, MetafieldRecommendation>();
    for (const field of fields) {
      deduped.set(`${field.namespace}.${field.key}`, field);
    }
    return [...deduped.values()];
  }

  private normalizeMetafieldType(type: string, fallback: string): string {
    const normalized = type.trim().toLowerCase();
    if (!normalized) {
      return fallback;
    }

    if (normalized === "string") {
      return fallback === "multi_line_text_field"
        ? "multi_line_text_field"
        : "single_line_text_field";
    }

    return normalized;
  }

  private normalizeText(value: string, maxLength: number): string {
    const collapsed = value.replace(/\s+/g, " ").trim();
    if (!collapsed) {
      return "";
    }

    return collapsed.length > maxLength ? collapsed.slice(0, maxLength).trim() : collapsed;
  }

  private allowsSafeWriteback(analysis: DeepSeekGeoAnalysis, field: string): boolean {
    const normalized = normalizeFieldAlias(field);
    if (analysis.safe_writeback_fields.length === 0) {
      return true;
    }

    return analysis.safe_writeback_fields.some((candidate) => {
      const value = normalizeFieldAlias(candidate);
      return value === normalized;
    });
  }

  private areSameStringSets(left: string[], right: string[]): boolean {
    const leftSet = new Set(left.map((item) => item.trim().toLowerCase()).filter(Boolean));
    const rightSet = new Set(right.map((item) => item.trim().toLowerCase()).filter(Boolean));

    if (leftSet.size !== rightSet.size) {
      return false;
    }

    for (const value of leftSet) {
      if (!rightSet.has(value)) {
        return false;
      }
    }

    return true;
  }

  private areTagsConsistent(expected: string[], actual: string[]): boolean {
    const normalizedExpected = this.normalizeTags(expected);
    const normalizedActual = this.normalizeTags(actual);

    if (this.areSameStringSets(normalizedExpected, normalizedActual)) {
      return true;
    }

    const actualSet = new Set(normalizedActual.map((item) => item.trim().toLowerCase()));
    return normalizedExpected.every((item) => actualSet.has(item.trim().toLowerCase()));
  }

  private normalizeHtml(value: string): string {
    return value
      .replace(/&nbsp;/gi, " ")
      .replace(/&amp;/gi, "&")
      .replace(/&quot;/gi, "\"")
      .replace(/&#39;/gi, "'")
      .replace(/<(\/?)(div|section|article|main|header|footer|aside)\b[^>]*>/gi, "<$1p>")
      .replace(/<h[1-6]\b[^>]*>/gi, "<p>")
      .replace(/<\/h[1-6]>/gi, "</p>")
      .replace(/\s(?:class|style|data-[a-z0-9_-]+|id|width|height)="[^"]*"/gi, "")
      .replace(/<!--[\s\S]*?-->/g, " ")
      .replace(/<br\s*\/?>/gi, "\n")
      .replace(/<\/p>/gi, "\n")
      .replace(/<\/li>/gi, "\n")
      .replace(/<p>\s*<\/p>/gi, " ")
      .replace(/<li>\s*<\/li>/gi, " ")
      .replace(/>\s+</g, "><")
      .replace(/\s+/g, " ")
      .trim();
  }

  private normalizePlainText(value: string): string {
    return value
      .replace(/\s+/g, " ")
      .replace(/[|｜]/g, "|")
      .trim()
      .toLowerCase();
  }

  private isEquivalentPlainText(expected: string, actual: string): boolean {
    const normalizedExpected = this.normalizePlainText(expected);
    const normalizedActual = this.normalizePlainText(actual);

    if (normalizedExpected === normalizedActual) {
      return true;
    }

    if (!normalizedExpected || !normalizedActual) {
      return false;
    }

    return (
      normalizedActual.includes(normalizedExpected) ||
      normalizedExpected.includes(normalizedActual)
    );
  }

  private isEquivalentSeoText(expected: string, actual: string, fallback: string): boolean {
    if (this.isEquivalentPlainText(expected, actual)) {
      return true;
    }

    const normalizedExpected = this.normalizePlainText(expected);
    const normalizedFallback = this.normalizePlainText(fallback);

    if (!normalizedExpected) {
      return true;
    }

    if (!normalizedFallback) {
      return false;
    }

    return (
      normalizedFallback.includes(normalizedExpected) ||
      normalizedExpected.includes(normalizedFallback)
    );
  }

  private stripHtml(value: string): string {
    return value
      .replace(/<!--[\s\S]*?-->/g, " ")
      .replace(/<style[\s\S]*?<\/style>/gi, " ")
      .replace(/<script[\s\S]*?<\/script>/gi, " ")
      .replace(/<br\s*\/?>/gi, " ")
      .replace(/<\/p>/gi, " ")
      .replace(/<\/li>/gi, " ")
      .replace(/<[^>]+>/g, " ")
      .replace(/&nbsp;/gi, " ")
      .replace(/&amp;/gi, "&")
      .replace(/&quot;/gi, "\"")
      .replace(/&#39;/gi, "'")
      .replace(/&ndash;|&mdash;/gi, "-")
      .replace(/\s+/g, " ")
      .trim()
      .toLowerCase();
  }

  private tokenizeDescriptionText(value: string): string[] {
    return this.stripHtml(value)
      .split(/[^a-z0-9]+/g)
      .map((item) => item.trim())
      .filter((item) => item.length >= 4);
  }

  private hasHighTextTokenOverlap(expected: string, actual: string): boolean {
    const expectedTokens = this.tokenizeDescriptionText(expected);
    const actualTokens = new Set(this.tokenizeDescriptionText(actual));

    if (expectedTokens.length === 0 || actualTokens.size === 0) {
      return false;
    }

    const matched = expectedTokens.filter((token) => actualTokens.has(token)).length;
    return matched / expectedTokens.length >= 0.78;
  }

  private isEquivalentDescriptionHtml(expected: string, actual: string): boolean {
    const normalizedExpected = this.normalizeHtml(expected);
    const normalizedActual = this.normalizeHtml(actual);

    if (normalizedExpected === normalizedActual) {
      return true;
    }

    const textExpected = this.stripHtml(expected);
    const textActual = this.stripHtml(actual);

    if (!textExpected || !textActual) {
      return false;
    }

    if (textExpected === textActual) {
      return true;
    }

    if (textActual.includes(textExpected) || textExpected.includes(textActual)) {
      return true;
    }

    return this.hasHighTextTokenOverlap(expected, actual);
  }
}
