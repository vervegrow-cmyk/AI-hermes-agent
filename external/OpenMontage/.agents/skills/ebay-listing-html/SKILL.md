# ebay-listing-html

Use this skill when the user wants a reusable eBay product description page in HTML, especially when they want:

- Amazon-style modular presentation adapted for eBay
- Pure HTML with inline CSS only
- Poster images first, then structured detail modules
- Safer copy that avoids unsupported claims
- A fixed Chinese output format plus copy-ready HTML

## What this skill produces

This skill standardizes the output into:

1. `【1. 素材分析结果】`
2. `【2. 详情页结构方案】`
3. `【3. 可直接复制到 eBay 的 HTML 源代码】`
4. `【4. 使用说明】`

If the user only wants the HTML file itself, you may skip the narrative sections and directly generate the HTML file.

## Required workflow

Follow these steps in order:

1. Analyze all uploaded or referenced images.
2. Classify each image into one of these roles:
   - Hero main image
   - Full poster / overview board
   - Detail / close-up image
   - Size image
   - Package image
   - Scenario / lifestyle image
   - Risky image
3. Flag risky content before writing HTML.
4. Use the first 1-2 strong poster images as full-width standalone sections.
5. Use later detail images in alternating table-based text-image modules.
6. Fill the universal template in `assets/ebay-universal-template.html`.
7. Keep the outer container full-width friendly to reduce eBay side whitespace.
8. Output final HTML that can be pasted into eBay `Show HTML Code`.

## Image risk rules

Do not silently trust the uploaded graphics. Check for:

- Third-party brands or logos
- Wrong battery life, size, power, material, rating, or count
- Unsupported claims like waterproof, IPX4, medical, certified, guaranteed
- Color or package contents that do not match the current listing

If the user explicitly asks to use all images anyway, still warn about the risk in `素材分析结果`, then proceed.

## eBay compatibility rules

Always follow these rules:

- No JavaScript
- No iframe
- No form
- No button
- No external CSS
- No external font dependency
- No video embed
- No outbound purchase links
- Inline CSS only
- Prefer simple `table` layout for 2-column sections
- Every image must use:

```html
style="width:100%;max-width:100%;height:auto;display:block;"
```

- Avoid narrow centered wrappers that create large left/right blank margins inside eBay
- Prefer:
  - outer wrapper `width:100%;margin:0;padding:0;`
  - inner content `width:100%;margin:0;`

## Copywriting rules

Write natural US-English product copy.

Do:

- Keep headings short and scan-friendly
- Repeat core attributes naturally across title, subtitle, features, module headings, specs, and FAQ
- Keep tone practical and buyer-focused
- Use concise feature explanations in 2 short paragraphs per module

Do not:

- Invent features
- Exaggerate performance
- Use unsupported compliance language
- Use platform words like Amazon, Prime, Best Seller

## GEO optimization rules

This skill includes a DeepSeek-style GEO optimization approach as a writing method, not as an external API call.

Apply these rules:

1. Keep the main keyword in:
   - title
   - subtitle
   - first paragraph
   - at least 2 module headings
2. Cover buyer-intent phrases naturally:
   - what it is
   - who it is for
   - where it is used
   - what problem it helps with
3. Spread important attributes across the page:
   - size
   - color
   - material
   - power / battery / charging
   - compatibility / use scenarios
4. Do not keyword-stuff.
5. Keep language readable for eBay mobile users.

## Inputs to request or infer

When available, collect:

- Product title
- Product subtitle
- 4 core tags
- 6-8 feature bullets
- 1-2 poster images
- 4-6 detail images
- Specs list
- Package includes
- Use note
- Shipping/service wording
- Forbidden words or risky claims

If some items are missing, infer conservatively from the provided product facts and images.

## Files in this skill

- Template: `assets/ebay-universal-template.html`
- Workflow: `references/workflow.md`
- Reusable prompt: `references/prompt-template.md`

## Default structure

Unless the user requests a different order, use:

1. Header title block
2. Key features table
3. Quick product summary
4. Poster image 1
5. Poster image 2
6. 4-6 alternating detail modules
7. Specifications
8. Suitable For + Package Includes
9. FAQ
10. Use Note
11. Shipping & Service

## Output notes

- When writing files locally, save a full page HTML file.
- If useful, also provide a body-only eBay paste variant.
- In the final answer, include clickable local file links when a file was created.
