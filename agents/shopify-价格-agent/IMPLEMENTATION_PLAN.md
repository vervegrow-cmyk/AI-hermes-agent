# shopify-价格-agent 实施方案

## 1. Agent 完整目标

### 1.1 业务目标

把已经通过 `Giga OpenAPI` 上传到 Shopify 的商品价格，按可配置规则自动同步到 Shopify，确保：

- Shopify 售价与 Giga 最新供货价保持一致或按策略调整
- 每次改价都有明确依据
- 低利润、异常价格、缺少映射的商品不会被误改
- 支持批量执行、定时执行、人工触发、预演模式

### 1.2 技术目标

构建一条完整链路：

1. 从 Giga OpenAPI 拉取最新价格数据
2. 读取本地 SKU 映射关系
3. 读取 Shopify 当前价格
4. 按规则计算目标售价
5. 生成同步计划
6. 先支持 dry-run 审核
7. 再支持真实写入 Shopify
8. 记录审计日志和结果报表

### 1.3 最终交付目标

这个 agent 最终要能回答四个问题：

- 哪些商品今天应该调价
- 每个商品为什么要调价
- 调价后利润是否仍然安全
- 哪些商品因为风险被跳过或转人工

## 2. 完成标准

### 2.1 MVP 完成标准

达到以下条件，视为第一阶段完成：

- 能从 Giga OpenAPI 获取商品 SKU 和最新供货价
- 能从 Shopify 获取对应 variant 当前价格
- 能通过本地映射把 `giga_sku` 对应到 `shopify_variant_id`
- 能生成 `dry-run` 价格同步计划
- 每条计划包含：
  - `giga_sku`
  - `shopify_variant_id`
  - `old_price`
  - `supplier_cost`
  - `target_price`
  - `delta`
  - `decision`
  - `reason_codes`
- 对缺失映射、异常成本、低毛利商品自动跳过
- 输出批次级汇总报告
- 不发生商品创建、发布、库存修改、订单创建

### 2.2 真实同步完成标准

达到以下条件，视为第二阶段完成：

- dry-run 结果可切换为真实同步
- 能实际调用 Shopify API 更新 variant price
- 写入后能回读 Shopify 验证价格已更新
- 每次更新记录：
  - 批次号
  - 执行时间
  - SKU
  - 旧价格
  - 新价格
  - 执行状态
  - 错误信息
- 部分失败不影响整批继续执行
- 能输出成功数、失败数、跳过数、人工审核数

### 2.3 生产可用完成标准

达到以下条件，视为可投入日常运行：

- 支持定时任务
- 支持按店铺、按 SKU、按批次重跑
- 支持幂等执行，避免重复改价
- 支持价格阈值保护
- 支持异常告警
- 支持审计报表落盘或入库
- 有测试覆盖核心决策逻辑

## 3. 业务范围

### 3.1 本 agent 应该做的

- Giga 商品价格采集
- Shopify 当前价格读取
- SKU 映射校验
- 成本与售价计算
- 定价策略判断
- Shopify 售价更新
- 审计日志与报表输出

### 3.2 本 agent 现阶段不应该做的

- 商品采集选品
- 商品创建
- 商品发布
- 库存同步
- 订单同步
- 履约处理
- 广告投放自动调价

## 4. 前期准备明细

### 4.1 外部账号与权限

- Giga OpenAPI 账号
- Giga OpenAPI 文档
- Giga API Key / Secret / Token
- Shopify Admin API 权限
- Shopify 店铺域名
- Shopify Admin Access Token

### 4.2 必须确认的接口信息

在动手开发前，必须确认 Giga 提供以下哪类接口：

- 商品列表接口
- 商品详情接口
- SKU 价格接口
- SKU 库存接口
- 批量查询接口
- 更新时间字段
- 分页规则
- 限流规则
- 鉴权方式
- 失败重试建议

如果这些信息不完整，先不要写真实同步逻辑，先做 mock 适配层。

### 4.3 数据映射准备

至少要准备一份稳定映射表，字段建议如下：

- `giga_product_id`
- `giga_sku`
- `shopify_product_id`
- `shopify_variant_id`
- `shopify_sku`
- `store_name`
- `status`
- `last_synced_at`

没有这份映射表，就不能安全做真实调价。

### 4.4 定价规则准备

在开发前要先定好这些规则：

- 基础售价公式
- 最低毛利率
- 最低毛利额
- 运费是否计入成本
- 平台费是否计入成本
- 汇率是否参与换算
- 小数取整规则
- 是否允许降价
- 单次最大涨幅
- 单次最大跌幅
- 低库存是否加价
- 缺货是否停售或跳过

### 4.5 运行环境准备

主项目里已有共享配置，但还需要补充 Giga 相关环境变量。

建议新增：

- `GIGA_API_BASE_URL`
- `GIGA_API_KEY`
- `GIGA_API_SECRET`
- `GIGA_TIMEOUT_SECONDS`
- `GIGA_SIGN_TYPE`
- `PRICE_SYNC_PRODUCT_MARKUP_RATE`
- `PRICE_SYNC_MIN_MARGIN_RATE`
- `PRICE_SYNC_MIN_MARGIN_AMOUNT`
- `PRICE_SYNC_MAX_UP_DELTA_RATE`
- `PRICE_SYNC_MAX_DOWN_DELTA_RATE`
- `PRICE_SYNC_DRY_RUN`

### 4.6 测试数据准备

至少准备 20 到 50 条样本 SKU，覆盖：

- 正常涨价
- 正常降价
- 价格不变
- 缺失映射
- Shopify 商品不存在
- Giga 价格为空
- 成本为 0
- 毛利过低
- 低库存
- API 限流或失败

## 5. 建议的能力拆分

参考仓库里已有的 `doba-shopify-agent` 价格同步模块，这个 agent 建议拆成下面几层。

### 5.1 Giga 价格源适配层

建议新增：

- `service/giga_client.py`
- `service/giga_price_source.py`

职责：

- 统一封装 Giga API 请求
- 把外部返回结构转换成内部标准价格快照
- 屏蔽签名、分页、限流、重试细节

### 5.2 Shopify 价格读取与写入层

建议新增：

- `service/shopify_price_sync_service.py`

职责：

- 读取 Shopify variant 当前价格
- 根据 `shopify_variant_id` 或 `sku` 更新价格
- 支持 `mock` / `real` 两种模式

这个思路可以直接复用：

- [agents/doba-shopify-agent/src/modules/price_sync/infrastructure/shopify_price_sync_service.py](/D:/桌面文件下载/AI-hermes-agent/agents/doba-shopify-agent/src/modules/price_sync/infrastructure/shopify_price_sync_service.py:1)

### 5.3 价格计算与决策层

建议新增：

- `service/pricing_rules.py`
- `service/plan_builder.py`

职责：

- 计算真实成本
- 计算最低安全售价
- 计算目标售价
- 判断 `increase_price` / `decrease_price` / `keep_price` / `manual_review`
- 给出原因码

这里最值得复用的是 `doba-shopify-agent` 的决策思路：

- [application/service.py](/D:/桌面文件下载/AI-hermes-agent/agents/doba-shopify-agent/src/modules/price_sync/application/service.py:1)

### 5.4 映射与批次管理层

建议新增：

- `service/mapping_repository.py`
- `service/batch_repository.py`
- `service/audit_repository.py`

职责：

- 管理 SKU 映射
- 管理每次同步批次
- 记录每条同步记录
- 便于重跑、追溯、统计

### 5.5 Agent 执行入口

建议把 `service/executor.py` 从占位实现升级为可执行任务分发器，支持：

- `task = "dry_run_price_sync"`
- `task = "apply_price_sync"`
- `task = "verify_price_sync"`
- `task = "sync_single_sku"`

## 6. 推荐 API 能力

当前已有标准 `/health` 和 `/execute`。

建议再补充这些接口：

- `POST /price-sync/dry-run`
- `POST /price-sync/apply`
- `POST /price-sync/verify`
- `POST /price-sync/single`
- `GET /price-sync/batches/{batch_id}`
- `GET /price-sync/report/latest`

## 7. 关键数据模型建议

建议内部统一这些模型：

- `GigaPriceSnapshot`
- `ShopifyPriceState`
- `SkuMappingRecord`
- `PriceCalculation`
- `PricingDecision`
- `PriceSyncItem`
- `PriceSyncRecord`
- `PriceSyncBatchResult`

建议每个 `PriceSyncItem` 至少包含：

- `giga_sku`
- `shopify_variant_id`
- `current_price`
- `supplier_cost`
- `shipping_cost`
- `platform_cost`
- `true_cost`
- `minimum_safe_price`
- `target_price`
- `delta`
- `decision`
- `reason_codes`
- `status`

## 8. 规则建议

### 8.1 最小安全规则

- 成本为空或小于等于 0：`manual_review`
- 缺少 SKU 映射：`sync_failed` 或 `skip`
- Shopify variant 不存在：`manual_review`
- 目标售价低于最低安全售价：强制抬回安全线

### 8.2 价格波动保护

- 单次涨价超过 20%：转人工
- 单次降价超过 20%：转人工
- 调整金额小于阈值时：`keep_price`

### 8.3 库存联动规则

- 库存低：允许轻微提价
- 库存高：允许轻微降价
- 缺货：跳过改价或转人工

## 9. 开发顺序建议

### 阶段 1：打通只读链路

- 增加 Giga 配置项
- 写 Giga client
- 能拉到样本 SKU 与价格
- 读取 Shopify 当前价格
- 建立最小 SKU 映射文件

### 阶段 2：打通 dry-run

- 实现价格计算
- 实现决策逻辑
- 输出同步计划
- 输出报表
- 补齐测试

### 阶段 3：开放真实同步

- 调用 Shopify 更新 variant 价格
- 写回同步记录
- 校验同步结果
- 增加失败重试与错误分类

### 阶段 4：可运维化

- 定时执行
- 告警通知
- 批次查询
- 单 SKU 重跑
- 审计留存

## 10. 验收清单

上线前建议逐条验收：

- 能成功连接 Giga OpenAPI
- 能成功连接 Shopify Admin API
- 能拿到 20+ 个样本 SKU
- 能完成 dry-run 批量计划生成
- dry-run 不会写 Shopify
- apply 模式能真实更新 Shopify 价格
- 缺失映射不会误更新
- 异常价格不会误更新
- 有完整日志和报表
- 测试覆盖核心决策逻辑

## 11. 与现有仓库的复用建议

可直接借鉴或迁移的现有能力：

- Shopify 认证与 client：
  - [shared/clients/shopify.py](/D:/桌面文件下载/AI-hermes-agent/shared/clients/shopify.py:1)
- 共享配置：
  - [shared/config/settings.py](/D:/桌面文件下载/AI-hermes-agent/shared/config/settings.py:1)
- 标准 agent runtime：
  - [shared/agent_runtime.py](/D:/桌面文件下载/AI-hermes-agent/shared/agent_runtime.py:1)
- 已有价格同步策略样板：
  - [doba price sync application](/D:/桌面文件下载/AI-hermes-agent/agents/doba-shopify-agent/src/modules/price_sync/application/service.py:1)
- Shopify 价格写入样板：
  - [doba shopify price sync service](/D:/桌面文件下载/AI-hermes-agent/agents/doba-shopify-agent/src/modules/price_sync/infrastructure/shopify_price_sync_service.py:1)

## 12. 现在最值得先做的 3 件事

1. 确认 Giga OpenAPI 的价格接口和鉴权方式。
2. 准备一份 `giga_sku -> shopify_variant_id` 映射样本。
3. 先把 dry-run 链路做出来，再开放真实同步。

---

如果按工程优先级来排，`shopify-价格-agent` 的第一版目标不是“自动赚钱”，而是“安全地知道该不该改价，并且不会改错价”。
