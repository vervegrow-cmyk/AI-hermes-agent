import { bootstrapEnv } from "./env-loader.js";
import { createProductAgenticGEORouter } from "./index.js";
import { ProductGeoCheckpointRepository } from "../../repositories/product-geo-checkpoint.repository.js";

function findArgValue(args: string[], name: string): string | undefined {
  const exact = `--${name}`;
  const prefixed = `--${name}=`;

  for (let index = args.length - 1; index >= 0; index -= 1) {
    const arg = args[index];
    if (arg.startsWith(prefixed)) {
      return arg.slice(prefixed.length);
    }
    if (arg === exact) {
      return args[index + 1];
    }
  }

  return undefined;
}

function parseNumber(value: string | undefined, fallback: number): number {
  if (!value) return fallback;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

async function main(): Promise<void> {
  bootstrapEnv();

  const args = process.argv.slice(2);
  const allowPartialWriteback = args.includes("--allow-partial-writeback");
  const strictPassOnly = args.includes("--strict-pass-only");
  const forceRetryFailed = args.includes("--force-retry-failed");
  const skipUnqualified = args.includes("--skip-unqualified");
  const aggressiveGeoOptimization = true;
  const autoFillMissingFields = true;
  const publishRegardlessScore = true;
  const forcePublishAfterOptimization = true;
  const continueIfBelowTarget = true;
  const sourceFirst = true;
  const policySecond = true;
  const deepseekLast = true;
  const deepseekContentOnly = true;
  const lockSourceTruthFields = true;
  const lockBusinessPolicyFields = true;
  const limit = parseNumber(findArgValue(args, "limit"), 50);
  const maxReoptimizeAttempts = parseNumber(findArgValue(args, "max-reoptimize-attempts"), 3);
  const targetGeoScore = parseNumber(findArgValue(args, "target-geo-score"), 85);
  const minimumPassScore = parseNumber(findArgValue(args, "minimum-pass-score"), 75);
  const scoreGateMode = (findArgValue(args, "score-gate-mode") ?? "advisory").toLowerCase();

  const checkpointRepository = new ProductGeoCheckpointRepository();
  const run = await checkpointRepository.getLatestResumableRun();

  if (!run) {
    console.log("当前没有可恢复的任务。");
    return;
  }

  const fromProductId = forceRetryFailed
    ? run.lastErrorProductId || run.currentProductId
    : run.currentProductId || run.lastErrorProductId;

  console.log("========================================");
  console.log("开始断点续传 ProductAgenticGEOAgent");
  console.log("========================================");
  console.log(`run_id: ${run.id}`);
  console.log(`mode: ${run.mode}`);
  console.log(`上次停止商品: ${fromProductId || "无"}`);
  console.log(`上次停止阶段: ${run.currentStage || run.lastErrorStage || "无"}`);
  console.log(`force_retry_failed: ${forceRetryFailed ? "已启用" : "未启用"}`);

  const router = createProductAgenticGEORouter();
  const result = await router.runActiveProductGEOAudit({
    runId: run.id,
    limit,
    dryRun: run.mode === "dry-run",
    allowPartialWriteback,
    strictPassOnly,
    maxReoptimizeAttempts,
    skipUnqualified,
    fromProductId: fromProductId || undefined,
    forceRetryFailed,
    aggressiveGeoOptimization,
    autoFillMissingFields,
    targetGeoScore,
    minimumPassScore,
    publishRegardlessScore,
    scoreGateMode: scoreGateMode === "advisory" ? "advisory" : "strict",
    forcePublishAfterOptimization,
    continueIfBelowTarget,
    sourceFirst,
    policySecond,
    deepseekLast,
    deepseekContentOnly,
    lockSourceTruthFields,
    lockBusinessPolicyFields,
  });

  console.log(`断点续传完成。总扫描商品数: ${result.scanned}`);
}

main().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(`断点续传失败: ${message}`);
  process.exitCode = 1;
});
