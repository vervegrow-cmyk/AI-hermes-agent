# Doba Shopify Agent Module Boundaries

## Runtime layout

The modular runtime now lives under `src/`:

- `src/app`: FastAPI wiring and task runners
- `src/shared/contracts`: shared DTO contracts used across modules
- `src/shared/repositories`: shared repository protocols and in-memory implementations
- `src/modules/product_screening`: normalization and screening logic
- `src/modules/risk_control`: policy and AI-based risk assessment
- `src/modules/shopify_listing`: publish preparation and Shopify runner
- `src/modules/inventory_sync`: inventory planning and runner
- `src/modules/price_sync`: price planning and runner
- `src/modules/sku_mapping`: SKU mapping resolution

## Allowed dependencies

- Modules may depend on:
  - `src/shared/contracts`
  - `src/shared/repositories`
  - Hermes shared runtime packages such as `shared.config`, `shared.schemas`, and `shared.agent_runtime`
- Modules may not import another module's `application`, `domain`, `infrastructure`, or `runners` package directly.
- Cross-module coordination must happen in `src/app/runners`.

## Side-effect rules

- Doba reads must stay in `infrastructure/supplier_adapters/`.
- DeepSeek-style AI scoring must stay in `risk_control/infrastructure/ai_scoring_service.py`.
- Shopify write actions must stay in module `runners/`.
- Screening and risk modules return contracts only and do not perform Shopify writes.

## Compatibility

- Existing routes remain available:
  - `GET /health`
  - `POST /execute`
  - `POST /evaluate-product`
  - `POST /evaluate-batch`
  - `POST /publish-approved`
- Legacy paths under `api/`, `models/`, `service/`, and `workflow/` are compatibility layers that delegate to `src/`.

