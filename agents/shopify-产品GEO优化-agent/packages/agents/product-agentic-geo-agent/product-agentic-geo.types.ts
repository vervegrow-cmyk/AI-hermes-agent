export type GeoPriority = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";

export type ApprovalStatus = "pending" | "approved" | "rejected";

export type WritebackStatus = "not_started" | "preview_only" | "written" | "failed";

export type RollbackStatus = "not_rolled_back" | "rolled_back" | "rollback_failed";

export interface RunActiveProductGEOAuditParams {
  limit?: number;
  dryRun?: boolean;
  allowPartialWriteback?: boolean;
  strictPassOnly?: boolean;
  maxReoptimizeAttempts?: number;
  skipUnqualified?: boolean;
  fromProductId?: string;
  runId?: string;
  forceRetryFailed?: boolean;
  enableSourceEnrichment?: boolean;
  disableSourceEnrichment?: boolean;
  sourceType?: SupplierSourceType;
  requireSourceEnrichment?: boolean;
  aggressiveGeoOptimization?: boolean;
  autoFillMissingFields?: boolean;
  targetGeoScore?: number;
  minimumPassScore?: number;
  publishRegardlessScore?: boolean;
  scoreGateMode?: "strict" | "advisory";
  forcePublishAfterOptimization?: boolean;
  continueIfBelowTarget?: boolean;
  sourceFirst?: boolean;
  policySecond?: boolean;
  deepseekLast?: boolean;
  deepseekContentOnly?: boolean;
  lockSourceTruthFields?: boolean;
  lockBusinessPolicyFields?: boolean;
}

export type SupplierSourceType = "AUTO" | "GIGA" | "DOBA" | "UNKNOWN";

export interface ShopifyActiveProductRef {
  id: string;
  handle: string;
  title: string;
}

export interface ProductGeoAgentCommand {
  type: "run-active-product-geo-audit";
  payload: RunActiveProductGEOAuditParams;
}

export type ProductGeoRunStatus =
  | "RUN_CREATED"
  | "RUN_STARTED"
  | "RUN_COMPLETED"
  | "RUN_FAILED"
  | "REOPTIMIZE_REQUIRED"
  | "ROLLBACK_REQUIRED"
  | "ROLLBACK_COMPLETED";

export type ProductGeoCheckpointStage =
  | "PRODUCT_PENDING"
  | "PRODUCT_STARTED"
  | "BEFORE_SNAPSHOT_CREATED"
  | "BEFORE_GEO_SCORED"
  | "SOURCE_TRUTH_ENRICHMENT_STARTED"
  | "SOURCE_TRUTH_ENRICHMENT_COMPLETED"
  | "SOURCE_TRUTH_FIELDS_LOCKED"
  | "BUSINESS_POLICY_INJECTION_STARTED"
  | "BUSINESS_POLICY_INJECTION_COMPLETED"
  | "POLICY_LOCKED_SNAPSHOT_CREATED"
  | "DEEPSEEK_CONTENT_OPTIMIZATION_STARTED"
  | "DEEPSEEK_ANALYZED"
  | "DEEPSEEK_CONTENT_OPTIMIZATION_COMPLETED"
  | "PREVIEW_GENERATED"
  | "PREVIEW_SCORED"
  | "PREVIEW_BLOCKED_WRITEBACK"
  | "POLICY_COMPLIANCE_CHECKED"
  | "FINAL_PAYLOAD_MERGED"
  | "FINAL_PAYLOAD_SAFE_TO_WRITE"
  | "SAFETY_CHECK_PASSED"
  | "SHOPIFY_WRITTEN"
  | "CHANNELS_PUBLISHED"
  | "AFTER_VALIDATED"
  | "FINAL_SCORED"
  | "SOURCE_POLICY_DEEPSEEK_PIPELINE_COMPLETED"
  | "REOPTIMIZE_REQUIRED"
  | "REOPTIMIZE_STARTED"
  | "REOPTIMIZE_DEEPSEEK_ANALYZED"
  | "REOPTIMIZE_PREVIEW_GENERATED"
  | "REOPTIMIZE_PREVIEW_SCORED"
  | "REOPTIMIZE_WRITEBACK_BLOCKED"
  | "REOPTIMIZE_WRITTEN"
  | "REOPTIMIZE_FINAL_SCORED"
  | "REOPTIMIZE_PASS"
  | "MAX_REOPTIMIZE_REACHED"
  | "NEED_MANUAL_DATA"
  | "UNQUALIFIED_SKIPPED"
  | "MODEL_REPEATED_WEAK_OUTPUT"
  | "PRODUCT_COMPLETED"
  | "PRODUCT_FAILED";

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
  publicationAvailable?: boolean;
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

export interface SupplierSourceResolution {
  sourceType: Exclude<SupplierSourceType, "AUTO">;
  supplierProductId: string;
  supplierSku: string;
  externalSourceId: string;
  matchedBy: string[];
}

export interface SupplierProductSourceData {
  sourceType: Exclude<SupplierSourceType, "AUTO">;
  supplierProductId: string;
  supplierSku: string;
  title: string;
  description: string;
  brand: string;
  vendor: string;
  productType: string;
  rawCategory: string;
  googleProductCategory: string;
  material: string;
  color: string;
  size: string;
  dimensions: Record<string, unknown>;
  weight: string;
  packageDimensions: Record<string, unknown>;
  packageWeight: string;
  warehouse: string;
  shippingOrigin: string;
  shippingTime: string;
  returnPolicy: string;
  warranty: string;
  mpn: string;
  gtin: string;
  barcode: string;
  packingList: string[];
  compatibility: string[];
  specifications: Record<string, unknown>;
  usageScenarios: string[];
  images: string[];
  rawPayload: Record<string, unknown>;
}

export interface EnrichedProductSnapshot {
  product: ShopifyProductSnapshot;
  sourceType: Exclude<SupplierSourceType, "AUTO">;
  supplierProductId: string;
  supplierSku: string;
  enrichedFields: string[];
  unresolvedFields: string[];
  sourceData: SupplierProductSourceData;
  sourceEnrichedGeoScore?: number;
  sourceEnrichmentDelta?: number;
}

export interface DeepSeekGeoInput {
  productId: string;
  auditMode?: "before" | "preview_after" | "final_after";
  aggressiveGeoOptimization?: boolean;
  autoFillMissingFields?: boolean;
  targetGeoScore?: number;
  minimumPassScore?: number;
  deepseekContentOnly?: boolean;
  lockSourceTruthFields?: boolean;
  lockBusinessPolicyFields?: boolean;
  title: string;
  descriptionHtml?: string;
  productType?: string;
  vendor?: string;
  tags?: string[];
  options?: ShopifyProductOption[];
  variants?: ShopifyProductVariant[];
  images?: ShopifyMediaImage[];
  metafields?: ShopifyMetafield[];
  sourceEnrichmentContext?: {
    sourceType: SupplierSourceType;
    supplierProductId?: string;
    supplierSku?: string;
    enrichedFields?: string[];
    unresolvedFields?: string[];
    supplierData?: Record<string, unknown>;
  };
  businessDefaults?: Record<string, unknown>;
  warehousePolicy?: Record<string, unknown>;
  lockedPolicyFields?: string[];
  contentFieldsDeepseekCanOptimize?: string[];
  truthFieldsDeepseekCannotGenerate?: string[];
  reoptimizeContext?: {
    reoptimizeAttempt: number;
    previousBeforeGeoScore?: number;
    previousPreviewAfterGeoScore?: number;
    previousFinalAfterGeoScore?: number;
    failedModules?: string[];
    lowScoreModules?: string[];
    missingFields?: string[];
    riskFlags?: string[];
    actualWrittenFields?: string[];
    fieldsNotWritten?: string[];
    finalScorerFeedback?: string;
    reoptimizeReason?: string;
  };
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

export interface DeepSeekPolicyCompliance {
  source_truth_used: boolean;
  business_policy_used: boolean;
  locked_policy_fields_modified: boolean;
  real_fields_invented: boolean;
  gtin_invented: boolean;
  warehouse_city_invented: boolean;
  sku_used_as_gtin: boolean;
  notes: string[];
}

export interface DeepSeekContentOptimizationResult {
  title: string;
  handle: string;
  seo_title: string;
  seo_description: string;
  description_html: string;
  tags: string[];
  summary: string;
  key_selling_points: string[];
  use_cases: string[];
  suitable_for: string[];
  package_includes: string[];
  how_to_use: string[];
  caution_notes: string[];
  faq_content: ProductFAQEntry[];
  image_alt: ImageAltRecommendation[];
  schema_projection: Record<string, unknown>;
  google_merchant_projection: Record<string, unknown>;
  openai_product_feed_projection: Record<string, unknown>;
  semantic_profile: ProductSemanticProfile;
  search_intents: SearchIntentProjection;
  agentic_ux_audit: AgenticUXAudit;
}

export interface ProductGeoAuditModule {
  before_geo_score: number;
  missing_fields: string[];
  risk_flags: string[];
  catalog_gaps: string[];
  google_merchant_gaps: string[];
  openai_feed_gaps: string[];
  schema_gaps: string[];
  agentic_ux_gaps: string[];
}

export interface BeforeAfterScoreModule {
  before_geo_score: number;
  after_geo_score: number;
  score_delta: number;
  optimization_result: ProductOptimizationResult;
  writeback_allowed: boolean;
}

export interface ProductGeoRecommendations {
  title: string;
  product_type?: string;
  shopify_category?: string;
  google_product_category?: string;
  supplier_category?: string;
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
  geo_audit: ProductGeoAuditModule;
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
  search_intents: SearchIntentProjection;
  product_detail_content: ProductDetailContent;
  seo_metadata: SeoMetadataRecommendation;
  faq_content: ProductFAQEntry[];
  schema_projection: Record<string, unknown>;
  google_merchant_projection: Record<string, unknown>;
  openai_product_feed_projection: Record<string, unknown>;
  agentic_ux_audit: AgenticUXAudit;
  before_after_score: BeforeAfterScoreModule;
  safe_writeback_plan: SafeWritebackPlanOutput;
  policy_compliance: DeepSeekPolicyCompliance;
  content_optimization_result: DeepSeekContentOptimizationResult;
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
  productDetailScore: number;
  trustInfoScore: number;
  variantOptionScore: number;
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
  productDetailScore: number;
  trustInfoScore: number;
  variantOptionScore: number;
  agenticUxScore: number;
}

export type ProductOptimizationResult =
  | "PASS"
  | "PARTIAL_PASS"
  | "WEAK_PASS"
  | "FAILED"
  | "RISK_BLOCKED"
  | "NEED_MANUAL_DATA"
  | "MAX_REOPTIMIZE_REACHED"
  | "UNQUALIFIED_SKIPPED"
  | "MODEL_REPEATED_WEAK_OUTPUT";

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
  geoAcceptanceMessage?: string;
}

export interface RunActiveProductGEOAuditResult {
  scanned: number;
  dryRun: boolean;
  results: ProductGeoAuditResult[];
  runId?: string;
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
  resolvedHandle?: string;
  blockedFields: string[];
  summaryLines: string[];
  publishedChannelIds: string[];
  publishedChannelNames: string[];
  channelResults: ProductGeoChannelPublicationRecord[];
}

export interface ProductAfterValidationResult {
  ok: boolean;
  checkedFields: string[];
  mismatchedFields: string[];
  message: string;
  warningOnly?: boolean;
}

export interface ProductGeoChannelPublicationRecord {
  id: string;
  shopifyProductId: string;
  channelName: string;
  publicationId: string;
  publishStatus: "published" | "already_published" | "unavailable" | "failed";
  failureReason: string;
  checkedAt: string;
}

export interface ProductGeoExecutionLogRecord {
  id: string;
  shopifyProductId: string;
  handle: string;
  sequence: number;
  stage: string;
  status: "success" | "failed";
  message: string;
  createdAt: string;
}

export interface ProductGeoRunRecord {
  id: string;
  mode: "dry-run" | "optimize-active";
  status: ProductGeoRunStatus;
  startedAt: string;
  updatedAt: string;
  finishedAt: string;
  totalProducts: number;
  completedCount: number;
  partialPassCount: number;
  failedCount: number;
  blockedWritebackCount: number;
  reoptimizeCount: number;
  maxReoptimizeAttempts: number;
  currentReoptimizeAttempt: number;
  unqualifiedCount: number;
  skippedUnqualifiedCount: number;
  needManualDataCount: number;
  sourceEnrichmentCount: number;
  sourceFetchFailedCount: number;
  needSupplierMappingCount: number;
  currentIndex: number;
  currentProductId: string;
  currentHandle: string;
  currentStage: string;
  lastSuccessProductId: string;
  lastErrorProductId: string;
  lastErrorStage: string;
  lastErrorMessage: string;
  resumeEnabled: boolean;
}

export interface ProductGeoProductCheckpointRecord {
  id: string;
  runId: string;
  productIndex: number;
  shopifyProductId: string;
  handle: string;
  title: string;
  status: ProductGeoCheckpointStage;
  currentStage: string;
  beforeSnapshotId: string;
  afterSnapshotId: string;
  beforeGeoScore: number;
  previewAfterGeoScore: number;
  finalAfterGeoScore: number;
  previewScoreDelta: number;
  finalScoreDelta: number;
  optimizationResult: ProductOptimizationResult | "";
  writebackStatus: WritebackStatus | "";
  publicationStatus: string;
  rollbackStatus: RollbackStatus | "";
  reoptimizeAttempt: number;
  maxReoptimizeAttempts: number;
  reoptimizeReason: string;
  sourceType: string;
  supplierProductId: string;
  supplierSku: string;
  sourceEnrichmentStatus: string;
  sourceEnrichedGeoScore: number;
  sourceEnrichmentDelta: number;
  unresolvedSourceFieldsJson: string[];
  supplierMappingStatus: string;
  failedModulesJson: string[];
  lowScoreModulesJson: string[];
  manualRequiredFieldsJson: string[];
  lastReoptimizeResult: ProductOptimizationResult | "";
  finalBlockReason: string;
  errorStage: string;
  errorMessage: string;
  startedAt: string;
  updatedAt: string;
  finishedAt: string;
}

export interface ProductGeoReoptimizeAttemptRecord {
  id: string;
  runId: string;
  shopifyProductId: string;
  handle: string;
  attemptNumber: number;
  beforeGeoScore: number;
  previewAfterGeoScore: number;
  finalAfterGeoScore: number;
  failedModulesJson: string[];
  lowScoreModulesJson: string[];
  riskFlagsJson: string[];
  reoptimizeReason: string;
  deepseekPromptJson: Record<string, unknown>;
  deepseekResultJson: Record<string, unknown>;
  writtenFieldsJson: string[];
  blockedReason: string;
  result: ProductOptimizationResult;
  createdAt: string;
  updatedAt: string;
}
