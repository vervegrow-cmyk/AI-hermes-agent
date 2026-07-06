import { bootstrapEnv } from "./env-loader.js";
import { ProductGeoRepository } from "../../repositories/product-geo.repository.js";
import { ProjectionExportService } from "../../services/projection-export.service.js";

function parseArg(name: string): string | undefined {
  return process.argv.slice(2).find((item) => item.startsWith(`--${name}=`))?.split("=")[1];
}

async function main(): Promise<void> {
  bootstrapEnv();

  const recommendationId = parseArg("recommendation-id");
  const productId = parseArg("product-id");

  if (!recommendationId && !productId) {
    throw new Error("必须提供 --recommendation-id 或 --product-id。");
  }

  const repository = new ProductGeoRepository();
  const exporter = new ProjectionExportService();

  const recommendation = recommendationId
    ? await repository.getRecommendationById(recommendationId)
    : await repository.getLatestRecommendationByProductId(productId ?? "");

  if (!recommendation) {
    throw new Error("未找到可导出的 recommendation 记录。");
  }

  const audit = await repository.getLatestAuditByProductId(recommendation.shopifyProductId);
  const semanticProfile = await repository.getLatestSemanticProfileByProductId(
    recommendation.shopifyProductId,
  );
  const exportResult = await exporter.exportRecommendationBundle(
    recommendation,
    (semanticProfile?.semanticProfile as unknown as Record<string, unknown> | null) ?? null,
    audit
      ? {
          beforeScores: audit.beforeScores,
          previewAfterScores: audit.previewAfterScores,
          finalAfterScores: audit.finalAfterScores,
          scoreDelta: audit.scoreDelta,
          optimizationResult: audit.optimizationResult,
        }
      : null,
  );

  console.log("导出完成。");
  console.log(`导出目录: ${exportResult.directory}`);
  for (const file of exportResult.files) {
    console.log(`- ${file}`);
  }
}

main().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(`ProductAgenticGEOAgent 导出失败: ${message}`);
  process.exitCode = 1;
});
