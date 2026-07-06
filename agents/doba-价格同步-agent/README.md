# Doba Price Sync Agent

This agent runs inside `AI-hermes-agent/agents/doba-价格同步-agent` and always reads shared configuration from the parent Hermes project via `shared.config.get_settings()`.

## Scope

- Fetch Doba SKU price snapshots
- Map `doba_sku -> shopify_variant_id`
- Read current Shopify variant price
- Calculate target price
- Decide `planned`, `skipped`, `manual_review`, or `failed`
- Run `dry-run`, `apply`, and `single-sku`
- Save runtime batches, state, and reports
- Print terminal detail lines

## Shared Environment

The agent does not maintain its own `.env`.

Settings are loaded from:

- `AI-hermes-agent/.env`
- `AI-hermes-agent.env`

Retailer-mode Doba sync uses shared settings such as:

- `DOBA_PRICE_SYNC_PLATFORM_NAME` or `DOBA_PRICE_SYNC_PLATFORM_ID`
- `DOBA_PRICE_SYNC_SHIP_TO_COUNTRY`
- `DOBA_PRICE_SYNC_FULL_PAGE_SIZE`

## Rounding Modes

- `ending_99`: round up to the next price ending in `.99`
- `ending_95`: round up to the next price ending in `.95`
- `nearest_dollar`: round to the nearest integer dollar
- `no_rounding`: keep the raw 2-decimal result

## Runtime Files

- `runtime/mappings.json`
- `runtime/mapping_template.json`
- `runtime/batches.json`
- `runtime/state.json`
- `runtime/reports/*.json`

## Live Doba Strategy

- `incremental`: `updated -> stock -> shipping`
- `single_sku`: `spu/detail -> stock -> shipping`
- `full`: `spu/list -> spu/detail -> stock -> shipping`
