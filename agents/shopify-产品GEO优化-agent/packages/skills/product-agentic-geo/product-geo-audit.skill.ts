import {
  DeepSeekGeoAnalysis,
  EnrichedProductSnapshot,
  ShopifyProductSnapshot,
} from "../../agents/product-agentic-geo-agent/product-agentic-geo.types.js";
import {
  DEEPSEEK_CONTENT_FIELDS_CAN_OPTIMIZE,
  DEEPSEEK_TRUTH_FIELDS_CANNOT_GENERATE,
} from "../../config/deepseek-content-optimization-fields.js";
import { DeepSeekGeoService } from "../../services/deepseek-geo.service.js";

export class ProductGEOAuditSkill {
  constructor(private readonly deepSeekGeoService: DeepSeekGeoService) {}

  async execute(
    product: ShopifyProductSnapshot,
    auditMode: "before" | "preview_after" | "final_after" = "before",
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
    },
    enrichedSnapshot?: EnrichedProductSnapshot | null,
    generationOptions?: {
      aggressiveGeoOptimization?: boolean;
      autoFillMissingFields?: boolean;
      targetGeoScore?: number;
      minimumPassScore?: number;
      deepseekContentOnly?: boolean;
      lockSourceTruthFields?: boolean;
      lockBusinessPolicyFields?: boolean;
      businessDefaults?: Record<string, unknown>;
      warehousePolicy?: Record<string, unknown>;
      lockedPolicyFields?: string[];
    },
  ): Promise<DeepSeekGeoAnalysis> {
    return this.deepSeekGeoService.analyzeProductGEO({
      auditMode,
      aggressiveGeoOptimization: generationOptions?.aggressiveGeoOptimization,
      autoFillMissingFields: generationOptions?.autoFillMissingFields,
      targetGeoScore: generationOptions?.targetGeoScore,
      minimumPassScore: generationOptions?.minimumPassScore,
      deepseekContentOnly: generationOptions?.deepseekContentOnly,
      lockSourceTruthFields: generationOptions?.lockSourceTruthFields,
      lockBusinessPolicyFields: generationOptions?.lockBusinessPolicyFields,
      productId: product.id,
      title: product.title,
      descriptionHtml: product.descriptionHtml,
      productType: product.productType,
      vendor: product.vendor,
      tags: product.tags,
      options: product.options,
      variants: product.variants,
      images: product.images,
      metafields: product.metafields,
      sourceEnrichmentContext: enrichedSnapshot
        ? {
            sourceType: enrichedSnapshot.sourceType,
            supplierProductId: enrichedSnapshot.supplierProductId,
            supplierSku: enrichedSnapshot.supplierSku,
            enrichedFields: enrichedSnapshot.enrichedFields,
            unresolvedFields: enrichedSnapshot.unresolvedFields,
            supplierData: {
              brand: enrichedSnapshot.sourceData.brand,
              vendor: enrichedSnapshot.sourceData.vendor,
              productType: enrichedSnapshot.sourceData.productType,
              rawCategory: enrichedSnapshot.sourceData.rawCategory,
              googleProductCategory: enrichedSnapshot.sourceData.googleProductCategory,
              material: enrichedSnapshot.sourceData.material,
              color: enrichedSnapshot.sourceData.color,
              size: enrichedSnapshot.sourceData.size,
              dimensions: enrichedSnapshot.sourceData.dimensions,
              weight: enrichedSnapshot.sourceData.weight,
              packageDimensions: enrichedSnapshot.sourceData.packageDimensions,
              packageWeight: enrichedSnapshot.sourceData.packageWeight,
              shippingOrigin: enrichedSnapshot.sourceData.shippingOrigin,
              shippingTime: enrichedSnapshot.sourceData.shippingTime,
              returnPolicy: enrichedSnapshot.sourceData.returnPolicy,
              warranty: enrichedSnapshot.sourceData.warranty,
              mpn: enrichedSnapshot.sourceData.mpn,
              gtin: enrichedSnapshot.sourceData.gtin,
              barcode: enrichedSnapshot.sourceData.barcode,
              packingList: enrichedSnapshot.sourceData.packingList,
              compatibility: enrichedSnapshot.sourceData.compatibility,
              specifications: enrichedSnapshot.sourceData.specifications,
              usageScenarios: enrichedSnapshot.sourceData.usageScenarios,
              images: enrichedSnapshot.sourceData.images,
            },
          }
        : undefined,
      businessDefaults: generationOptions?.businessDefaults,
      warehousePolicy: generationOptions?.warehousePolicy,
      lockedPolicyFields: generationOptions?.lockedPolicyFields,
      contentFieldsDeepseekCanOptimize: generationOptions?.deepseekContentOnly
        ? [...DEEPSEEK_CONTENT_FIELDS_CAN_OPTIMIZE]
        : undefined,
      truthFieldsDeepseekCannotGenerate: [...DEEPSEEK_TRUTH_FIELDS_CANNOT_GENERATE],
      reoptimizeContext,
    });
  }
}
