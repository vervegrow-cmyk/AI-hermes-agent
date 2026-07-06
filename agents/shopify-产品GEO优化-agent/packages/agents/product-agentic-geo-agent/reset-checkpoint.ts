import { bootstrapEnv } from "./env-loader.js";
import { ProductGeoCheckpointRepository } from "../../repositories/product-geo-checkpoint.repository.js";

async function main(): Promise<void> {
  bootstrapEnv();

  const repository = new ProductGeoCheckpointRepository();
  const resetCount = await repository.resetIncompleteRuns();

  console.log(`已重置未完成 checkpoint 数量: ${resetCount}`);
  console.log("历史 audit、snapshot、recommendation、execution log 不会被删除。");
}

main().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(`重置 checkpoint 失败: ${message}`);
  process.exitCode = 1;
});
