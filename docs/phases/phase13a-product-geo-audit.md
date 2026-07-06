# Phase13A Product GEO Audit

## Goal

Stand up the first production-safe slice of `ProductAgenticGEOAgent`.

## Included

- Shopify `ACTIVE` product scan
- `ShopifyProductSnapshot` normalization
- DeepSeek strict JSON analysis
- GEO scoring
- semantic profile generation
- recommendation generation
- Google Merchant projection
- OpenAI product feed projection
- schema projection
- before / after preview construction
- repository persistence contracts
- snapshot persistence

## Excluded

- Shopify writeback
- rollback execution
- live monitoring loops
- checkout path automation
- automatic approval workflows

## Phase13A outcome

At the end of Phase13A, each audited product should have:

- an audit score set
- semantic understanding output
- missing field and risk detection
- structured title / description / FAQ / alt / schema / feed suggestions
- before / after preview data
- a persisted snapshot record

## Core code

- [product-agentic-geo.agent.ts](/D:/桌面文件下载/AI-hermes-agent/packages/agents/product-agentic-geo-agent/product-agentic-geo.agent.ts)
- [deepseek-geo.service.ts](/D:/桌面文件下载/AI-hermes-agent/packages/services/deepseek-geo.service.ts)
- [shopify-product-geo.service.ts](/D:/桌面文件下载/AI-hermes-agent/packages/services/shopify-product-geo.service.ts)
