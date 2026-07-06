# ProductAgenticGEOAgent

`ProductAgenticGEOAgent` is a dedicated optimization agent for Shopify products that are already live and saleable.

It is explicitly not:

- a product listing agent
- a theme beautification agent
- an ad buying agent
- an order or checkout automation agent

Its job is to scan all Shopify `ACTIVE` products, read title, description, images, variants, category, metafields, SEO, inventory, and price context, call DeepSeek for semantic understanding and GEO auditing, detect information gaps across Shopify Catalog, Google Merchant, OpenAI Product Feed, AI search, and AI shopping assistants, generate structured before/after optimization recommendations, and prepare low-risk safe writeback plus high-risk human review workflows.

## Mainline

The intended mainline is:

1. Scan Shopify `ACTIVE` saleable products.
2. Normalize a `ShopifyProductSnapshot`.
3. Call DeepSeek with strict JSON output.
4. Score GEO, catalog, merchant, feed, schema, and agentic UX readiness.
5. Generate structured suggestions for title, description, FAQ, image alt, schema, feed, trust signals, and search intent.
6. Produce before/after previews.
7. Allow only low-risk fields into safe writeback.
8. Route high-risk fields into manual review.
9. Persist snapshots for rollback and long-term monitoring.

## Scope

Phase13A includes:

- scan Shopify `ACTIVE` and published products
- load a `ShopifyProductSnapshot`
- call DeepSeek with strict JSON output
- generate GEO audit, semantic profile, and structured recommendations
- build Google Merchant, OpenAI product feed, and schema projections
- save recommendations and snapshots
- form before/after preview payloads
- do not write back to Shopify

## Architecture

The TypeScript scaffold follows:

`Router -> Orchestrator -> Agent -> Skill -> Service -> Repository`

Main entrypoints:

- [product-agentic-geo.router.ts](/D:/桌面文件下载/AI-hermes-agent/packages/agents/product-agentic-geo-agent/product-agentic-geo.router.ts)
- [product-agentic-geo.orchestrator.ts](/D:/桌面文件下载/AI-hermes-agent/packages/agents/product-agentic-geo-agent/product-agentic-geo.orchestrator.ts)
- [product-agentic-geo.agent.ts](/D:/桌面文件下载/AI-hermes-agent/packages/agents/product-agentic-geo-agent/product-agentic-geo.agent.ts)

## Boundaries

Allowed in Phase13A:

- read Shopify product data
- score GEO readiness
- generate semantic profiles
- generate SEO, FAQ, image alt, schema, Merchant, and OpenAI projection suggestions
- store before and after snapshots of the audit run
- prepare low-risk safe writeback candidates for later phases

Not allowed in Phase13A:

- modify Shopify product data
- change SKU, variant_id, price, inventory, barcode, or GTIN
- touch checkout, shipping rate, live theme code, orders, or ad budget

Later phases may allow low-risk writeback for:

- SEO title
- SEO description
- image alt
- GEO custom metafields
- FAQ metafields
- semantic profile metafields

Manual review remains mandatory for:

- product title
- handle
- product type
- category
- tags
- collections
- variant option name
- variant option value

## Environment variables

- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL`
- `DEEPSEEK_MODEL`
- `SHOPIFY_ADMIN_ACCESS_TOKEN` or `SHOPIFY_TOKEN`
- `SHOPIFY_SHOP_DOMAIN` or `SHOPIFY_STORE` or `SHOPIFY_SHOP`
- `SHOPIFY_API_VERSION`

## Output artifacts

Phase13A persists four core record shapes in repository contracts:

- `product_geo_audits`
- `product_semantic_profiles`
- `product_geo_recommendations`
- `product_geo_writeback_snapshots`
