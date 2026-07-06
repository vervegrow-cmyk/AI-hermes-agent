import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

import { ProductGeoRecommendationRecord } from "../agents/product-agentic-geo-agent/product-agentic-geo.types.js";

export class ProjectionExportService {
  private readonly exportDir = path.resolve(process.cwd(), "runtime-exports");

  async exportRecommendationBundle(
    recommendation: ProductGeoRecommendationRecord,
    semanticProfile?: Record<string, unknown> | null,
    audit?: {
      beforeScores: unknown;
      previewAfterScores: unknown;
      finalAfterScores: unknown;
      scoreDelta: unknown;
      optimizationResult: string;
    } | null,
  ): Promise<{
    directory: string;
    files: string[];
  }> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    const safeProductId = recommendation.shopifyProductId.replace(/[^\w-]+/g, "_");
    const targetDir = path.join(this.exportDir, `${timestamp}-${safeProductId}`);

    await mkdir(targetDir, { recursive: true });

    const files = [
      {
        name: "google-merchant-projection.json",
        data: recommendation.recommendedGoogleMerchant,
      },
      {
        name: "openai-product-feed-projection.json",
        data: recommendation.recommendedOpenAiFeed,
      },
      {
        name: "schema-projection.json",
        data: recommendation.recommendedSchema,
      },
      {
        name: "faq-content.json",
        data: recommendation.faqContent,
      },
      {
        name: "semantic-profile.json",
        data: semanticProfile ?? {},
      },
      {
        name: "product-detail-content.json",
        data: recommendation.productDetailContent,
      },
      {
        name: "search-intents.json",
        data: recommendation.searchIntents,
      },
      {
        name: "summary.json",
        data: {
          recommendationId: recommendation.id,
          shopifyProductId: recommendation.shopifyProductId,
          seoMetadata: recommendation.seoMetadata,
          safeWritebackPlan: recommendation.safeWritebackPlan,
          approvalStatus: recommendation.approvalStatus,
          audit,
        },
      },
    ];

    for (const file of files) {
      await writeFile(path.join(targetDir, file.name), JSON.stringify(file.data, null, 2), "utf8");
    }

    return {
      directory: targetDir,
      files: files.map((file) => path.join(targetDir, file.name)),
    };
  }
}
