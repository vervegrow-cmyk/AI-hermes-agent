import { bootstrapEnv } from "./env-loader.js";
import { createProductAgenticGEORouter } from "./index.js";

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

function parseBoolean(value: string | undefined, fallback: boolean): boolean {
  if (value === undefined) {
    return fallback;
  }
  return value.toLowerCase() === "true";
}

function parseNumber(value: string | undefined, fallback: number): number {
  if (!value) {
    return fallback;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function firstNonEmpty(...values: Array<string | undefined | null>): string {
  for (const value of values) {
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }
  return "";
}

function printPreflight(
  limit: number,
  dryRun: boolean,
  allowPartialWriteback: boolean,
  strictPassOnly: boolean,
  maxReoptimizeAttempts: number,
  skipUnqualified: boolean,
  sourceEnrichmentEnabled: boolean,
  sourceType: string,
  requireSourceEnrichment: boolean,
  aggressiveGeoOptimization: boolean,
  autoFillMissingFields: boolean,
  targetGeoScore: number,
  minimumPassScore: number,
  publishRegardlessScore: boolean,
  scoreGateMode: string,
  forcePublishAfterOptimization: boolean,
  continueIfBelowTarget: boolean,
  sourceFirst: boolean,
  policySecond: boolean,
  deepseekLast: boolean,
  deepseekContentOnly: boolean,
  lockSourceTruthFields: boolean,
  lockBusinessPolicyFields: boolean,
): void {
  const divider = "-".repeat(88);
  const shopDomain = firstNonEmpty(
    process.env.SHOPIFY_SHOP_DOMAIN,
    process.env.SHOPIFY_STORE,
    process.env.SHOPIFY_SHOP,
  );
  const authMode = (process.env.SHOPIFY_AUTH_MODE ?? "custom_admin_token").trim().toLowerCase();
  const hasAdminToken = Boolean(
    (process.env.SHOPIFY_ADMIN_ACCESS_TOKEN ?? "").trim() ||
      (process.env.SHOPIFY_TOKEN ?? "").trim(),
  );
  const hasClientCredentials = Boolean(
    (process.env.SHOPIFY_CLIENT_ID ?? "").trim() &&
      (process.env.SHOPIFY_CLIENT_SECRET ?? "").trim(),
  );
  const hasDeepSeek = Boolean((process.env.DEEPSEEK_API_KEY ?? "").trim());

  console.log(divider);
  console.log("\u5f00\u59cb\u6267\u884c ProductAgenticGEOAgent \u4e32\u884c\u6a21\u5f0f\u4efb\u52a1");
  console.log(`\u53c2\u6570: limit=${limit}, dryRun=${dryRun}`);
  console.log(`\u6267\u884c\u6a21\u5f0f: \u4e25\u683c\u4e32\u884c\uff0c\u4e00\u6b21\u53ea\u5904\u7406\u4e00\u4e2a\u5546\u54c1`);
  console.log(`Shopify \u5e97\u94fa: ${shopDomain || "\u672a\u914d\u7f6e"}`);
  console.log(`Shopify \u8ba4\u8bc1\u6a21\u5f0f: ${authMode}`);
  console.log(`Shopify Admin Token: ${hasAdminToken ? "\u5df2\u914d\u7f6e" : "\u672a\u914d\u7f6e"}`);
  console.log(`Shopify Client Credentials: ${hasClientCredentials ? "\u5df2\u914d\u7f6e" : "\u672a\u914d\u7f6e"}`);
  console.log(`DeepSeek API Key: ${hasDeepSeek ? "\u5df2\u914d\u7f6e" : "\u672a\u914d\u7f6e"}`);
  console.log(
    `Partial Writeback: ${
      allowPartialWriteback ? "\u5df2\u542f\u7528" : "\u672a\u542f\u7528"
    }`,
  );
  console.log(
    `Strict Pass Only: ${strictPassOnly ? "\u5df2\u542f\u7528" : "\u672a\u542f\u7528"}`,
  );
  console.log(`Max Reoptimize Attempts: ${maxReoptimizeAttempts}`);
  console.log(`Skip Unqualified: ${skipUnqualified ? "\u5df2\u542f\u7528" : "\u672a\u542f\u7528"}`);
  console.log(
    `Source Enrichment: ${sourceEnrichmentEnabled ? "\u5df2\u542f\u7528" : "\u672a\u542f\u7528"}`,
  );
  console.log(`Source Type: ${sourceType}`);
  console.log(
    `Require Source Enrichment: ${
      requireSourceEnrichment ? "\u5df2\u542f\u7528" : "\u672a\u542f\u7528"
    }`,
  );
  console.log(
    `Aggressive GEO Optimization: ${
      aggressiveGeoOptimization ? "\u5df2\u542f\u7528" : "\u672a\u542f\u7528"
    }`,
  );
  console.log(
    `Auto Fill Missing Fields: ${
      autoFillMissingFields ? "\u5df2\u542f\u7528" : "\u672a\u542f\u7528"
    }`,
  );
  console.log(`Target GEO Score: ${targetGeoScore}`);
  console.log(`Minimum Pass Score: ${minimumPassScore}`);
  console.log(`Publish Regardless Score: ${publishRegardlessScore ? "\u5df2\u542f\u7528" : "\u672a\u542f\u7528"}`);
  console.log(`Score Gate Mode: ${scoreGateMode}`);
  console.log(`Force Publish After Optimization: ${forcePublishAfterOptimization ? "\u5df2\u542f\u7528" : "\u672a\u542f\u7528"}`);
  console.log(`Continue If Below Target: ${continueIfBelowTarget ? "\u5df2\u542f\u7528" : "\u672a\u542f\u7528"}`);
  console.log(`Source First: ${sourceFirst ? "\u5df2\u542f\u7528" : "\u672a\u542f\u7528"}`);
  console.log(`Policy Second: ${policySecond ? "\u5df2\u542f\u7528" : "\u672a\u542f\u7528"}`);
  console.log(`DeepSeek Last: ${deepseekLast ? "\u5df2\u542f\u7528" : "\u672a\u542f\u7528"}`);
  console.log(`DeepSeek Content Only: ${deepseekContentOnly ? "\u5df2\u542f\u7528" : "\u672a\u542f\u7528"}`);
  console.log(`Lock Source Truth Fields: ${lockSourceTruthFields ? "\u5df2\u542f\u7528" : "\u672a\u542f\u7528"}`);
  console.log(`Lock Business Policy Fields: ${lockBusinessPolicyFields ? "\u5df2\u542f\u7528" : "\u672a\u542f\u7528"}`);
  console.log(
    `\u5199\u56de\u6a21\u5f0f: ${
      dryRun
        ? "Dry Run \u9884\u89c8\uff0c\u4e0d\u771f\u5b9e\u5199\u56de"
        : "\u771f\u5b9e\u5199\u56de\u6a21\u5f0f"
    }`,
  );
  console.log(divider);
}

async function main(): Promise<void> {
  bootstrapEnv();

  const args = process.argv.slice(2);
  const allowPartialWriteback = args.includes("--allow-partial-writeback");
  const strictPassOnly = args.includes("--strict-pass-only");
  const skipUnqualified = args.includes("--skip-unqualified");
  const enableSourceEnrichment = true;
  const disableSourceEnrichment = args.includes("--disable-source-enrichment");
  const requireSourceEnrichment = args.includes("--require-source-enrichment");
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

  const limit = parseNumber(findArgValue(args, "limit"), 10);
  const dryRun = parseBoolean(findArgValue(args, "dry-run"), false);
  const fromProductId = findArgValue(args, "from-product-id");
  const maxReoptimizeAttempts = parseNumber(findArgValue(args, "max-reoptimize-attempts"), 3);
  const sourceType = (findArgValue(args, "source-type") ?? "AUTO").toUpperCase();
  const targetGeoScore = parseNumber(findArgValue(args, "target-geo-score"), 85);
  const minimumPassScore = parseNumber(findArgValue(args, "minimum-pass-score"), 75);
  const scoreGateMode = (findArgValue(args, "score-gate-mode") ?? "advisory").toLowerCase();
  const sourceEnrichmentEnabled = disableSourceEnrichment ? false : enableSourceEnrichment;

  printPreflight(
    limit,
    dryRun,
    allowPartialWriteback,
    strictPassOnly,
    maxReoptimizeAttempts,
    skipUnqualified,
    sourceEnrichmentEnabled,
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
  );
  if (fromProductId) {
    console.log(`从指定商品开始执行: ${fromProductId}`);
  }

  const router = createProductAgenticGEORouter();
  const result = await router.runActiveProductGEOAudit({
    limit,
    dryRun,
    allowPartialWriteback,
    strictPassOnly,
    maxReoptimizeAttempts,
    skipUnqualified,
    fromProductId,
    enableSourceEnrichment: sourceEnrichmentEnabled,
    disableSourceEnrichment,
    sourceType: sourceType as "AUTO" | "GIGA" | "DOBA" | "UNKNOWN",
    requireSourceEnrichment,
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

  console.log("\u5168\u90e8\u5546\u54c1\u5904\u7406\u5b8c\u6210\u3002");
  console.log(`\u603b\u626b\u63cf\u5546\u54c1\u6570: ${result.scanned}`);
  console.log(`Dry Run: ${result.dryRun}`);
  console.log(`\u6210\u529f\u5904\u7406\u5546\u54c1\u6570: ${result.results.length}`);
}

main().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(`ProductAgenticGEOAgent \u6267\u884c\u5931\u8d25: ${message}`);
  process.exitCode = 1;
});
