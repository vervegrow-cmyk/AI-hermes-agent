import { ProductGeoChannelPublicationRepository } from "../../repositories/product-geo-channel-publication.repository.js";
import { ProductGeoCheckpointRepository } from "../../repositories/product-geo-checkpoint.repository.js";
import { ProductGeoExecutionLogRepository } from "../../repositories/product-geo-execution-log.repository.js";
import { ProductGeoRepository } from "../../repositories/product-geo.repository.js";
import { ProductGeoReoptimizeAttemptRepository } from "../../repositories/product-geo-reoptimize-attempt.repository.js";
import { ProductGeoSnapshotRepository } from "../../repositories/product-geo-snapshot.repository.js";
import { DeepSeekGeoService } from "../../services/deepseek-geo.service.js";
import { BusinessPolicyInjectionService } from "../../services/business-policy-injection.service.js";
import { DefaultFieldPolicyService } from "../../services/default-field-policy.service.js";
import { DobaProductSourceService } from "../../services/doba-product-source.service.js";
import { GoogleMerchantProjectionService } from "../../services/google-merchant-projection.service.js";
import { OpenAIProductFeedProjectionService } from "../../services/openai-product-feed-projection.service.js";
import { GigaProductSourceService } from "../../services/giga-product-source.service.js";
import { ProductDataMergeService } from "../../services/product-data-merge.service.js";
import { SchemaMarkupService } from "../../services/schema-markup.service.js";
import { ShopifyProductGeoService } from "../../services/shopify-product-geo.service.js";
import { SupplierSourceResolverService } from "../../services/supplier-source-resolver.service.js";
import { AgenticSearchIntentSkill } from "../../skills/product-agentic-geo/agentic-search-intent.skill.js";
import { AgenticUXReadinessSkill } from "../../skills/product-agentic-geo/agentic-ux-readiness.skill.js";
import { CatalogFieldOptimizationSkill } from "../../skills/product-agentic-geo/catalog-field-optimization.skill.js";
import { BusinessPolicyInjectionSkill } from "../../skills/product-agentic-geo/business-policy-injection.skill.js";
import { GoogleMerchantReadinessSkill } from "../../skills/product-agentic-geo/google-merchant-readiness.skill.js";
import { ImageAltMediaSemanticSkill } from "../../skills/product-agentic-geo/image-alt-media-semantic.skill.js";
import { OpenAIProductFeedProjectionSkill } from "../../skills/product-agentic-geo/openai-product-feed-projection.skill.js";
import { ProductFAQTrustSkill } from "../../skills/product-agentic-geo/product-faq-trust.skill.js";
import { ProductGEOAuditSkill } from "../../skills/product-agentic-geo/product-geo-audit.skill.js";
import { ProductGEOMonitoringSkill } from "../../skills/product-agentic-geo/product-geo-monitoring.skill.js";
import { ProductGEOValidationSkill } from "../../skills/product-agentic-geo/product-geo-validation.skill.js";
import { ProductGEOWriteBackSkill } from "../../skills/product-agentic-geo/product-geo-writeback.skill.js";
import { ProductSchemaGenerationSkill } from "../../skills/product-agentic-geo/product-schema-generation.skill.js";
import { ProductSemanticProfileSkill } from "../../skills/product-agentic-geo/product-semantic-profile.skill.js";
import { ShopifyActiveProductScanSkill } from "../../skills/product-agentic-geo/shopify-active-product-scan.skill.js";
import { ShopifyTaxonomyMappingSkill } from "../../skills/product-agentic-geo/shopify-taxonomy-mapping.skill.js";
import { SourceDataEnrichmentSkill } from "../../skills/product-agentic-geo/source-data-enrichment.skill.js";
import { VariantOptionNormalizationSkill } from "../../skills/product-agentic-geo/variant-option-normalization.skill.js";
import { ProductAgenticGEOAgent } from "./product-agentic-geo.agent.js";
import { ProductAgenticGEOOrchestrator } from "./product-agentic-geo.orchestrator.js";
import { ProductAgenticGEORouter } from "./product-agentic-geo.router.js";

export function createProductAgenticGEORouter(): ProductAgenticGEORouter {
  const shopifyService = new ShopifyProductGeoService();
  const deepSeekGeoService = new DeepSeekGeoService();
  const defaultFieldPolicyService = new DefaultFieldPolicyService();
  const businessPolicyInjectionService = new BusinessPolicyInjectionService(
    defaultFieldPolicyService,
  );
  const googleMerchantProjectionService = new GoogleMerchantProjectionService(
    defaultFieldPolicyService,
  );
  const openAiProjectionService = new OpenAIProductFeedProjectionService(
    defaultFieldPolicyService,
  );
  const schemaMarkupService = new SchemaMarkupService();
  const gigaProductSourceService = new GigaProductSourceService();
  const dobaProductSourceService = new DobaProductSourceService();
  const supplierSourceResolverService = new SupplierSourceResolverService();
  const productDataMergeService = new ProductDataMergeService(defaultFieldPolicyService);

  const productGeoRepository = new ProductGeoRepository();
  const snapshotRepository = new ProductGeoSnapshotRepository();
  const channelPublicationRepository = new ProductGeoChannelPublicationRepository();
  const checkpointRepository = new ProductGeoCheckpointRepository();
  const executionLogRepository = new ProductGeoExecutionLogRepository();
  const reoptimizeAttemptRepository = new ProductGeoReoptimizeAttemptRepository();

  const agent = new ProductAgenticGEOAgent(
    new ShopifyActiveProductScanSkill(shopifyService),
    new ProductGEOAuditSkill(deepSeekGeoService),
    new ProductSemanticProfileSkill(),
    new BusinessPolicyInjectionSkill(businessPolicyInjectionService),
    new CatalogFieldOptimizationSkill(),
    new ShopifyTaxonomyMappingSkill(),
    new VariantOptionNormalizationSkill(),
    new GoogleMerchantReadinessSkill(googleMerchantProjectionService),
    new OpenAIProductFeedProjectionSkill(openAiProjectionService),
    new AgenticSearchIntentSkill(),
    new ProductFAQTrustSkill(),
    new ImageAltMediaSemanticSkill(),
    new ProductSchemaGenerationSkill(schemaMarkupService),
    new AgenticUXReadinessSkill(),
    new ProductGEOWriteBackSkill(shopifyService),
    new ProductGEOValidationSkill(),
    new ProductGEOMonitoringSkill(),
    new SourceDataEnrichmentSkill(
      gigaProductSourceService,
      dobaProductSourceService,
      supplierSourceResolverService,
      productDataMergeService,
    ),
    productGeoRepository,
    snapshotRepository,
    channelPublicationRepository,
    checkpointRepository,
    executionLogRepository,
    reoptimizeAttemptRepository,
  );

  return new ProductAgenticGEORouter(new ProductAgenticGEOOrchestrator(agent));
}

export * from "./product-agentic-geo.agent.js";
export * from "./product-agentic-geo.orchestrator.js";
export * from "./product-agentic-geo.router.js";
export * from "./product-agentic-geo.types.js";
