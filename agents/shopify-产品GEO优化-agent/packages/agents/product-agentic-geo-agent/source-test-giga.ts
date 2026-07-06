import { bootstrapEnv } from "./env-loader.js";
import { runGigaSourceTest } from "../../services/upstream-source-test.service.js";

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

function printReport(report: Awaited<ReturnType<typeof runGigaSourceTest>>): void {
  console.log("========================================");
  console.log("GIGA 上游商品数据测试完成");
  console.log("========================================");
  console.log(`请求结果: ${report.ok ? "成功" : "失败"}`);
  console.log(`HTTP 状态: ${report.status}`);
  console.log(`接口路径: ${report.endpoint}`);
  console.log(`响应落盘: ${report.outputPath}`);
  console.log("GEO 相关字段识别:");
  if (report.geoSignalSummary.matchedPaths.length === 0) {
    console.log("- 当前响应里还没有识别到明显的 GEO 结构字段");
  } else {
    for (const line of report.geoSignalSummary.matchedPaths) {
      console.log(`- ${line}`);
    }
  }
  if (report.geoSignalSummary.missingSignals.length > 0) {
    console.log(`仍缺少的关键维度: ${report.geoSignalSummary.missingSignals.join("、")}`);
  }
  console.log("响应预览:");
  console.log(JSON.stringify(report.responsePreview, null, 2));
}

async function main(): Promise<void> {
  bootstrapEnv();

  const args = process.argv.slice(2);
  const endpoint =
    findArgValue(args, "endpoint") ??
    process.env.GIGA_SOURCE_TEST_ENDPOINT ??
    "/b2b-overseas-api/v1/buyer/inventory/quantity/v2";
  const sku = findArgValue(args, "sku") ?? process.env.GIGA_SOURCE_TEST_SKU ?? "";
  const method = (findArgValue(args, "method") ?? "POST").toUpperCase();
  const bodyJson = findArgValue(args, "body-json");

  let body: unknown = undefined;
  if (bodyJson) {
    body = JSON.parse(bodyJson);
  } else if (sku) {
    body = { skus: [sku] };
  } else if (method !== "GET") {
    body = { skus: [] };
  }

  console.log("开始测试 GIGA 上游接口...");
  console.log(`接口路径: ${endpoint}`);
  if (sku) {
    console.log(`测试 SKU: ${sku}`);
  }

  const report = await runGigaSourceTest({
    endpoint,
    method,
    body,
  });

  printReport(report);
}

main().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(`GIGA 上游测试失败: ${message}`);
  process.exitCode = 1;
});
