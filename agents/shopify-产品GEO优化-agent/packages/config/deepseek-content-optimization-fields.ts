export const DEEPSEEK_CONTENT_FIELDS_CAN_OPTIMIZE = [
  "title",
  "handle",
  "seo_title",
  "seo_description",
  "description_html",
  "summary",
  "key_selling_points",
  "use_cases",
  "suitable_for",
  "package_includes",
  "how_to_use",
  "caution_notes",
  "faq_content",
  "image_alt",
  "schema_projection",
  "google_merchant_projection",
  "openai_product_feed_projection",
  "semantic_profile",
  "agentic_ux_audit",
  "product_type",
  "tags",
  "search_intents",
] as const;

export const DEEPSEEK_TRUTH_FIELDS_CANNOT_GENERATE = [
  "gtin",
  "upc",
  "barcode",
  "brand",
  "material",
  "weight",
  "dimensions",
  "package_weight",
  "package_dimensions",
  "warehouse_city",
  "warehouse_state",
  "warehouse_origin",
  "shipping_origin",
  "inventory",
  "price",
  "sku",
  "variant_id",
] as const;

export const DEEPSEEK_SAFE_WRITEBACK_CONTENT_FIELDS = [
  "title",
  "handle",
  "description_html",
  "tags",
  "seo_title",
  "seo_description",
  "image_alt",
  "metafields",
] as const;

export type DeepseekContentField =
  (typeof DEEPSEEK_CONTENT_FIELDS_CAN_OPTIMIZE)[number];

export type DeepseekTruthField =
  (typeof DEEPSEEK_TRUTH_FIELDS_CANNOT_GENERATE)[number];

export type DeepseekSafeWritebackField =
  (typeof DEEPSEEK_SAFE_WRITEBACK_CONTENT_FIELDS)[number];
