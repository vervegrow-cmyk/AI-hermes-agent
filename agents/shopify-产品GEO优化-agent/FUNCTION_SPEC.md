# ProductAgenticGEOAgent 功能规格

## 目标输入

- Shopify 现有 `ACTIVE` 商品
- 商品标题、描述、图片、Alt、变体、类目、metafields、SEO、库存、价格等字段

## 核心处理链

1. 扫描 Shopify 在售商品
2. 读取商品结构化数据
3. 调用 DeepSeek 进行语义理解和 GEO 体检
4. 识别在以下场景中的信息缺口：
   - Shopify Catalog
   - Google Merchant
   - OpenAI Product Feed
   - AI 搜索
   - AI 购物助手
5. 生成结构化优化建议：
   - 标题
   - 描述
   - FAQ
   - 图片 Alt
   - Schema
   - Feed
   - 搜索意图
   - 信任信息
6. 形成 before / after 预览
7. 低风险字段可安全写回
8. 高风险字段进入人工审核
9. 所有写回保存快照并支持回滚
10. 持续监控优化效果

## 输出目标

最终把 Shopify 现有商品转成：

- AI 能理解
- AI 能推荐
- AI 能购买
- 各类 Catalog / Feed 能稳定消费

## 不做的事

- 不做新品上架
- 不做主题装修
- 不做广告投放
- 不改 SKU
- 不改 variant_id
- 不改 price
- 不改 inventory
- 不改 barcode / GTIN
