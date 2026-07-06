# shopify-价格-agent

这个 agent 的定位是：

`Giga OpenAPI -> 价格采集与计算 -> Shopify Variant 价格同步`

它的核心职责不是创建商品，也不是改库存，而是针对已经通过 Giga OpenAPI 上架到 Shopify 的商品，持续判断是否需要调价，并把新的价格安全地同步到 Shopify。

## 当前状态

当前主链已经落地：

- 复用主项目根目录 `.env`
- 提供标准 FastAPI agent 入口
- 支持 `dry-run` / `apply` / `single sku`
- 支持增量同步和最小批次审计
- 支持多 SKU 商品按 variant 粒度同步

当前仍建议继续补强真实 Giga 字段对齐、映射治理和真实 Shopify 联调。

## 推荐先看

- [IMPLEMENTATION_PLAN.md](</D:/桌面文件下载/AI-hermes-agent/agents/shopify-价格-agent/IMPLEMENTATION_PLAN.md>)
- [service/executor.py](</D:/桌面文件下载/AI-hermes-agent/agents/shopify-价格-agent/service/executor.py>)
- [api/app.py](</D:/桌面文件下载/AI-hermes-agent/agents/shopify-价格-agent/api/app.py>)

## 本地启动

```powershell
python agents/shopify-价格-agent/main.py
```

## 设计原则

- 只处理价格，不负责新商品创建
- 先支持 `dry-run`，再开放真实写入 Shopify
- 每次同步必须可审计、可回滚、可复盘
- SKU 映射必须先建立，否则禁止真实同步
- 价格变更必须有原因码、旧值、新值、成本依据

## 当前定价规则

当前主链统一使用：

`shopify售价 = giga单价 * 1.15 + 普通物流费/件`

## 日常命令手册

### 全店真实价格同步

```powershell
cd "D:\桌面文件下载\AI-hermes-agent\agents\shopify-价格-agent"
$env:PYTHONPATH="D:\桌面文件下载\AI-hermes-agent"
python workflow\run_price_sync_cli.py --store-name 4ea863-98.myshopify.com --mode apply --sync-scope full
```

用途：

- 对指定 Shopify 店铺执行一次全店价格同步主链
- 自动扫描店铺内已识别的 Giga SKU 与 Shopify variant 映射
- 自动从 Giga OpenAPI 拉取最新价格数据
- 按当前公式计算目标售价：
  `Shopify售价 = supplier_cost * 1.15 + shipping_cost`
- 逐 SKU、逐 variant 判断是否需要真实改价
- 对需要更新的项真实写入 Shopify
- 在终端持续打印执行进度和每条 SKU 的处理结果

这条命令的核心能力：

- `--store-name`
  指定要同步的 Shopify 店铺
- `--mode apply`
  真实执行改价，不是预演
- `--sync-scope full`
  全量扫描当前店铺已识别的候选 SKU，不只跑增量

执行时会经历这些阶段：

1. 启动批次任务
2. 扫描或刷新 Shopify 映射
3. 拉取 Giga 最新价格快照
4. 读取 Shopify 当前价格
5. 生成价格同步计划
6. 逐条执行真实改价
7. 保存批次结果、明细、状态与报表

终端输出说明：

- `SKU XXX 价格无变化，跳过`
  表示当前 Shopify 价格已经等于最新目标价，不重复写入
- `SKU YYY 更新成功：59.99 -> 54.99`
  表示该 SKU 已真实更新到 Shopify
- `SKU ZZZ 需人工处理：168.43 -> 0.00，原因 invalid_supplier_cost`
  表示上游 Giga 成本价无效或异常，系统为安全起见不自动改价

适用场景：

- 全店做一次真实价格同步
- 将所有通过 Giga OpenAPI 对应到 Shopify 的商品价格更新一遍
- 运营批量校正售价
- 验证完整价格同步主链是否稳定可跑

注意事项：

- 这是一条真实写入命令，会直接更新 Shopify 价格
- 同步最小单位是 `variant`，不是 `product`
- 只有满足自动同步条件的 SKU 才会被写入
- 映射缺失、成本异常、数据异常的 SKU 会被跳过或转人工处理
- 如果很多 SKU 显示“价格无变化，跳过”，通常说明店铺价格已经和 Giga 最新价格一致
