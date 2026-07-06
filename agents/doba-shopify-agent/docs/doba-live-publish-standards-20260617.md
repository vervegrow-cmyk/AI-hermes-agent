# Doba Live Publish Standards 20260617

## Purpose

This document defines the mandatory development standards and completion goals
for the real Doba -> Shopify publishing workflow in this repository.

It is the project-level source of truth for:

- runtime boundaries
- archive and candidate-pool design
- Shopify publish rules
- logging and checkpoint behavior
- performance expectations
- definition of done

## Core Objective

Build a real, resumable, high-throughput Doba -> Shopify publish pipeline that:

- reads Doba product data once into local archive records
- derives a qualified publish candidate pool from archive data
- publishes one real Shopify product at a time
- merges all SKUs of the same Doba product into one Shopify product
- avoids repeated full-catalog rescans during live publish

## Mandatory Architecture Standards

### 1. Archive-first

All downstream modules must prefer local archive data over re-fetching raw Doba
data.

Mandatory consumers:

- Shopify Listing Runtime
- Inventory Sync
- Price Sync
- Risk Control

Allowed exception:

- the archive collector may call Doba directly
- live publish may call Shopify directly
- live publish may call Doba only when archive fields are truly missing and the
  missing fields block a publish decision

### 2. Two-stage pipeline

The workflow must be split into two distinct stages:

1. `Supplier Archive Runtime`
   - collect Doba source records
   - normalize and persist archive records
   - persist product, variant, inventory, shipping, seller, category, and ship
     from data

2. `Shopify Listing Runtime`
   - consume archive records
   - build a qualified publish candidate pool
   - publish one qualified product at a time to Shopify

Live publish must not depend on full Doba re-scan as its primary source of
truth once archive data exists.

### 3. Candidate-pool before publish

Before real publish, the system must derive a local publish pool containing only
products that satisfy all blocking rules.

The candidate pool must exclude:

- non-US or unknown ship-from products
- products whose publishable inventory is not strictly greater than `10`
- products missing valid variant data
- products whose Shopify category cannot be resolved
- products already published successfully
- products already existing in Shopify as `ACTIVE`

## Mandatory Data Standards

### 4. Supplier archive record requirements

Each archived Doba product must preserve, at minimum:

- Doba product ID
- Doba SPU number
- supplier ID
- seller name
- title
- description
- category ID
- category name
- category path when available
- source vendor fixed to `DOBA`
- target channels defaulting to:
  - `Inbox`
  - `Shop`
  - `Pinterest`
  - `Facebook & Instagram`
- image URLs
- variant list
- SKU list
- SKU code list
- item numbers
- stock snapshots
- selling price
- shipping cost per item
- cost price = selling price + normal shipping cost
- available inventory
- warehouse fields
- ship-from raw value
- resolved ship-from country
- seller and supplier metadata

If Doba does not return a real ship-from field, archive must store:

- `ship_from_country = UNKNOWN`
- raw upstream source fields for traceability

### 5. Shopify publish mapping record requirements

Each successfully published product must persist:

- Doba product ID
- Doba SPU number
- Shopify product ID
- Shopify variant IDs
- SKU to Shopify variant mapping
- shopify status
- published channels
- category mapping
- doba category ID and name
- shopify category ID and name
- timestamp of publish
- last known error if any

## Mandatory Business Rules

### 6. SKU merge rule

All variants belonging to the same Doba product must publish into a single
Shopify product.

Forbidden behavior:

- one SKU published as one standalone Shopify product when multiple SKUs belong
  to the same Doba product

Required behavior:

- one Doba product -> one Shopify product
- multiple Doba SKUs -> multiple Shopify variants

### 7. Pre-publish decision rules

Before publish, the runtime must check:

- whether the product already exists in Shopify
- whether the Shopify product is already `ACTIVE`
- whether publishable inventory is strictly greater than `10`
- whether ship-from is `US` or `United States`
- whether required category and category metafields are available

Decision rules:

- existing `ACTIVE` Shopify product -> skip
- non-US or unknown ship-from -> skip
- inventory `<= 10` -> skip
- unresolved required category mapping -> fail or hold for category remediation

### 8. Pricing rule

Mandatory formulas:

- `cost_price = Doba sellingPrice + normal shipping fee per item`
- `shopify_sale_price = Doba sellingPrice * 1.25`

The publish runtime must log both cost price and sale price per variant.

### 9. Shopify write requirements

Every published Shopify product must include:

- Shopify category
- product category metafields
- vendor = `DOBA`
- collection `NEW ARRIVALS`
- publication to:
  - `Inbox`
  - `Shop`
  - `Pinterest`
  - `Facebook & Instagram`

## Runtime Standards

### 10. Real-time output

The runtime must emit real-time logs for every scanned product, not only at the
end of the run.

Each result line must include:

- progress
- total
- current index
- page number
- Doba product ID
- Doba SPU number
- title
- SKU list
- SKU code list
- Shopify product ID
- Shopify status
- variant count
- cost prices
- sale prices
- inventories
- category ID
- category name
- category metafields
- ship-from country
- warehouse list
- seller name
- target channels
- published channels
- final action
- reason

### 11. Checkpoint and resume

The publish runtime must be resumable by a single command rerun.

Checkpoint must persist:

- next page
- next index
- scanned count
- published count
- skipped count
- failed count
- successful SPU numbers
- last failure data
- resume command

Manual interruption behavior:

- `Ctrl+C` must persist resume position
- the process must stop cleanly without corrupting the checkpoint

### 12. Failure handling

There are two accepted failure modes:

1. `soft failure`
   - record failure
   - persist checkpoint
   - continue to next product

2. `hard failure`
   - stop the run only when the error implies unsafe or invalid publish
   - examples:
     - invalid credentials
     - missing required Shopify publications
     - fatal schema mismatch that makes all further writes unsafe

The system must not stop the whole scan because one product fails normally.

### 13. Variant repair

If Shopify variant bulk create returns an incomplete variant set, the runtime
must:

- wait and re-read product variants
- retry the read several times
- detect missing SKUs
- perform SKU-level repair create for missing variants
- re-read and confirm all expected variants exist

If variants still do not match after repair attempts, record a product failure
with missing SKU details.

## Performance Standards

### 14. Required filtering order

To improve throughput, filtering must happen as early as possible:

1. Doba list API server-side filters
2. archive qualification
3. Shopify duplicate / active check
4. publish execution

The live publish command should always prefer service-side filters such as:

- `shipTo=US`
- `minInventory=11`
- any future Doba list filters for price, processing time, market restriction,
  pickup availability, or category

### 15. Archive-driven efficiency target

The target end state is:

- full Doba catalog scan happens in archive collection, not every publish run
- live publish consumes a much smaller local qualified pool
- repeated publish retries do not re-scan the full Doba catalog

### 16. Operational targets

The project should optimize for:

- minimizing low-value scans caused by inventory below threshold
- minimizing repeated scans of non-US ship-from products
- minimizing repeated category mapping failures
- maximizing percentage of scanned products that reach publish attempt

## Completion Goals

### Goal A. Supplier archive completeness

Done when:

- archive stores all mandatory product and variant fields
- ship-from resolution is preserved with `UNKNOWN` fallback
- archive can be reused by inventory, price, risk, and publish runtimes

### Goal B. Candidate-pool publishing

Done when:

- a local qualified publish pool exists
- live publish consumes the pool rather than the full raw Doba scan
- low-inventory and non-US products are filtered before publish stage

### Goal C. Shopify product correctness

Done when:

- same-product multi-SKU records publish as one Shopify product
- all expected variants exist after publish
- Shopify category and category metafields are written
- product is added to `NEW ARRIVALS`
- target channels are published correctly

### Goal D. Runtime resilience

Done when:

- rerunning the same command resumes correctly
- user interruption preserves checkpoint and resume position
- single-product failures do not kill the whole run
- variant repair runs automatically when bulk create is incomplete

### Goal E. Observability

Done when:

- every scanned product emits a real-time result
- report file is readable and actionable
- last failure always identifies SKU, reason, completed count, and resume
  command

### Goal F. Efficiency improvement

Done when:

- live runs stop spending the majority of time on obviously unpublishable items
- server-side Doba filters are enabled by default where safe
- archive qualification reduces Shopify publish-time scan volume materially

## Definition Of Done For This Project

The Doba -> Shopify live publish project is complete only when all conditions
below are true:

- real Doba API is used for source collection
- real Shopify publish is used for product creation and channel publication
- archive is the primary downstream data source
- qualified candidate pool exists before live publish
- multi-SKU merge works reliably
- US-only and inventory `> 10` rules are enforced before publish
- category and metafield writes are reliable
- checkpoint resume is stable
- single failures auto-continue safely
- real-time logs expose enough detail for operations
- the operator can rerun one command and safely continue from the last position

## Current Gap To Close

The current runtime already supports:

- real publish
- checkpoint resume
- real-time output
- ACTIVE-product skip
- US ship-from enforcement
- inventory threshold enforcement
- variant repair and retry
- auto-continue after normal product failures
- pre-publish structured enrichment payloads for:
  - semantic summary
  - structured product details
  - SEO content
  - FAQ generation
  - image alt generation
  - Google Merchant projection
  - OpenAI Product Feed projection
  - Schema.org product projection
  - heuristic GEO scoring

The enrichment layer is currently attached to candidate generation and publish
result summaries, but it is not yet a mandatory gating stage for publish.

The main remaining gap is efficiency:

- the runtime still depends too much on full Doba scanning during live publish
- candidate qualification must move earlier into archive and candidate-pool
  generation

## Recommended Execution Commands

Archive collection:

```powershell
python -m src.app.runners.run_supplier_archive
```

Current live publish command:

```powershell
python -m src.app.runners.run_doba_shopify_live_publish --report-path "docs/audits/doba-shopify-live-publish-report.json" --target-country US --inventory-threshold 10 --list-min-inventory 11 --page-size 20 --channels Inbox Shop Pinterest "Facebook & Instagram"
```

## Next Mandatory Delivery

The next implementation milestone must deliver:

- archive-based qualified publish pool generation
- live publish consuming the qualified pool
- fewer low-value scans during real publish
- explicit completion report for candidate-pool efficiency gain
