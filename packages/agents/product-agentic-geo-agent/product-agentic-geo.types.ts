export type GeoPriority = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";

export type ApprovalStatus = "pending" | "approved" | "rejected";

export type WritebackStatus = "not_started" | "preview_only" | "written" | "failed";

export type RollbackStatus = "not_rolled_back" | "rolled_back" | "rollback_failed";

export interface RunActiveProductGEOAuditParams {
  limit?: number;
  dryRun?: boolean;
}

export interface ShopifyActiveProductRef {
  id: string;
  handle: string;
  title: string;
}

export interface ProductGeoAgentCommand {
  type: "run-active-product-geo-audit";
  payload: RunActiveProductGEOAuditParams;
}

export interface SeoMetadata {
  title: string;
  description: string;
}

export interface ShopifyCollectionRef {
  id: string;
  handle: string;
  title: string;
}

export interface ShopifyMediaImage {
  id: string;
  url: string;
  altText: string;
  mediaContentType: string;
  position: number;
}

export interface ShopifyProductOptionValue {
  id: string;
  name: string;
}

export interface ShopifyProductOption {
  id: string;
  name: string;
  position: number;
  values: ShopifyProductOptionValue[];
}

export interface ShopifySelectedOption {
  name: string;
  value: string;
}

export interface ShopifyProductVariant {
  id: string;
  title: string;
  sku: string;
  barcode: string;
  price: string;
  compareAtPrice: string;
  inventoryQuantity: number;
  availableForSale: boolean;
  selectedOptions: ShopifySelectedOption[];
}

export interface ShopifyMetafield {
  namespace: string;
  key: string;
  type: string;
  value: string;
}

export interface ShopifyCategoryRef {
  id: string;
  fullName: string;
}

export interface ShopifyPublication {
  id: string;
  name: string;
  catalogTitle: string;
  isPublished: boolean;
}

export interface ShopifyProductSnapshot {
  id: string;
  title: string;
  handle: string;
  status: string;
  vendor: string;
  productType: string;
  tags: string[];
  descriptionHtml: string;
  seo: SeoMetadata;
  options: ShopifyProductOption[];
  variants: ShopifyProductVariant[];
  images: ShopifyMediaImage[];
  metafields: ShopifyMetafield[];
  category: ShopifyCategoryRef | null;
  collections: ShopifyCollectionRef[];
  publishedInStore: boolean;
  availableForSale: boolean;
  salesChannels: ShopifyPublication[];
}

export interface DeepSeekGeoInput {
  productId: string;
  auditMode?: "before" | "preview_after" | "final_after";
  title: string;
  descriptionHtml?: string;
  productType?: string;
  vendor?: string;
  tags?: string[];
  options?: ShopifyProductOption[];
  variants?: ShopifyProductVariant[];
  images?: ShopifyMediaImage[];
  metafields?: ShopifyMetafield[];
}

export interface ProductSemanticProfile {
  what_is_it: string;
  primary_use_case: string;
  target_buyers: string[];
  shopping_scenarios: string[];
  recommendation_triggers: string[];
  not_suitable_for: string[];
  key_attributes?: string[];
}

export interface ProductFAQEntry {
  question: string;
  answer: string;
}

export interface ImageAltRecommendation {
  image_id: string;
  alt: string;
}

export interface MetafieldRecommendation {
  namespace: string;
  key: string;
  type: string;
  value: string;
}

export interface SearchIntentProjection {
  core_queries: string[];
  problem_queries: string[];
  comparison_queries: string[];
  gift_queries: string[];
  agent_recommendation_triggers: string[];
}

export interface ProductDetailContent {
  summary: string;
  key_selling_points: string[];
  use_cases: string[];
  specifications: string[];
  package_includes: string[];
  how_to_use: string[];
  suitable_for: string[];
  caution_notes: string[];
  description_html: string;
}

export interface SeoMetadataRecommendation {
  seo_title: string;
  seo_description: string;
  handle_suggestion: string;
  image_alt_suggestions: ImageAltRecommendation[];
  internal_link_suggestions: string[];
}

export interface AgenticUXAudit {
  can_identify_title: boolean;
  can_identify_price: boolean;
  can_select_variant: boolean;
  can_add_to_cart: boolean;
  can_enter_checkout: boolean;
  can_read_shipping_return: boolean;
  issues: string[];
}

export interface SafeWritebackPlanOutput {
  safe_fields: string[];
  approval_required_fields: string[];
  forbidden_fields: string[];
}

export interface ProductGeoRecommendations {
  title: string;
  description_html: string;
  seo_title: string;
  seo_description: string;
  handle_suggestion: string;
  description_outline: string[];
  tags: string[];
  faq: ProductFAQEntry[];
  image_alt: ImageAltRecommendation[];
  metafields: MetafieldRecommendation[];
  search_intents: SearchIntentProjection;
  openai_feed_projection: Record<string, unknown>;
  google_merchant_projection: Record<string, unknown>;
  schema_projection: Record<string, unknown>;
}

export interface DeepSeekGeoAnalysis {
  geo_score: number;
  catalog_score: number;
  google_merchant_score: number;
  openai_feed_score: number;
  schema_score: number;
  faq_score: number;
  image_alt_score: number;
  agentic_ux_score: number;
  missing_fields: string[];
  risk_flags: string[];
  semantic_profile: ProductSemanticProfile;
  product_detail_content: ProductDetailContent;
  seo_metadata: SeoMetadataRecommendation;
  faq_content: ProductFAQEntry[];
  schema_projection: Record<string, unknown>;
  google_merchant_projection: Record<string, unknown>;
  openai_product_feed_projection: Record<string, unknown>;
  agentic_ux_audit: AgenticUXAudit;
  safe_writeback_plan: SafeWritebackPlanOutput;
  recommendations: ProductGeoRecommendations;
  safe_writeback_fields: string[];
  approval_required_fields: string[];
  forbidden_fields: string[];
}

export interface ProductGeoScoreSet {
  geoScore: number;
  catalogScore: number;
  googleMerchantScore: number;
  openAiFeedScore: number;
  schemaScore: number;
  faqScore: number;
  imageAltScore: number;
  agenticUxScore: number;
}

export interface ProductGeoScoreDelta {
  geoScore: number;
  catalogScore: number;
  googleMerchantScore: number;
  openAiFeedScore: number;
  schemaScore: number;
  faqScore: number;
  imageAltScore: number;
  agenticUxScore: number;
}

export type ProductOptimizationResult = "PASS" | "WEAK_PASS" | "FAILED" | "RISK_BLOCKED";

export interface ProductGeoAuditRecord {
  id: string;
  shopifyProductId: string;
  shopifyHandle: string;
  status: string;
  beforeScores: ProductGeoScoreSet;
  previewAfterScores: ProductGeoScoreSet;
  finalAfterScores: ProductGeoScoreSet;
  scoreDelta: ProductGeoScoreDelta;
  missingFields: string[];
  riskFlags: string[];
  priority: GeoPriority;
  optimizationResult: ProductOptimizationResult;
  createdAt: string;
  updatedAt: string;
}

export interface ProductSemanticProfileRecord {
  id: string;
  shopifyProductId: string;
  semanticProfile: ProductSemanticProfile;
  createdAt: string;
  updatedAt: string;
}

export interface ProductGeoRecommendationRecord {
  id: string;
  shopifyProductId: string;
  recommendedTitle: string;
  recommendedSeoTitle: string;
  recommendedSeoDescription: string;
  recommendedDescriptionHtml: string;
  recommendedTags: string[];
  recommendedMetafields: MetafieldRecommendation[];
  recommendedFaq: ProductFAQEntry[];
  recommendedImageAlt: ImageAltRecommendation[];
  recommendedSchema: Record<string, unknown>;
  recommendedOpenAiFeed: Record<string, unknown>;
  recommendedGoogleMerchant: Record<string, unknown>;
  searchIntents: SearchIntentProjection;
  productDetailContent: ProductDetailContent;
  seoMetadata: SeoMetadataRecommendation;
  faqContent: ProductFAQEntry[];
  agenticUxAudit: AgenticUXAudit;
  safeWritebackPlan: SafeWritebackPlanOutput;
  approvalStatus: ApprovalStatus;
  createdAt: string;
  updatedAt: string;
}

export interface ProductGeoWritebackSnapshotRecord {
  id: string;
  shopifyProductId: string;
  beforePayload: Record<string, unknown>;
  afterPayload: Record<string, unknown>;
  changedFields: string[];
  writebackStatus: WritebackStatus;
  rollbackStatus: RollbackStatus;
  createdAt: string;
  updatedAt: string;
}

export interface ProductGeoAuditResult {
  sequence: number;
  productId: string;
  title: string;
  handle: string;
  originalTitle: string;
  beforeScores: ProductGeoScoreSet;
  previewAfterScores: ProductGeoScoreSet;
  finalAfterScores: ProductGeoScoreSet;
  scoreDelta: ProductGeoScoreDelta;
  missingFields: string[];
  riskFlags: string[];
  priority: GeoPriority;
  optimizationResult: ProductOptimizationResult;
  snapshotId: string;
  recommendationId: string;
  recommendationSummary: string[];
  actualWritebackFields: string[];
  forbiddenFieldsConfirmed: string[];
  writebackStatus: WritebackStatus;
  validationOk: boolean;
  validationMessage: string;
}

export interface RunActiveProductGEOAuditResult {
  scanned: number;
  dryRun: boolean;
  results: ProductGeoAuditResult[];
}

export interface ProductGeoPipelineContext {
  product: ShopifyProductSnapshot;
  snapshotId: string;
  beforeAnalysis?: DeepSeekGeoAnalysis;
  previewAnalysis?: DeepSeekGeoAnalysis;
  finalAnalysis?: DeepSeekGeoAnalysis;
}

export interface ProductGeoValidationResult {
  ok: boolean;
  errors: string[];
}

export interface ProductSafeWritebackPlan {
  title?: string;
  descriptionHtml?: string;
  tags?: string[];
  seoTitle?: string;
  seoDescription?: string;
  handle?: string;
  imageAltUpdates: ImageAltRecommendation[];
  metafields: MetafieldRecommendation[];
  fieldsToWrite: string[];
  blockedFields: string[];
  approvalRequiredFields: string[];
  forbiddenFieldsConfirmed: string[];
  salesChannelsToPublish: ShopifyPublication[];
}

export interface ProductWritebackResult {
  attempted: boolean;
  dryRun: boolean;
  status: WritebackStatus;
  fieldsWritten: string[];
  blockedFields: string[];
  summaryLines: string[];
  publishedChannelIds: string[];
  publishedChannelNames: string[];
}

export interface ProductAfterValidationResult {
  ok: boolean;
  checkedFields: string[];
  mismatchedFields: string[];
  message: string;
}
