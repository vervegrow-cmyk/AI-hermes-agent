# eBay GEO Workflow

## Goal

Create an eBay description page that is:
- easy for eBay search to categorize
- easy for Google and AI systems to summarize
- readable like a normal product page
- safe from obvious compliance overclaims

## Minimum Page Structure

For most listings, keep this order:

1. kicker
2. title
3. subtitle or first-screen summary
4. tags or chips
5. key features
6. quick product summary
7. poster images
8. alternating detail modules
9. specifications
10. training uses or suitable-for section
11. package includes
12. common questions
13. use note
14. shipping and service

## Title Formula

Use this order when possible:

`Core product type + size or quantity + defining feature + user context`

Examples:
- `3-in-1 Foam Plyometric Jump Box 12/14/16 in Soft Plyo Box Home Gym`
- `Spin Mop Replacement Head Set 6 Pack Microfiber Mop Refills for 360 Spin Mop`

Avoid:
- filler adjectives with no search value
- all-caps hype
- claims that need proof but are not documented

## GEO Copy Signals To Include

Every page should clearly answer:
- what is this product
- who is it for
- what can it be used for
- what makes it different from adjacent product types
- what size, material, or compatibility constraints matter

Good GEO content naturally includes:
- product-definition paragraphs
- scenario-based detail sections
- specifications table
- FAQ section
- descriptive image alt text

## Copywriting Pattern

### First-screen summary

Use 1-2 sentences that define:
- product type
- user type
- main use cases

### Quick product summary

Use 2-3 short paragraphs:
- paragraph 1: product definition and audience
- paragraph 2: use cases and dimensions or compatibility
- paragraph 3: materials, finish, convenience, or care

### Detail modules

Each module should do one job:
- explain one feature
- connect that feature to a realistic use case
- repeat the core product term naturally

### FAQ

FAQ should target long-tail search phrases users would ask directly:
- dimensions or compatibility
- who it is best for
- where it can be used
- whether it is easy to clean, assemble, refill, store, or transport

## Image Alt Text

Alt text should describe the image in product-search language, not generic accessibility-only wording.

Use:
- product type
- relevant feature
- relevant use case

Example:
- `Soft plyo box for box jumps step-ups squats and HIIT workouts`

Avoid:
- keyword dumps
- punctuation-heavy fragments
- risky claims such as guaranteed safety or zero slip

## Deliverables

When possible, produce:
- `full html`
- `body html`
- optional `deepseek` variants
- optional `imgbb-hosted` variants when local images must become public links

## Image Hosting Workflow

If the page contains local image paths and the target platform needs public URLs:

1. Prefer stable local filenames before upload.
2. Upload the images with `scripts/upload_to_imgbb.py` if you only need links.
3. Use `scripts/upload_html_images_to_imgbb.py` if you want the HTML rewritten automatically.
4. Re-check alt text and ordering after rewrite.
5. Keep the rewritten output as a new file rather than silently overwriting the source unless the user asked for replacement.

## Final Review Checklist

- Title clearly defines the product
- First summary defines audience and use
- Long-tail phrases appear naturally
- FAQ covers common buyer queries
- Specifications are concrete
- Alt text is descriptive
- No scripts or framework markup
- No obvious risky or medicalized claims
