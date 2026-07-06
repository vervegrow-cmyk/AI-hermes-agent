# Doba Retailer API 学习记忆文档

## 说明

本文件整理自当前会话中用户提供的 Doba Retailer API 内容，用于在
`doba-shopify-agent` 项目内保存一份可持续复用的本地知识文档。

适用上下文：

- 零售商 API
- 零售商识别码：`314932`
- 账号名：`雪拉·吕`

注意：

- 本文件主要记录用户提供的接口说明、业务范围、限制、更新日志和开发约束。
- 若后续与 Doba 官方文档有差异，应以最新官方文档为准。
- 已明确弃用的接口仅保留记忆，不应进入新实现。

---

## 一、Doba Retailer API 总体范围

### 能力范围

1. 搜索 Doba 供应商商品，并将其重新整理后上架到自有网站或第三方店铺。
2. 收集商店订单，并通过 Doba 向供应商下单。
3. 获取物流信息，并同步回销售渠道。

### 使用前提

1. 注册 Doba 账号。
2. 购买标准计划或企业计划。
3. 申请开发者并通过审核。
4. 获取并保存：
   - `App Key`
   - `Public Key`
   - `Private Key`
5. 公钥和私钥成对存在，重置后需要重新提交公钥才会生效。

### 开发和支持约束

- Doba 仅提供 API 访问和技术咨询，不直接代做集成。
- 需要技术团队自行完成接口编排和业务代码。
- 邮件支持：`api@doba.com`
- 提问时应主动提供：
  - 零售商身份
  - 问题描述
  - 请求参数
  - 返回参数
- 必须关注接口调用频率要求和套餐等级限制。

---

## 二、项目分层中的使用原则

结合当前项目 `开发功能结构`，这些接口应按以下层次使用：

### Phase 00 - Supplier Archive Runtime

归档和字典类接口：

- 查询类别列表
- 查询供应商详情
- 查询 SPU 列表
- 查询 SPU 详情
- 查询更新信息
- 查询库存与价格
- 查询标签列表
- 按标签查询 SPU ID

### 后续能力，不应混入当前 Supplier Archive

- Import Order
- 获取订单发货信息
- 获取订单详情
- 确认订单已收到
- 取消订单
- 获取运输方式列表
- 产品运输率估算
- 查询信用卡/借记卡
- 订单付款
- 预付余额检查
- 获取国家/地区列表
- 获取第三方市场/平台列表

### 明确禁用

- 管理更新信息（已弃用）

---

## 三、更新日志关键记忆

### 2025-11-27

- `Import Order` 的 `dsPlatformId` 支持更多平台。
- `Query SPU Detail` 新增响应参数 `packagingInformations`。
- 旧参数 `packagingInformation` 已弃用，90 天后移除。

### 2025-09-25

`Get Order Detail` 新增响应参数：

- `deliveredButNotReceivedProtectionFee`
- `nonDefectiveRemorseReturnProtectionFee`

### 2025-08-15

- API 调用限制会随套餐等级变化。
- 超限返回 `429 Too Many Requests`。
- 支持批处理查询的接口，单次最大输入统一为 `20`。
- 影响接口：
  - 查询 SPU 详情
  - 查询库存与价格
  - 产品运输率估算
  - 获取订单发货信息
  - 确认订单已收到
  - 取消订单

### 2025-05-28

- `Import Order` 的 `dsPlatformId` 变为必填。
- `Query SPU Detail` 新增请求参数 `skuId`。
- `Query SPU List` 新增请求参数 `pickupAvailable`。
- `Query Inventory and Price` 新增：
  - `saleDetail`
  - `pickupSellingPrice`
  - `pickupSaleDetail`

### 2025-02-25

- `Query SPU List` 新增请求参数 `excludeMarketRestrictions`。

### 2024-11-12

- `Query SPU List` 新增请求参数：
  - `maxEstProcessingTime`
  - `minInventory`
  - `maxPrice`
  - `minPrice`
- `Query SPU List` 新增响应参数：
  - `processingTime`
  - `certificateFiles`
  - `storeUrl`
- `Query SPU Detail` 新增响应参数 `skuUrl`。
- `Query Updated Info` 新增请求参数 `itemNo`。
- `Manage Update Info` 被弃用。

### 其他重要历史信息

- 2023-05-09：`tagId` 对“按标签查询 SPU ID”不再强制。
- 2022-07-18：新增 `PrePay Balance Check`。
- 2022-05-26：
  - `Product Shipping Rate Estimate` 的 `shipToProvince`、`shipToZipcode` 可选。
  - `Query SPU List` 新增 `spuNo`。
  - `Query SPU Detail` 支持 `spuNo`。
  - `Query SPU Detail` 单次最多查询 50 个 SPU 的旧说明，后续会受 2025 批量规则影响。
  - `Import Order` / `Get Order Detail` 新增 `encryptOrdBatchIds`。
- 2022-05-18：
  - 尺寸单位统一为 `in.`
  - 重量统一为 `lb`
- 2021-12-28：
  - `Get Order Detail` 不加过滤参数时只能查近 30 天订单。
- 2020-07-10：
  - Retailer API 正式发布，使用前必须申请 access key。

---

## 四、产品接口记忆

### 1. 查询类别列表

- URL：`https://openapi.doba.com/api/category/doba/list`
- 请求参数：无
- 关键字段：
  - `catId`
  - `catName`
  - `parentId`
  - `level`
  - `node`
- 关键结论：
  - 需要保存 `catId` 和 `catName`
  - 类目层级可通过 `level`、`parentId`、`node` 判断

### 2. 查询供应商详情

- URL：`https://openapi.doba.com/api/supplier/doba/list`
- 请求参数：
  - `pageNumber`，默认 1
  - `pageSize`，默认 20，最大 100
  - `supplierId`，可选
- 关键字段：
  - `businessCategory`
  - `companyProfile`
  - `productsQuantity`
  - `returnPolicy`
  - `supplierCount`
  - `supplierId`
  - `supplierName`
- 关键结论：
  - `supplierId` 是重要上游主键
  - 后续可据此拉取供应商相关 SPU

### 3. 查询 SPU 列表

- URL：`https://openapi.doba.com/api/goods/doba/spu/list`
- 核心筛选参数：
  - `busiId`
  - `catId`
  - `freeShipping`
  - `keyword`
  - `pageNumber`
  - `pageSize`
  - `shipFrom`
  - `shipTo`
  - `listingTimeAfter`
  - `listingTimeBefore`
  - `maxEstProcessingTime`
  - `minInventory`
  - `maxPrice`
  - `minPrice`
  - `excludeMarketRestrictions`
  - `pickupAvailable`
- 关键响应字段：
  - `busiId`
  - `sellerName`
  - `spuId`
  - `title`
  - `spuNo`
  - `pictureUrl`
  - `inventory`
  - `maxPrice`
  - `minPrice`
  - `certificateFiles`
  - `processingTime`
  - `storeUrl`
- 关键结论：
  - `spuId`、`spuNo` 是重要桥接字段
  - `processingTime`、`certificateFiles`、`storeUrl` 对履约与合规很重要

### 4. 查询 SPU 详情

- URL：`https://openapi.doba.com/api/goods/doba/spu/detail`
- 支持查询参数：
  - `itemNo`
  - `spuId`
  - `spuNo`
  - `skuId`
- 规则：
  - 支持逗号分隔批量
  - 当前应按最多 20 条处理
- 关键结论：
  - `spuNo` 可与 Doba 产品文件进行交叉关联
  - 详情拉取应作为 `SPU list` 之后的第二阶段抓取

### 5. 查询更新信息

- URL：`https://openapi.doba.com/api/goods/doba/updated`
- 请求参数：
  - `pageNo`
  - `pageSize`
  - `updateTimeAfter`，必填
  - `updateTimeBefore`，必填
  - `updateType`
  - `itemNo`
- `updateType` 含义：
  - `1` 产品价格
  - `2` 产品库存
  - `3` 产品状态
  - `4` 新变体
- 关键响应字段：
  - `itemNo`
  - `updateType`
  - `updateDetail`
  - `updateTime`
- 关键结论：
  - 这是后续库存同步、价格同步、新变体处理的重要上游更新流

### 6. 管理更新信息（已弃用）

- URL：`https://openapi.doba.com/api/goods/doba/spu/delete`
- 状态：**即将弃用，请不要使用**
- 结论：
  - 只做历史记录
  - 新实现禁止使用

### 7. 查询库存与价格

- URL：`https://openapi.doba.com/api/goods/doba/stock`
- 请求参数：
  - `itemNo`，必填，最多 20
- 关键响应字段：
  - `skuId`
  - `skuCode`
  - `itemNo`
  - `sellingPrice`
  - `msrpPrice`
  - `mapPrice`
  - `regionId`
  - `availableNum`
  - `saleDetail`
  - `pickupSellingPrice`
  - `pickupSaleDetail`
- 关键结论：
  - 这是库存同步和价格同步的重要实时数据源
  - 不能只看 `sellingPrice`，还要考虑促销价与 pickup 价

### 8. 查询标签列表

- URL：`https://openapi.doba.com/api/inventory/doba/queryTagList`
- 请求参数：无
- 关键响应字段：
  - `tagId`
  - `tagName`
- 特殊约束：
  - 对无标签 SPU：
    - `tagId = 0`
    - `tagName = products_with_no_tag`

### 9. 按标签查询 SPU ID

- URL：`https://openapi.doba.com/api/inventory/doba/querySpuIdByTag`
- 请求参数：
  - `tagId`
  - `pageNumber`
  - `pageSize`
- 响应字段：
  - `spuIds`
  - `totalQuantity`
- 关键结论：
  - 需要支持分页
  - `tagId=0` 表示无标签 SPU

---

## 五、订单接口记忆（后期）

### 1. Import Order

- URL：`https://openapi.doba.com/api/order/doba/importOrder`
- 前置准备：
  - 获取运输方式列表
  - 获取国家/地区列表
- 关键请求：
  - `billingAddress`
  - `openApiImportDSOrderList`
- `openApiImportDSOrderList` 中关键字段：
  - `dsPlatformId`
  - `goodsDetailDTOList`
  - `orderNumber`
  - `remark`
  - `shippingAddress`
  - `storeOrderAmount`
  - `storeOrderBusiId`
- `goodsDetailDTOList` 中字段：
  - `itemNo`
  - `quantityOrdered`
  - `shippingMethodId`
- 关键响应字段：
  - `orderSuccessResList`
  - `orderFailedResList`
  - `addressInvalidResList`
  - `goodRemovedResList`
  - `goodUnsupportResList`
  - `goodUnderStockResList`
  - `logisticsInvalidResList`
  - `encryptOrdBatchIds`
  - `ordBatchId`
  - `ordBusiId`
  - `orderPayURL`
- 关键结论：
  - `encryptOrdBatchIds` 是后续支付链的重要字段
  - `dsPlatformId` 为强制字段

### 2. 获取订单发货信息

- URL：`https://openapi.doba.com/api/order/doba/queryLogisTrack`
- 请求参数：
  - `ordBusiId`，最多 20
- 注意：
  - `businessData` 是数组
- 关键响应字段：
  - `logisComNameEn`
  - `logisShippingMethodNameEn`
  - `logisTrackDetails`
  - `ordBusiId`
  - `waybillId`

### 3. 确认订单已收到

- URL：`https://openapi.doba.com/api/order/doba/signOrder`
- 请求参数：
  - `ordBusiIds`，最多 20
- 注意：
  - `businessData` 是数组
- 关键字段：
  - `ordBusiId`

### 4. 取消订单

- URL：`https://openapi.doba.com/api/order/doba/closeOrder`
- 请求参数：
  - `closeReasonType`
    - `101` 误造订单
    - `102` 不再需要
    - `103` 付款失败
    - `104` 其他
  - `closerRemark`，最大 500
  - `ordBusiIds`，最多 20
- 注意：
  - `businessData` 是数组
- 关键字段：
  - `ordBusiId`
- 关键结论：
  - 属于高风险动作，后续应加审计和风控门槛

---

## 六、航运接口记忆（后期）

### 1. 获取运输方式列表

- URL：`https://openapi.doba.com/api/ship/list`
- 请求参数：无
- 响应字段：
  - `shipId`
  - `shipName`
  - `shipProdType`
- 关键结论：
  - 用于物流方式映射

### 2. 产品运输率估算

- URL：`https://openapi.doba.com/api/shipping/doba/cost/goods`
- 请求参数：
  - `shipToCountry`，必填
  - `shipToProvince`
  - `shipToCity`
  - `shipToZipCode`
  - `platformId`
  - `shipId`
  - `goods`，最多 20
- `goods[]` 字段：
  - `itemNo`
  - `quantity`
- 注意：
  - `businessData` 是数组
- 关键响应字段：
  - `itemNo`
  - `quantity`
  - `costs`
- `costs[]` 字段：
  - `shipId`
  - `shipName`
  - `shipFee`
  - `shipTime`
  - `onlineTime`
  - `currencyId`
  - `shippingMethodId`
  - `excludingProvince`
- 关键结论：
  - 这是物流成本估算和发货可达性判断的重要来源

---

## 七、支付接口记忆（后期）

### 1. 查询信用卡/借记卡列表

- URL：`https://openapi.doba.com/api/pay/payManage/doba/queryPaymentCardList`
- 请求参数：
  - `cardId`，可选
- 响应字段：
  - `cardHolderName`
  - `cardId`
  - `cardNum`
  - `cardSubType`
  - `cardType`
  - `expireDate`
- 关键结论：
  - 如果要卡支付，必须先获取 `cardId`
  - 属于敏感支付信息，应脱敏处理

### 2. 订单付款

- URL：`https://openapi.doba.com/api/pay/payment/doba/submit`
- 请求参数：
  - `encryptOrdBatchIds`，必填
  - `paymentMethodCode`，必填
    - `7` = PrePay
    - `0` = Credit/Debit Card
  - `cardId`
    - 卡支付时必填
- 响应字段：
  - `totalPay`
  - `ordPayBatchId`
- 关键结论：
  - 卡支付会产生交易费用
  - 支付动作属于高风险动作

---

## 八、基础信息接口记忆（后期）

### 1. 获取国家/地区列表

- URL：`https://openapi.doba.com/api/region/doba/country/list`
- 请求参数：
  - `countryCode`，可选
- 规则：
  - 不传：返回国家列表
  - 传国家代码：返回对应州/省列表
- 注意：
  - 用户提供的示例响应与接口用途不匹配
  - 只确认接口语义和请求逻辑，不确认示例字段模型

### 2. 获取第三方市场/平台列表

- URL：`https://openapi.doba.com/api/platform/list`
- 请求参数：无
- 响应字段：
  - `platformId`
  - `platformName`
- 关键结论：
  - 是 `dsPlatformId` / `platformId` 的来源

---

## 九、实现时必须记住的工程约束

### 批量上限

- SPU 详情：按当前规则每批最多 20
- 库存与价格：每批最多 20
- 运输率估算：goods 每批最多 20
- 订单发货信息：每批最多 20
- 确认订单已收到：每批最多 20
- 取消订单：每批最多 20
- 更新信息中的 `itemNo`：最多 100

### 高风险动作

后续需要风控或人工审核的动作：

- 发布商品
- 大幅价格调整
- 批量库存修改
- 自动下单
- 订单取消
- 订单支付

### 明确不应做的事情

- 不使用 `Manage Update Info`
- 不使用已废弃字段 `packagingInformation`
- 不让下游模块越层直接请求 Doba 原始接口
- 不把支付敏感信息写入普通日志

---

## 十、建议的后续接入顺序

1. Phase 00
   - 类目
   - 供应商
   - SPU 列表
   - SPU 详情
   - 更新流
   - 库存与价格
   - 标签与标签到 SPU 映射
2. Phase 01+
   - 基于归档数据进行产品筛选
3. 后期
   - 物流方式
   - 运费估算
   - 平台字典
   - 国家/地区字典
   - 订单导入
   - 物流追踪
   - 订单确认
   - 订单取消
   - 支付能力

---

## 十一、本文件用途

本文件可作为以下工作的本地参考：

- Supplier Archive 真实 Doba 适配器设计
- 契约建模与字段命名
- 分页/分片/限流策略设计
- 风控与支付流程设计
- 后续阶段开发边界校验

