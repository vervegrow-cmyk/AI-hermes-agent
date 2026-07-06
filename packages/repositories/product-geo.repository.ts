import { randomUUID } from "node:crypto";

import {
  AgenticUXAudit,
  ApprovalStatus,
  ProductDetailContent,
  ProductGeoAuditRecord,
  ProductGeoRecommendationRecord,
  ProductSemanticProfile,
  ProductSemanticProfileRecord,
  ProductFAQEntry,
  SafeWritebackPlanOutput,
  SearchIntentProjection,
  SeoMetadataRecommendation,
} from "../agents/product-agentic-geo-agent/product-agentic-geo.types.js";

export const PRODUCT_GEO_AUDITS_TABLE_SQL = `
CREATE TABLE product_geo_audits (
  id UUID PRIMARY KEY,
  shopify_product_id TEXT NOT NULL,
  shopify_handle TEXT,
  status TEXT,
  before_scores_json JSONB,
  preview_after_scores_json JSONB,
  final_after_scores_json JSONB,
  score_delta_json JSONB,
  missing_fields_json JSONB,
  risk_flags_json JSONB,
  priority TEXT,
  optimization_result TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);`;

export const PRODUCT_SEMANTIC_PROFILES_TABLE_SQL = `
CREATE TABLE product_semantic_profiles (
  id UUID PRIMARY KEY,
  shopify_product_id TEXT NOT NULL,
  what_is_it TEXT,
  primary_use_case TEXT,
  target_buyers_json JSONB,
  shopping_scenarios_json JSONB,
  key_attributes_json JSONB,
  recommendation_triggers_json JSONB,
  not_suitable_for_json JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);`;

export const PRODUCT_GEO_RECOMMENDATIONS_TABLE_SQL = `
CREATE TABLE product_geo_recommendations (
  id UUID PRIMARY KEY,
  shopify_product_id TEXT NOT NULL,
  recommended_title TEXT,
  recommended_seo_title TEXT,
  recommended_seo_description TEXT,
  recommended_description_html TEXT,
  recommended_tags_json JSONB,
  recommended_metafields_json JSONB,
  recommended_faq_json JSONB,
  recommended_image_alt_json JSONB,
  recommended_schema_json JSONB,
  recommended_openai_feed_json JSONB,
  approval_status TEXT DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);`;

export class ProductGeoRepository {
  readonly audits: ProductGeoAuditRecord[] = [];
  readonly semanticProfiles: ProductSemanticProfileRecord[] = [];
  readonly recommendations: ProductGeoRecommendationRecord[] = [];

  async saveAudit(
    input: Omit<ProductGeoAuditRecord, "id" | "createdAt" | "updatedAt">,
  ): Promise<ProductGeoAuditRecord> {
    const now = new Date().toISOString();
    const record: ProductGeoAuditRecord = {
      id: randomUUID(),
      ...input,
      createdAt: now,
      updatedAt: now,
    };
    this.audits.push(record);
    return record;
  }

  async saveSemanticProfile(input: {
    shopifyProductId: string;
    semanticProfile: ProductSemanticProfile;
  }): Promise<ProductSemanticProfileRecord> {
    const now = new Date().toISOString();
    const record: ProductSemanticProfileRecord = {
      id: randomUUID(),
      shopifyProductId: input.shopifyProductId,
      semanticProfile: input.semanticProfile,
      createdAt: now,
      updatedAt: now,
    };
    this.semanticProfiles.push(record);
    return record;
  }

  async saveRecommendations(input: {
    shopifyProductId: string;
    recommendations: {
      title: string;
      description_html: string;
      seo_title: string;
      seo_description: string;
      handle_suggestion: string;
      description_outline: string[];
      tags: string[];
      metafields: ProductGeoRecommendationRecord["recommendedMetafields"];
      faq: ProductGeoRecommendationRecord["recommendedFaq"];
      image_alt: ProductGeoRecommendationRecord["recommendedImageAlt"];
      schema_projection: Record<string, unknown>;
      openai_feed_projection: Record<string, unknown>;
      google_merchant_projection: Record<string, unknown>;
      search_intents: SearchIntentProjection;
    };
    productDetailContent: ProductDetailContent;
    seoMetadata: SeoMetadataRecommendation;
    faqContent: ProductFAQEntry[];
    agenticUxAudit: AgenticUXAudit;
    safeWritebackPlan: SafeWritebackPlanOutput;
    approvalStatus: ApprovalStatus;
  }): Promise<ProductGeoRecommendationRecord> {
    const now = new Date().toISOString();
    const record: ProductGeoRecommendationRecord = {
      id: randomUUID(),
      shopifyProductId: input.shopifyProductId,
      recommendedTitle: input.recommendations.title,
      recommendedSeoTitle: input.recommendations.seo_title,
      recommendedSeoDescription: input.recommendations.seo_description,
      recommendedDescriptionHtml: input.recommendations.description_html,
      recommendedTags: input.recommendations.tags,
      recommendedMetafields: input.recommendations.metafields,
      recommendedFaq: input.recommendations.faq,
      recommendedImageAlt: input.recommendations.image_alt,
      recommendedSchema: input.recommendations.schema_projection,
      recommendedOpenAiFeed: input.recommendations.openai_feed_projection,
      recommendedGoogleMerchant: input.recommendations.google_merchant_projection,
      searchIntents: input.recommendations.search_intents,
      productDetailContent: input.productDetailContent,
      seoMetadata: input.seoMetadata,
      faqContent: input.faqContent,
      agenticUxAudit: input.agenticUxAudit,
      safeWritebackPlan: input.safeWritebackPlan,
      approvalStatus: input.approvalStatus,
      createdAt: now,
      updatedAt: now,
    };
    this.recommendations.push(record);
    return record;
  }
}
