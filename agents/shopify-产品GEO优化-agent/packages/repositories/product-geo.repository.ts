import { randomUUID } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

import {
  AgenticUXAudit,
  ApprovalStatus,
  ProductDetailContent,
  ProductFAQEntry,
  ProductGeoAuditRecord,
  ProductGeoRecommendationRecord,
  ProductSemanticProfile,
  ProductSemanticProfileRecord,
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

interface ProductGeoStore {
  audits: ProductGeoAuditRecord[];
  semanticProfiles: ProductSemanticProfileRecord[];
  recommendations: ProductGeoRecommendationRecord[];
}

function compactStoredValue(
  value: unknown,
  options: {
    maxDepth?: number;
    maxKeys?: number;
    maxItems?: number;
    maxStringLength?: number;
  } = {},
): unknown {
  const maxDepth = options.maxDepth ?? 4;
  const maxKeys = options.maxKeys ?? 25;
  const maxItems = options.maxItems ?? 20;
  const maxStringLength = options.maxStringLength ?? 500;
  const seen = new WeakSet<object>();

  const truncate = (input: string): string =>
    input.length > maxStringLength ? `${input.slice(0, maxStringLength)}...` : input;

  const visit = (input: unknown, depth: number): unknown => {
    if (input == null) {
      return input;
    }

    if (typeof input === "string") {
      return truncate(input);
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

      return Object.fromEntries(
        Object.entries(input)
          .slice(0, maxKeys)
          .map(([key, nested]) => [key, visit(nested, depth + 1)]),
      );
    }

    return String(input);
  };

  return visit(value, 0);
}

const EMPTY_STORE: ProductGeoStore = {
  audits: [],
  semanticProfiles: [],
  recommendations: [],
};

export class ProductGeoRepository {
  readonly audits: ProductGeoAuditRecord[] = [];
  readonly semanticProfiles: ProductSemanticProfileRecord[] = [];
  readonly recommendations: ProductGeoRecommendationRecord[] = [];

  private readonly dataDir = path.resolve(process.cwd(), "runtime-data");
  private readonly storePath = path.join(this.dataDir, "product-geo-store.json");
  private loaded = false;

  async saveAudit(
    input: Omit<ProductGeoAuditRecord, "id" | "createdAt" | "updatedAt">,
  ): Promise<ProductGeoAuditRecord> {
    await this.load();

    const now = new Date().toISOString();
    const record: ProductGeoAuditRecord = {
      id: randomUUID(),
      ...(compactStoredValue(input, {
        maxDepth: 3,
        maxKeys: 20,
        maxItems: 15,
        maxStringLength: 300,
      }) as Omit<ProductGeoAuditRecord, "id" | "createdAt" | "updatedAt">),
      createdAt: now,
      updatedAt: now,
    };

    this.audits.push(record);
    await this.persist();
    return record;
  }

  async saveSemanticProfile(input: {
    shopifyProductId: string;
    semanticProfile: ProductSemanticProfile;
  }): Promise<ProductSemanticProfileRecord> {
    await this.load();

    const now = new Date().toISOString();
    const record: ProductSemanticProfileRecord = {
      id: randomUUID(),
      shopifyProductId: input.shopifyProductId,
      semanticProfile: compactStoredValue(input.semanticProfile, {
        maxDepth: 3,
        maxKeys: 20,
        maxItems: 15,
        maxStringLength: 300,
      }) as ProductSemanticProfile,
      createdAt: now,
      updatedAt: now,
    };

    this.semanticProfiles.push(record);
    await this.persist();
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
    await this.load();

    const now = new Date().toISOString();
    const record: ProductGeoRecommendationRecord = {
      id: randomUUID(),
      shopifyProductId: input.shopifyProductId,
      recommendedTitle: String(compactStoredValue(input.recommendations.title, { maxStringLength: 300 }) ?? ""),
      recommendedSeoTitle: String(compactStoredValue(input.recommendations.seo_title, { maxStringLength: 300 }) ?? ""),
      recommendedSeoDescription: String(compactStoredValue(input.recommendations.seo_description, { maxStringLength: 500 }) ?? ""),
      recommendedDescriptionHtml: String(compactStoredValue(input.recommendations.description_html, { maxStringLength: 2000 }) ?? ""),
      recommendedTags: compactStoredValue(input.recommendations.tags, {
        maxDepth: 2,
        maxItems: 20,
        maxStringLength: 80,
      }) as string[],
      recommendedMetafields: compactStoredValue(input.recommendations.metafields, {
        maxDepth: 3,
        maxKeys: 10,
        maxItems: 20,
        maxStringLength: 300,
      }) as ProductGeoRecommendationRecord["recommendedMetafields"],
      recommendedFaq: compactStoredValue(input.recommendations.faq, {
        maxDepth: 3,
        maxKeys: 10,
        maxItems: 12,
        maxStringLength: 300,
      }) as ProductGeoRecommendationRecord["recommendedFaq"],
      recommendedImageAlt: compactStoredValue(input.recommendations.image_alt, {
        maxDepth: 3,
        maxKeys: 10,
        maxItems: 12,
        maxStringLength: 200,
      }) as ProductGeoRecommendationRecord["recommendedImageAlt"],
      recommendedSchema: compactStoredValue(input.recommendations.schema_projection, {
        maxDepth: 4,
        maxKeys: 20,
        maxItems: 15,
        maxStringLength: 300,
      }) as Record<string, unknown>,
      recommendedOpenAiFeed: compactStoredValue(input.recommendations.openai_feed_projection, {
        maxDepth: 4,
        maxKeys: 20,
        maxItems: 15,
        maxStringLength: 300,
      }) as Record<string, unknown>,
      recommendedGoogleMerchant: compactStoredValue(input.recommendations.google_merchant_projection, {
        maxDepth: 4,
        maxKeys: 20,
        maxItems: 15,
        maxStringLength: 300,
      }) as Record<string, unknown>,
      searchIntents: compactStoredValue(input.recommendations.search_intents, {
        maxDepth: 3,
        maxKeys: 15,
        maxItems: 15,
        maxStringLength: 200,
      }) as SearchIntentProjection,
      productDetailContent: compactStoredValue(input.productDetailContent, {
        maxDepth: 3,
        maxKeys: 15,
        maxItems: 15,
        maxStringLength: 500,
      }) as ProductDetailContent,
      seoMetadata: compactStoredValue(input.seoMetadata, {
        maxDepth: 3,
        maxKeys: 15,
        maxItems: 15,
        maxStringLength: 300,
      }) as SeoMetadataRecommendation,
      faqContent: compactStoredValue(input.faqContent, {
        maxDepth: 3,
        maxKeys: 10,
        maxItems: 12,
        maxStringLength: 300,
      }) as ProductFAQEntry[],
      agenticUxAudit: compactStoredValue(input.agenticUxAudit, {
        maxDepth: 3,
        maxKeys: 15,
        maxItems: 10,
        maxStringLength: 200,
      }) as AgenticUXAudit,
      safeWritebackPlan: compactStoredValue(input.safeWritebackPlan, {
        maxDepth: 3,
        maxKeys: 20,
        maxItems: 20,
        maxStringLength: 200,
      }) as SafeWritebackPlanOutput,
      approvalStatus: input.approvalStatus,
      createdAt: now,
      updatedAt: now,
    };

    this.recommendations.push(record);
    await this.persist();
    return record;
  }

  async getLatestRecommendationByProductId(
    shopifyProductId: string,
  ): Promise<ProductGeoRecommendationRecord | null> {
    await this.load();

    return (
      this.recommendations
        .filter((item) => item.shopifyProductId === shopifyProductId)
        .sort((left, right) => right.createdAt.localeCompare(left.createdAt))[0] ?? null
    );
  }

  async getLatestAuditByProductId(shopifyProductId: string): Promise<ProductGeoAuditRecord | null> {
    await this.load();

    return (
      this.audits
        .filter((item) => item.shopifyProductId === shopifyProductId)
        .sort((left, right) => right.createdAt.localeCompare(left.createdAt))[0] ?? null
    );
  }

  async getRecommendationById(id: string): Promise<ProductGeoRecommendationRecord | null> {
    await this.load();
    return this.recommendations.find((item) => item.id === id) ?? null;
  }

  async getLatestSemanticProfileByProductId(
    shopifyProductId: string,
  ): Promise<ProductSemanticProfileRecord | null> {
    await this.load();

    return (
      this.semanticProfiles
        .filter((item) => item.shopifyProductId === shopifyProductId)
        .sort((left, right) => right.createdAt.localeCompare(left.createdAt))[0] ?? null
    );
  }

  private async load(): Promise<void> {
    if (this.loaded) {
      return;
    }

    await mkdir(this.dataDir, { recursive: true });

    try {
      const raw = await readFile(this.storePath, "utf8");
      const parsed = JSON.parse(raw) as Partial<ProductGeoStore>;
      this.audits.push(...(parsed.audits ?? []));
      this.semanticProfiles.push(...(parsed.semanticProfiles ?? []));
      this.recommendations.push(...(parsed.recommendations ?? []));
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      if (!message.includes("ENOENT")) {
        throw error;
      }
      await this.persist();
    }

    this.loaded = true;
  }

  private async persist(): Promise<void> {
    await mkdir(this.dataDir, { recursive: true });
    const store: ProductGeoStore = {
      audits: this.audits,
      semanticProfiles: this.semanticProfiles,
      recommendations: this.recommendations,
    };
    await writeFile(this.storePath, JSON.stringify(store ?? EMPTY_STORE, null, 2), "utf8");
  }
}
