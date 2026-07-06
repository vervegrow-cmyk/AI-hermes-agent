# Invocation Templates

Use these templates when the user wants a reusable copy-paste prompt for the skill.

## Short Chinese Templates

### 1. Generate a GEO draft

```text
用 $ebay-geo-html-builder 根据这些产品图、现有HTML和 ebay-universal-template.html 生成 eBay GEO 详情页，输出 full html 和 body html。
```

### 2. Generate GEO and then polish with DeepSeek

```text
用 $ebay-geo-html-builder 先生成 GEO 版 eBay 详情页，再用 DeepSeek 优化英文文案，保持 HTML 结构、样式和图片链接不变，输出 full html 和 body html。
```

### 3. Generate the final publishable version

```text
用 $ebay-geo-html-builder 生成这个产品的最终可发布版 eBay 详情页。
如果 HTML 里存在本地图片路径，且环境已配置 IMGBB_API_KEY，请自动上传图片到 ImgBB，替换为原图公网链接，并输出 final full html、final body html 和 final manifest。
```

## Short English Templates

### 1. Generate a GEO draft

```text
Use $ebay-geo-html-builder to generate a GEO-optimized eBay detail page from these product images, the current HTML, and ebay-universal-template.html. Output full html and body html.
```

### 2. Generate GEO and then polish with DeepSeek

```text
Use $ebay-geo-html-builder to generate the GEO version first, then run DeepSeek to polish the English copy while keeping the HTML structure, inline styles, and image URLs unchanged. Output full html and body html.
```

### 3. Generate the final publishable version

```text
Use $ebay-geo-html-builder to generate the final publishable eBay detail page. If local image paths are still present and IMGBB_API_KEY is configured, automatically upload the images to ImgBB, replace them with original-image public URLs, and output final full html, final body html, and final manifest.
```

## Recommended Default

When the user simply wants the end result and has not asked for a draft-first workflow, prefer this version:

```text
Use $ebay-geo-html-builder to generate the final publishable eBay detail page for this product, including GEO optimization, risk-term cleanup, and automatic ImgBB finalization when local image paths are present.
```
