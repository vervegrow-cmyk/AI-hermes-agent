# Doba Shopify Integration Checklist

## Scope

This checklist covers only the preparation work inside `agents/doba-shopify-agent`
before connecting real Doba and Shopify APIs. The agent continues to reuse the
repository root `.env`, `shared/` modules, and shared infrastructure.

## Structure Audit

Current folder status:

- `pyproject.toml`: present
- `README.md`: present
- `api/`: present
- `service/`: present
- `workflow/`: present
- `tests/`: present
- `docs/`: added in this preparation step
- `tests/fixtures/`: added in this preparation step

## Configuration Checklist

### Doba API

Required config keys already expected by the current agent code:

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
- `DOBA_AD_BUFFER`
- `DOBA_SHOPIFY_FEE_BUFFER`
- `DOBA_PUBLISH_DUPLICATES`

Still needed from the real Doba integration:

- auth scheme details
- token refresh rules if any
- pagination format
- rate limit headers and retry policy
- inventory and shipping endpoints
- supplier product status vocabulary

### Shopify

Current agent reuses shared Shopify settings:

- `SHOPIFY_TOKEN`
- `SHOPIFY_ADMIN_ACCESS_TOKEN`
- `SHOPIFY_STORE`
- `SHOPIFY_SHOP`
- `SHOPIFY_SHOP_DOMAIN`
- `SHOPIFY_CLIENT_ID`
- `SHOPIFY_CLIENT_SECRET`
- `SHOPIFY_AUTH_MODE`
- `SHOPIFY_API_VERSION`
- `SHOPIFY_APP_AUTOMATION_TOKEN`

Recommended split:

- Admin API:
  - `SHOPIFY_STORE`
  - `SHOPIFY_TOKEN` or `SHOPIFY_ADMIN_ACCESS_TOKEN`
  - `SHOPIFY_CLIENT_ID`
  - `SHOPIFY_CLIENT_SECRET`
  - `SHOPIFY_AUTH_MODE=client_credentials` for owned-store OAuth
- CLI/CD:
  - `SHOPIFY_APP_AUTOMATION_TOKEN`

Current runtime behavior:

- `custom_admin_token`: uses `SHOPIFY_ADMIN_ACCESS_TOKEN`, falling back to `SHOPIFY_TOKEN`
- `client_credentials`: exchanges `SHOPIFY_CLIENT_ID` and `SHOPIFY_CLIENT_SECRET`
  against `https://{shop}.myshopify.com/admin/oauth/access_token`
- `authorization_code`: helper methods exist for install URL generation and callback
  token exchange for standalone install flows

Current live Shopify capability status:

- `python -m src.app.runners.run_shopify_connection_check`: performs a real `shop` GraphQL query
- `shopify_listing`: can query remote SKU duplicates and create real draft products when
  `SHOPIFY_PILOT_CREATE_APPROVED=true`
- `inventory_sync.apply_inventory_sync`: can resolve SKU to variant/inventory item and call
  `inventorySetQuantities`
- `price_sync.apply_price_sync`: can resolve SKU to variant and call
  `productVariantsBulkUpdate`

Additional Shopify details still needed before real publish:

- whether to use Admin REST or GraphQL
- product creation payload shape
- draft vs active publish policy
- duplicate lookup method
- image upload flow
- category and metafield mapping rules

## Data Contract Checklist

Reference: [doba-field-mapping.md](./doba-field-mapping.md)

Minimum incoming product fields for evaluation:

- `supplier_id`
- `product_id`
- `sku`
- `title`
- `category_path`
- `supplier_status`
- `cost`
- `msrp` or equivalent pricing basis
- `inventory`
- `ship_from_country`
- `ships_to_countries`
- `shipping_cost`
- `delivery_days`
- `description`
- `image_urls`
- `attributes`

Fields that are highly recommended before auto-publish:

- `brand`
- `variant_attributes`
- package dimensions
- weight

## Duplicate Product Strategy

Phase-one duplicate policy:

- Default duplicate key: normalized SKU
- Fallback duplicate key: supplier product ID
- Candidate-side key already exists as `normalized_product.duplicate_key`
- Do not auto-publish duplicates unless `DOBA_PUBLISH_DUPLICATES=true`

Duplicate checks needed before real Shopify publish:

1. Lookup by SKU
2. Lookup by handle derived from normalized title
3. Optional lookup by supplier product ID stored in metafield or tag

Recommended behavior:

- exact SKU hit: skip publish
- same handle but different SKU: manual review
- same supplier product ID: skip publish

## Publish Strategy

Reference: [shopify-publish-rules.md](./shopify-publish-rules.md)

Phase-one publish rules:

- only `approved` products may create Shopify drafts
- default status is draft, not active
- `manual_review` and `rejected` are never published automatically
- bulk publish should be idempotent on duplicate key
- publish result should include created draft ID or skip reason

## Decision Log Persistence Plan

Current code can build an in-memory decision log record, but does not persist it.

Recommended shared Postgres table shape:

- `id`
- `request_id`
- `supplier_id`
- `product_id`
- `sku`
- `duplicate_key`
- `decision_status`
- `decision_reasons_json`
- `expected_profit`
- `margin_rate`
- `shipping_ratio`
- `score`
- `target_market`
- `shopify_store`
- `shopify_draft_id`
- `publish_action`
- `raw_product_json`
- `normalized_product_json`
- `created_at`

Minimum requirements:

- one record per evaluation attempt
- store both decision and source payload snapshots
- make re-evaluation traceable

## Stub Audit

### `service/doba_client.py`

Current state:

- reads products only from `payload`
- no HTTP client
- no auth
- no pagination

Needed before real integration:

- request signing or token auth
- paginated product fetch
- endpoint-specific error handling
- timeout and retry policy
- raw response normalization

### `service/shopify_client.py`

Current state:

- returns mock `draft_id`
- no Shopify API call
- no duplicate check

Needed before real integration:

- admin API client
- duplicate lookup
- draft product create
- image and variant payload mapping
- rate limit handling

### `service/decision_log.py`

Current state:

- builds a dict only
- no database persistence

Needed before real integration:

- shared Postgres persistence
- request correlation ID support
- replay-safe inserts
- query helpers for audits

### `workflow/publish_candidates.py`

Current state:

- normalizes and evaluates
- optionally calls draft stub
- does not persist logs
- does not perform duplicate reads

Needed before real integration:

- evaluation plus persistence transaction flow
- duplicate preflight
- explicit publish skip reasons
- batch error isolation

## Local Sample Data

Prepared fixtures:

- `tests/fixtures/approved_product.json`
- `tests/fixtures/manual_review_product.json`
- `tests/fixtures/rejected_product.json`
- `tests/fixtures/batch_products.json`

These are intended for local evaluation and workflow tests before connecting real APIs.

## External Information Still Required

- Doba API authentication specification
- Doba product list and shipping endpoint examples
- target Shopify API surface and credentials format
- target market for first rollout
- whether branded products are allowed in phase one
- where supplier product ID should be stored in Shopify for duplicate checks
