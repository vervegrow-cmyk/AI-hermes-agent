import { bootstrapEnv } from "./env-loader.js";
import { ProductGeoCheckpointRepository } from "../../repositories/product-geo-checkpoint.repository.js";

async function main(): Promise<void> {
  bootstrapEnv();

  const repository = new ProductGeoCheckpointRepository();
  const run = (await repository.getLatestResumableRun()) ?? (await repository.getLatestRun());

  if (!run) {
    console.log("当前还没有 ProductAgenticGEOAgent 任务记录。");
    return;
  }

  console.log("========================================");
  console.log("ProductAgenticGEOAgent 最近任务状态");
  console.log("========================================");
  console.log(`run_id: ${run.id}`);
  console.log(`mode: ${run.mode}`);
  console.log(`status: ${run.status}`);
  console.log(`total_products: ${run.totalProducts}`);
  console.log(`completed_count: ${run.completedCount}`);
  console.log(`partial_pass_count: ${run.partialPassCount}`);
  console.log(`blocked_writeback_count: ${run.blockedWritebackCount}`);
  console.log(`failed_count: ${run.failedCount}`);
  console.log(`reoptimize_count: ${run.reoptimizeCount ?? 0}`);
  console.log(`max_reoptimize_attempts: ${run.maxReoptimizeAttempts ?? 0}`);
  console.log(`current_reoptimize_attempt: ${run.currentReoptimizeAttempt ?? 0}`);
  console.log(`unqualified_count: ${run.unqualifiedCount ?? 0}`);
  console.log(`skipped_unqualified_count: ${run.skippedUnqualifiedCount ?? 0}`);
  console.log(`need_manual_data_count: ${run.needManualDataCount ?? 0}`);
  console.log(`current_index: ${run.currentIndex}`);
  console.log(`current_product_id: ${run.currentProductId || "无"}`);
  console.log(`current_handle: ${run.currentHandle || "无"}`);
  console.log(`current_stage: ${run.currentStage || "无"}`);
  console.log(`last_error_stage: ${run.lastErrorStage || "无"}`);
  console.log(`last_error_message: ${run.lastErrorMessage || "无"}`);
  console.log(`resume_enabled: ${run.resumeEnabled ? "是" : "否"}`);
  const checkpoints = await repository.getProductCheckpointsByRunId(run.id);
  const currentCheckpoint =
    checkpoints.find((item) => item.shopifyProductId === run.currentProductId) ??
    checkpoints[checkpoints.length - 1];
  if (currentCheckpoint) {
    console.log(`product_checkpoint_stage: ${currentCheckpoint.currentStage || "无"}`);
    console.log(`product_reoptimize_attempt: ${currentCheckpoint.reoptimizeAttempt ?? 0}`);
    console.log(
      `product_max_reoptimize_attempts: ${currentCheckpoint.maxReoptimizeAttempts ?? 0}`,
    );
    console.log(`product_reoptimize_reason: ${currentCheckpoint.reoptimizeReason || "无"}`);
    console.log(
      `product_failed_modules: ${
        (currentCheckpoint.failedModulesJson ?? []).length > 0
          ? currentCheckpoint.failedModulesJson.join(", ")
          : "无"
      }`,
    );
    console.log(
      `product_manual_required_fields: ${
        (currentCheckpoint.manualRequiredFieldsJson ?? []).length > 0
          ? currentCheckpoint.manualRequiredFieldsJson.join(", ")
          : "无"
      }`,
    );
  }
  console.log("resume command: npm run shopify:geo:resume");
}

main().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(`查看任务状态失败: ${message}`);
  process.exitCode = 1;
});
