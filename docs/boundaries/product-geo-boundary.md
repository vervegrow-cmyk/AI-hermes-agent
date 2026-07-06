# Product GEO Boundary

## Mission

Optimize existing Shopify `ACTIVE` products for:

- catalog understanding
- AI shopping assistant comprehension
- Google Merchant readiness
- OpenAI / ChatGPT product feed projection
- agentic commerce recommendation quality
- AI-understandable and AI-purchasable product readiness

## Core chain

The core chain is:

1. scan all Shopify `ACTIVE` saleable products
2. read title, description, images, variants, category, metafields, SEO, inventory, and price context
3. call DeepSeek for semantic understanding and GEO auditing
4. detect information gaps for Shopify Catalog, Google Merchant, OpenAI Product Feed, AI search, and AI shopping assistants
5. generate structured optimization suggestions
6. create before/after previews
7. safe-write only low-risk fields in later phases
8. route high-risk fields into manual review
9. snapshot every writeback and support rollback
10. monitor post-optimization quality over time

## Safe writeback classes

Low-risk fields that may become eligible in later phases:

- SEO title
- SEO description
- image alt
- GEO custom metafields
- FAQ metafields
- semantic profile metafields

## Approval-required fields

- product title
- handle
- product type
- category
- tags
- collections
- variant option name
- variant option value

## Forbidden fields

- SKU
- variant_id
- price
- inventory
- barcode
- GTIN
- checkout
- shipping rate
- live theme code
- orders
- GIGA order
- ad budget

## Phase13A boundary

Phase13A is strictly read-analyze-store.

The agent may:

- read Shopify product data
- call DeepSeek
- validate JSON output
- save audits, semantic profiles, recommendations, and snapshots
- form before/after preview data

The agent may not:

- write back to Shopify
- mutate operational commerce fields
- take any action that changes the live storefront
