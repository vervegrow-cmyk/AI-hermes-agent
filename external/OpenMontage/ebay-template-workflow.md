# eBay Detail Page Workflow

## Fixed Structure

Use [ebay-universal-template.html](D:/桌面文件下载/AI-hermes-agent/external/OpenMontage/ebay-universal-template.html) as the locked base.

This structure is already tuned for eBay:

1. Full-width outer layout to reduce left/right white margins
2. Inline CSS only
3. First 1-2 poster images shown as full-width visual sections
4. Detail images shown in alternating table-based text/image modules
5. Specs, package, note, and shipping sections kept compact

## What To Upload Next Time

For a new product, provide:

1. Product title
2. Short subtitle
3. 4 core tags
4. 6-8 key feature bullets
5. 1-2 poster images
6. 4-6 detail or close-up images
7. Specs table content
8. Package includes
9. Use note
10. Any forbidden words or unverified claims

## Best Prompt Pattern

Use this format when asking for a new eBay page:

```text
请基于我现在使用的 ebay-universal-template.html 结构生成新的 eBay 详情页。

要求：
1. 保持现有 HTML 结构风格不变
2. 前两张综合海报图整屏展示
3. 后续细节图按左右交错图文模块排版
4. 所有样式继续使用 inline CSS
5. 继续优先兼容 eBay，避免左右大白边
6. 不要使用 JavaScript、iframe、外部 CSS
7. 不要写未确认参数
8. 输出最终完整 HTML，并直接另存为一个新的本地 html 文件

产品标题：
{{产品标题}}

副标题：
{{副标题}}

4个标签：
{{标签1}}
{{标签2}}
{{标签3}}
{{标签4}}

卖点：
{{卖点列表}}

规格：
{{规格列表}}

包装清单：
{{包装清单}}

注意事项：
{{注意事项}}

禁用词 / 风险词：
{{禁用词}}

以下是我上传的图片，请分析后直接套入这个固定模板：
{{图片}}
```

## Reuse Rule

Future optimization should be done by:

1. Replacing placeholders and product copy
2. Reordering image modules when needed
3. Adjusting only spacing, not the overall frame logic

Do not switch back to centered narrow wrappers unless the user explicitly wants larger side margins.
