---
name: ebay-geo-html-builder
description: "Build or optimize eBay product description HTML for GEO, Google search understanding, and eBay conversion while preserving an existing template structure. Use when the user wants to: (1) generate a new eBay detail page from product images, an existing listing, or a universal HTML template, (2) improve an existing eBay HTML page for GEO/SEO/AI-search clarity, (3) rewrite eBay product copy to be more compliant and search-friendly, (4) optionally run DeepSeek to polish the finished HTML without changing layout, or (5) finalize a ready-to-publish eBay HTML by uploading local images to ImgBB, replacing local paths with public original-image URLs, and exporting matching full/body deliverables."
---

# Ebay Geo Html Builder

## Overview

Generate structured, compliant, search-friendly eBay product description HTML from a template or existing listing. Preserve layout first, then improve product definition, GEO language, FAQ coverage, alt text, and risk wording.

Prefer the fully automated finalization path when the user clearly wants a publish-ready result and the environment already has `IMGBB_API_KEY`.

## Workflow

1. Read any repository-level instructions first if working inside a project that requires routing files such as `AGENT_GUIDE.md`.
2. Identify the source inputs:
   - product images or image notes
   - existing `full html` and/or `body html`
   - a universal template such as `ebay-universal-template.html`
   - GEO optimization notes from the user
3. Preserve the structural contract before editing copy:
   - keep the section order
   - keep image URLs unless the user asks to change them
   - keep inline-style compatibility for eBay
   - produce both a `full html` and a `body html` version when practical
4. Extract the product definition before writing:
   - what the product is
   - who it is for
   - main use cases
   - materials, dimensions, included parts, and constraints
   - core keywords, long-tail keywords, scene words, and risky phrases
5. Build the GEO-safe version first by hand:
   - clear title
   - strong first-screen summary
   - key features table
   - product summary
   - image alt text
   - detail modules
   - specifications
   - suitable-for or package section
   - common questions
   - use note and service note
6. Read [references/workflow.md](references/workflow.md) when you need title formulas, required sections, or output rules.
7. Read [references/risk-terms.md](references/risk-terms.md) when you need safer replacements for risky eBay wording or need FAQ templates.
8. If the user wants DeepSeek optimization, or the environment clearly has DeepSeek configured, run `scripts/deepseek_optimize_html.py` on the stabilized HTML.
9. After DeepSeek output, do a human review:
   - remove any overly absolute claims it reintroduces
   - preserve the HTML structure
   - make sure the key long-tail phrases still feel natural
10. If the listing still uses local image paths and the user wants public image hosting, use ImgBB:
   - run `scripts/upload_to_imgbb.py` to upload one image or a whole folder and return public links
   - run `scripts/upload_html_images_to_imgbb.py` to upload local HTML image sources and rewrite them to `i.ibb.co` URLs
   - prefer original-image URLs, not ImgBB medium/display URLs, so eBay detail images stay sharp
11. If the user wants a final ready-to-paste eBay deliverable and local image paths are present, prefer the one-shot finalization path:
   - run `scripts/finalize_html_with_imgbb.py`
   - this uploads local HTML images to ImgBB, writes a rewritten `full html`, writes a matching `body html`, and saves an upload manifest
   - treat this as the default path when all are true:
     - the user wants a final or publish-ready result
     - local image paths are still present in HTML
     - `IMGBB_API_KEY` is configured
12. If only a full HTML exists and a body-only version is needed, run `scripts/extract_html_body.py`.
13. Before finalizing, run `scripts/scan_risk_terms.py` if the listing is safety-sensitive, medical-adjacent, or full of aggressive marketing claims.

## Default Decision Rules

- Generate `*-geo.html` and `*-geo-body.html` when the user wants a draft, a structure-first version, or a GEO-only revision.
- Generate `*-deepseek.html` and `*-deepseek-body.html` only when the user explicitly asks for DeepSeek or when polishing quality is clearly part of the request.
- Generate `*-final.html`, `*-final-body.html`, and `*-final-manifest.json` when the user wants the final publishable version and local image paths are present.
- If an older `*-imgbb*.html` naming pattern already exists in the working directory, do not overwrite it silently; create the newer `*-final*` outputs unless the user asks to replace the older files.

## Invocation Templates

Use the short prompts below when the user wants a predictable outcome and minimal back-and-forth.

- GEO draft:
  - `Use $ebay-geo-html-builder to generate a GEO-optimized eBay detail page from these product images and this template. Output full html and body html.`
- GEO + DeepSeek:
  - `Use $ebay-geo-html-builder to generate the GEO version first, then run DeepSeek to polish the English copy without changing layout or image URLs.`
- Final publishable version:
  - `Use $ebay-geo-html-builder to generate the final publishable eBay detail page. If local image paths are present and IMGBB_API_KEY is configured, automatically upload images to ImgBB, replace them with original-image public URLs, and output final full html, final body html, and final manifest.`

Read [references/invocation-templates.md](references/invocation-templates.md) when the user wants copy-paste prompt templates in Chinese or English.

## Output Rules

- Prefer ASCII-only HTML.
- Keep HTML eBay-safe: no script tags, no embedded stylesheets, no framework markup.
- Keep copy specific, natural, and product-defining rather than keyword-stuffed.
- Favor phrases that help search systems understand:
  - product type
  - intended user
  - workout or usage scenarios
  - dimensions or compatibility
  - included items
- Avoid promising results, safety guarantees, or medical positioning.
- If generating multiple variants, name them clearly:
  - `*-geo.html`
  - `*-geo-body.html`
  - `*-deepseek.html`
  - `*-deepseek-body.html`
  - `*-final.html`
  - `*-final-body.html`
  - `*-final-manifest.json`

## Naming Guidance

- Use `*-geo.*` for the first structured draft.
- Use `*-deepseek.*` for the polished text-only revision.
- Use `*-final.*` for the publish-ready version with public image links.
- Keep older compatibility names only when the repo or user explicitly depends on them.

## When To Use DeepSeek

Use DeepSeek after the HTML is already structurally correct and compliant enough to polish. Do not use it as a substitute for understanding the product, choosing the template structure, or performing risk cleanup.

Use `scripts/deepseek_optimize_html.py` when:
- the user explicitly asks for DeepSeek
- the environment has `DEEPSEEK_API_KEY`
- you want a smoother commercial tone without changing layout

Do not let DeepSeek silently:
- remove required sections
- add scripts or markdown fences
- change image URLs
- introduce risky absolute claims such as injury prevention, guaranteed safety, zero risk, or medical recovery language

## ImgBB Finalization Rules

- Prefer the one-shot `scripts/finalize_html_with_imgbb.py` path over manually chaining upload and body extraction when the goal is final delivery.
- Rewrite HTML to ImgBB original-image URLs, not the `display_url` medium image, because eBay enlarges detail images and medium links can appear blurry.
- Save the manifest even when only one image is uploaded so the mapping can be reused later.
- If the HTML already contains remote image URLs, leave them unchanged unless the user explicitly asks to rehost everything.

## Resources

### Template asset

Use [assets/ebay-universal-template.html](assets/ebay-universal-template.html) as the default structural scaffold for standard eBay detail pages.

### Scripts

- `scripts/extract_html_body.py`
  Use to extract the inner `<body>` content from a full eBay HTML file.
- `scripts/deepseek_optimize_html.py`
  Use to polish an existing HTML file with DeepSeek while keeping structure intact.
- `scripts/upload_to_imgbb.py`
  Use to upload one image or an entire folder to ImgBB and return public URLs.
- `scripts/upload_html_images_to_imgbb.py`
  Use to find local image sources inside HTML, upload them to ImgBB, and rewrite the HTML to public image URLs.
- `scripts/finalize_html_with_imgbb.py`
  Use for the one-shot finishing flow: upload local HTML images to ImgBB, rewrite the full HTML, export the matching body HTML, and save a manifest in one run.
- `scripts/scan_risk_terms.py`
  Use to scan HTML for risky compliance phrases and suggest safer replacements.

### References

- [references/workflow.md](references/workflow.md)
  Read for title formulas, section requirements, GEO signals, and output checklist.
- [references/risk-terms.md](references/risk-terms.md)
  Read for risky phrase replacements, safer wording patterns, FAQ templates, and long-tail wording examples.
- [references/invocation-templates.md](references/invocation-templates.md)
  Read for reusable copy-paste prompts covering draft, DeepSeek, and final publishable runs.
