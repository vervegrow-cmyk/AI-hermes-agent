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

export class ProductGEOValidationSkill {
  execute(analysis: DeepSeekGeoAnalysis): ProductGeoValidationResult {
    const errors: string[] = [];

    for (const field of analysis.forbidden_fields) {
      if (!FORBIDDEN_FIELDS.has(field.toLowerCase())) {
        errors.push(`模型返回了未受支持的禁止字段标记: ${field}`);
      }
    }

    if (
      analysis.safe_writeback_fields.some((field) =>
        FORBIDDEN_FIELDS.has(field.toLowerCase()),
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

    const fieldsToWrite = [
      ...(this.allowsSafeWriteback(analysis, "title") && normalizedTitle ? ["title"] : []),
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
      ...(this.allowsSafeWriteback(analysis, "metafields") && metafields.length > 0
        ? ["metafields"]
        : []),
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
      handle: undefined,
      imageAltUpdates: fieldsToWrite.includes("image_alt") ? imageAltUpdates : [],
      metafields: fieldsToWrite.includes("metafields") ? metafields : [],
      fieldsToWrite: [...new Set(fieldsToWrite)],
      blockedFields: [],
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
      if (
        this.normalizeHtml(plan.descriptionHtml ?? "") !==
        this.normalizeHtml(productAfter.descriptionHtml)
      ) {
        mismatchedFields.push("description_html");
      }
    }

    if (actuallyWrittenFields.includes("tags")) {
      checkedFields.push("tags");
      if (!this.areSameStringSets(plan.tags ?? [], productAfter.tags)) {
        mismatchedFields.push("tags");
      }
    }

    if (actuallyWrittenFields.includes("seo_title")) {
      checkedFields.push("seo_title");
      if ((plan.seoTitle ?? "") !== productAfter.seo.title) {
        mismatchedFields.push("seo_title");
      }
    }

    if (actuallyWrittenFields.includes("seo_description")) {
      checkedFields.push("seo_description");
      if ((plan.seoDescription ?? "") !== productAfter.seo.description) {
        mismatchedFields.push("seo_description");
      }
    }

    if (actuallyWrittenFields.includes("image_alt")) {
      checkedFields.push("image_alt");
      const imageMap = new Map(productAfter.images.map((image) => [image.id, image.altText]));
      for (const image of plan.imageAltUpdates) {
        if (imageMap.get(image.image_id) !== image.alt) {
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
      const unpublished = productAfter.salesChannels.filter((item) => !item.isPublished);
      if (unpublished.length > 0) {
        mismatchedFields.push(
          `sales_channels:${unpublished
            .map((item) => item.name || item.catalogTitle || item.id)
            .join("|")}`,
        );
      }
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

  private buildImageAltUpdates(
    product: ShopifyProductSnapshot,
    recommendations: ImageAltRecommendation[],
  ): ImageAltRecommendation[] {
    const validImageIds = new Set(product.images.map((image) => image.id));
    return recommendations
      .filter((image) => validImageIds.has(image.image_id))
      .map((image) => ({
        image_id: image.image_id,
        alt: this.normalizeText(image.alt, IMAGE_ALT_MAX_LENGTH),
      }))
      .filter((image) => image.alt.length > 0);
  }

  private normalizeTags(tags: string[]): string[] {
    const deduped = new Map<string, string>();

    for (const tag of tags) {
      const normalized = this.normalizeText(tag, TAG_MAX_LENGTH);
      if (!normalized) {
        continue;
      }

      const key = normalized.toLowerCase();
      if (!deduped.has(key)) {
        deduped.set(key, normalized);
      }
    }

    return [...deduped.values()];
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
      const existing = existingMetafields.get(
        `${recommendation.namespace}.${recommendation.key}`,
      );

      if (!existing) {
        continue;
      }

      if (!SUPPORTED_METAFIELD_TYPES.has(existing.type)) {
        continue;
      }

      const normalizedType = this.normalizeMetafieldType(recommendation.type, existing.type);
      if (normalizedType !== existing.type) {
        continue;
      }

      writable.push({
        namespace: existing.namespace,
        key: existing.key,
        type: existing.type,
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
    const normalized = field.trim().toLowerCase();
    if (analysis.safe_writeback_fields.length === 0) {
      return true;
    }

    return analysis.safe_writeback_fields.some((candidate) => {
      const value = candidate.trim().toLowerCase();
      return (
        value === normalized ||
        (normalized === "description_html" && (value === "descriptionhtml" || value === "description_html")) ||
        (normalized === "seo_title" && (value === "seotitle" || value === "seo_title")) ||
        (normalized === "seo_description" &&
          (value === "seodescription" || value === "seo_description")) ||
        (normalized === "image_alt" && (value === "imagealt" || value === "image_alt"))
      );
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

  private normalizeHtml(value: string): string {
    return value
      .replace(/>\s+</g, "><")
      .replace(/\s+/g, " ")
      .trim();
  }
}
