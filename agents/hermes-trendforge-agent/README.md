# hermes-trendforge-agent

This agent can be developed from this folder while reusing the top-level `AI-hermes-agent` dependencies, `.env`, and shared services.

## Local run

```powershell
python main.py
```

If this folder has its own virtualenv, install the local dev dependencies once:

```powershell
python -m pip install -e .[dev]
```

## Tests

```powershell
pytest
```

## Firecrawl tool endpoints

This agent now exposes Firecrawl-backed endpoints while reusing the shared top-level
`FIRECRAWL_BASE_URL` setting:

```powershell
POST /tools/firecrawl/scrape
POST /discover-insights-web
POST /execute   # capability=firecrawl-scrape or discover-insights-web
```

Example execute payload:

```json
{
  "request_id": "req-1",
  "task": "scrape a page",
  "capability": "firecrawl-scrape",
  "payload": {
    "urls": ["https://example.com"],
    "formats": ["markdown"],
    "only_main_content": true
  }
}
```

## Docker build

Use the repository root as the build context while staying in this directory:

```powershell
docker build -f Dockerfile ../..
```
