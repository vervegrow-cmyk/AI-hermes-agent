# Shopify Product GEO Optimization Agent

This agent is for two concrete jobs:

1. Product GEO
   Make Shopify product pages easier for AI systems to understand, summarize, cite, and recommend.
2. Agentic Storefront Readiness
   Prepare product data for Shopify Catalog, ChatGPT, Google AI Mode/Gemini, Microsoft Copilot, and Shop AI search.

## Environment variable inheritance

This project automatically loads:

1. `D:\桌面文件下载\AI-hermes-agent\.env`
2. `D:\桌面文件下载\AI-hermes-agent\agents\shopify-产品GEO优化-agent\.env` if present

That means:

- shared root environment variables are available through `os.getenv(...)`
- shared root environment variables are available through `shared.config.get_settings()`
- local agent `.env` values can override the root defaults

## DeepSeek-first model setup

The agent defaults to DeepSeek for rewrite generation.

Required root env keys:

```env
DEEPSEEK_API_KEY=your_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

Optional agent-specific overrides:

```env
SHOPIFY_GEO_LLM_PROVIDER=deepseek
SHOPIFY_GEO_LLM_MODEL=deepseek-chat
AGENT_PORT=8094
AGENT_NAME=shopify-geo-optimization-agent
```

## Run

```powershell
cd D:\桌面文件下载\AI-hermes-agent\agents\shopify-产品GEO优化-agent
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -e .
python main.py
```

## API

- `GET /health`
- `POST /execute`

Example payload:

```json
{
  "task": "audit_product_geo",
  "capability": "product-geo-audit",
  "payload": {
    "use_llm": true,
    "product": {
      "title": "UltraSoft Cooling Bed Sheet Set for Hot Sleepers",
      "description": "Breathable sheet set designed to reduce heat buildup and improve comfort.",
      "benefits": ["Cooling feel", "Easy care", "Deep pocket fit"],
      "specifications": {
        "material": "Microfiber",
        "fit": "Deep pocket",
        "sizes": "Twin to King",
        "care": "Machine washable"
      },
      "faq": [
        "Will it fit thick mattresses?",
        "Is it machine washable?",
        "Does it feel cool overnight?"
      ],
      "brand": "North Loom",
      "category": "Bedding",
      "audience": "Hot sleepers",
      "use_cases": ["Summer bedding", "Guest room refresh"]
    }
  }
}
```

## Output highlights

The agent returns:

- GEO score and structured recommendations
- readiness checks for key AI shopping/search surfaces
- environment and Shopify session readiness
- optional DeepSeek rewrite suggestions for product copy
