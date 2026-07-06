import { bootstrapEnv } from "./env-loader.js";
import { runDobaSourceTest } from "../../services/upstream-source-test.service.js";

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

function printReport(report: Awaited<ReturnType<typeof runDobaSourceTest>>): void {
  console.log("========================================");
  console.log("DOBA 上游商品数据测试完成");
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
  const itemNo = findArgValue(args, "item-no") ?? process.env.DOBA_SOURCE_TEST_ITEM_NO ?? "";
  const spuId = findArgValue(args, "spu-id") ?? "";
  const spuNo = findArgValue(args, "spu-no") ?? "";
  const skuId = findArgValue(args, "sku-id") ?? "";
  const explicitEndpoint = findArgValue(args, "endpoint") ?? process.env.DOBA_SOURCE_TEST_ENDPOINT;

  const endpoint =
    explicitEndpoint ??
    (itemNo || spuId || spuNo || skuId ? "/api/goods/doba/spu/detail" : "/api/category/doba/list");

  const query: Record<string, string> = {};
  if (itemNo) {
    query.itemNo = itemNo;
  }
  if (spuId) {
    query.spuId = spuId;
  }
  if (spuNo) {
    query.spuNo = spuNo;
  }
  if (skuId) {
    query.skuId = skuId;
  }

  console.log("开始测试 DOBA 上游接口...");
  console.log(`接口路径: ${endpoint}`);
  if (Object.keys(query).length > 0) {
    console.log(`测试参数: ${JSON.stringify(query)}`);
  } else {
    console.log("当前未传 itemNo / spuId / spuNo / skuId，先做基础连通性和类目数据测试。");
  }

  const report = await runDobaSourceTest({
    endpoint,
    method: "GET",
    query,
  });

  printReport(report);
}

main().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(`DOBA 上游测试失败: ${message}`);
  process.exitCode = 1;
});
