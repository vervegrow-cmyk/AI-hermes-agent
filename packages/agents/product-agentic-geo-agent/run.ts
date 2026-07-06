import { createProductAgenticGEORouter } from "./index.js";

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

function printPreflight(limit: number, dryRun: boolean): void {
  const divider = "-".repeat(88);
  const shopDomain =
    process.env.SHOPIFY_SHOP_DOMAIN ??
    process.env.SHOPIFY_STORE ??
    process.env.SHOPIFY_SHOP ??
    "";
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
    `\u5199\u56de\u6a21\u5f0f: ${
      dryRun
        ? "Dry Run \u9884\u89c8\uff0c\u4e0d\u771f\u5b9e\u5199\u56de"
        : "\u771f\u5b9e\u5199\u56de\u6a21\u5f0f"
    }`,
  );
  console.log(divider);
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const limitArg = args.find((item) => item.startsWith("--limit="));
  const dryRunArg = args.find((item) => item.startsWith("--dry-run="));

  const limit = parseNumber(limitArg?.split("=")[1], 10);
  const dryRun = parseBoolean(dryRunArg?.split("=")[1], false);

  printPreflight(limit, dryRun);

  const router = createProductAgenticGEORouter();
  const result = await router.runActiveProductGEOAudit({ limit, dryRun });

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
