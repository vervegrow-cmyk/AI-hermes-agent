# ProductAgenticGEOAgent 主链说明

## 一句话定位

`ProductAgenticGEOAgent` 是一个专门针对 Shopify 现有 `ACTIVE` 在售商品的 GEO / Agentic Shopping 优化 Agent。

它不是：

- 上架 Agent
- 页面美化 Agent
- 广告 Agent
- 订单 Agent

它只做一件事：

扫描 Shopify 现有在售商品，识别信息缺口，调用 DeepSeek 做语义理解和 GEO 体检，生成结构化优化建议，形成 before / after 预览，并在后续阶段支持安全写回、人工审核、快照和回滚。

## 主链目标

把 Shopify 现有商品逐步变成：

- AI 能理解的商品
- AI 能总结和引用的商品
- AI 购物助手能推荐的商品
- Catalog / Google Merchant / OpenAI Product Feed 能消费的标准化商品资产
- Agentic Shopping 场景中可购买、可决策、可解释的商品

## 主链功能

### 1. Shopify ACTIVE 商品扫描

扫描 Shopify 所有符合以下条件的商品：

- `status = ACTIVE`
- 已发布
- 可购买
- 非 Draft
- 非 Archived

读取字段包括：

- 标题
- 描述
- 图片
- 图片 Alt
- 变体
- options
- 类目
- collections
- tags
- vendor
- product type
- SEO title / description
- metafields
- category metafields
- 库存
- 价格
- compare_at_price
- barcode / GTIN / UPC
- publishing status

输出标准化 `ShopifyProductSnapshot`。

### 2. DeepSeek 语义理解与 GEO 体检

把 Shopify 原始商品数据发送给 DeepSeek，要求返回严格 JSON。

DeepSeek 负责：

- 商品语义理解
- GEO 缺口识别
- 标题 / 描述 / FAQ / Alt / Schema / Feed 建议
- 搜索意图生成
- Merchant / OpenAI Feed readiness 判断
- 风险字段识别

系统负责：

- JSON parse
- schema validation
- 风险边界校验
- 保存分析结果

### 3. 结构化优化建议生成

生成 AI / Catalog / Google / Shopping Feed 能理解的结构化建议，包括：

- 商品标题建议
- 商品描述建议
- FAQ 建议
- 图片 Alt 建议
- Schema 建议
- Google Merchant projection
- OpenAI Product Feed projection
- 搜索意图建议
- 信任信息建议

### 4. Before / After 预览

每个商品都形成：

- 当前字段快照
- 建议字段快照
- changed fields
- 风险等级
- 是否允许安全写回

### 5. 写回分层

低风险字段可进入 safe writeback：

- SEO title
- SEO description
- image alt
- GEO custom metafields
- FAQ metafields
- semantic profile metafields

高风险字段必须进入人工审核：

- product title
- handle
- product type
- category
- tags
- collections
- variant option name
- variant option value

### 6. 快照、回滚、持续监控

所有写回在后续阶段都必须支持：

- before snapshot
- after snapshot
- changed fields
- rollback payload
- rollback execution
- 优化效果持续监控

## 当前阶段

当前仓库里已经落下的是 `Phase13A` 骨架，范围是：

- 扫描 ACTIVE 商品
- 调用 DeepSeek
- 生成 GEO audit
- 保存 recommendation
- 保存 snapshot
- 不写回 Shopify

Safe writeback、人工审核流、回滚和持续监控属于后续阶段。
