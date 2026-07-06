import {
  DeepSeekGeoAnalysis,
  EnrichedProductSnapshot,
  ProductGeoAuditResult,
  ProductGeoScoreDelta,
  ProductGeoScoreSet,
  ProductOptimizationResult,
  ProductWritebackResult,
  RunActiveProductGEOAuditParams,
  RunActiveProductGEOAuditResult,
  ShopifyProductSnapshot,
  SupplierSourceResolution,
  SupplierSourceType,
} from "./product-agentic-geo.types.js";
import { ProductGeoChannelPublicationRepository } from "../../repositories/product-geo-channel-publication.repository.js";
import { ProductGeoCheckpointRepository } from "../../repositories/product-geo-checkpoint.repository.js";
import { ProductGeoExecutionLogRepository } from "../../repositories/product-geo-execution-log.repository.js";
import { ProductGeoReoptimizeAttemptRepository } from "../../repositories/product-geo-reoptimize-attempt.repository.js";
import { ProductGeoRepository } from "../../repositories/product-geo.repository.js";
import { ProductGeoSnapshotRepository } from "../../repositories/product-geo-snapshot.repository.js";
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

export class ProductAgenticGEOAgent {
  constructor(
    private readonly shopifyActiveProductScanSkill: ShopifyActiveProductScanSkill,
    private readonly productGeoAuditSkill: ProductGEOAuditSkill,
    private readonly productSemanticProfileSkill: ProductSemanticProfileSkill,
    private readonly businessPolicyInjectionSkill: BusinessPolicyInjectionSkill,
    private readonly catalogFieldOptimizationSkill: CatalogFieldOptimizationSkill,
    private readonly shopifyTaxonomyMappingSkill: ShopifyTaxonomyMappingSkill,
    private readonly variantOptionNormalizationSkill: VariantOptionNormalizationSkill,
    private readonly googleMerchantReadinessSkill: GoogleMerchantReadinessSkill,
    private readonly openAIProductFeedProjectionSkill: OpenAIProductFeedProjectionSkill,
    private readonly agenticSearchIntentSkill: AgenticSearchIntentSkill,
    private readonly productFAQTrustSkill: ProductFAQTrustSkill,
    private readonly imageAltMediaSemanticSkill: ImageAltMediaSemanticSkill,
    private readonly productSchemaGenerationSkill: ProductSchemaGenerationSkill,
    private readonly agenticUXReadinessSkill: AgenticUXReadinessSkill,
    private readonly productGEOWriteBackSkill: ProductGEOWriteBackSkill,
    private readonly productGEOValidationSkill: ProductGEOValidationSkill,
    private readonly productGEOMonitoringSkill: ProductGEOMonitoringSkill,
    private readonly sourceDataEnrichmentSkill: SourceDataEnrichmentSkill,
    private readonly productGeoRepository: ProductGeoRepository,
    private readonly snapshotRepository: ProductGeoSnapshotRepository,
    private readonly channelPublicationRepository: ProductGeoChannelPublicationRepository,
    private readonly checkpointRepository: ProductGeoCheckpointRepository,
    private readonly executionLogRepository: ProductGeoExecutionLogRepository,
    private readonly reoptimizeAttemptRepository: ProductGeoReoptimizeAttemptRepository,
  ) {}

  private buildGenerationOptions(options: {
    aggressiveGeoOptimization: boolean;
    autoFillMissingFields: boolean;
    targetGeoScore: number;
    minimumPassScore: number;
    deepseekContentOnly?: boolean;
    lockSourceTruthFields?: boolean;
    lockBusinessPolicyFields?: boolean;
    businessDefaults?: Record<string, unknown>;
    warehousePolicy?: Record<string, unknown>;
    lockedPolicyFields?: string[];
  }): {
    aggressiveGeoOptimization: boolean;
    autoFillMissingFields: boolean;
    targetGeoScore: number;
    minimumPassScore: number;
    deepseekContentOnly?: boolean;
    lockSourceTruthFields?: boolean;
    lockBusinessPolicyFields?: boolean;
    businessDefaults?: Record<string, unknown>;
    warehousePolicy?: Record<string, unknown>;
    lockedPolicyFields?: string[];
  } {
    return {
      aggressiveGeoOptimization: options.aggressiveGeoOptimization,
      autoFillMissingFields: options.autoFillMissingFields,
      targetGeoScore: options.targetGeoScore,
      minimumPassScore: options.minimumPassScore,
      deepseekContentOnly: options.deepseekContentOnly,
      lockSourceTruthFields: options.lockSourceTruthFields,
      lockBusinessPolicyFields: options.lockBusinessPolicyFields,
      businessDefaults: options.businessDefaults,
      warehousePolicy: options.warehousePolicy,
      lockedPolicyFields: options.lockedPolicyFields,
    };
  }

  async runActiveProductGEOAudit(
    params: RunActiveProductGEOAuditParams = {},
  ): Promise<RunActiveProductGEOAuditResult> {
    const limit = params.limit ?? 50;
    const dryRun = params.dryRun ?? false;
    const allowPartialWriteback = params.allowPartialWriteback ?? false;
    const strictPassOnly = params.strictPassOnly ?? false;
    const maxReoptimizeAttempts = params.maxReoptimizeAttempts ?? 3;
    const skipUnqualified = params.skipUnqualified ?? false;
    const enableSourceEnrichment =
      params.disableSourceEnrichment === true ? false : (params.enableSourceEnrichment ?? true);
    const sourceType = params.sourceType ?? "AUTO";
    const requireSourceEnrichment = params.requireSourceEnrichment ?? false;
    const aggressiveGeoOptimization = params.aggressiveGeoOptimization ?? true;
    const autoFillMissingFields = params.autoFillMissingFields ?? true;
    const targetGeoScore = params.targetGeoScore ?? 85;
    const minimumPassScore = params.minimumPassScore ?? 75;
    const publishRegardlessScore = params.publishRegardlessScore ?? true;
    const scoreGateMode = params.scoreGateMode ?? "advisory";
    const forcePublishAfterOptimization = params.forcePublishAfterOptimization ?? true;
    const continueIfBelowTarget = params.continueIfBelowTarget ?? true;
    const sourceFirst = params.sourceFirst ?? true;
    const policySecond = params.policySecond ?? true;
    const deepseekLast = params.deepseekLast ?? true;
    const deepseekContentOnly = params.deepseekContentOnly ?? true;
    const lockSourceTruthFields = params.lockSourceTruthFields ?? true;
    const lockBusinessPolicyFields = params.lockBusinessPolicyFields ?? true;
    const products = await this.shopifyActiveProductScanSkill.execute({ limit });
    const results: ProductGeoAuditResult[] = [];
    const mode = dryRun ? "dry-run" : "optimize-active";
    const existingRun = params.runId ? await this.checkpointRepository.getRun(params.runId) : null;
    const run =
      existingRun ??
      (await this.checkpointRepository.createRun({
        mode,
        status: "RUN_CREATED",
        startedAt: new Date().toISOString(),
        finishedAt: "",
        totalProducts: products.length,
        completedCount: 0,
        partialPassCount: 0,
        failedCount: 0,
        blockedWritebackCount: 0,
        reoptimizeCount: 0,
        maxReoptimizeAttempts,
        currentReoptimizeAttempt: 0,
        unqualifiedCount: 0,
        skippedUnqualifiedCount: 0,
        needManualDataCount: 0,
        sourceEnrichmentCount: 0,
        sourceFetchFailedCount: 0,
        needSupplierMappingCount: 0,
        currentIndex: 0,
        currentProductId: "",
        currentHandle: "",
        currentStage: "RUN_CREATED",
        lastSuccessProductId: "",
        lastErrorProductId: "",
        lastErrorStage: "",
        lastErrorMessage: "",
        resumeEnabled: true,
      }));
    await this.checkpointRepository.updateRun(run.id, {
      status: "RUN_STARTED",
      currentStage: "RUN_STARTED",
      totalProducts: products.length,
      maxReoptimizeAttempts,
    });

    const startIndex = this.resolveStartIndex(products, params.fromProductId);
    const checkpoints = await this.checkpointRepository.getProductCheckpointsByRunId(run.id);
    const completedProductIds = new Set(
      checkpoints.filter((item) => item.status === "PRODUCT_COMPLETED").map((item) => item.shopifyProductId),
    );

    for (const [index, productRef] of products.entries()) {
      if (index < startIndex) {
        continue;
      }
      if (completedProductIds.has(productRef.id)) {
        continue;
      }
      try {
        await this.checkpointRepository.updateRun(run.id, {
          currentIndex: index + 1,
          currentProductId: productRef.id,
          currentHandle: productRef.handle,
          currentStage: "PRODUCT_STARTED",
        });
        const result = await this.auditSingleProduct(productRef.id, index + 1, {
          dryRun,
          allowPartialWriteback,
          strictPassOnly,
          maxReoptimizeAttempts,
          skipUnqualified,
          runId: run.id,
          enableSourceEnrichment,
          sourceType,
          requireSourceEnrichment,
          aggressiveGeoOptimization,
          autoFillMissingFields,
          targetGeoScore,
          minimumPassScore,
          publishRegardlessScore,
          scoreGateMode,
          forcePublishAfterOptimization,
          continueIfBelowTarget,
          sourceFirst,
          policySecond,
          deepseekLast,
          deepseekContentOnly,
          lockSourceTruthFields,
          lockBusinessPolicyFields,
        });
        results.push(result);
        const shouldStopRun =
          result.optimizationResult === "RISK_BLOCKED" ||
          (result.optimizationResult === "FAILED" && result.writebackStatus !== "written");
        if (shouldStopRun) {
          throw new Error(
            `商品处理失败。阶段: GEO 优化验收。商品ID: ${result.productId}。原因: ${result.geoAcceptanceMessage ?? result.optimizationResult}`,
          );
        }
        await this.checkpointRepository.updateRun(run.id, {
          completedCount: results.length,
          partialPassCount:
            results.filter((item) => item.optimizationResult === "PARTIAL_PASS").length,
          unqualifiedCount:
            results.filter((item) => item.optimizationResult !== "PASS").length,
          skippedUnqualifiedCount:
            results.filter((item) => item.optimizationResult === "UNQUALIFIED_SKIPPED").length,
          needManualDataCount:
            results.filter((item) => item.optimizationResult === "NEED_MANUAL_DATA").length,
          blockedWritebackCount:
            checkpoints.filter((item) => item.status === "PREVIEW_BLOCKED_WRITEBACK").length +
            (result.writebackStatus === "preview_only" ? 1 : 0),
          lastSuccessProductId: result.productId,
          currentStage: "PRODUCT_COMPLETED",
        });

        if (strictPassOnly && result.optimizationResult === "PARTIAL_PASS") {
          throw new Error(
            `商品处理失败。阶段: GEO 优化验收。商品ID: ${result.productId}。原因: strict-pass-only 已启用，PARTIAL_PASS 不允许继续执行。`,
          );
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        await this.checkpointRepository.updateRun(run.id, {
          status: "RUN_FAILED",
          failedCount: 1,
          lastErrorProductId: productRef.id,
          lastErrorStage: "PRODUCT_FAILED",
          lastErrorMessage: message,
          currentStage: "PRODUCT_FAILED",
        });
        this.printFailureLog(index + 1, productRef.id, productRef.handle, error);
        throw error;
      }
    }

    await this.checkpointRepository.updateRun(run.id, {
      status: "RUN_COMPLETED",
      currentStage: "RUN_COMPLETED",
      finishedAt: new Date().toISOString(),
      resumeEnabled: false,
      completedCount: results.length,
      partialPassCount: results.filter((item) => item.optimizationResult === "PARTIAL_PASS").length,
      unqualifiedCount: results.filter((item) => item.optimizationResult !== "PASS").length,
      skippedUnqualifiedCount:
        results.filter((item) => item.optimizationResult === "UNQUALIFIED_SKIPPED").length,
      needManualDataCount:
        results.filter((item) => item.optimizationResult === "NEED_MANUAL_DATA").length,
    });

    return { scanned: products.length, dryRun, results, runId: run.id };
  }

  private async auditSingleProduct(
    productId: string,
    sequence: number,
    options: {
      dryRun: boolean;
      allowPartialWriteback: boolean;
      strictPassOnly: boolean;
      maxReoptimizeAttempts: number;
      skipUnqualified: boolean;
      runId: string;
      enableSourceEnrichment: boolean;
      sourceType: SupplierSourceType;
      requireSourceEnrichment: boolean;
      aggressiveGeoOptimization: boolean;
      autoFillMissingFields: boolean;
      targetGeoScore: number;
      minimumPassScore: number;
      publishRegardlessScore: boolean;
      scoreGateMode: "strict" | "advisory";
      forcePublishAfterOptimization: boolean;
      continueIfBelowTarget: boolean;
      sourceFirst: boolean;
      policySecond: boolean;
      deepseekLast: boolean;
      deepseekContentOnly: boolean;
      lockSourceTruthFields: boolean;
      lockBusinessPolicyFields: boolean;
    },
  ): Promise<ProductGeoAuditResult> {
    let currentStage = "商品读取";
    let product: ShopifyProductSnapshot | null = null;

    const reoptimizeAttempt =
      ((options as typeof options & { reoptimizeAttempt?: number }).reoptimizeAttempt ?? 1);

    try {
      product = await this.shopifyActiveProductScanSkill.readProduct(productId);
      await this.checkpointRepository.upsertProductCheckpoint({
        runId: options.runId,
        productIndex: sequence,
        shopifyProductId: product.id,
        handle: product.handle,
        title: product.title,
        status: "PRODUCT_STARTED",
        currentStage: "PRODUCT_STARTED",
        beforeSnapshotId: "",
        afterSnapshotId: "",
        beforeGeoScore: 0,
        previewAfterGeoScore: 0,
        finalAfterGeoScore: 0,
        previewScoreDelta: 0,
        finalScoreDelta: 0,
        optimizationResult: "",
        writebackStatus: "",
        publicationStatus: "",
        rollbackStatus: "",
        reoptimizeAttempt: 0,
        maxReoptimizeAttempts: options.maxReoptimizeAttempts,
        reoptimizeReason: "",
        failedModulesJson: [],
        lowScoreModulesJson: [],
        manualRequiredFieldsJson: [],
        sourceType: "",
        supplierProductId: "",
        supplierSku: "",
        sourceEnrichmentStatus: "",
        sourceEnrichedGeoScore: 0,
        sourceEnrichmentDelta: 0,
        unresolvedSourceFieldsJson: [],
        supplierMappingStatus: "",
        lastReoptimizeResult: "",
        finalBlockReason: "",
        errorStage: "",
        errorMessage: "",
        startedAt: new Date().toISOString(),
        finishedAt: "",
      });
      await this.log(product.id, product.handle, sequence, currentStage, "success", "商品读取成功");

      currentStage = "before snapshot 创建";
      const beforeSnapshot = await this.snapshotRepository.createBeforeSnapshot(product);
      await this.checkpointRepository.upsertProductCheckpoint({
        runId: options.runId,
        productIndex: sequence,
        shopifyProductId: product.id,
        handle: product.handle,
        title: product.title,
        status: "BEFORE_SNAPSHOT_CREATED",
        currentStage: "BEFORE_SNAPSHOT_CREATED",
        beforeSnapshotId: beforeSnapshot.id,
        afterSnapshotId: "",
        beforeGeoScore: 0,
        previewAfterGeoScore: 0,
        finalAfterGeoScore: 0,
        previewScoreDelta: 0,
        finalScoreDelta: 0,
        optimizationResult: "",
        writebackStatus: "",
        publicationStatus: "",
        rollbackStatus: "",
        reoptimizeAttempt: 0,
        maxReoptimizeAttempts: options.maxReoptimizeAttempts,
        reoptimizeReason: "",
        failedModulesJson: [],
        lowScoreModulesJson: [],
        manualRequiredFieldsJson: [],
        sourceType: "",
        supplierProductId: "",
        supplierSku: "",
        sourceEnrichmentStatus: "",
        sourceEnrichedGeoScore: 0,
        sourceEnrichmentDelta: 0,
        unresolvedSourceFieldsJson: [],
        supplierMappingStatus: "",
        lastReoptimizeResult: "",
        finalBlockReason: "",
        errorStage: "",
        errorMessage: "",
        startedAt: new Date().toISOString(),
        finishedAt: "",
      });
      await this.log(product.id, product.handle, sequence, currentStage, "success", beforeSnapshot.id);

      currentStage = "优化前 GEO 评分";
      const beforeAnalysis = await this.productGeoAuditSkill.execute(
        product,
        "before",
        (options as typeof options & { reoptimizeContext?: Record<string, unknown> }).reoptimizeContext as
          | {
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
            }
          | undefined,
        undefined,
        this.buildGenerationOptions(options),
      );
      const beforeScores = this.toScoreSet(beforeAnalysis);
      let workingProduct = product;
      let enrichedSnapshot: EnrichedProductSnapshot | null = null;
      let policyLockedSnapshot: Record<string, unknown> | null = null;
      let lockedPolicyFields: string[] = [];
      await this.saveCheckpoint(options.runId, product, sequence, {
        status: "BEFORE_GEO_SCORED",
        currentStage: "BEFORE_GEO_SCORED",
        beforeSnapshotId: beforeSnapshot.id,
        beforeGeoScore: beforeScores.geoScore,
      });

      if (options.sourceFirst || options.policySecond || options.deepseekLast) {
        console.log("==============================");
        console.log("【三段式 GEO 优化管线】");
        console.log("==============================");
        console.log("1. Source Truth Enrichment：先回源补真实字段");
        console.log("2. Business Policy Injection：系统注入固定业务模板");
        console.log("3. DeepSeek Content Optimization：只做高质量内容优化");
      }

      currentStage = "缺失字段识别";
      const recommendationSummary = this.buildRecommendationSummary(product, beforeAnalysis);
      await this.log(
        product.id,
        product.handle,
        sequence,
        currentStage,
        "success",
        beforeAnalysis.missing_fields.join("、") || "无",
      );

      currentStage = "安全字段校验";
      const shouldRunSourceTruth =
        options.sourceFirst ||
        (options.enableSourceEnrichment &&
          this.sourceDataEnrichmentSkill.shouldEnrich(product, beforeAnalysis, beforeScores));
      if (shouldRunSourceTruth) {
        currentStage = "供应商源数据回补";
        await this.saveCheckpoint(options.runId, product, sequence, {
          status: "SOURCE_TRUTH_ENRICHMENT_STARTED",
          currentStage: "SOURCE_TRUTH_ENRICHMENT_STARTED",
          beforeSnapshotId: beforeSnapshot.id,
          beforeGeoScore: beforeScores.geoScore,
        });
        enrichedSnapshot = await this.trySourceEnrichment(
          product,
          beforeAnalysis,
          beforeScores,
          options.sourceType,
          options.requireSourceEnrichment,
          sequence,
        );
        if (enrichedSnapshot) {
          workingProduct = enrichedSnapshot.product;
          const currentRun = await this.checkpointRepository.getRun(options.runId);
          await this.checkpointRepository.updateRun(options.runId, {
            sourceEnrichmentCount: (currentRun?.sourceEnrichmentCount ?? 0) + 1,
          });
          await this.saveCheckpoint(options.runId, product, sequence, {
            status: "SOURCE_TRUTH_ENRICHMENT_COMPLETED",
            currentStage: "SOURCE_TRUTH_ENRICHMENT_COMPLETED",
            beforeSnapshotId: beforeSnapshot.id,
            beforeGeoScore: beforeScores.geoScore,
            sourceType: enrichedSnapshot.sourceType,
            supplierProductId: enrichedSnapshot.supplierProductId,
            supplierSku: enrichedSnapshot.supplierSku,
            sourceEnrichmentStatus: "SOURCE_DATA_MERGED",
            sourceEnrichedGeoScore: enrichedSnapshot.sourceEnrichedGeoScore ?? 0,
            sourceEnrichmentDelta: enrichedSnapshot.sourceEnrichmentDelta ?? 0,
            unresolvedSourceFieldsJson: enrichedSnapshot.unresolvedFields,
            supplierMappingStatus: "SOURCE_RESOLVED",
          });
          await this.log(
            product.id,
            product.handle,
            sequence,
            currentStage,
            "success",
            this.buildSourceEnrichmentSummary(
              enrichedSnapshot.sourceType,
              enrichedSnapshot.enrichedFields,
              enrichedSnapshot.unresolvedFields,
            ),
          );
          await this.log(
            product.id,
            product.handle,
            sequence,
            `${currentStage}_summary`,
            "success",
            this.buildSourceEnrichmentSummary(
              enrichedSnapshot.sourceType,
              enrichedSnapshot.enrichedFields,
              enrichedSnapshot.unresolvedFields,
            ),
          );
          console.log(
            this.buildSourceEnrichmentSummary(
              enrichedSnapshot.sourceType,
              enrichedSnapshot.enrichedFields,
              enrichedSnapshot.unresolvedFields,
            ),
          );
        } else {
          const currentRun = await this.checkpointRepository.getRun(options.runId);
          await this.checkpointRepository.updateRun(options.runId, {
            sourceFetchFailedCount: (currentRun?.sourceFetchFailedCount ?? 0) + 1,
            needSupplierMappingCount: (currentRun?.needSupplierMappingCount ?? 0) + 1,
          });
          await this.saveCheckpoint(options.runId, product, sequence, {
            status: "SOURCE_TRUTH_ENRICHMENT_STARTED",
            currentStage,
            beforeSnapshotId: beforeSnapshot.id,
            beforeGeoScore: beforeScores.geoScore,
            sourceType: "UNKNOWN",
            supplierProductId: "",
            supplierSku: "",
            sourceEnrichmentStatus: "SOURCE_FETCH_FAILED",
            sourceEnrichedGeoScore: 0,
            sourceEnrichmentDelta: 0,
            unresolvedSourceFieldsJson: beforeAnalysis.missing_fields,
            supplierMappingStatus: "NEED_SUPPLIER_MAPPING",
          });
          if (options.requireSourceEnrichment) {
            throw new Error("已启用 require-source-enrichment，但当前商品无法完成 GIGA / DOBA 回源补数。");
          }
        }
      }

      if (options.policySecond) {
        currentStage = "系统业务模板注入";
        await this.saveCheckpoint(options.runId, product, sequence, {
          status: "BUSINESS_POLICY_INJECTION_STARTED",
          currentStage: "BUSINESS_POLICY_INJECTION_STARTED",
          beforeSnapshotId: beforeSnapshot.id,
          beforeGeoScore: beforeScores.geoScore,
        });
        const injectedPolicy = this.businessPolicyInjectionSkill.execute(
          workingProduct,
          enrichedSnapshot?.sourceData,
        );
        workingProduct = injectedPolicy.product;
        policyLockedSnapshot = injectedPolicy.policyLockedSnapshot;
        lockedPolicyFields = injectedPolicy.lockedPolicyFields;
        await this.saveCheckpoint(options.runId, product, sequence, {
          status: "POLICY_LOCKED_SNAPSHOT_CREATED",
          currentStage: "POLICY_LOCKED_SNAPSHOT_CREATED",
          beforeSnapshotId: beforeSnapshot.id,
          beforeGeoScore: beforeScores.geoScore,
        });
      }

      const optimizationGenerationOptions = this.buildGenerationOptions({
        ...options,
        businessDefaults:
          (policyLockedSnapshot?.business_defaults as Record<string, unknown> | undefined) ??
          undefined,
        warehousePolicy:
          ((policyLockedSnapshot?.business_defaults as Record<string, unknown> | undefined)
            ?.warehouse_policy as Record<string, unknown> | undefined) ?? undefined,
        lockedPolicyFields,
      });

      await this.saveCheckpoint(options.runId, product, sequence, {
        status: "DEEPSEEK_CONTENT_OPTIMIZATION_STARTED",
        currentStage: "DEEPSEEK_CONTENT_OPTIMIZATION_STARTED",
        beforeSnapshotId: beforeSnapshot.id,
        beforeGeoScore: beforeScores.geoScore,
      });

      const optimizationAnalysis = enrichedSnapshot || policyLockedSnapshot
        ? await this.productGeoAuditSkill.execute(
            workingProduct,
            "before",
            (options as typeof options & { reoptimizeContext?: Record<string, unknown> })
              .reoptimizeContext as
              | {
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
            }
              | undefined,
            enrichedSnapshot,
            optimizationGenerationOptions,
          )
        : beforeAnalysis;

      const effectiveRecommendationSummary = enrichedSnapshot
        ? this.buildRecommendationSummary(workingProduct, optimizationAnalysis)
        : recommendationSummary;

      const validation = this.productGEOValidationSkill.execute(optimizationAnalysis);
      if (!validation.ok) {
        throw new Error(`安全边界校验失败: ${validation.errors.join("；")}`);
      }

      currentStage = "优化建议生成";
      const recommendations = this.catalogFieldOptimizationSkill.execute(optimizationAnalysis);
      recommendations.google_merchant_projection = this.googleMerchantReadinessSkill.execute(
        workingProduct,
        optimizationAnalysis,
      );
      recommendations.openai_feed_projection = this.openAIProductFeedProjectionSkill.execute(
        workingProduct,
        optimizationAnalysis,
      );
      recommendations.schema_projection = this.productSchemaGenerationSkill.execute(
        workingProduct,
        optimizationAnalysis,
      );

      this.productSemanticProfileSkill.execute(optimizationAnalysis);
      const taxonomyMapping = this.shopifyTaxonomyMappingSkill.execute(workingProduct);
      if (!optimizationAnalysis.recommendations.product_type && taxonomyMapping.productType) {
        optimizationAnalysis.recommendations.product_type = taxonomyMapping.productType;
      }
      if (!optimizationAnalysis.recommendations.shopify_category && taxonomyMapping.category) {
        optimizationAnalysis.recommendations.shopify_category = taxonomyMapping.category;
      }
      if (
        !optimizationAnalysis.recommendations.google_product_category &&
        taxonomyMapping.googleProductCategory
      ) {
        optimizationAnalysis.recommendations.google_product_category =
          taxonomyMapping.googleProductCategory;
      }
      if (!optimizationAnalysis.recommendations.supplier_category && taxonomyMapping.supplierCategory) {
        optimizationAnalysis.recommendations.supplier_category = taxonomyMapping.supplierCategory;
      }
      this.variantOptionNormalizationSkill.execute(workingProduct);
      this.agenticSearchIntentSkill.execute(optimizationAnalysis);
      this.productFAQTrustSkill.execute(optimizationAnalysis);
      this.imageAltMediaSemanticSkill.execute(optimizationAnalysis);
      this.agenticUXReadinessSkill.execute(optimizationAnalysis);
      this.productGEOMonitoringSkill.execute();

      const safeWritebackPlan = this.productGEOValidationSkill.buildSafeWritebackPlan(
        workingProduct,
        optimizationAnalysis,
      );
      await this.saveCheckpoint(options.runId, product, sequence, {
        status: "DEEPSEEK_CONTENT_OPTIMIZATION_COMPLETED",
        currentStage: "DEEPSEEK_CONTENT_OPTIMIZATION_COMPLETED",
        beforeSnapshotId: beforeSnapshot.id,
        beforeGeoScore: beforeScores.geoScore,
      });
      await this.saveCheckpoint(options.runId, product, sequence, {
        status: "DEEPSEEK_ANALYZED",
        currentStage: "DEEPSEEK_ANALYZED",
        beforeSnapshotId: beforeSnapshot.id,
        beforeGeoScore: beforeScores.geoScore,
      });

      currentStage = "after preview 生成";
      const previewProduct = this.buildPreviewProduct(workingProduct, safeWritebackPlan);
      await this.saveCheckpoint(options.runId, product, sequence, {
        status: "PREVIEW_GENERATED",
        currentStage: "PREVIEW_GENERATED",
        beforeSnapshotId: beforeSnapshot.id,
        beforeGeoScore: beforeScores.geoScore,
      });

      currentStage = "优化后 GEO 重新评分";
      const previewAnalysis = await this.productGeoAuditSkill.execute(
        previewProduct,
        "preview_after",
        undefined,
        enrichedSnapshot,
        optimizationGenerationOptions,
      );
      const previewAfterScoresRaw = this.toScoreSet(previewAnalysis);
      const previewAfterScores = this.applyWritebackConsistency(
        beforeScores,
        previewAfterScoresRaw,
        safeWritebackPlan.fieldsToWrite,
      );
      const previewScoreDelta = this.buildScoreDelta(beforeScores, previewAfterScores);
      const previewOptimizationResult = this.resolveOptimizationResult({
        beforeScores,
        afterScores: previewAfterScores,
        scoreDelta: previewScoreDelta,
        blockedFields: safeWritebackPlan.blockedFields,
        productState: previewProduct,
      });

      const previewWritebackAllowed = safeWritebackPlan.blockedFields.length === 0;
      const writebackBlockedReason = previewWritebackAllowed
        ? ""
        : `存在禁止写回字段: ${safeWritebackPlan.blockedFields.join("、")}`;

      currentStage = "before / after 鍒嗘暟瀵规瘮";
      this.assertOptimizationAllowed(
        previewOptimizationResult,
        beforeScores,
        previewAfterScores,
        previewScoreDelta,
        safeWritebackPlan.blockedFields,
        previewAnalysis,
      );
      await this.saveCheckpoint(options.runId, product, sequence, {
        status: "PREVIEW_SCORED",
        currentStage: "PREVIEW_SCORED",
        beforeSnapshotId: beforeSnapshot.id,
        beforeGeoScore: beforeScores.geoScore,
        previewAfterGeoScore: previewAfterScores.geoScore,
        previewScoreDelta: previewScoreDelta.geoScore,
        optimizationResult: previewOptimizationResult,
      });

      const shouldWriteToShopify = !options.dryRun && previewWritebackAllowed;

      let writebackResult: ProductWritebackResult;
      if (!shouldWriteToShopify) {
        await this.saveCheckpoint(options.runId, product, sequence, {
          status: "PREVIEW_BLOCKED_WRITEBACK",
          currentStage: "PREVIEW_BLOCKED_WRITEBACK",
          beforeSnapshotId: beforeSnapshot.id,
          beforeGeoScore: beforeScores.geoScore,
          previewAfterGeoScore: previewAfterScores.geoScore,
          previewScoreDelta: previewScoreDelta.geoScore,
          optimizationResult: previewOptimizationResult,
          writebackStatus: "preview_only",
        });
        writebackResult = {
          attempted: true,
          dryRun: true,
          status: "preview_only",
          fieldsWritten: options.dryRun ? safeWritebackPlan.fieldsToWrite : [],
          blockedFields: [...safeWritebackPlan.blockedFields],
          summaryLines: options.dryRun
            ? [
                `Dry Run 模式，预览写回字段: ${safeWritebackPlan.fieldsToWrite.join("、") || "无"}`,
                `Dry Run 模式，预览补发布销售渠道: ${
                  safeWritebackPlan.salesChannelsToPublish.map((item) => item.name).join("、") || "无"
                }`,
              ]
            : [
                "写回状态：已阻止，未写回 Shopify。",
                `【写回阻止】原因：${writebackBlockedReason || "安全校验未通过"}`,
              ],
          publishedChannelIds: [],
          publishedChannelNames: [],
          channelResults: (product?.salesChannels ?? []).map((channel) => ({
            id: "",
            shopifyProductId: product?.id ?? productId,
            channelName: channel.name,
            publicationId: channel.id,
            publishStatus:
              channel.publicationAvailable === false
                ? "unavailable"
                : channel.isPublished
                  ? "already_published"
                  : "failed",
            failureReason:
              channel.publicationAvailable === false
                ? "渠道不存在或不可用"
                : options.dryRun
                  ? ""
                  : "写回未执行，因此本轮未发布销售渠道。",
            checkedAt: new Date().toISOString(),
          })),
        };
      } else {
        currentStage = "Shopify 写回";
        writebackResult = await this.productGEOWriteBackSkill.execute({
          productId: product.id,
          plan: safeWritebackPlan,
          dryRun: false,
        });
        await this.saveCheckpoint(options.runId, product, sequence, {
          status: "SHOPIFY_WRITTEN",
          currentStage: "SHOPIFY_WRITTEN",
          beforeSnapshotId: beforeSnapshot.id,
          beforeGeoScore: beforeScores.geoScore,
          previewAfterGeoScore: previewAfterScores.geoScore,
          previewScoreDelta: previewScoreDelta.geoScore,
          optimizationResult: previewOptimizationResult,
          writebackStatus: writebackResult.status,
        });
      }

      await this.channelPublicationRepository.saveMany(
        writebackResult.channelResults.map((item) => ({
          shopifyProductId: item.shopifyProductId,
          channelName: item.channelName,
          publicationId: item.publicationId,
          publishStatus: item.publishStatus,
          failureReason: item.failureReason,
          checkedAt: item.checkedAt,
        })),
      );
      await this.saveCheckpoint(options.runId, product, sequence, {
        status: "CHANNELS_PUBLISHED",
        currentStage: "CHANNELS_PUBLISHED",
        beforeSnapshotId: beforeSnapshot.id,
        beforeGeoScore: beforeScores.geoScore,
        previewAfterGeoScore: previewAfterScores.geoScore,
        previewScoreDelta: previewScoreDelta.geoScore,
        optimizationResult: previewOptimizationResult,
        writebackStatus: writebackResult.status,
        publicationStatus: writebackResult.channelResults
          .map((item) => `${item.channelName}:${item.publishStatus}`)
          .join(", "),
      });

      const validationPlan =
        writebackResult.resolvedHandle && writebackResult.resolvedHandle !== safeWritebackPlan.handle
          ? { ...safeWritebackPlan, handle: writebackResult.resolvedHandle }
          : safeWritebackPlan;

      currentStage = "after validation";
      const {
        productAfter,
        validation: afterValidation,
        attempts: validationAttempts,
      } = shouldWriteToShopify
        ? await this.validateWritebackWithRetry(
            product,
            previewProduct,
            validationPlan,
            writebackResult.fieldsWritten,
          )
        : {
            productAfter: previewProduct,
            validation: this.productGEOValidationSkill.validateAfterWriteback(
              product,
              previewProduct,
              validationPlan,
              writebackResult.fieldsWritten,
              true,
            ),
            attempts: 1,
          };
      if (!afterValidation.ok) {
        if (shouldWriteToShopify) {
          const rollbackOutcome = await this.rollbackToBeforeSnapshot(beforeSnapshot.id);
          await this.saveCheckpoint(options.runId, product, sequence, {
            status: "PRODUCT_FAILED",
            currentStage: rollbackOutcome.ok ? "ROLLBACK_COMPLETED" : "ROLLBACK_REQUIRED",
            beforeSnapshotId: beforeSnapshot.id,
            beforeGeoScore: beforeScores.geoScore,
            previewAfterGeoScore: previewAfterScores.geoScore,
            previewScoreDelta: previewScoreDelta.geoScore,
            optimizationResult: previewOptimizationResult,
            writebackStatus: writebackResult.status,
            rollbackStatus: rollbackOutcome.ok ? "rolled_back" : "rollback_failed",
            errorStage: currentStage,
            errorMessage: `${afterValidation.message}；已执行 rollback: ${rollbackOutcome.message}`,
          });
          throw new Error(`${afterValidation.message}；已执行 rollback: ${rollbackOutcome.message}`);
        }
        throw new Error(afterValidation.message);
      }
      await this.log(
        product.id,
        product.handle,
        sequence,
        currentStage,
        "success",
        afterValidation.warningOnly
          ? `${afterValidation.message}，校验尝试次数: ${validationAttempts}`
          : `写回后校验通过，校验尝试次数: ${validationAttempts}`,
      );
      await this.saveCheckpoint(options.runId, product, sequence, {
        status: "AFTER_VALIDATED",
        currentStage: "AFTER_VALIDATED",
        beforeSnapshotId: beforeSnapshot.id,
        beforeGeoScore: beforeScores.geoScore,
        previewAfterGeoScore: previewAfterScores.geoScore,
        previewScoreDelta: previewScoreDelta.geoScore,
        optimizationResult: previewOptimizationResult,
        writebackStatus: writebackResult.status,
      });

      currentStage = "final_after_geo_score 生成";
      const finalAnalysis =
        shouldWriteToShopify
          ? await this.productGeoAuditSkill.execute(
              productAfter,
              "final_after",
              undefined,
              enrichedSnapshot,
              optimizationGenerationOptions,
            )
          : previewAnalysis;
      currentStage = "FINAL_ANALYSIS_DONE";
      const finalAfterScoresRaw = this.toScoreSet(finalAnalysis);
      const finalAfterScores = this.applyWritebackConsistency(
        beforeScores,
        finalAfterScoresRaw,
        shouldWriteToShopify ? writebackResult.fieldsWritten : safeWritebackPlan.fieldsToWrite,
      );
      const finalScoreDelta = this.buildScoreDelta(beforeScores, finalAfterScores);
      const finalOptimizationResult = this.resolveOptimizationResult({
        beforeScores,
        afterScores: finalAfterScores,
        scoreDelta: finalScoreDelta,
        blockedFields: safeWritebackPlan.blockedFields,
        productState: productAfter,
      });
      await this.saveCheckpoint(options.runId, product, sequence, {
        status: "FINAL_SCORED",
        currentStage: "FINAL_SCORED",
        beforeSnapshotId: beforeSnapshot.id,
        beforeGeoScore: beforeScores.geoScore,
        previewAfterGeoScore: previewAfterScores.geoScore,
        finalAfterGeoScore: finalAfterScores.geoScore,
        previewScoreDelta: previewScoreDelta.geoScore,
        finalScoreDelta: finalScoreDelta.geoScore,
        optimizationResult: finalOptimizationResult,
        writebackStatus: writebackResult.status,
      });

      const priority = this.resolvePriority(finalAfterScores.geoScore);
      currentStage = "FINAL_AUDIT_PERSISTING";
      const auditRecord = await this.productGeoRepository.saveAudit({
        shopifyProductId: product.id,
        shopifyHandle: product.handle,
        status: product.status,
        beforeScores,
        previewAfterScores,
        finalAfterScores,
        scoreDelta: finalScoreDelta,
        missingFields: optimizationAnalysis.missing_fields,
        riskFlags: optimizationAnalysis.risk_flags,
        priority,
        optimizationResult: finalOptimizationResult,
      });

      currentStage = "FINAL_SEMANTIC_PROFILE_PERSISTING";
      await this.productGeoRepository.saveSemanticProfile({
        shopifyProductId: product.id,
        semanticProfile: optimizationAnalysis.semantic_profile,
      });

      currentStage = "FINAL_RECOMMENDATION_PERSISTING";
      const recommendationRecord = await this.productGeoRepository.saveRecommendations({
        shopifyProductId: product.id,
        recommendations,
        productDetailContent: optimizationAnalysis.product_detail_content,
        seoMetadata: optimizationAnalysis.seo_metadata,
        faqContent: optimizationAnalysis.faq_content,
        agenticUxAudit: optimizationAnalysis.agentic_ux_audit,
        safeWritebackPlan: optimizationAnalysis.safe_writeback_plan,
        approvalStatus: "approved",
      });

      currentStage = "FINAL_SNAPSHOT_ATTACHING";
      await this.snapshotRepository.attachAfterSnapshot({
        snapshotId: beforeSnapshot.id,
        afterPayload: {
          dryRun: options.dryRun,
          optimizationAnalysis,
          previewAnalysis,
          finalAnalysis,
          recommendations,
          safeWritebackPlan,
          writebackResult,
          afterValidation,
          beforeScores,
          previewAfterScores,
          finalAfterScores,
          finalScoreDelta,
          optimizationResult: finalOptimizationResult,
          previewOptimizationResult,
          previewWritebackAllowed,
          writebackBlockedReason,
        } as Record<string, unknown>,
        changedFields: writebackResult.fieldsWritten,
        writebackStatus: writebackResult.status,
      });

      const geoAcceptanceMessage =
        finalAfterScores.geoScore >= 75
          ? "GEO 优化验收：PASS"
          : `GEO 优化验收：${finalOptimizationResult}，原因：final_after_geo_score = ${finalAfterScores.geoScore}，低于完整 PASS 阈值 75。`;

      const result: ProductGeoAuditResult = {
        sequence,
        productId: product.id,
        title: product.title,
        originalTitle: product.title,
        handle: product.handle,
        beforeScores: auditRecord.beforeScores,
        previewAfterScores: auditRecord.previewAfterScores,
        finalAfterScores: auditRecord.finalAfterScores,
        scoreDelta: auditRecord.scoreDelta,
        missingFields: auditRecord.missingFields,
        riskFlags: auditRecord.riskFlags,
        priority,
        optimizationResult: auditRecord.optimizationResult,
        snapshotId: beforeSnapshot.id,
        recommendationId: recommendationRecord.id,
        recommendationSummary: effectiveRecommendationSummary,
        actualWritebackFields: writebackResult.fieldsWritten,
        forbiddenFieldsConfirmed: safeWritebackPlan.forbiddenFieldsConfirmed,
        writebackStatus: writebackResult.status,
        validationOk: afterValidation.ok,
        validationMessage: afterValidation.message,
        geoAcceptanceMessage,
      };

      const lowScoreModules = this.collectLowScoreModules(result.finalAfterScores);
      const failedModules = this.collectFailedModules(
        result.finalAfterScores,
        optimizationAnalysis.risk_flags,
        productAfter,
      );
      const manualRequiredFields = this.collectManualRequiredFields(productAfter, optimizationAnalysis);
      const reoptimizeReason = this.buildReoptimizeReason(
        result,
        failedModules,
        lowScoreModules,
        manualRequiredFields,
      );
      const fieldsNotWritten = safeWritebackPlan.fieldsToWrite.filter(
        (field) => !writebackResult.fieldsWritten.includes(field),
      );

      await this.reoptimizeAttemptRepository.save({
        runId: options.runId,
        shopifyProductId: product.id,
        handle: product.handle,
        attemptNumber: reoptimizeAttempt,
        beforeGeoScore: result.beforeScores.geoScore,
        previewAfterGeoScore: result.previewAfterScores.geoScore,
        finalAfterGeoScore: result.finalAfterScores.geoScore,
        failedModulesJson: failedModules,
        lowScoreModulesJson: lowScoreModules,
        riskFlagsJson: result.riskFlags,
        reoptimizeReason,
        deepseekPromptJson: {
          reoptimizeAttempt,
          reoptimizeContext:
            (options as typeof options & { reoptimizeContext?: Record<string, unknown> })
              .reoptimizeContext ?? null,
        },
        deepseekResultJson: optimizationAnalysis as unknown as Record<string, unknown>,
        writtenFieldsJson: writebackResult.fieldsWritten,
        blockedReason: writebackBlockedReason,
        result: result.optimizationResult,
      });

      const repeatedWeakOutput = this.isRepeatedWeakOutput(
        ((options as typeof options & { reoptimizeContext?: { finalScorerFeedback?: string } })
          .reoptimizeContext?.finalScorerFeedback ?? ""),
        reoptimizeReason,
      );
      const directPublishMode =
        options.forcePublishAfterOptimization ||
        (options.publishRegardlessScore && options.continueIfBelowTarget);
      const needsManualData = manualRequiredFields.length > 0;
      const needsReoptimize =
        !directPublishMode &&
        result.optimizationResult !== "PASS" &&
        !repeatedWeakOutput &&
        reoptimizeAttempt < options.maxReoptimizeAttempts;

      if (needsReoptimize) {
        await this.checkpointRepository.updateRun(options.runId, {
          status: "REOPTIMIZE_REQUIRED",
          currentStage: "REOPTIMIZE_REQUIRED",
          currentReoptimizeAttempt: reoptimizeAttempt,
          reoptimizeCount: reoptimizeAttempt,
        });
        await this.saveCheckpoint(options.runId, product, sequence, {
          status: "REOPTIMIZE_REQUIRED",
          currentStage: "REOPTIMIZE_REQUIRED",
          beforeSnapshotId: beforeSnapshot.id,
          beforeGeoScore: beforeScores.geoScore,
          previewAfterGeoScore: previewAfterScores.geoScore,
          finalAfterGeoScore: finalAfterScores.geoScore,
          previewScoreDelta: previewScoreDelta.geoScore,
          finalScoreDelta: finalScoreDelta.geoScore,
          optimizationResult: result.optimizationResult,
          reoptimizeAttempt,
          maxReoptimizeAttempts: options.maxReoptimizeAttempts,
          reoptimizeReason,
          failedModulesJson: failedModules,
          lowScoreModulesJson: lowScoreModules,
          manualRequiredFieldsJson: manualRequiredFields,
          lastReoptimizeResult: result.optimizationResult,
          finalBlockReason: "",
        });
        this.printReoptimizeRequiredLog(
          result,
          reoptimizeAttempt,
          options.maxReoptimizeAttempts,
          reoptimizeReason,
          failedModules,
        );
        return this.auditSingleProduct(productId, sequence, {
          ...options,
          reoptimizeAttempt: reoptimizeAttempt + 1,
          reoptimizeContext: {
            previousBeforeGeoScore: result.beforeScores.geoScore,
            previousPreviewAfterGeoScore: result.previewAfterScores.geoScore,
            previousFinalAfterGeoScore: result.finalAfterScores.geoScore,
            failedModules,
            lowScoreModules,
            missingFields: result.missingFields,
            riskFlags: result.riskFlags,
            actualWrittenFields: result.actualWritebackFields,
            fieldsNotWritten,
            finalScorerFeedback: reoptimizeReason,
            reoptimizeReason,
          },
        } as typeof options);
      }

      if (directPublishMode && result.optimizationResult !== "PASS") {
        result.geoAcceptanceMessage =
          result.finalAfterScores.geoScore >= options.minimumPassScore
            ? result.geoAcceptanceMessage
            : `当前已按强优化直发模式完成真实写回与销售渠道发布，final_after_geo_score = ${result.finalAfterScores.geoScore}，低于目标 ${options.minimumPassScore}，系统仅记录质量状态，不阻断后续商品。`;
      } else if (false && needsManualData) {
        result.optimizationResult = "NEED_MANUAL_DATA";
        result.geoAcceptanceMessage = `需要人工补充数据: ${manualRequiredFields.join("、")}`;
      } else if (repeatedWeakOutput) {
        result.optimizationResult = "MODEL_REPEATED_WEAK_OUTPUT";
        result.geoAcceptanceMessage = "模型连续输出相似弱优化方案，已阻断自动重优化。";
      } else if (result.optimizationResult !== "PASS" && reoptimizeAttempt >= options.maxReoptimizeAttempts) {
        result.optimizationResult = options.skipUnqualified
          ? "UNQUALIFIED_SKIPPED"
          : "MAX_REOPTIMIZE_REACHED";
        result.geoAcceptanceMessage = options.skipUnqualified
          ? `达到最大重优化次数 ${options.maxReoptimizeAttempts}，已按参数跳过不合格商品。`
          : `达到最大重优化次数 ${options.maxReoptimizeAttempts}，仍未达到 GEO PASS。`;
      }

      currentStage = "中文终端日志打印";
      this.printSuccessLog(
        result,
        writebackResult,
        previewAnalysis,
        productAfter,
        writebackBlockedReason,
        shouldWriteToShopify,
        options.minimumPassScore,
      );
      await this.log(product.id, product.handle, sequence, currentStage, "success", "当前商品优化成功");
      await this.saveCheckpoint(options.runId, product, sequence, {
        status: "PRODUCT_COMPLETED",
        currentStage: "PRODUCT_COMPLETED",
        beforeSnapshotId: beforeSnapshot.id,
        afterSnapshotId: beforeSnapshot.id,
        beforeGeoScore: beforeScores.geoScore,
        previewAfterGeoScore: previewAfterScores.geoScore,
        finalAfterGeoScore: finalAfterScores.geoScore,
        previewScoreDelta: previewScoreDelta.geoScore,
        finalScoreDelta: finalScoreDelta.geoScore,
        optimizationResult: finalOptimizationResult,
        writebackStatus: writebackResult.status,
        publicationStatus: writebackResult.channelResults
          .map((item) => `${item.channelName}:${item.publishStatus}`)
          .join(", "),
        finishedAt: new Date().toISOString(),
      });
      return result;
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      if (product) {
        await this.log(product.id, product.handle, sequence, currentStage, "failed", message);
        await this.saveCheckpoint(options.runId, product, sequence, {
          status: "PRODUCT_FAILED",
          currentStage: "PRODUCT_FAILED",
          errorStage: currentStage,
          errorMessage: message,
          finishedAt: new Date().toISOString(),
        });
      }
      throw new Error(`商品处理失败。阶段: ${currentStage}。商品ID: ${product?.id ?? productId}。原因: ${message}`);
    }
  }

  private toScoreSet(analysis: DeepSeekGeoAnalysis): ProductGeoScoreSet {
    const productDetailScore = this.deriveProductDetailScore(analysis);
    const trustInfoScore = this.deriveTrustInfoScore(analysis);
    const variantOptionScore = this.deriveVariantOptionScore(analysis);
    const geoScore = this.aggregateGeoScore({
      catalogScore: analysis.catalog_score,
      googleMerchantScore: analysis.google_merchant_score,
      openAiFeedScore: analysis.openai_feed_score,
      schemaScore: analysis.schema_score,
      faqScore: analysis.faq_score,
      imageAltScore: analysis.image_alt_score,
      productDetailScore,
      trustInfoScore,
      variantOptionScore,
      agenticUxScore: analysis.agentic_ux_score,
    });

    return {
      geoScore,
      catalogScore: analysis.catalog_score,
      googleMerchantScore: analysis.google_merchant_score,
      openAiFeedScore: analysis.openai_feed_score,
      schemaScore: analysis.schema_score,
      faqScore: analysis.faq_score,
      imageAltScore: analysis.image_alt_score,
      productDetailScore,
      trustInfoScore,
      variantOptionScore,
      agenticUxScore: analysis.agentic_ux_score,
    };
  }

  private applyWritebackConsistency(
    beforeScores: ProductGeoScoreSet,
    afterScores: ProductGeoScoreSet,
    actualFields: string[],
  ): ProductGeoScoreSet {
    const fields = new Set(actualFields);
    const normalized: ProductGeoScoreSet = { ...afterScores };

    if (!fields.has("image_alt")) {
      normalized.imageAltScore = beforeScores.imageAltScore;
    }
    if (!fields.has("metafields")) {
      normalized.faqScore = beforeScores.faqScore;
      normalized.schemaScore = beforeScores.schemaScore;
    }
    if (!fields.has("description_html")) {
      normalized.productDetailScore = beforeScores.productDetailScore;
      normalized.trustInfoScore = beforeScores.trustInfoScore;
    }
    if (!fields.has("tags") && !fields.has("title")) {
      normalized.variantOptionScore = beforeScores.variantOptionScore;
    }
    if (!fields.has("metafields") && !fields.has("seo_title") && !fields.has("seo_description") && !fields.has("description_html") && !fields.has("tags")) {
      normalized.googleMerchantScore = beforeScores.googleMerchantScore;
      normalized.openAiFeedScore = beforeScores.openAiFeedScore;
    }
    if (!fields.has("sales_channels")) {
      normalized.agenticUxScore = Math.min(normalized.agenticUxScore, beforeScores.agenticUxScore);
    }

    normalized.geoScore = this.aggregateGeoScore({
      catalogScore: normalized.catalogScore,
      googleMerchantScore: normalized.googleMerchantScore,
      openAiFeedScore: normalized.openAiFeedScore,
      schemaScore: normalized.schemaScore,
      faqScore: normalized.faqScore,
      imageAltScore: normalized.imageAltScore,
      productDetailScore: normalized.productDetailScore,
      trustInfoScore: normalized.trustInfoScore,
      variantOptionScore: normalized.variantOptionScore,
      agenticUxScore: normalized.agenticUxScore,
    });

    return normalized;
  }

  private aggregateGeoScore(scores: Omit<ProductGeoScoreSet, "geoScore">): number {
    const weighted =
      scores.catalogScore * 0.14 +
      scores.googleMerchantScore * 0.14 +
      scores.openAiFeedScore * 0.12 +
      scores.schemaScore * 0.1 +
      scores.faqScore * 0.08 +
      scores.imageAltScore * 0.08 +
      scores.productDetailScore * 0.12 +
      scores.trustInfoScore * 0.08 +
      scores.variantOptionScore * 0.06 +
      scores.agenticUxScore * 0.08;

    return Math.round(weighted);
  }

  private deriveProductDetailScore(analysis: DeepSeekGeoAnalysis): number {
    let score = 0;
    if (analysis.product_detail_content.summary) score += 20;
    score += Math.min(20, analysis.product_detail_content.key_selling_points.length * 5);
    score += Math.min(20, analysis.product_detail_content.use_cases.length * 5);
    score += Math.min(20, analysis.product_detail_content.specifications.length * 4);
    score += Math.min(20, analysis.product_detail_content.how_to_use.length * 5);
    return Math.min(100, score);
  }

  private deriveTrustInfoScore(analysis: DeepSeekGeoAnalysis): number {
    const faqText = analysis.faq_content
      .map((item) => `${item.question} ${item.answer}`)
      .join(" ")
      .toLowerCase();
    const descriptionText = analysis.product_detail_content.description_html.toLowerCase();
    const missingText = [...analysis.missing_fields, ...analysis.risk_flags].join(" ").toLowerCase();
    const merchantProjection = this.extractSearchableText(analysis.google_merchant_projection);
    const openAiProjection = this.extractSearchableText(analysis.openai_product_feed_projection);
    const schemaProjection = this.extractSearchableText(analysis.schema_projection);

    const hasShipping =
      faqText.includes("ship") ||
      descriptionText.includes("ship") ||
      merchantProjection.includes("shipping") ||
      openAiProjection.includes("shipping") ||
      schemaProjection.includes("shipping");
    const hasReturn =
      faqText.includes("return") ||
      descriptionText.includes("return") ||
      merchantProjection.includes("return") ||
      openAiProjection.includes("return") ||
      schemaProjection.includes("return");
    const hasTax =
      faqText.includes("tax") ||
      descriptionText.includes("tax") ||
      merchantProjection.includes("tax") ||
      openAiProjection.includes("tax");
    const hasWarranty =
      faqText.includes("warranty") ||
      descriptionText.includes("warranty") ||
      merchantProjection.includes("warranty") ||
      openAiProjection.includes("warranty");

    let score = 30;
    if (hasShipping) score += 20;
    if (hasReturn) score += 20;
    if (hasTax) score += 15;
    if (hasWarranty) score += 5;
    score += Math.min(10, analysis.faq_content.length * 2);
    if (schemaProjection.includes("faqpage")) score += 5;
    if (schemaProjection.includes("offershippingdetails")) score += 5;

    if (missingText.includes("shipping")) score -= 10;
    if (missingText.includes("return")) score -= 10;
    if (missingText.includes("tax")) score -= 10;
    if (missingText.includes("warranty")) score -= 5;

    return Math.max(0, Math.min(100, score));
  }

  private extractSearchableText(value: unknown, maxLength = 12000, maxDepth = 4): string {
    const parts: string[] = [];
    const seen = new WeakSet<object>();
    let currentLength = 0;

    const pushPart = (part: string): void => {
      if (!part || currentLength >= maxLength) {
        return;
      }

      const next = part.slice(0, Math.max(0, maxLength - currentLength));
      if (!next) {
        return;
      }

      parts.push(next);
      currentLength += next.length + 1;
    };

    const visit = (input: unknown, depth: number): void => {
      if (currentLength >= maxLength || depth > maxDepth || input == null) {
        return;
      }

      if (typeof input === "string") {
        const normalized = input.replace(/\s+/g, " ").trim();
        if (normalized) {
          pushPart(normalized.slice(0, 500));
        }
        return;
      }

      if (typeof input === "number" || typeof input === "boolean") {
        pushPart(String(input));
        return;
      }

      if (Array.isArray(input)) {
        for (const item of input.slice(0, 20)) {
          visit(item, depth + 1);
          if (currentLength >= maxLength) {
            break;
          }
        }
        return;
      }

      if (typeof input === "object") {
        if (seen.has(input)) {
          return;
        }
        seen.add(input);

        for (const [key, nested] of Object.entries(input).slice(0, 30)) {
          pushPart(key);
          visit(nested, depth + 1);
          if (currentLength >= maxLength) {
            break;
          }
        }
      }
    };

    visit(value, 0);
    return parts.join(" ").slice(0, maxLength).toLowerCase();
  }

  private deriveVariantOptionScore(analysis: DeepSeekGeoAnalysis): number {
    const riskText = analysis.risk_flags.join(" ").toLowerCase();
    if (riskText.includes("variant")) return 45;
    if (analysis.geo_audit.catalog_gaps.some((item) => item.toLowerCase().includes("variant"))) {
      return 55;
    }
    return 80;
  }

  private buildScoreDelta(beforeScores: ProductGeoScoreSet, afterScores: ProductGeoScoreSet): ProductGeoScoreDelta {
    return {
      geoScore: afterScores.geoScore - beforeScores.geoScore,
      catalogScore: afterScores.catalogScore - beforeScores.catalogScore,
      googleMerchantScore: afterScores.googleMerchantScore - beforeScores.googleMerchantScore,
      openAiFeedScore: afterScores.openAiFeedScore - beforeScores.openAiFeedScore,
      schemaScore: afterScores.schemaScore - beforeScores.schemaScore,
      faqScore: afterScores.faqScore - beforeScores.faqScore,
      imageAltScore: afterScores.imageAltScore - beforeScores.imageAltScore,
      productDetailScore: afterScores.productDetailScore - beforeScores.productDetailScore,
      trustInfoScore: afterScores.trustInfoScore - beforeScores.trustInfoScore,
      variantOptionScore: afterScores.variantOptionScore - beforeScores.variantOptionScore,
      agenticUxScore: afterScores.agenticUxScore - beforeScores.agenticUxScore,
    };
  }

  private resolveOptimizationResult(input: {
    beforeScores: ProductGeoScoreSet;
    afterScores: ProductGeoScoreSet;
    scoreDelta: ProductGeoScoreDelta;
    blockedFields: string[];
    productState: ShopifyProductSnapshot;
  }): ProductOptimizationResult {
    const { beforeScores, afterScores, scoreDelta, blockedFields, productState } = input;
    if (blockedFields.length > 0) return "RISK_BLOCKED";
    if (productState.status !== "ACTIVE" || !productState.availableForSale) return "FAILED";
    if (scoreDelta.geoScore <= 0) return "FAILED";

    const criticalModulesLow =
      afterScores.faqScore <= 0 ||
      afterScores.schemaScore <= 0 ||
      afterScores.imageAltScore <= 0 ||
      afterScores.googleMerchantScore < 50 ||
      afterScores.openAiFeedScore < 50;

    if (afterScores.geoScore >= 75 && scoreDelta.geoScore >= 10 && !criticalModulesLow) {
      return "PASS";
    }
    if (afterScores.geoScore >= beforeScores.geoScore) {
      return "PARTIAL_PASS";
    }
    return "FAILED";
  }

  private collectLowScoreModules(scores: ProductGeoScoreSet): string[] {
    const modules: Array<[string, number, number]> = [
      ["catalog_score", scores.catalogScore, 60],
      ["google_merchant_score", scores.googleMerchantScore, 60],
      ["openai_feed_score", scores.openAiFeedScore, 60],
      ["schema_score", scores.schemaScore, 60],
      ["faq_score", scores.faqScore, 60],
      ["image_alt_score", scores.imageAltScore, 60],
      ["product_detail_score", scores.productDetailScore, 70],
    ];
    return modules.filter(([, score, threshold]) => score < threshold).map(([name]) => name);
  }

  private collectFailedModules(
    scores: ProductGeoScoreSet,
    riskFlags: string[],
    product: ShopifyProductSnapshot,
  ): string[] {
    const failed = this.collectLowScoreModules(scores);
    if ((product.productType ?? "").trim().toLowerCase() === "part") {
      failed.push("generic_product_type_part");
    }
    if (riskFlags.some((flag) => /mismatch|category|taxonomy|generic product type/i.test(flag))) {
      failed.push("taxonomy_or_category_mismatch");
    }
    return [...new Set(failed)];
  }

  private collectManualRequiredFields(
    product: ShopifyProductSnapshot,
    analysis: DeepSeekGeoAnalysis,
  ): string[] {
    const required: string[] = [];
    const missing = new Set(analysis.missing_fields.map((item) => item.toLowerCase()));
    const hasBarcode = product.variants.some((variant) => variant.barcode?.trim());
    const googleProjection = this.readJsonMetafield(product, "product_geo", "google_merchant_projection");
    const hasCustomProductFallback =
      googleProjection !== null &&
      ((googleProjection.custom_product === true ||
        googleProjection.custom_product === "true") ||
        (typeof googleProjection.mpn === "string" && googleProjection.mpn.trim().length > 0));

    if (!hasBarcode && !hasCustomProductFallback) {
      required.push("真实 GTIN / barcode 或确认 custom_product = true");
    }
    if (missing.has("material") || missing.has("dimensions") || missing.has("weight")) {
      required.push("真实材质 / 尺寸 / 重量");
    }
    if (missing.has("shipping_info") || missing.has("return_policy")) {
      required.push("真实发货 / 退货政策");
    }
    if (analysis.risk_flags.some((flag) => /category|taxonomy|google_product_category/i.test(flag))) {
      required.push("正确 Shopify / Google 商品类目");
    }
    return [...new Set(required)];
  }

  private readJsonMetafield(
    product: ShopifyProductSnapshot,
    namespace: string,
    key: string,
  ): Record<string, unknown> | null {
    const metafield = product.metafields.find(
      (field) => field.namespace === namespace && field.key === key,
    );
    if (!metafield?.value) {
      return null;
    }

    try {
      const parsed = JSON.parse(metafield.value) as unknown;
      if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
        return parsed as Record<string, unknown>;
      }
    } catch {
      return null;
    }

    return null;
  }

  private buildReoptimizeReason(
    result: ProductGeoAuditResult,
    failedModules: string[],
    lowScoreModules: string[],
    manualRequiredFields: string[],
  ): string {
    const reasons: string[] = [];
    if (result.finalAfterScores.geoScore < 75) reasons.push("final_after_geo_score < 75");
    if (result.scoreDelta.geoScore < 10) reasons.push("final_score_delta < 10");
    reasons.push(...failedModules);
    reasons.push(...lowScoreModules);
    reasons.push(...manualRequiredFields.map((item) => `required_data:${item}`));
    return [...new Set(reasons)].join(" | ");
  }

  private isRepeatedWeakOutput(previousFeedback: string, currentFeedback: string): boolean {
    if (!previousFeedback || !currentFeedback) {
      return false;
    }
    if (previousFeedback === currentFeedback && currentFeedback.includes("final_after_geo_score < 75")) {
      return true;
    }
    return false;
  }

  private printReoptimizeRequiredLog(
    result: ProductGeoAuditResult,
    attempt: number,
    maxAttempts: number,
    reason: string,
    failedModules: string[],
  ): void {
    console.log("=".repeat(30));
    console.log("【GEO 优化未达标，进入重优化】");
    console.log("=".repeat(30));
    console.log(`商品序号：${result.sequence}`);
    console.log(`Shopify Product ID：${result.productId}`);
    console.log(`Handle：${result.handle}`);
    console.log(`当前优化结果：${result.optimizationResult}`);
    console.log(`当前 final_after_geo_score：${result.finalAfterScores.geoScore}`);
    console.log("合格阈值：75");
    console.log(`当前重优化轮次：${attempt} / ${maxAttempts}`);
    console.log("【不合格原因】");
    for (const moduleName of failedModules) {
      console.log(`- ${moduleName}`);
    }
    console.log(`- ${reason}`);
    console.log("【处理动作】");
    console.log("状态：REOPTIMIZE_REQUIRED");
    console.log("下一步：重新调用 DeepSeek，针对失败模块重新生成优化方案。");
  }

  private assertOptimizationAllowed(
    optimizationResult: ProductOptimizationResult,
    beforeScores: ProductGeoScoreSet,
    previewAfterScores: ProductGeoScoreSet,
    scoreDelta: ProductGeoScoreDelta,
    blockedFields: string[],
    previewAnalysis: DeepSeekGeoAnalysis,
  ): void {
    void beforeScores;
    void previewAfterScores;
    void scoreDelta;
    void previewAnalysis;

    if (blockedFields.length > 0 || optimizationResult === "RISK_BLOCKED") {
      throw new Error(`优化命中禁止写回字段: ${blockedFields.join("、")}`);
    }
  }

  private buildDetailedPreviewFailureReason(
    beforeScores: ProductGeoScoreSet,
    previewAfterScores: ProductGeoScoreSet,
    scoreDelta: ProductGeoScoreDelta,
    previewAnalysis: DeepSeekGeoAnalysis,
  ): string {
    const gapLines = [
      ...previewAnalysis.geo_audit.catalog_gaps.map((item) => `Catalog Gap: ${item}`),
      ...previewAnalysis.geo_audit.google_merchant_gaps.map((item) => `Google Merchant Gap: ${item}`),
      ...previewAnalysis.geo_audit.openai_feed_gaps.map((item) => `OpenAI Feed Gap: ${item}`),
      ...previewAnalysis.geo_audit.schema_gaps.map((item) => `Schema Gap: ${item}`),
      ...previewAnalysis.geo_audit.agentic_ux_gaps.map((item) => `Agentic UX Gap: ${item}`),
    ];

    return [
      "预览复评分未达到写回要求。",
      `before_after_score: before=${previewAnalysis.before_after_score.before_geo_score}, after=${previewAnalysis.before_after_score.after_geo_score}, delta=${previewAnalysis.before_after_score.score_delta}, result=${previewAnalysis.before_after_score.optimization_result}, writeback_allowed=${previewAnalysis.before_after_score.writeback_allowed}`,
      `系统综合评分对比: 优化前 ${beforeScores.geoScore}, 预览后 ${previewAfterScores.geoScore}, 提升 ${this.formatDelta(scoreDelta.geoScore)}`,
      `模块提升: Catalog ${this.formatDelta(scoreDelta.catalogScore)}, Google Merchant ${this.formatDelta(scoreDelta.googleMerchantScore)}, OpenAI Feed ${this.formatDelta(scoreDelta.openAiFeedScore)}, Schema ${this.formatDelta(scoreDelta.schemaScore)}, FAQ ${this.formatDelta(scoreDelta.faqScore)}, Image Alt ${this.formatDelta(scoreDelta.imageAltScore)}, Detail ${this.formatDelta(scoreDelta.productDetailScore)}, Trust ${this.formatDelta(scoreDelta.trustInfoScore)}, Variant ${this.formatDelta(scoreDelta.variantOptionScore)}, Agentic UX ${this.formatDelta(scoreDelta.agenticUxScore)}`,
      `剩余缺口: ${gapLines.join("；") || "无"}`,
      "通过标准: 优化后 GEO >= 75 且提升 >= 10。",
    ].join(" ");
  }
  private buildPreviewProduct(
    product: ShopifyProductSnapshot,
    plan: {
      title?: string;
      handle?: string;
      descriptionHtml?: string;
      tags?: string[];
      seoTitle?: string;
      seoDescription?: string;
      imageAltUpdates: Array<{ image_id: string; alt: string }>;
      salesChannelsToPublish: Array<{ id: string }>;
      metafields?: Array<{ namespace: string; key: string; type: string; value: string }>;
    },
  ): ShopifyProductSnapshot {
    const imageAltMap = new Map(plan.imageAltUpdates.map((item) => [item.image_id, item.alt]));
    const publishIds = new Set(plan.salesChannelsToPublish.map((item) => item.id));
    const metafieldMap = new Map((plan.metafields ?? []).map((field) => [`${field.namespace}.${field.key}`, field]));
    const existingMetafields = product.metafields.map((field) => {
      const next = metafieldMap.get(`${field.namespace}.${field.key}`);
      return next ? { ...field, type: next.type, value: next.value } : field;
    });
    const existingKeys = new Set(product.metafields.map((field) => `${field.namespace}.${field.key}`));
    const newMetafields = (plan.metafields ?? [])
      .filter((field) => !existingKeys.has(`${field.namespace}.${field.key}`))
      .map((field) => ({ ...field }));

    return {
      ...product,
      title: plan.title ?? product.title,
      handle: plan.handle ?? product.handle,
      descriptionHtml: plan.descriptionHtml ?? product.descriptionHtml,
      tags: plan.tags ?? product.tags,
      seo: {
        title: plan.seoTitle ?? product.seo.title,
        description: plan.seoDescription ?? product.seo.description,
      },
      images: product.images.map((image) => ({
        ...image,
        altText: imageAltMap.get(image.id) ?? image.altText,
      })),
      metafields: [...existingMetafields, ...newMetafields],
      salesChannels: product.salesChannels.map((channel) => ({
        ...channel,
        isPublished: channel.isPublished || publishIds.has(channel.id),
      })),
      publishedInStore:
        product.publishedInStore ||
        product.salesChannels.some(
          (channel) => channel.name === "在线商店" && (channel.isPublished || publishIds.has(channel.id)),
        ),
    };
  }

  private async saveCheckpoint(
    runId: string,
    product: ShopifyProductSnapshot,
    sequence: number,
    patch: {
      status: import("./product-agentic-geo.types.js").ProductGeoCheckpointStage;
      currentStage: string;
      beforeSnapshotId?: string;
      afterSnapshotId?: string;
      beforeGeoScore?: number;
      previewAfterGeoScore?: number;
      finalAfterGeoScore?: number;
      previewScoreDelta?: number;
      finalScoreDelta?: number;
      optimizationResult?: ProductOptimizationResult | "";
      writebackStatus?: import("./product-agentic-geo.types.js").WritebackStatus | "";
      publicationStatus?: string;
      rollbackStatus?: import("./product-agentic-geo.types.js").RollbackStatus | "";
      reoptimizeAttempt?: number;
      maxReoptimizeAttempts?: number;
      reoptimizeReason?: string;
      sourceType?: string;
      supplierProductId?: string;
      supplierSku?: string;
      sourceEnrichmentStatus?: string;
      sourceEnrichedGeoScore?: number;
      sourceEnrichmentDelta?: number;
      unresolvedSourceFieldsJson?: string[];
      supplierMappingStatus?: string;
      failedModulesJson?: string[];
      lowScoreModulesJson?: string[];
      manualRequiredFieldsJson?: string[];
      lastReoptimizeResult?: ProductOptimizationResult | "";
      finalBlockReason?: string;
      errorStage?: string;
      errorMessage?: string;
      startedAt?: string;
      finishedAt?: string;
    },
  ): Promise<void> {
    const existing = await this.checkpointRepository.getProductCheckpoint(runId, product.id);
    await this.checkpointRepository.upsertProductCheckpoint({
      runId,
      productIndex: sequence,
      shopifyProductId: product.id,
      handle: product.handle,
      title: product.title,
      status: patch.status,
      currentStage: patch.currentStage,
      beforeSnapshotId: patch.beforeSnapshotId ?? existing?.beforeSnapshotId ?? "",
      afterSnapshotId: patch.afterSnapshotId ?? existing?.afterSnapshotId ?? "",
      beforeGeoScore: patch.beforeGeoScore ?? existing?.beforeGeoScore ?? 0,
      previewAfterGeoScore: patch.previewAfterGeoScore ?? existing?.previewAfterGeoScore ?? 0,
      finalAfterGeoScore: patch.finalAfterGeoScore ?? existing?.finalAfterGeoScore ?? 0,
      previewScoreDelta: patch.previewScoreDelta ?? existing?.previewScoreDelta ?? 0,
      finalScoreDelta: patch.finalScoreDelta ?? existing?.finalScoreDelta ?? 0,
      optimizationResult: patch.optimizationResult ?? existing?.optimizationResult ?? "",
      writebackStatus: patch.writebackStatus ?? existing?.writebackStatus ?? "",
      publicationStatus: patch.publicationStatus ?? existing?.publicationStatus ?? "",
      rollbackStatus: patch.rollbackStatus ?? existing?.rollbackStatus ?? "",
      reoptimizeAttempt: patch.reoptimizeAttempt ?? existing?.reoptimizeAttempt ?? 0,
      maxReoptimizeAttempts:
        patch.maxReoptimizeAttempts ?? existing?.maxReoptimizeAttempts ?? 0,
      reoptimizeReason: patch.reoptimizeReason ?? existing?.reoptimizeReason ?? "",
      sourceType: patch.sourceType ?? existing?.sourceType ?? "",
      supplierProductId: patch.supplierProductId ?? existing?.supplierProductId ?? "",
      supplierSku: patch.supplierSku ?? existing?.supplierSku ?? "",
      sourceEnrichmentStatus:
        patch.sourceEnrichmentStatus ?? existing?.sourceEnrichmentStatus ?? "",
      sourceEnrichedGeoScore:
        patch.sourceEnrichedGeoScore ?? existing?.sourceEnrichedGeoScore ?? 0,
      sourceEnrichmentDelta:
        patch.sourceEnrichmentDelta ?? existing?.sourceEnrichmentDelta ?? 0,
      unresolvedSourceFieldsJson:
        patch.unresolvedSourceFieldsJson ?? existing?.unresolvedSourceFieldsJson ?? [],
      supplierMappingStatus:
        patch.supplierMappingStatus ?? existing?.supplierMappingStatus ?? "",
      failedModulesJson: patch.failedModulesJson ?? existing?.failedModulesJson ?? [],
      lowScoreModulesJson: patch.lowScoreModulesJson ?? existing?.lowScoreModulesJson ?? [],
      manualRequiredFieldsJson:
        patch.manualRequiredFieldsJson ?? existing?.manualRequiredFieldsJson ?? [],
      lastReoptimizeResult:
        patch.lastReoptimizeResult ?? existing?.lastReoptimizeResult ?? "",
      finalBlockReason: patch.finalBlockReason ?? existing?.finalBlockReason ?? "",
      errorStage: patch.errorStage ?? existing?.errorStage ?? "",
      errorMessage: patch.errorMessage ?? existing?.errorMessage ?? "",
      startedAt: patch.startedAt ?? existing?.startedAt ?? new Date().toISOString(),
      finishedAt: patch.finishedAt ?? existing?.finishedAt ?? "",
    });
  }

  private async validateWritebackWithRetry(
    productBefore: ShopifyProductSnapshot,
    previewProduct: ShopifyProductSnapshot,
    plan: import("./product-agentic-geo.types.js").ProductSafeWritebackPlan,
    actuallyWrittenFields: string[],
  ): Promise<{
    productAfter: ShopifyProductSnapshot;
    validation: import("./product-agentic-geo.types.js").ProductAfterValidationResult;
    attempts: number;
  }> {
    let attempts = 0;
    let latestProduct = previewProduct;
    let latestValidation = this.productGEOValidationSkill.validateAfterWriteback(
      productBefore,
      previewProduct,
      plan,
      actuallyWrittenFields,
      true,
    );

    for (let index = 0; index < 3; index += 1) {
      attempts = index + 1;
      latestProduct = await this.shopifyActiveProductScanSkill.readProduct(productBefore.id);
      latestValidation = this.productGEOValidationSkill.validateAfterWriteback(
        productBefore,
        latestProduct,
        plan,
        actuallyWrittenFields,
        false,
      );
      if (latestValidation.ok) {
        break;
      }
      if (index < 2) {
        await this.sleep(1200);
      }
    }

    return {
      productAfter: latestProduct,
      validation: latestValidation,
      attempts,
    };
  }

  private async rollbackToBeforeSnapshot(
    snapshotId: string,
  ): Promise<{ ok: boolean; message: string }> {
    try {
      const snapshot = await this.snapshotRepository.getSnapshot(snapshotId);
      if (!snapshot) {
        return { ok: false, message: `未找到 before snapshot: ${snapshotId}` };
      }

      const beforePayload = snapshot.beforePayload as unknown as ShopifyProductSnapshot;
      const rollbackResult = await this.shopifyActiveProductScanSkill.rollbackProductSnapshot(
        beforePayload,
      );
      await this.snapshotRepository.markRolledBack(snapshotId, "rolled_back");
      return {
        ok: true,
        message: `已回滚字段: ${rollbackResult.restoredFields.join("、") || "无"}；已回滚渠道: ${rollbackResult.unpublishedChannelNames.join("、") || "无"}`,
      };
    } catch (error) {
      await this.snapshotRepository.markRolledBack(snapshotId, "rollback_failed");
      return {
        ok: false,
        message: error instanceof Error ? error.message : String(error),
      };
    }
  }

  private async sleep(ms: number): Promise<void> {
    await new Promise((resolve) => setTimeout(resolve, ms));
  }

  private resolveStartIndex(
    products: Array<{ id: string }>,
    fromProductId?: string,
  ): number {
    if (!fromProductId) {
      return 0;
    }

    const index = products.findIndex((product) => product.id === fromProductId);
    return index >= 0 ? index : 0;
  }

  private shouldTriggerSourceEnrichment(
    product: ShopifyProductSnapshot,
    analysis: DeepSeekGeoAnalysis,
    beforeScores: ProductGeoScoreSet,
  ): boolean {
    return (
      beforeScores.geoScore < 75 ||
      beforeScores.catalogScore < 60 ||
      beforeScores.googleMerchantScore < 60 ||
      beforeScores.openAiFeedScore < 60 ||
      product.productType.trim().toLowerCase() === "part" ||
      analysis.missing_fields.some((field) =>
        ["material", "weight", "dimensions", "brand", "vendor", "barcode", "gtin"].some((keyword) =>
          field.toLowerCase().includes(keyword),
        ),
      ) ||
      analysis.risk_flags.some((flag) =>
        ["category", "taxonomy", "source_data_missing", "missing_supplier_specs"].some((keyword) =>
          flag.toLowerCase().includes(keyword),
        ),
      )
    );
  }

  private async trySourceEnrichment(
    product: ShopifyProductSnapshot,
    analysis: DeepSeekGeoAnalysis,
    beforeScores: ProductGeoScoreSet,
    preferredSourceType: SupplierSourceType,
    requireSourceEnrichment: boolean,
    sequence: number,
  ): Promise<EnrichedProductSnapshot | null> {
    console.log("==============================");
    console.log("【供应商源数据回补】");
    console.log("==============================");
    console.log(`Shopify Product ID: ${product.id}`);
    console.log(`Handle: ${product.handle}`);
    console.log(`触发原因: ${analysis.risk_flags.join(" | ") || analysis.missing_fields.join(" | ") || "GEO 评分不足"}`);

    const merged = await this.sourceDataEnrichmentSkill.execute({
      product,
      analysis,
      beforeScores,
      preferredSourceType,
    });
    if (!merged) {
      console.log("识别来源: UNKNOWN");
      console.log("处理结果: 无法识别 GIGA / DOBA 来源，继续使用 Shopify 当前数据。");
      await this.log(
        product.id,
        product.handle,
        sequence,
        "供应商来源识别",
        "success",
        "未识别到 GIGA / DOBA 来源，继续使用 Shopify 当前数据。",
      );
      return null;
    }

    const resolution = {
      sourceType: merged.sourceType,
      supplierProductId: merged.supplierProductId,
      supplierSku: merged.supplierSku,
    };
    const enrichedAnalysis = await this.productGeoAuditSkill.execute(
      merged.product,
      "preview_after",
      undefined,
      undefined,
      this.buildGenerationOptions({
        aggressiveGeoOptimization: true,
        autoFillMissingFields: true,
        targetGeoScore: 85,
        minimumPassScore: 75,
      }),
    );
    merged.sourceEnrichedGeoScore = this.toScoreSet(enrichedAnalysis).geoScore;
    merged.sourceEnrichmentDelta = merged.sourceEnrichedGeoScore - beforeScores.geoScore;

    console.log(`识别来源: ${resolution.sourceType}`);
    console.log(`Supplier Product ID: ${resolution.supplierProductId || "未提供"}`);
    console.log(`Supplier SKU: ${resolution.supplierSku || "未提供"}`);
    console.log("回源结果: 成功");
    console.log(`补齐字段: ${merged.enrichedFields.join("、") || "无"}`);
    console.log(`仍缺字段: ${merged.unresolvedFields.join("、") || "无"}`);
    console.log(`回源前 GEO 分数: ${beforeScores.geoScore}`);
    console.log(`回源后 GEO 分数: ${merged.sourceEnrichedGeoScore}`);
    console.log(`回源提升: ${this.formatDelta(merged.sourceEnrichmentDelta)}`);

    await this.log(
      product.id,
      product.handle,
      sequence,
      "供应商回源补数评分",
      "success",
      `回源前 ${beforeScores.geoScore}，回源后 ${merged.sourceEnrichedGeoScore}，提升 ${this.formatDelta(merged.sourceEnrichmentDelta)}`,
    );

    if (merged.unresolvedFields.length > 0 && requireSourceEnrichment) {
      await this.log(
        product.id,
        product.handle,
        sequence,
        "供应商回源补数不足",
        "failed",
        `供应商仍缺失字段: ${merged.unresolvedFields.join("、")}`,
      );
    }

    return merged;
  }

  private buildRecommendationSummary(product: ShopifyProductSnapshot, analysis: DeepSeekGeoAnalysis): string[] {
    const lines: string[] = [];
    if (analysis.product_detail_content.summary) lines.push(`产品详情摘要: ${analysis.product_detail_content.summary}`);
    if (analysis.product_detail_content.key_selling_points.length > 0) lines.push(`核心卖点数量: ${analysis.product_detail_content.key_selling_points.length}`);
    if (analysis.seo_metadata.seo_title) lines.push(`SEO 标题建议: ${analysis.seo_metadata.seo_title}`);
    if (analysis.seo_metadata.seo_description) lines.push(`SEO 描述建议: ${analysis.seo_metadata.seo_description}`);
    if (analysis.faq_content.length > 0) lines.push(`FAQ 建议数量: ${analysis.faq_content.length}`);
    if (analysis.seo_metadata.image_alt_suggestions.length > 0) lines.push(`图片 Alt 建议数量: ${analysis.seo_metadata.image_alt_suggestions.length}`);
    if (analysis.agentic_ux_audit.issues.length > 0) lines.push(`Agentic UX 问题数量: ${analysis.agentic_ux_audit.issues.length}`);
    if (analysis.recommendations.metafields.length > 0) lines.push(`结构化 Metafields 数量: ${analysis.recommendations.metafields.length}`);
    if (lines.length === 0) lines.push(`商品 ${product.handle} 暂无可输出的优化摘要。`);
    return lines;
  }

  private describeEnrichedFields(fields: string[]): string {
    if (fields.length === 0) {
      return "无";
    }

    return fields
      .map((field) => {
        if (field === "descriptionHtml_context") {
          return "描述上下文";
        }
        if (field === "vendor") {
          return "brand/vendor";
        }
        if (field === "productType") {
          return "product type";
        }
        return field;
      })
      .join(" / ");
  }

  private describeUnresolvedFields(fields: string[]): string {
    if (fields.length === 0) {
      return "无";
    }

    return fields
      .map((field) => {
        if (field === "gtin_or_barcode") {
          return "GTIN / barcode";
        }
        if (field === "supplier_category") {
          return "supplier category";
        }
        return field;
      })
      .join(" / ");
  }

  private buildSourceEnrichmentSummary(
    sourceType: string,
    enrichedFields: string[],
    unresolvedFields: string[],
  ): string {
    if (
      enrichedFields.length === 1 &&
      enrichedFields[0] === "descriptionHtml_context" &&
      unresolvedFields.length > 0
    ) {
      return `来源 ${sourceType}，仅补齐了描述上下文，未补齐 ${this.describeUnresolvedFields(unresolvedFields)} 等真实字段`;
    }

    return `来源 ${sourceType}，补齐字段: ${this.describeEnrichedFields(enrichedFields)}；仍缺字段: ${this.describeUnresolvedFields(unresolvedFields)}`;
  }

  private printSuccessLog(
    result: ProductGeoAuditResult,
    writebackResult: ProductWritebackResult,
    previewAnalysis: DeepSeekGeoAnalysis,
    productAfter: ShopifyProductSnapshot,
    writebackBlockedReason: string,
    didWriteToShopify: boolean,
    minimumPassScore: number,
  ): void {
    const divider = "=".repeat(88);
    console.log(divider);
    console.log(`商品序号: ${result.sequence}`);
    console.log(`Shopify Product ID: ${result.productId}`);
    console.log(`Handle: ${result.handle}`);
    console.log(`原始标题: ${result.originalTitle}`);
    console.log(`优化前 GEO 分数: ${result.beforeScores.geoScore}`);
    console.log(`优化后预览 GEO 分数: ${result.previewAfterScores.geoScore}`);
    console.log(`写回后最终 GEO 分数: ${result.finalAfterScores.geoScore}`);
    console.log(`分数提升值: ${this.formatDelta(result.scoreDelta.geoScore)}`);
    console.log(`缺失字段: ${result.missingFields.join("、") || "无"}`);
    console.log(`风险字段: ${result.riskFlags.join("、") || "无"}`);
    console.log("优化建议摘要:");
    for (const line of result.recommendationSummary) console.log(`- ${line}`);
    console.log("预览复评分结果:");
    console.log(
      `- DeepSeek before_after_score(参考): before=${previewAnalysis.before_after_score.before_geo_score}, after=${previewAnalysis.before_after_score.after_geo_score}, delta=${previewAnalysis.before_after_score.score_delta}, result=${previewAnalysis.before_after_score.optimization_result}, writeback_allowed=${previewAnalysis.before_after_score.writeback_allowed}`,
    );
    console.log("系统主评分:");
    console.log(`- before_geo_score: ${result.beforeScores.geoScore}`);
    console.log(`- preview_after_geo_score: ${result.previewAfterScores.geoScore}`);
    console.log(`- final_after_geo_score: ${result.finalAfterScores.geoScore}`);
    console.log("GEO 评分对比:");
    console.log(`- Catalog: ${result.beforeScores.catalogScore} -> ${result.finalAfterScores.catalogScore}，提升 ${this.formatDelta(result.scoreDelta.catalogScore)}`);
    console.log(`- Google Merchant: ${result.beforeScores.googleMerchantScore} -> ${result.finalAfterScores.googleMerchantScore}，提升 ${this.formatDelta(result.scoreDelta.googleMerchantScore)}`);
    console.log(`- OpenAI Feed: ${result.beforeScores.openAiFeedScore} -> ${result.finalAfterScores.openAiFeedScore}，提升 ${this.formatDelta(result.scoreDelta.openAiFeedScore)}`);
    console.log(`- Schema: ${result.beforeScores.schemaScore} -> ${result.finalAfterScores.schemaScore}，提升 ${this.formatDelta(result.scoreDelta.schemaScore)}`);
    console.log(`- FAQ: ${result.beforeScores.faqScore} -> ${result.finalAfterScores.faqScore}，提升 ${this.formatDelta(result.scoreDelta.faqScore)}`);
    console.log(`- Image Alt: ${result.beforeScores.imageAltScore} -> ${result.finalAfterScores.imageAltScore}，提升 ${this.formatDelta(result.scoreDelta.imageAltScore)}`);
    console.log(`- Product Detail: ${result.beforeScores.productDetailScore} -> ${result.finalAfterScores.productDetailScore}，提升 ${this.formatDelta(result.scoreDelta.productDetailScore)}`);
    console.log(`- Trust Info: ${result.beforeScores.trustInfoScore} -> ${result.finalAfterScores.trustInfoScore}，提升 ${this.formatDelta(result.scoreDelta.trustInfoScore)}`);
    console.log(`- Variant Option: ${result.beforeScores.variantOptionScore} -> ${result.finalAfterScores.variantOptionScore}，提升 ${this.formatDelta(result.scoreDelta.variantOptionScore)}`);
    console.log(`- Agentic UX: ${result.beforeScores.agenticUxScore} -> ${result.finalAfterScores.agenticUxScore}，提升 ${this.formatDelta(result.scoreDelta.agenticUxScore)}`);
    console.log(`优化结果类型: ${result.optimizationResult}`);
    console.log(`实际写回字段: ${result.actualWritebackFields.join("、") || "无"}`);
    console.log(`禁止修改字段确认: ${result.forbiddenFieldsConfirmed.join("、") || "无"}`);
    console.log(`写回结果: ${result.writebackStatus}`);
    if (didWriteToShopify && result.finalAfterScores.geoScore < minimumPassScore) {
      console.log("==============================");
      console.log("【GEO 未达目标但继续真实写回】");
      console.log("==============================");
      console.log(`当前 preview_after_geo_score: ${result.previewAfterScores.geoScore}`);
      console.log(`当前 final_after_geo_score: ${result.finalAfterScores.geoScore}`);
      console.log(`目标分数: ${minimumPassScore}`);
      console.log("写回策略: publish-regardless-score");
      console.log("处理结果: 系统安全校验已通过，商品已真实写回 Shopify 并继续发布销售渠道。");
    }
    if (!didWriteToShopify && writebackBlockedReason) {
      console.log(`【写回阻止】原因：${writebackBlockedReason}`);
    }
    for (const line of writebackResult.summaryLines) console.log(`- ${line}`);
    console.log("销售渠道最终状态:");
    const channelResultMap = new Map(writebackResult.channelResults.map((channel) => [channel.channelName, channel]));
    for (const channel of productAfter.salesChannels) {
      const tracked = channelResultMap.get(channel.name);
      const label = tracked
        ? tracked.publishStatus === "published"
          ? "新增发布成功"
          : tracked.publishStatus === "already_published"
            ? "已发布"
            : tracked.publishStatus === "unavailable"
              ? "渠道不可用"
              : "发布失败"
        : channel.publicationAvailable === false
          ? "渠道不可用"
          : channel.isPublished
            ? "已发布"
            : "未发布";
      const reason = tracked?.failureReason ?? (channel.publicationAvailable === false ? "渠道不存在或不可用" : "");
      console.log(`${channel.name}: ${label}${reason ? `，原因: ${reason}` : ""}`);
    }
    console.log("【Shopify 写回校验】");
    console.log(`结果: ${result.validationOk ? "通过" : "失败"}`);
    console.log(`说明: ${result.validationMessage}`);
    console.log("【GEO 优化验收】");
    console.log(`结果: ${result.optimizationResult}`);
    console.log(`说明: ${result.geoAcceptanceMessage ?? "无"}`);
    console.log(divider);
  }

  private printFailureLog(sequence: number, productId: string, handle: string, error: unknown): void {
    const divider = "!".repeat(88);
    const message = error instanceof Error ? error.message : String(error);
    console.log(divider);
    console.log(`商品序号: ${sequence}`);
    console.log(`Shopify Product ID: ${productId}`);
    console.log(`Handle: ${handle}`);
    console.log("执行结果: 失败");
    console.log(`失败详情: ${message}`);
    console.log("后续处理: 已停止后续商品执行，不再继续批量运行。");
    console.log(divider);
  }
  private async log(
    shopifyProductId: string,
    handle: string,
    sequence: number,
    stage: string,
    status: "success" | "failed",
    message: string,
  ): Promise<void> {
    await this.executionLogRepository.save({
      shopifyProductId,
      handle,
      sequence,
      stage,
      status,
      message,
    });
  }

  private formatDelta(value: number): string {
    return `${value >= 0 ? "+" : ""}${value}`;
  }

  resolvePriority(score: number): ProductGeoAuditResult["priority"] {
    if (score < 40) return "CRITICAL";
    if (score < 60) return "HIGH";
    if (score < 75) return "MEDIUM";
    return "LOW";
  }
}
