# Doba Field Mapping

## Purpose

This document defines the local contract from raw Doba product payloads into the
agent's internal `DobaProductInput` and `NormalizedProduct` schemas.

## Mapping Table

| Doba source field | Internal field | Required | Notes |
| --- | --- | --- | --- |
| `supplier_id` | `supplier_id` | yes | Stable supplier identifier |
| `product_id` | `product_id` | yes | Supplier product identifier |
| `sku` | `sku` | yes | Primary duplicate key |
| `title` | `title` | yes | Used for normalized Shopify title |
| `brand` | `brand` | recommended | Branded items are manual review in phase one |
| `category_path` | `category_path` | yes | Split into `category_tokens` during normalization |
| `supplier_status` | `supplier_status` | yes | Expected values should be normalized to lowercase |
| `cost` | `cost` | yes | Supplier base cost |
| `msrp` or map | `msrp` | recommended | Used as pricing reference |
| `inventory_quantity` | `inventory` | yes | Must be integer |
| `ship_from_country` | `ship_from_country` | yes | ISO-like uppercase country code |
| `ships_to_countries` | `ships_to_countries` | yes | List of allowed markets |
| `shipping_cost` | `shipping_cost` | yes | Pre-listing estimate is required for auto-approval |
| `delivery_days` | `delivery_days` | yes | Used for fulfillment SLA |
| `weight` | `weight_kg` | optional | Needed later for shipping validation |
| `package_length` | `package_length_cm` | optional | Needed later for oversize checks |
| `package_width` | `package_width_cm` | optional | Needed later for oversize checks |
| `package_height` | `package_height_cm` | optional | Needed later for oversize checks |
| `description` | `description` | recommended | Missing description can still pass if attributes are strong |
| `images[]` | `image_urls` | yes | At least one usable image |
| `variant_attributes` | `variant_attributes` | optional | Used later for Shopify variants |
| `attributes` | `attributes` | yes | Supports PDP bullet generation |

## Normalization Rules

### Title

- trim whitespace
- collapse repeated spaces
- cap normalized title length at 120 chars

### Pricing

- if `msrp > 0`, use it as the first pricing reference
- otherwise derive price from `cost * 2.2`
- enforce a floor price of `25.00`

### Category

- split `category_path` on `>`, `/`, `|`, and `,`
- lowercase tokens for rule matching

### Duplicate Key

- use SKU if present
- otherwise fallback to product ID
- lowercase and trim before storage

## Validation Expectations

Reject immediately if these are missing or invalid:

- `product_id` and `sku` are both missing
- `title` missing
- `cost <= 0`
- `inventory < DOBA_MIN_INVENTORY`
- `image_urls` empty

Send to manual review if:

- `brand` is present
- only one image is available
- margin or delivery time is borderline

## Open Mapping Questions

- What are the exact Doba field names for shipping and ETA
- Whether Doba returns variant inventory separately
- Whether Doba exposes supplier status codes or free text
- Whether Doba has category IDs that should be preserved alongside path text
