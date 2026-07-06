# shopify-价格-agent 全案设计

## 1. 设计定位

### 1.1 Agent 名称

`shopify-价格-agent`

### 1.2 核心职责

负责将已经通过 `Giga OpenAPI` 上传到 Shopify 的商品，按 `SKU / Variant` 粒度执行价格同步。

### 1.3 设计原则

- 同步最小单位是 `Shopify Variant`
- 默认先 `dry-run`，真实写入需显式开启
- 价格同步优先安全，不优先激进自动化
- 所有改价必须可解释、可审计、可追溯
- 同步应以增量为主，全量对账为辅
- 多 SKU 商品必须逐 variant 处理，不能按 product 粗暴覆盖

## 2. 一句话目标

让系统稳定回答并执行这四件事：

1. 哪些 SKU 价格发生了变化
2. 哪些 Shopify variant 应该改价
3. 为什么改、改多少、利润是否安全
4. 哪些 SKU 因风险、映射冲突或数据异常被跳过

## 3. 总体架构

建议拆成 7 层。

### 3.1 接入层

- `api/app.py`
- `api/routes_price_sync.py`

职责：

- 接收外部请求
- 校验参数
- 启动任务
- 返回批次状态

### 3.2 执行编排层

- `service/executor.py`
- `service/orchestrator.py`

职责：

- 统一调度 dry-run / apply / verify / single-sku
- 管理同步批次生命周期
- 组织读数据、算计划、写 Shopify、落审计

### 3.3 Giga 数据源层

- `service/giga_client.py`
- `service/giga_price_source.py`

职责：

- 调 Giga OpenAPI
- 处理签名、分页、限流、重试
- 标准化输出价格快照

### 3.4 Shopify 读取与写入层

- `service/shopify_reader.py`
- `service/shopify_price_sync_service.py`

职责：

- 读取 Shopify variant 当前价格
- 批量更新价格
- 校验更新结果

### 3.5 决策计算层

- `service/pricing_rules.py`
- `service/plan_builder.py`

职责：

- 计算成本
- 计算安全售价
- 计算目标售价
- 输出决策与原因码

### 3.6 映射与状态层

- `service/mapping_repository.py`
- `service/state_repository.py`
- `service/batch_repository.py`
- `service/audit_repository.py`

职责：

- 管理 `giga_sku -> shopify_variant_id` 映射
- 记录上次同步状态
- 记录批次、明细、错误

### 3.7 报表与运维层

- `service/report_builder.py`
- `service/alerting.py`

职责：

- 生成批次报表
- 生成异常清单
- 发出告警

## 4. 关键设计结论

### 4.1 同步主键

真实同步主键必须是：

- `store_name + giga_sku + shopify_variant_id`

不能只用：

- `giga_sku`
- `shopify_sku`
- `shopify_product_id`

原因：

- 同一个 SKU 可能跨店重复
- Shopify SKU 可能重复
- 一个 product 下可能有多个 variant

### 4.2 同步最小单位

必须按 `variant` 同步，不按 `product` 同步。

### 4.3 首次与后续同步策略

- 首次：全量基线同步
- 后续：增量同步
- 补偿：定期全量对账

### 4.4 多 SKU 商品策略

一个 Giga 商品可对应多个 SKU。

处理规则：

- 每个 `giga_sku` 单独映射一个 `shopify_variant_id`
- 每个 variant 单独计算价格
- 同一 `shopify_product_id` 下多个 variant 允许批量提交
- 但决策必须逐 variant 计算

## 5. 完整业务流程

### 5.1 dry-run 流程

1. 接收执行请求
2. 创建 `batch_id`
3. 读取 Giga 变化数据或全量数据
4. 读取本地 SKU 映射
5. 读取 Shopify 当前价格状态
6. 标准化并合并数据
7. 对每个 SKU 计算成本、利润和目标售价
8. 输出 `PriceSyncItem`
9. 对异常项标记 `manual_review` / `skip`
10. 生成批次汇总报告
11. 存储批次与明细
12. 返回预演结果

### 5.2 apply 流程

1. 读取同批或即时生成的同步计划
2. 对计划项做二次保护校验
3. 仅处理可同步项
4. 按 `shopify_product_id` 分组
5. 批量调用 Shopify 更新 variant price
6. 回读价格校验
7. 写入同步记录
8. 更新本地状态快照
9. 输出报告

### 5.3 verify 流程

1. 根据批次号读取本批成功项
2. 回查 Shopify 当前价格
3. 比较目标价与实际价
4. 标记 `verified` / `mismatch`

## 6. 数据模型设计

## 6.1 GigaPriceSnapshot

建议字段：

- `store_name`
- `giga_product_id`
- `giga_sku`
- `supplier_cost`
- `shipping_cost`
- `currency`
- `inventory`
- `status`
- `source_updated_at`
- `raw_hash`

## 6.2 SkuMappingRecord

建议字段：

- `store_name`
- `giga_product_id`
- `giga_sku`
- `shopify_product_id`
- `shopify_variant_id`
- `shopify_sku`
- `variant_title`
- `mapping_status`
- `source_of_truth`
- `created_at`
- `updated_at`

`mapping_status` 建议值：

- `active`
- `missing_target`
- `duplicated_source`
- `duplicated_target`
- `disabled`
- `manual_review`

## 6.3 ShopifyPriceState

建议字段：

- `store_name`
- `shopify_product_id`
- `shopify_variant_id`
- `shopify_sku`
- `current_price`
- `compare_at_price`
- `inventory_quantity`
- `updated_at`

## 6.4 PriceCalculation

建议字段：

- `giga_sku`
- `supplier_cost`
- `shipping_cost`
- `platform_cost`
- `warehouse_cost`
- `true_cost`
- `minimum_safe_price`
- `recommended_price`
- `target_price`
- `gross_margin_amount`
- `gross_margin_rate`
- `net_margin_amount`
- `net_margin_rate`

## 6.5 PricingDecision

建议字段：

- `giga_sku`
- `shopify_variant_id`
- `decision`
- `old_price`
- `new_price`
- `delta_amount`
- `delta_rate`
- `reason_codes`
- `risk_level`

`decision` 建议值：

- `keep_price`
- `increase_price`
- `decrease_price`
- `manual_review`
- `skip`

## 6.6 PriceSyncState

这是增量同步的关键模型，建议新增。

字段：

- `store_name`
- `giga_sku`
- `shopify_variant_id`
- `last_source_hash`
- `last_source_updated_at`
- `last_target_price`
- `last_shopify_price`
- `last_decision`
- `last_sync_status`
- `last_sync_batch_id`
- `last_sync_at`

## 6.7 PriceSyncBatch

建议字段：

- `batch_id`
- `store_name`
- `mode`
- `sync_scope`
- `requested_by`
- `started_at`
- `finished_at`
- `status`
- `processed_count`
- `syncable_count`
- `success_count`
- `failed_count`
- `skipped_count`
- `manual_review_count`

## 7. SKU 重复与冲突处理

这是生产设计里最重要的一块。

### 7.1 允许的重复

- 不同店铺下同一个 `giga_sku`
- 同一 product 下多个不同 variant

### 7.2 不允许自动处理的重复

- 同一店铺里，一个 `giga_sku` 映射到多个 `shopify_variant_id`
- 同一店铺里，多个 `giga_sku` 映射到同一个 `shopify_variant_id`
- Shopify 中多个 variant 使用同一个 SKU 且系统无法唯一确定目标

### 7.3 冲突处理策略

发现冲突时：

- 不执行真实改价
- 生成 `manual_review`
- 记录冲突类型
- 输出冲突报表

### 7.4 冲突类型建议

- `duplicate_giga_sku`
- `duplicate_shopify_sku`
- `one_to_many_mapping`
- `many_to_one_mapping`
- `missing_variant`
- `variant_not_unique`

## 8. 增量同步设计

### 8.1 第一次同步

第一次必须做全量：

- 建立价格基线
- 建立映射基线
- 建立本地状态表

### 8.2 后续同步

后续以增量为主。

优先级：

1. Giga 原生 `updated_since`
2. Giga 原生 `updated_at`
3. 本地 `raw_hash` 比较

### 8.3 哪些变化触发重算

以下任一变化都应触发重算：

- 供货价变了
- 运费变了
- 库存变了
- 商品状态变了
- 定价规则版本变了
- Shopify 当前价与本地状态不一致

### 8.4 为什么不能永远只做增量

因为可能存在：

- Giga 漏发更新时间
- 本地状态丢失
- Shopify 端被人工改价
- 历史失败项未补偿

所以要补一个周期性全量对账：

- 每天小范围增量
- 每周或每天低峰期全量对账

## 9. 同步效率优化设计

### 9.1 慢的根因

最常见的慢点：

- Giga 单条查询太多
- Shopify 单 SKU 查 variant 太多
- Shopify 单 variant 写价格太多
- 没有增量，每次全量跑

### 9.2 优化原则

- 先本地映射，后远程调用
- 先筛变化，再做计算
- 先按 product 聚合，再写 Shopify

### 9.3 推荐优化方案

#### 方案 A：本地映射优先

不要每次执行时都调用 Shopify `find_variant_by_sku` 去找目标。

正确做法：

- 先查本地映射表
- 只有缺映射时才回查 Shopify

#### 方案 B：增量拉取 Giga

尽量只拉变化部分，避免每次全量扫描。

#### 方案 C：按 product 分组写 Shopify

把同一个 `shopify_product_id` 下多个 variant 的价格更新打包提交。

#### 方案 D：有限并发

- Giga 读取：可并发分页
- Shopify 写入：受控并发
- 不能无限并发，避免 429

#### 方案 E：状态缓存

每次成功同步后，把：

- 上次源数据 hash
- 上次目标价
- 上次 Shopify 实际价

写入本地状态，避免无效同步。

## 10. 多 SKU 商品处理

### 10.1 标准模型

一个商品可以有：

- 1 个 product
- N 个 variant
- N 个 `giga_sku`

所以系统必须支持：

- product 级分组
- variant 级决策

### 10.2 处理原则

- 价格计算在 variant 级别
- 审计日志在 variant 级别
- 批量写入在 product 级别

### 10.3 举例

例如一个 T-shirt：

- 红色 S -> `giga_sku_A` -> `variant_1`
- 红色 M -> `giga_sku_B` -> `variant_2`
- 蓝色 S -> `giga_sku_C` -> `variant_3`

那么：

- 3 个 SKU 各自单独算价
- 最后按同一个 `shopify_product_id` 聚合写入

## 11. 状态机设计

建议为每条同步项定义状态机。

### 11.1 Item 状态

- `pending`
- `validated`
- `planned`
- `skipped`
- `manual_review`
- `syncing`
- `synced`
- `verify_failed`
- `sync_failed`

### 11.2 Batch 状态

- `created`
- `running`
- `completed`
- `partially_failed`
- `failed`
- `cancelled`

## 12. API 设计

### 12.1 对外接口

- `POST /price-sync/dry-run`
- `POST /price-sync/apply`
- `POST /price-sync/verify`
- `POST /price-sync/single`
- `GET /price-sync/batches/{batch_id}`
- `GET /price-sync/report/latest`
- `GET /price-sync/manual-review`

### 12.2 推荐请求参数

#### dry-run

- `store_name`
- `sync_scope`: `full | incremental | single_sku`
- `sku_list`
- `force_recalculate`

#### apply

- `batch_id`
- `store_name`
- `confirm`

## 13. 定价规则设计

### 13.1 基础价格公式

建议公式：

`target_price = supplier_cost * 1.15 + shipping_cost`

### 13.2 规则版本化

必须加一个：

- `pricing_rule_version`

原因：

- 规则变更会导致即使 Giga 价格没变，也要重算

### 13.3 安全保护

- 成本 <= 0：人工审核
- 目标价 < 安全价：强制提升
- 单次涨价 > 阈值：人工审核
- 单次降价 > 阈值：人工审核
- 缺映射：跳过

## 14. 幂等与回滚

### 14.1 幂等键

建议：

`idempotency_key = store_name + giga_sku + shopify_variant_id + target_price + source_updated_at`

如果同 key 已成功执行过，则跳过重复写入。

### 14.2 回滚能力

不要求第一版自动回滚，但必须记录：

- `old_price`
- `new_price`
- `batch_id`

这样后续可做：

- 按批次回滚
- 按 SKU 回滚

## 15. 告警与监控

### 15.1 必须告警的情况

- Giga API 全量失败
- Shopify API 429 大量出现
- 映射冲突率超阈值
- 手工审核比例过高
- 成功率过低

### 15.2 核心监控指标

- 每批处理 SKU 数
- 变化 SKU 数
- 实际写入数
- 跳过数
- 手工审核数
- 平均执行时长
- Shopify 429 比例
- 映射冲突率

## 16. 环境变量建议

除已有变量外，建议扩展：

- `GIGA_API_BASE_URL`
- `GIGA_API_KEY`
- `GIGA_API_SECRET`
- `GIGA_TIMEOUT_SECONDS`
- `GIGA_SIGN_TYPE`
- `GIGA_PAGE_SIZE`
- `PRICE_SYNC_PRODUCT_MARKUP_RATE`
- `PRICE_SYNC_MIN_MARGIN_RATE`
- `PRICE_SYNC_MIN_MARGIN_AMOUNT`
- `PRICE_SYNC_MAX_UP_DELTA_RATE`
- `PRICE_SYNC_MAX_DOWN_DELTA_RATE`
- `PRICE_SYNC_MIN_DELTA_AMOUNT`
- `PRICE_SYNC_DRY_RUN`
- `PRICE_SYNC_FULL_RECONCILE_CRON`

## 17. 开发里程碑

### 17.1 里程碑 A：设计基线

- 增加 Giga 配置项
- 定义数据模型
- 定义映射表结构
- 定义状态表结构

### 17.2 里程碑 B：只读链路

- 接入 Giga client
- 获取 Giga SKU 价格
- 读取 Shopify 价格
- 建立映射样本

### 17.3 里程碑 C：dry-run

- 价格规则实现
- 计划生成
- 报表输出
- 状态表落地

### 17.4 里程碑 D：真实同步

- Shopify 价格更新
- 回读校验
- 失败分类
- 幂等处理

### 17.5 里程碑 E：生产化

- 增量同步
- 全量对账
- 告警
- 手工审核列表
- 重跑能力

## 18. 验收标准补强版

除了原来的验收项，再补这些：

- 能识别重复 SKU 冲突
- 能识别一对多映射冲突
- 第二次执行默认走增量
- 能按 product 聚合多个 variant 更新
- 规则版本变化后能触发重算
- 有幂等保护
- 有状态表记录
- 有全量对账机制

## 19. 最终建议

这个 agent 的真正第一目标不是“自动调价”，而是：

`在 SKU 级别安全、可解释、可增量地完成 Shopify 价格同步`

所以开发优先级建议固定为：

1. 唯一主键和映射规则
2. dry-run 决策正确性
3. 增量同步
4. 批量写入效率
5. 生产运维能力

---

如果只保留一句话作为这个方案的核心约束，那就是：

`所有同步都按 variant 做决策，按增量做执行，按批次做审计，按冲突做人工兜底。`
