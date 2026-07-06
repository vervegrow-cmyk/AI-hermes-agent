# shopify-价格-agent 主链版本

## 1. 版本定位

这是 `shopify-价格-agent` 的第一版主链方案。

目标不是一次性做完整生产体系，而是先把最重要、最有价值、最容易上线的主链闭环做出来：

- 读取 Giga 最新价格
- 识别哪些 SKU 真的发生了变化
- 计算这些 SKU 是否应该改价
- 输出 dry-run 结果
- 对可同步项更新 Shopify variant 价格
- 支持多 SKU 商品
- 每次只更新变化价格，不做无意义全量更新

这版明确不追求：

- 自动回滚
- 独立 verify API
- 完整告警系统
- 复杂状态机
- 过细的 repository 分层
- 全量对账定时任务

## 2. 主链目标

### 2.1 一句话目标

`安全地把 Giga 变化过的 SKU 价格，同步到对应的 Shopify variant。`

### 2.2 第一版必须解决的问题

1. 哪些 Giga SKU 价格变了
2. 这些 SKU 对应哪个 Shopify variant
3. 这些 SKU 是否满足调价条件
4. 需要更新时如何安全写入 Shopify
5. 多 SKU 商品如何逐 variant 处理

## 3. 第一版范围

## 3.1 必做能力

- Giga 价格读取
- 本地映射读取
- Shopify 当前价格读取
- 价格变化识别
- dry-run 计划生成
- apply 真实写入
- 多 SKU 商品逐 variant 处理
- 最小批次审计
- 增量同步

## 3.2 后置能力

- 独立 verify API
- 手工审核列表接口
- 自动回滚
- 告警通知
- 全量对账 cron
- 复杂监控

## 4. 第一版主链架构

第一版只保留 6 个核心模块。

### 4.1 `service/giga_client.py`

职责：

- 调 Giga OpenAPI
- 获取商品 SKU、成本价、库存、更新时间
- 支持全量拉取和增量拉取

### 4.2 `service/mapping_repository.py`

职责：

- 读取 `giga_sku -> shopify_variant_id`
- 校验映射是否唯一
- 识别一对多、缺失映射

### 4.3 `service/shopify_price_sync_service.py`

职责：

- 读取 Shopify 当前 variant 价格
- 批量或逐条更新 Shopify variant price
- 写入后回读校验

### 4.4 `service/pricing_rules.py`

职责：

- 计算真实成本
- 计算最低安全售价
- 计算目标售价
- 判断是否改价

### 4.5 `service/plan_builder.py`

职责：

- 合并 Giga 数据、映射数据、Shopify 当前价格
- 识别变化 SKU
- 生成 dry-run / apply 可用计划

### 4.6 `service/executor.py`

职责：

- 主流程调度
- 支持三个任务：
  - `dry_run_price_sync`
  - `apply_price_sync`
  - `sync_single_sku`

## 5. 主链数据模型

第一版只保留最必要的模型。

## 5.1 `GigaPriceSnapshot`

字段建议：

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

说明：

- `raw_hash` 用来判断数据是否变化
- 如果 Giga 有 `updated_since`，优先用时间增量
- 如果没有，就用 `raw_hash` 做补充判断

## 5.2 `SkuMappingRecord`

字段建议：

- `store_name`
- `giga_sku`
- `shopify_product_id`
- `shopify_variant_id`
- `shopify_sku`
- `mapping_status`
- `updated_at`

第一版 `mapping_status` 只保留：

- `active`
- `missing_target`
- `duplicated_source`
- `duplicated_target`

## 5.3 `ShopifyPriceState`

字段建议：

- `store_name`
- `shopify_product_id`
- `shopify_variant_id`
- `current_price`
- `updated_at`

## 5.4 `PriceSyncItem`

字段建议：

- `store_name`
- `giga_sku`
- `shopify_product_id`
- `shopify_variant_id`
- `old_price`
- `supplier_cost`
- `target_price`
- `delta`
- `decision`
- `reason_codes`
- `status`

## 5.5 `PriceSyncBatch`

字段建议：

- `batch_id`
- `store_name`
- `mode`
- `status`
- `processed_count`
- `success_count`
- `failed_count`
- `skipped_count`
- `manual_review_count`
- `started_at`
- `finished_at`

## 6. 同步主键

第一版同步主键固定为：

- `store_name + giga_sku + shopify_variant_id`

禁止使用以下字段单独作为真实同步主键：

- `giga_sku`
- `shopify_sku`
- `shopify_product_id`

原因：

- `giga_sku` 可能跨店重复
- `shopify_sku` 可能重复
- 一个 product 可能有多个 variant

## 7. 多 SKU 商品处理

## 7.1 主链规则

多 SKU 商品必须按 `variant` 粒度处理。

规则：

- 一个 `giga_sku` 对应一个 `shopify_variant_id`
- 每个 `giga_sku` 单独计算价格
- 每个 `giga_sku` 单独判断是否更新
- 最后按 `shopify_product_id` 分组提交写入

## 7.2 实际处理方式

如果一个 Shopify product 有多个 variant：

- 红色 S
- 红色 M
- 蓝色 S

那么系统会：

1. 分别读取三个 `giga_sku`
2. 分别判断是否变化
3. 分别计算目标价
4. 只更新变化的那几个 variant

不会：

- 整个 product 一起盲改
- 未变化 variant 跟着一起更新

## 8. 增量同步主链

这是第一版最关键的优化点。

## 8.1 同步策略

- 第一次运行：全量
- 后续运行：增量

## 8.2 增量判断优先级

第一版按这个顺序判断是否需要进入同步计划：

1. 如果 Giga 支持 `updated_since`：
   - 只拉取上次成功同步后的变化数据
2. 如果 Giga 不支持：
   - 拉取候选数据
   - 用 `raw_hash` 对比上次记录
3. 如果 hash 不变：
   - 不进入同步计划
4. 如果 hash 变了：
   - 进入价格决策

## 8.3 哪些变化才算“要处理”

只有下面字段变化时，才进入主链：

- `supplier_cost`
- `shipping_cost`
- `inventory`
- `status`
- `source_updated_at`

## 8.4 哪些情况即使价格没变也要重算

第一版保留一个简单条件：

- `force_recalculate = true`

可用于：

- 临时全量检查
- 规则调整后人工触发

## 9. 每次只更新变化价格

这版主链的核心原则是：

`只更新变化 SKU，只更新变化 variant，只更新价格真的需要变化的项。`

## 9.1 三层过滤

### 第一层：源数据过滤

只取 Giga 有变化的 SKU。

### 第二层：决策过滤

如果重新计算后：

- `target_price == old_price`
- 或差异小于最小阈值

则标记：

- `decision = keep_price`
- `status = skipped`

### 第三层：写入过滤

只有以下条件同时满足才真实写 Shopify：

- 映射唯一
- Shopify variant 存在
- 价格确实变化
- 未触发人工审核
- 未命中幂等重复

## 9.2 结果

这样每次执行都不会：

- 全量扫描后全量写 Shopify
- 把未变化价格重复写一遍
- 因微小浮动造成无意义更新

## 10. dry-run 主流程

第一版 dry-run 流程：

1. 创建 `batch_id`
2. 读取 Giga 增量或全量数据
3. 读取 SKU 映射
4. 过滤掉缺映射和重复映射
5. 读取 Shopify 当前价格
6. 计算目标价
7. 比较 `old_price` 与 `target_price`
8. 生成 `PriceSyncItem`
9. 输出：
   - `increase_price`
   - `decrease_price`
   - `keep_price`
   - `manual_review`
10. 保存批次结果

dry-run 不做任何 Shopify 写入。

## 11. apply 主流程

第一版 apply 流程：

1. 基于即时计划或 dry-run 结果生成可执行项
2. 二次校验：
   - 映射唯一
   - variant 存在
   - 价格差异存在
   - 未命中幂等
3. 按 `shopify_product_id` 分组
4. 对需要改价的 variant 写 Shopify
5. 每次更新后立即回读校验
6. 记录结果
7. 输出批次报告

## 12. 定价规则主链版

第一版规则只保留必要规则。

## 12.1 基础公式

建议：

`target_price = supplier_cost * 1.15 + shipping_cost`

## 12.2 必要输入

- `supplier_cost`
- `shipping_cost`
- `current_price`

## 12.3 第一版必须保留的保护规则

- 成本 <= 0：`manual_review`
- 缺映射：`skip`
- 映射重复：`manual_review`
- 目标价低于安全价：强制抬回
- 单次涨幅过大：`manual_review`
- 单次跌幅过大：`manual_review`
- 差异过小：`keep_price`

补充说明：

- 当前第一版默认把“普通物流费/件”直接作为 `shipping_cost`
- 当前第一版不再额外叠加 `platform_cost` 和 `warehouse_cost`

## 13. 冲突处理主链版

第一版只处理最必要冲突。

## 13.1 直接跳过或人工审核的情况

- 一个 `giga_sku` 对应多个 `shopify_variant_id`
- 多个 `giga_sku` 对应同一个 `shopify_variant_id`
- Shopify 找不到对应 variant
- Shopify SKU 不唯一且无法定位

## 13.2 第一版动作

- 不做自动修复
- 不做智能猜测
- 直接输出：
  - `decision = manual_review`
  - `status = skipped`
  - `reason_codes`

## 14. 幂等设计主链版

第一版必须保留幂等。

幂等键建议：

`store_name + giga_sku + shopify_variant_id + target_price + source_updated_at`

如果已经成功写过相同 key：

- 不重复写 Shopify
- 直接标记 `skipped`

## 15. 状态机简化版

第一版只保留最小状态。

## 15.1 Item 状态

- `planned`
- `skipped`
- `manual_review`
- `synced`
- `failed`

## 15.2 Batch 状态

- `running`
- `completed`
- `failed`

## 16. API 简化版

第一版接口收缩为 3 个。

### 16.1 `POST /price-sync/dry-run`

用途：

- 生成预演计划

### 16.2 `POST /price-sync/apply`

用途：

- 执行真实改价

### 16.3 `GET /price-sync/batches/{batch_id}`

用途：

- 查看批次结果

### 16.4 `POST /price-sync/single`

用途：

- 单 SKU 强制重跑
- 默认跳过增量缓存
- 适合修复映射后补跑或排错

## 17. 报表与审计主链版

第一版只做最小审计。

每条记录至少保存：

- `batch_id`
- `giga_sku`
- `shopify_variant_id`
- `old_price`
- `new_price`
- `decision`
- `status`
- `error_message`
- `created_at`

报表先落：

- JSON
- Markdown

不做：

- 独立 dashboard
- Prometheus 指标
- 告警联动

## 18. 第一版不做的内容

下面这些全部明确后置：

- `verify` 独立接口
- 自动回滚
- 告警系统
- 手工审核列表接口
- 复杂风险等级
- 规则版本自动全量重算
- 定时全量对账任务
- 过细 repository 分层

## 19. 第一版验收标准

满足以下条件即可视为主链版完成：

- 能从 Giga 拉到 SKU 价格
- 能读取映射关系
- 能读取 Shopify 当前价格
- 能识别变化 SKU
- dry-run 能输出价格计划
- apply 只更新变化价格
- 一个 product 下多个 variant 能独立处理
- 映射冲突会被跳过或转人工
- 有最小批次记录
- 有幂等保护

## 20. 推荐开发顺序

### 步骤 1

- 完成 `giga_client.py`
- 完成 `mapping_repository.py`

### 步骤 2

- 完成 `shopify_price_sync_service.py`
- 完成 Shopify 当前价格读取

### 步骤 3

- 完成 `pricing_rules.py`
- 完成 `plan_builder.py`

### 步骤 4

- 完成 `executor.py`
- 打通：
  - `dry_run_price_sync`
  - `apply_price_sync`
  - `sync_single_sku`

### 步骤 5

- 增加最小批次记录
- 增加 JSON / Markdown 报表输出

## 21. 主链版结论

这版不是完整生产平台，而是一个真正能落地的价格同步主链。

它的核心特点是：

- 只做价格
- 只做主链
- 只改变化项
- 多 SKU 按 variant 逐个处理
- 先保证安全，再谈复杂自动化

如果只保留一句话来定义这版：

`第一版只做“变化 SKU -> 价格决策 -> Shopify variant 更新”这条最短主链。`
