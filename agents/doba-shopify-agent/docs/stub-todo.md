# Stub TODO

## Priority Order

1. `service/doba_client.py`
2. `service/shopify_client.py`
3. `service/decision_log.py`
4. `workflow/publish_candidates.py`

## `service/doba_client.py`

- Replace payload-only loading with real Doba API client
- Define auth, timeout, retry, and pagination behavior
- Normalize raw Doba responses into `DobaProductInput`
- Add market-aware product fetch filters

## `service/shopify_client.py`

- Implement duplicate checks before create
- Build real Shopify draft product payloads
- Create products through the selected Shopify API
- Return stable publish status codes instead of mock draft IDs

## `service/decision_log.py`

- Persist logs to shared Postgres
- Store raw and normalized snapshots
- Add request correlation fields
- Make logging replay-safe for repeated jobs

## `workflow/publish_candidates.py`

- Add duplicate preflight before publish
- Persist evaluation logs for every decision
- Separate evaluation failures from publish failures in batch mode
- Return richer per-item results for operational debugging
