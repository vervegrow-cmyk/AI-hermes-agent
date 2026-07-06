import { bootstrapEnv } from "./env-loader.js";
import { ProductGeoSnapshotRepository } from "../../repositories/product-geo-snapshot.repository.js";
import { ShopifyProductGeoService } from "../../services/shopify-product-geo.service.js";
import { ShopifyProductSnapshot } from "./product-agentic-geo.types.js";

function parseArg(name: string): string | undefined {
  return process.argv.slice(2).find((item) => item.startsWith(`--${name}=`))?.split("=")[1];
}

async function main(): Promise<void> {
  bootstrapEnv();

  const snapshotId = parseArg("snapshot-id");
  if (!snapshotId) {
    throw new Error("缺少 --snapshot-id 参数。");
  }

  const snapshotRepository = new ProductGeoSnapshotRepository();
  const shopifyService = new ShopifyProductGeoService();
  const snapshot = await snapshotRepository.getSnapshot(snapshotId);

  if (!snapshot) {
    throw new Error(`未找到 snapshot: ${snapshotId}`);
  }

  const productBefore = snapshot.beforePayload as unknown as ShopifyProductSnapshot;

  console.log("开始执行回滚...");
  console.log(`Snapshot ID: ${snapshotId}`);
  console.log(`Shopify Product ID: ${snapshot.shopifyProductId}`);

  try {
    const result = await shopifyService.rollbackProductSnapshot(productBefore);
    await snapshotRepository.markRolledBack(snapshotId, "rolled_back");

    console.log("回滚完成。");
    console.log(`恢复字段: ${result.restoredFields.join("、") || "无"}`);
    console.log(`取消发布渠道: ${result.unpublishedChannelNames.join("、") || "无"}`);
  } catch (error) {
    await snapshotRepository.markRolledBack(snapshotId, "rollback_failed");
    throw error;
  }
}

main().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(`ProductAgenticGEOAgent 回滚失败: ${message}`);
  process.exitCode = 1;
});
