import {
  DeepSeekGeoAnalysis,
  ProductGeoAuditResult,
  ProductGeoScoreDelta,
  ProductGeoScoreSet,
  ProductOptimizationResult,
  RunActiveProductGEOAuditParams,
  RunActiveProductGEOAuditResult,
  ShopifyProductSnapshot,
} from "./product-agentic-geo.types.js";
import { ProductGeoRepository } from "../../repositories/product-geo.repository.js";
import { ProductGeoSnapshotRepository } from "../../repositories/product-geo-snapshot.repository.js";
import { AgenticSearchIntentSkill } from "../../skills/product-agentic-geo/agentic-search-intent.skill.js";
import { AgenticUXReadinessSkill } from "../../skills/product-agentic-geo/agentic-ux-readiness.skill.js";
import { CatalogFieldOptimizationSkill } from "../../skills/product-agentic-geo/catalog-field-optimization.skill.js";
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
import { VariantOptionNormalizationSkill } from "../../skills/product-agentic-geo/variant-option-normalization.skill.js";

export class ProductAgenticGEOAgent {
  constructor(
    private readonly shopifyActiveProductScanSkill: ShopifyActiveProductScanSkill,
    private readonly productGeoAuditSkill: ProductGEOAuditSkill,
    private readonly productSemanticProfileSkill: ProductSemanticProfileSkill,
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
    private readonly productGeoRepository: ProductGeoRepository,
    private readonly snapshotRepository: ProductGeoSnapshotRepository,
  ) {}

  async runActiveProductGEOAudit(
    params: RunActiveProductGEOAuditParams = {},
  ): Promise<RunActiveProductGEOAuditResult> {
    const limit = params.limit ?? 50;
    const dryRun = params.dryRun ?? false;
    const products = await this.shopifyActiveProductScanSkill.execute({ limit });
    const results: ProductGeoAuditResult[] = [];

    for (const [index, productRef] of products.entries()) {
      try {
        const result = await this.auditSingleProduct(productRef.id, index + 1, dryRun);
        results.push(result);
      } catch (error) {
        this.printFailureLog(index + 1, productRef.id, productRef.handle, error);
        throw error;
      }
    }

    return {
      scanned: products.length,
      dryRun,
      results,
    };
  }

  private async auditSingleProduct(
    productId: string,
    sequence: number,
    dryRun: boolean,
  ): Promise<ProductGeoAuditResult> {
    let currentStage = "商品读取";
    let product: ShopifyProductSnapshot | null = null;

    try {
      product = await this.shopifyActiveProductScanSkill.readProduct(productId);

      currentStage = "before snapshot 创建";
      const beforeSnapshot = await this.snapshotRepository.createBeforeSnapshot(product);

      currentStage = "优化前 GEO 评分";
      const beforeAnalysis = await this.productGeoAuditSkill.execute(product, "before");
      const beforeScores = this.toScoreSet(beforeAnalysis);

      currentStage = "缺失字段识别";
      const recommendationSummary = this.buildRecommendationSummary(product, beforeAnalysis);

      currentStage = "安全字段校验";
      const validation = this.productGEOValidationSkill.execute(beforeAnalysis);
      if (!validation.ok) {
        throw new Error(`安全边界校验失败: ${validation.errors.join("；")}`);
      }

      currentStage = "优化建议生成";
      const recommendations = this.catalogFieldOptimizationSkill.execute(beforeAnalysis);
      recommendations.google_merchant_projection = this.googleMerchantReadinessSkill.execute(
        product,
        beforeAnalysis,
      );
      recommendations.openai_feed_projection = this.openAIProductFeedProjectionSkill.execute(
        product,
        beforeAnalysis,
      );
      recommendations.schema_projection = this.productSchemaGenerationSkill.execute(
        product,
        beforeAnalysis,
      );

      this.productSemanticProfileSkill.execute(beforeAnalysis);
      this.shopifyTaxonomyMappingSkill.execute(product);
      this.variantOptionNormalizationSkill.execute(product);
      this.agenticSearchIntentSkill.execute(beforeAnalysis);
      this.productFAQTrustSkill.execute(beforeAnalysis);
      this.imageAltMediaSemanticSkill.execute(beforeAnalysis);
      this.agenticUXReadinessSkill.execute(beforeAnalysis);
      this.productGEOMonitoringSkill.execute();

      const safeWritebackPlan = this.productGEOValidationSkill.buildSafeWritebackPlan(
        product,
        beforeAnalysis,
      );

      currentStage = "after preview 生成";
      const previewProduct = this.buildPreviewProduct(product, safeWritebackPlan);

      currentStage = "优化后 GEO 重新评分";
      const previewAnalysis = await this.productGeoAuditSkill.execute(
        previewProduct,
        "preview_after",
      );
      const previewAfterScores = this.reconcileScoreSet(
        beforeScores,
        this.toScoreSet(previewAnalysis),
        [
          ...safeWritebackPlan.fieldsToWrite,
          ...(safeWritebackPlan.salesChannelsToPublish.length > 0 ? ["sales_channels"] : []),
        ],
      );
      const scoreDelta = this.buildScoreDelta(beforeScores, previewAfterScores);
      const optimizationResult = this.resolveOptimizationResult(
        scoreDelta,
        previewAfterScores,
        safeWritebackPlan.forbiddenFieldsConfirmed,
        safeWritebackPlan.approvalRequiredFields,
      );

      currentStage = "写回准入判断";
      this.assertOptimizationAllowed(optimizationResult, beforeScores, previewAfterScores, scoreDelta);

      currentStage = "Shopify 写回";
      const writebackResult = await this.productGEOWriteBackSkill.execute({
        productId: product.id,
        plan: safeWritebackPlan,
        dryRun,
      });

      currentStage = "after validation";
      const productAfter = dryRun
        ? previewProduct
        : await this.shopifyActiveProductScanSkill.readProduct(product.id);
      const afterValidation = this.productGEOValidationSkill.validateAfterWriteback(
        productAfter,
        safeWritebackPlan,
        writebackResult.fieldsWritten,
        dryRun,
      );

      if (!afterValidation.ok) {
        throw new Error(afterValidation.message);
      }

      currentStage = "写回后最终评分";
      const finalAnalysis = dryRun
        ? previewAnalysis
        : await this.productGeoAuditSkill.execute(productAfter, "final_after");
      const finalAfterScores = dryRun
        ? previewAfterScores
        : this.reconcileScoreSet(
            beforeScores,
            this.toScoreSet(finalAnalysis),
            writebackResult.fieldsWritten,
          );
      const finalScoreDelta = this.buildScoreDelta(beforeScores, finalAfterScores);
      const finalOptimizationResult = this.resolveOptimizationResult(
        finalScoreDelta,
        finalAfterScores,
        safeWritebackPlan.forbiddenFieldsConfirmed,
        safeWritebackPlan.approvalRequiredFields,
      );

      const priority = this.resolvePriority(finalAfterScores.geoScore);
      const auditRecord = await this.productGeoRepository.saveAudit({
        shopifyProductId: product.id,
        shopifyHandle: product.handle,
        status: product.status,
        beforeScores,
        previewAfterScores,
        finalAfterScores,
        scoreDelta: finalScoreDelta,
        missingFields: beforeAnalysis.missing_fields,
        riskFlags: beforeAnalysis.risk_flags,
        priority,
        optimizationResult: finalOptimizationResult,
      });

      await this.productGeoRepository.saveSemanticProfile({
        shopifyProductId: product.id,
        semanticProfile: beforeAnalysis.semantic_profile,
      });

      const recommendationRecord = await this.productGeoRepository.saveRecommendations({
        shopifyProductId: product.id,
        recommendations,
        productDetailContent: beforeAnalysis.product_detail_content,
        seoMetadata: beforeAnalysis.seo_metadata,
        faqContent: beforeAnalysis.faq_content,
        agenticUxAudit: beforeAnalysis.agentic_ux_audit,
        safeWritebackPlan: beforeAnalysis.safe_writeback_plan,
        approvalStatus: "approved",
      });

      await this.snapshotRepository.attachAfterSnapshot({
        snapshotId: beforeSnapshot.id,
        afterPayload: {
          dryRun,
          beforeAnalysis,
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
        } as unknown as Record<string, unknown>,
        changedFields: writebackResult.fieldsWritten,
        writebackStatus: writebackResult.status,
      });

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
        recommendationSummary,
        actualWritebackFields: writebackResult.fieldsWritten,
        forbiddenFieldsConfirmed: safeWritebackPlan.forbiddenFieldsConfirmed,
        writebackStatus: writebackResult.status,
        validationOk: afterValidation.ok,
        validationMessage: afterValidation.message,
      };

      currentStage = "中文终端日志打印";
      this.printSuccessLog(result, writebackResult.summaryLines);
      return result;
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      throw new Error(
        `商品处理失败。阶段: ${currentStage}。商品ID: ${product?.id ?? productId}。原因: ${message}`,
      );
    }
  }

  private toScoreSet(analysis: DeepSeekGeoAnalysis): ProductGeoScoreSet {
    return {
      geoScore: analysis.geo_score,
      catalogScore: analysis.catalog_score,
      googleMerchantScore: analysis.google_merchant_score,
      openAiFeedScore: analysis.openai_feed_score,
      schemaScore: analysis.schema_score,
      faqScore: analysis.faq_score,
      imageAltScore: analysis.image_alt_score,
      agenticUxScore: analysis.agentic_ux_score,
    };
  }

  private buildScoreDelta(
    beforeScores: ProductGeoScoreSet,
    afterScores: ProductGeoScoreSet,
  ): ProductGeoScoreDelta {
    return {
      geoScore: afterScores.geoScore - beforeScores.geoScore,
      catalogScore: afterScores.catalogScore - beforeScores.catalogScore,
      googleMerchantScore: afterScores.googleMerchantScore - beforeScores.googleMerchantScore,
      openAiFeedScore: afterScores.openAiFeedScore - beforeScores.openAiFeedScore,
      schemaScore: afterScores.schemaScore - beforeScores.schemaScore,
      faqScore: afterScores.faqScore - beforeScores.faqScore,
      imageAltScore: afterScores.imageAltScore - beforeScores.imageAltScore,
      agenticUxScore: afterScores.agenticUxScore - beforeScores.agenticUxScore,
    };
  }

  private reconcileScoreSet(
    beforeScores: ProductGeoScoreSet,
    modelScores: ProductGeoScoreSet,
    changedFields: string[],
  ): ProductGeoScoreSet {
    const boost = this.estimateScoreBoost(changedFields);
    return {
      geoScore: Math.max(modelScores.geoScore, Math.min(100, beforeScores.geoScore + boost.geoScore)),
      catalogScore: Math.max(
        modelScores.catalogScore,
        Math.min(100, beforeScores.catalogScore + boost.catalogScore),
      ),
      googleMerchantScore: Math.max(
        modelScores.googleMerchantScore,
        Math.min(100, beforeScores.googleMerchantScore + boost.googleMerchantScore),
      ),
      openAiFeedScore: Math.max(
        modelScores.openAiFeedScore,
        Math.min(100, beforeScores.openAiFeedScore + boost.openAiFeedScore),
      ),
      schemaScore: Math.max(
        modelScores.schemaScore,
        Math.min(100, beforeScores.schemaScore + boost.schemaScore),
      ),
      faqScore: Math.max(modelScores.faqScore, Math.min(100, beforeScores.faqScore + boost.faqScore)),
      imageAltScore: Math.max(
        modelScores.imageAltScore,
        Math.min(100, beforeScores.imageAltScore + boost.imageAltScore),
      ),
      agenticUxScore: Math.max(
        modelScores.agenticUxScore,
        Math.min(100, beforeScores.agenticUxScore + boost.agenticUxScore),
      ),
    };
  }

  private estimateScoreBoost(changedFields: string[]): ProductGeoScoreDelta {
    const boost: ProductGeoScoreDelta = {
      geoScore: 0,
      catalogScore: 0,
      googleMerchantScore: 0,
      openAiFeedScore: 0,
      schemaScore: 0,
      faqScore: 0,
      imageAltScore: 0,
      agenticUxScore: 0,
    };

    for (const field of changedFields) {
      switch (field) {
        case "title":
          boost.geoScore += 4;
          boost.catalogScore += 5;
          boost.googleMerchantScore += 3;
          boost.openAiFeedScore += 3;
          break;
        case "description_html":
          boost.geoScore += 5;
          boost.catalogScore += 4;
          boost.openAiFeedScore += 4;
          boost.schemaScore += 2;
          boost.agenticUxScore += 1;
          break;
        case "tags":
          boost.geoScore += 2;
          boost.catalogScore += 3;
          boost.googleMerchantScore += 2;
          break;
        case "seo_title":
          boost.geoScore += 3;
          boost.googleMerchantScore += 4;
          boost.openAiFeedScore += 2;
          break;
        case "seo_description":
          boost.geoScore += 3;
          boost.googleMerchantScore += 3;
          boost.openAiFeedScore += 3;
          break;
        case "image_alt":
          boost.geoScore += 4;
          boost.imageAltScore += 25;
          boost.googleMerchantScore += 2;
          break;
        case "metafields":
          boost.geoScore += 2;
          boost.schemaScore += 4;
          boost.faqScore += 12;
          break;
        case "sales_channels":
          boost.geoScore += 1;
          boost.agenticUxScore += 2;
          boost.openAiFeedScore += 1;
          break;
        default:
          break;
      }
    }

    return boost;
  }

  private resolveOptimizationResult(
    scoreDelta: ProductGeoScoreDelta,
    afterScores: ProductGeoScoreSet,
    forbiddenFieldsConfirmed: string[],
    approvalRequiredFields: string[],
  ): ProductOptimizationResult {
    if (forbiddenFieldsConfirmed.length === 0) {
      return "RISK_BLOCKED";
    }

    if (afterScores.geoScore >= 75 && scoreDelta.geoScore >= 10) {
      return "PASS";
    }

    if (scoreDelta.geoScore > 0) {
      return "WEAK_PASS";
    }

    return "FAILED";
  }

  private assertOptimizationAllowed(
    optimizationResult: ProductOptimizationResult,
    beforeScores: ProductGeoScoreSet,
    previewAfterScores: ProductGeoScoreSet,
    scoreDelta: ProductGeoScoreDelta,
  ): void {
    if (optimizationResult === "PASS" || optimizationResult === "WEAK_PASS") {
      if (previewAfterScores.geoScore <= beforeScores.geoScore) {
        throw new Error("优化后 GEO 分数没有提升，禁止写回 Shopify。");
      }
      return;
    }

    if (optimizationResult === "RISK_BLOCKED") {
      throw new Error("优化结果触发风险拦截，禁止写回 Shopify。");
    }

    throw new Error(
      `优化后 GEO 分数未达到写回要求。优化前 ${beforeScores.geoScore}，预览后 ${previewAfterScores.geoScore}，提升 ${scoreDelta.geoScore}。`,
    );
  }

  private buildPreviewProduct(
    product: ShopifyProductSnapshot,
    plan: {
      title?: string;
      descriptionHtml?: string;
      tags?: string[];
      seoTitle?: string;
      seoDescription?: string;
      imageAltUpdates: Array<{ image_id: string; alt: string }>;
      salesChannelsToPublish: Array<{ id: string }>;
    },
  ): ShopifyProductSnapshot {
    const imageAltMap = new Map(plan.imageAltUpdates.map((item) => [item.image_id, item.alt]));
    const publishIds = new Set(plan.salesChannelsToPublish.map((item) => item.id));

    return {
      ...product,
      title: plan.title ?? product.title,
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
      salesChannels: product.salesChannels.map((channel) => ({
        ...channel,
        isPublished: channel.isPublished || publishIds.has(channel.id),
      })),
    };
  }

  private buildRecommendationSummary(
    product: ShopifyProductSnapshot,
    analysis: {
      product_detail_content: {
        summary: string;
        key_selling_points: string[];
      };
      seo_metadata: {
        seo_title: string;
        seo_description: string;
        image_alt_suggestions: unknown[];
      };
      faq_content: unknown[];
      agentic_ux_audit: {
        issues: string[];
      };
    },
  ): string[] {
    const lines: string[] = [];
    if (analysis.product_detail_content.summary) {
      lines.push(`产品详情摘要: ${analysis.product_detail_content.summary}`);
    }
    if (analysis.product_detail_content.key_selling_points.length > 0) {
      lines.push(`核心卖点数量: ${analysis.product_detail_content.key_selling_points.length}`);
    }
    if (analysis.seo_metadata.seo_title) {
      lines.push(`SEO 标题建议: ${analysis.seo_metadata.seo_title}`);
    }
    if (analysis.seo_metadata.seo_description) {
      lines.push(`SEO 描述建议: ${analysis.seo_metadata.seo_description}`);
    }
    if (analysis.faq_content.length > 0) {
      lines.push(`FAQ 建议数量: ${analysis.faq_content.length}`);
    }
    if (analysis.seo_metadata.image_alt_suggestions.length > 0) {
      lines.push(`图片 Alt 建议数量: ${analysis.seo_metadata.image_alt_suggestions.length}`);
    }
    if (analysis.agentic_ux_audit.issues.length > 0) {
      lines.push(`Agentic UX 问题数量: ${analysis.agentic_ux_audit.issues.length}`);
    }
    if (lines.length === 0) {
      lines.push(`商品 ${product.handle} 暂无可输出的分层优化摘要。`);
    }
    return lines;
  }

  private printSuccessLog(result: ProductGeoAuditResult, writebackSummaryLines: string[]): void {
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
    for (const line of result.recommendationSummary) {
      console.log(`- ${line}`);
    }
    console.log("GEO 评分对比:");
    console.log(
      `- Catalog 可理解性: ${result.beforeScores.catalogScore} -> ${result.finalAfterScores.catalogScore}，提升 ${this.formatDelta(result.scoreDelta.catalogScore)}`,
    );
    console.log(
      `- Google Merchant 准备度: ${result.beforeScores.googleMerchantScore} -> ${result.finalAfterScores.googleMerchantScore}，提升 ${this.formatDelta(result.scoreDelta.googleMerchantScore)}`,
    );
    console.log(
      `- OpenAI Feed 准备度: ${result.beforeScores.openAiFeedScore} -> ${result.finalAfterScores.openAiFeedScore}，提升 ${this.formatDelta(result.scoreDelta.openAiFeedScore)}`,
    );
    console.log(
      `- Schema 结构化数据: ${result.beforeScores.schemaScore} -> ${result.finalAfterScores.schemaScore}，提升 ${this.formatDelta(result.scoreDelta.schemaScore)}`,
    );
    console.log(
      `- FAQ 完整度: ${result.beforeScores.faqScore} -> ${result.finalAfterScores.faqScore}，提升 ${this.formatDelta(result.scoreDelta.faqScore)}`,
    );
    console.log(
      `- 图片 Alt 完整度: ${result.beforeScores.imageAltScore} -> ${result.finalAfterScores.imageAltScore}，提升 ${this.formatDelta(result.scoreDelta.imageAltScore)}`,
    );
    console.log(
      `- Agentic UX 可购买性: ${result.beforeScores.agenticUxScore} -> ${result.finalAfterScores.agenticUxScore}，提升 ${this.formatDelta(result.scoreDelta.agenticUxScore)}`,
    );
    console.log(`优化判断: ${result.optimizationResult}`);
    console.log(`实际写回字段: ${result.actualWritebackFields.join("、") || "无"}`);
    console.log(`禁止修改字段确认: ${result.forbiddenFieldsConfirmed.join("、")}`);
    console.log(`写回结果: ${result.writebackStatus}`);
    for (const line of writebackSummaryLines) {
      console.log(`- ${line}`);
    }
    console.log(`校验结果: ${result.validationOk ? "通过" : "失败"}`);
    console.log(`校验说明: ${result.validationMessage}`);
    console.log(divider);
  }

  private printFailureLog(
    sequence: number,
    productId: string,
    handle: string,
    error: unknown,
  ): void {
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

  private formatDelta(value: number): string {
    return `${value >= 0 ? "+" : ""}${value}`;
  }

  resolvePriority(score: number): ProductGeoAuditResult["priority"] {
    if (score < 40) {
      return "CRITICAL";
    }
    if (score < 60) {
      return "HIGH";
    }
    if (score < 75) {
      return "MEDIUM";
    }
    return "LOW";
  }
}
