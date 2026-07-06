# Shopify Publish Rules

## Phase-One Rules

- Publish target is Shopify draft products only
- Only `approved` decisions may reach Shopify create calls
- `manual_review` and `rejected` decisions must stay out of auto-publish
- Duplicate checks run before every create call
- Every publish attempt must create a decision log record

## Duplicate Check Order

1. Shopify variant SKU search
2. Shopify product handle search
3. Supplier product ID lookup from metafield or tag

## Publish Outcomes

### `draft_created`

Use when:

- product is approved
- no duplicate collision is found
- Shopify accepted the draft payload

### `duplicate_skipped`

Use when:

- exact SKU match already exists
- same supplier product ID already exists

### `manual_review_skipped`

Use when:

- decision status is `manual_review`
- title or taxonomy collision needs operator review

### `rejected_skipped`

Use when:

- decision status is `rejected`

## Shopify Payload Expectations

Before real integration, define:

- product title from `normalized_title`
- body HTML or description from normalized description
- vendor from `brand` or supplier fallback
- product category mapping from `category_path`
- images from `image_urls`
- variants from `variant_attributes`
- tags including supplier and market metadata
- metafields storing supplier product ID and duplicate key

## Idempotency Strategy

- Persist decision logs keyed by request and duplicate key
- Query Shopify before create
- Reuse duplicate key as the stable replay guard

## Publish Policy Questions

- Which Shopify API surface is preferred
- Whether to attach supplier metadata as tags, metafields, or both
- Whether inventory is tracked at publish time or later sync
- Whether collections should be assigned immediately or later
