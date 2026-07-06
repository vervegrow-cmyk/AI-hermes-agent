# doba-shopify-agent

## Modular Runtime Status

This agent now uses an isolated modular runtime under `src/` while keeping the
existing FastAPI routes compatible.

Core structure:

```text
src/
  app/
  shared/contracts/
  shared/repositories/
  modules/product_screening/
  modules/shopify_listing/
  modules/inventory_sync/
  modules/price_sync/
  modules/risk_control/
  modules/sku_mapping/
tests/
  contracts/
  integration/
  inventory_sync/
  price_sync/
  product_screening/
  risk_control/
  shopify_listing/
  sku_mapping/
```

Module boundaries are documented in `docs/module-boundaries.md`.

## Test Commands

Documented command aliases:

- `test:product-screening` -> `python -m pytest tests/product_screening`
- `test:shopify-listing` -> `python -m pytest tests/shopify_listing`
- `test:inventory-sync` -> `python -m pytest tests/inventory_sync`
- `test:price-sync` -> `python -m pytest tests/price_sync`
- `test:contracts` -> `python -m pytest tests/contracts`
- `test:doba-shopify-agent` -> `python -m pytest tests`

## Daily Commands

### Force Publish Doba Catalog To Shopify Channels

Use the repository root as `PYTHONPATH`, then run the vendor publish runner from
this agent folder:

```powershell
$env:PYTHONPATH='D:\桌面文件下载\AI-hermes-agent'
.\.venv\Scripts\python.exe -m src.app.runners.run_publish_vendor_catalog --vendor Doba --channels "Online Store" "Shop" "Pinterest" "Facebook & Instagram" --report-path "docs/audits/doba-force-publish-report.json"
```

This command will:

- scan products where `vendor == Doba`
- publish them to `Online Store`, `Shop`, `Pinterest`, and `Facebook & Instagram`
- write the execution report to `docs/audits/doba-force-publish-report.json`

Detailed command manual:

- `docs/common-commands-manual-20260614.md`

## Current Status

This directory now contains a runnable first-phase agent scaffold.

It supports:

- shared Hermes runtime integration
- Doba product normalization
- hard rejection rules
- manual-review vs approved decisioning
- Shopify draft publish stubs for approved products
- local tests from this folder

Preparation files added for real integration readiness:

- `docs/integration-checklist.md`
- `docs/doba-field-mapping.md`
- `docs/shopify-publish-rules.md`
- `docs/stub-todo.md`
- `tests/fixtures/approved_product.json`
- `tests/fixtures/manual_review_product.json`
- `tests/fixtures/rejected_product.json`
- `tests/fixtures/batch_products.json`

Current API routes:

- `GET /health`
- `POST /execute`
- `POST /evaluate-product`
- `POST /evaluate-batch`
- `POST /publish-approved`

## Local Development

From this folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe main.py
```

Run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Docker build from this folder, using the repository root as build context:

```powershell
docker build -f Dockerfile ../..
```

## Purpose

This agent is intended to select eligible Doba products and publish them to Shopify
through the shared Hermes platform runtime.

## Shared Environment Assumptions

This agent should follow the same repository rules as the other agents:

- Reuse `shared/` modules for settings, logging, runtime, and storage.
- Reuse the root `.env` and shared service stack.
- Do not create a separate database or private runtime.
- Expose at least `GET /health` and `POST /execute`.

Current shared runtime already includes Shopify-related configuration. Doba-specific
configuration is not defined yet and will need to be added.

## Recommended Agent Scope

This agent should own the product selection and listing decision flow:

1. Pull candidate products from Doba.
2. Normalize Doba product data into an internal schema.
3. Apply hard filters to reject obviously ineligible products.
4. Apply business scoring for margin, shipping, and content quality.
5. Send only approved products to Shopify as draft or controlled publish targets.
6. Persist decision logs so every rejection or approval is explainable.

This agent should not own:

- Storefront theme rendering
- Long-form marketing content generation
- Trend discovery outside product selection
- Independent inventory databases outside shared storage

## Proposed Decision States

Each candidate product should end in one of three states:

- `approved`: safe to create in Shopify
- `manual_review`: missing confidence or borderline metrics
- `rejected`: should not be listed

## Listing Rules

### Must pass

A product is eligible only if all of the following are true:

- It has a stable supplier product ID or SKU.
- It has a non-empty title and a usable primary image.
- It has a valid sell price, cost, and inventory value.
- It has enough product attributes to build a Shopify listing.
- It can ship to the target market within an acceptable SLA.
- It does not fall into a restricted or prohibited category.
- It does not create obvious legal, safety, or IP risk.
- It leaves enough margin after shipping, fees, and buffer.

### Reject immediately

Reject without scoring if any of the following is true:

- Missing SKU or supplier identifier
- Missing title
- Missing price or zero price
- Missing inventory or inventory less than minimum threshold
- Missing main image
- Supplier status is inactive, discontinued, or backordered without ETA
- Product category is restricted by Shopify or local law
- Product appears to contain weapons, adult content, tobacco, vaping, drug paraphernalia, or hazardous materials
- Product makes medical, therapeutic, or regulated ingestible claims without a compliant review path
- Product is branded in a way that suggests counterfeit or unauthorized resale risk
- Shipping cost or package size makes the listing obviously unprofitable
- Product is already listed in Shopify and duplicate policy says skip

### Manual review

Send to manual review when the product is not clearly bad, but confidence is not high:

- Margin is above break-even but below target threshold
- Shipping time is long but still within a defined upper bound
- Product title or description quality is poor and needs cleanup
- Category mapping to Shopify taxonomy is uncertain
- Brand ownership or resale permission is unclear
- Variant structure is messy or incomplete
- Images exist but quality is borderline
- Product includes batteries, cosmetics, supplements, medical-adjacent claims, or child-safety implications

## Recommended Filter Dimensions

### 1. Supplier viability

- Supplier status must be active
- Product must not be discontinued
- Product inventory must be above a configurable minimum
- Product should have recent inventory updates if Doba exposes update timestamps

### 2. Catalog completeness

Required minimum fields:

- supplier product id
- sku
- title
- brand if available
- category
- cost
- sell price input or pricing basis
- inventory
- weight or package dimensions if shipping is calculated
- main image
- description or bullet attributes

If more than one of the core merchandising fields is missing, reject the product.

### 3. Commercial viability

Suggested first-pass thresholds:

- minimum gross margin dollars: `>= 15`
- minimum gross margin rate: `>= 25%`
- shipping cost to retail price ratio: `<= 35%`
- minimum retail price floor: `>= 25`
- avoid very low-ticket products unless bundle logic exists

Suggested formula:

`expected_profit = target_sale_price - supplier_cost - shipping_cost - shopify_fee_buffer - ad_buffer`

If expected profit is below threshold, reject.

### 4. Fulfillment quality

- Ships to the target market
- Estimated delivery time within target SLA
- No oversize or overweight exception unless explicitly allowed
- No fragile or return-heavy item classes in phase one

For phase one, prefer products that are:

- small parcel
- easy to describe
- low breakage risk
- low return complexity

### 5. Compliance and policy risk

Default reject list for phase one:

- weapons and weapon accessories
- adult products
- tobacco, nicotine, or vaping products
- supplements and ingestibles
- medical devices or treatment-claim products
- hazardous chemicals or flammable materials
- counterfeit-risk branded goods
- products aimed at children with unclear safety compliance

### 6. Content quality

Approve only when the product can produce a minimally acceptable Shopify PDP:

- title can be normalized into a clear product name
- description is understandable and not spammy
- at least 2 to 3 usable images are preferred
- image resolution is acceptable
- major attributes are available for bullets or metafields

### 7. Shopify fit

- Category can map to a Shopify product category or internal taxonomy
- Variants can be represented cleanly
- No obvious duplicate handle or duplicate SKU collision
- Product status should default to draft for early rollout

## Phase One Product Preference

To reduce operational risk, phase one should prefer:

- unbranded or low-IP-risk home goods
- simple lifestyle accessories
- lightweight storage or organization products
- products with clear utility and low explanation cost
- products with stable inventory and short shipping windows

Phase one should avoid:

- electronics with warranty complexity
- high-return apparel sizing problems
- fragile furniture or large parcels
- regulated beauty or health items
- trending products with unclear compliance

## Minimum Data Contract From Doba

Before implementation, confirm that the Doba source can provide:

- supplier id
- product id
- sku
- title
- brand
- category path
- cost
- map or msrp if available
- inventory quantity
- warehouse or ship-from country
- shipping price or shipping rules
- lead time or ETA
- weight and package dimensions
- description
- image URLs
- variant attributes
- product status

If Doba cannot provide shipping, inventory, or status reliably, the agent should not
auto-publish and should stay in `manual_review` mode.

## Proposed Execution Flow

Recommended service breakdown:

- `service/doba_client.py`: fetch and paginate Doba products
- `service/normalizer.py`: map Doba fields into internal product schema
- `service/filter_engine.py`: hard filters and scoring rules
- `service/shopify_client.py`: create draft products in Shopify
- `service/decision_log.py`: persist approval and rejection reasons
- `workflow/publish_candidates.py`: orchestration entrypoint

Suggested task names:

- `sync-candidates`
- `evaluate-product`
- `evaluate-batch`
- `publish-approved`
- `recheck-manual-review`

## Config To Add

Likely new environment variables:

- `DOBA_API_BASE_URL`
- `DOBA_API_KEY`
- `DOBA_API_SECRET`
- `DOBA_DEFAULT_MARKET`
- `DOBA_ALLOWED_SHIP_FROM_COUNTRIES`
- `DOBA_MIN_INVENTORY`
- `DOBA_MIN_MARGIN_DOLLARS`
- `DOBA_MIN_MARGIN_RATE`
- `DOBA_MAX_SHIPPING_RATIO`
- `DOBA_MAX_DELIVERY_DAYS`
- `DOBA_RESTRICTED_CATEGORIES`
- `DOBA_MANUAL_REVIEW_CATEGORIES`

These are already expected by the current code path through shared settings. Real
API integration still needs the final Doba auth contract and Shopify API choice.

## Implementation Order

Recommended build order:

1. Scaffold the FastAPI agent from the shared template.
2. Define the normalized product schema and decision schema.
3. Implement hard filters with explainable rejection reasons.
4. Add profitability and shipping scoring.
5. Add Shopify draft creation only for `approved` products.
6. Persist decisions to shared Postgres.
7. Add tests for approved, manual review, and rejected cases.

## Open Questions

These decisions should be confirmed before coding:

- Which Doba API or export format will be used
- Which market is the first publish target
- Whether listings should start as draft only
- Whether duplicate checking uses Shopify SKU, handle, or both
- Whether brand-name products are allowed at all in phase one
- Whether margin thresholds differ by category
- Whether shipping cost is known before listing time

## Recommended Next Step

The next concrete step is to scaffold the agent and encode the hard filter engine first.

That gives us a safe pipeline:

- pull product
- normalize
- score
- explain reject or approve

Only after that should we connect automated Shopify product creation.
