# eBay GEO HTML Builder

`ebay-geo-html-builder` is a project-local skill for generating, optimizing, and finalizing eBay product description HTML.

It is designed for a one-pass workflow:

1. generate or rebuild eBay HTML from product images, listing notes, or an existing template
2. improve GEO, Google-search, and AI-search readability
3. scan and reduce risky wording
4. optionally polish copy with DeepSeek
5. optionally upload local images to ImgBB and rewrite HTML to public original-image URLs

## Location

The skill lives inside this repository:

`./.agents/skills/ebay-geo-html-builder/`

That means anyone who clones this repo and opens it in a compatible Codex-style agent can call the skill from inside this project.

## What It Contains

- `SKILL.md`
  - trigger rules, workflow, output naming, and finalization rules
- `agents/openai.yaml`
  - UI metadata such as display name and default prompt
- `assets/ebay-universal-template.html`
  - reusable eBay-safe HTML scaffold
- `references/`
  - GEO workflow, risk wording, invocation templates, and image-hosting notes
- `scripts/`
  - `extract_html_body.py`
  - `scan_risk_terms.py`
  - `deepseek_optimize_html.py`
  - `upload_to_imgbb.py`
  - `upload_html_images_to_imgbb.py`
  - `finalize_html_with_imgbb.py`

## Typical Outputs

Depending on the request, the skill usually writes one or more of these:

- `*-geo.html`
- `*-geo-body.html`
- `*-deepseek.html`
- `*-deepseek-body.html`
- `*-final.html`
- `*-final-body.html`
- `*-final-manifest.json`

## Environment Variables

Recommended variables in `.env`:

- `IMGBB_API_KEY`
  - required for final publishable HTML when local image paths must be uploaded and replaced
- `DEEPSEEK_API_KEY`
  - optional, used by `deepseek_optimize_html.py`
- `DEEPSEEK_BASE_URL`
  - optional if your DeepSeek-compatible endpoint is not the default
- `DEEPSEEK_MODEL`
  - optional, commonly `deepseek-chat`

`IMGBB_API_KEY` is the important one for publish-ready eBay description HTML with public image URLs.

## How To Call It

From a chat inside this repository, use one of these prompts.

### 1. GEO draft

```text
Use $ebay-geo-html-builder to generate a GEO-optimized eBay detail page from these product images and this template. Output full html and body html.
```

### 2. GEO + DeepSeek polish

```text
Use $ebay-geo-html-builder to generate the GEO version first, then run DeepSeek to polish the English copy without changing layout or image URLs.
```

### 3. Final publishable version

```text
Use $ebay-geo-html-builder to generate the final publishable eBay detail page.
If local image paths are present and IMGBB_API_KEY is configured, automatically upload images to ImgBB, replace them with original-image public URLs, and output final full html, final body html, and final manifest.
```

## Best Use Cases

Use this skill when you need to:

- build a new eBay detail page from product posters or images
- rewrite an old eBay HTML page into a cleaner GEO-friendly version
- reduce risky claims such as absolute safety, guaranteed outcomes, or medical-adjacent language
- convert a local-image HTML draft into a publishable public-URL version

## Notes For GitHub Users

- keep this skill in `./.agents/skills/` so it travels with the repo
- commit the skill files, references, and scripts
- do not commit `.env`
- before using ImgBB finalization, copy `.env.example` to `.env` and fill `IMGBB_API_KEY`
- before using DeepSeek polish, add your DeepSeek-compatible credentials to `.env`

## Validation

If you update the skill itself, validate it with:

```powershell
python C:\Users\Administrator\.codex\skills\.system\skill-creator\scripts\quick_validate.py .agents\skills\ebay-geo-html-builder
```
