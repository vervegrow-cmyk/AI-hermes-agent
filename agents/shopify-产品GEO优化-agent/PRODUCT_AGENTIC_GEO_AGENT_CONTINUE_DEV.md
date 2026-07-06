# ProductAgenticGEOAgent 连续开发任务

当前项目目录：

`D:\桌面文件下载\AI-hermes-agent\agents\shopify-产品GEO优化-agent`

本项目用于串行优化 Shopify 现有 `ACTIVE` 在售商品，让商品同时适配：

- Shopify Catalog
- Google Merchant
- OpenAI Product Feed
- AI 搜索
- AI Shopping / Agentic Shopping

当前主链要求：

1. 扫描 Shopify `ACTIVE` 商品
2. 读取商品基础数据、SEO、图片、变体、metafields、类目、库存和价格
3. 创建 `before snapshot`
4. 生成 `before_geo_score`
5. 调用 DeepSeek 生成结构化优化建议
6. 生成 `preview_after_geo_score`
7. 先过写回门槛，再决定是否允许真实写回
8. 写回 Shopify 后重新读取真实商品
9. 生成 `final_after_geo_score`
10. 发布到所有可用销售渠道
11. 保存 checkpoint、snapshot、audit、execution log
12. 打印中文详细日志

默认真实写回门槛：

- `preview_after_geo_score >= 75`
- `preview_score_delta >= 10`
- 未触碰 forbidden fields
- `safe_writeback_plan` 校验通过

如果不满足门槛：

- 默认阻止写回
- 默认阻止销售渠道发布
- 仅保存建议、审计、checkpoint 和快照

支持的主链命令：

```powershell
Set-Location -LiteralPath "D:\桌面文件下载\AI-hermes-agent\agents\shopify-产品GEO优化-agent"
```

功能：
进入项目目录。

```powershell
npm install
```

功能：
安装项目依赖。

```powershell
npm run shopify:geo:dry-run
```

功能：
串行扫描 ACTIVE 商品，只做读取、评分、DeepSeek 分析、建议生成、checkpoint 保存和中文日志打印，不写回 Shopify。

```powershell
npm run shopify:geo:dry-run -- --limit 10
```

功能：
只对前 10 个 ACTIVE 商品执行 dry-run。

```powershell
npm run shopify:geo:optimize-active
```

功能：
执行真实 GEO 优化，默认只有预览评分达标才允许写回 Shopify 并发布销售渠道。

```powershell
npm run shopify:geo:optimize-active -- --limit 1
```

功能：
只真实测试 1 个商品，适合验证写回、复评分和日志。

```powershell
npm run shopify:geo:optimize-active -- --allow-partial-writeback
```

功能：
允许 `PARTIAL_PASS` 商品在用户明确授权时也进行真实写回。

```powershell
npm run shopify:geo:optimize-active -- --strict-pass-only
```

功能：
只允许完整 `PASS` 继续执行，遇到 `PARTIAL_PASS` 也停止。

```powershell
npm run shopify:geo:optimize-active -- --from-product-id gid://shopify/Product/10213639717170
```

功能：
从指定 Shopify Product ID 开始执行主链。

```powershell
npm run shopify:geo:resume
```

功能：
从最近一个未完成 run 的 checkpoint 继续执行，已完成商品会自动跳过。

```powershell
npm run shopify:geo:resume -- --force-retry-failed
```

功能：
强制从上次失败商品重新开始恢复执行。

```powershell
npm run shopify:geo:status
```

功能：
查看最近一个可恢复任务的 `run_id`、当前商品、阶段、完成数、失败数和恢复命令。

```powershell
npm run shopify:geo:reset-checkpoint
```

功能：
将未完成 run 标记为失败并关闭恢复标记，但不会删除历史审计、快照和执行日志。

```powershell
npm run product-geo:export -- --product-id=gid://shopify/Product/你的商品ID
```

功能：
导出当前商品的 Google Merchant / OpenAI Feed / Schema 结构化 JSON。

```powershell
npm run product-geo:rollback -- --snapshot-id=你的_snapshot_id
```

功能：
按 snapshot 回滚指定商品的写回内容。
