# Firecrawl Local Integration

## Local service

- Base URL: `http://127.0.0.1:3003`
- Health check: `GET /`
- Smoke test: `GET /e2e-test`

## Start and stop

From [external/firecrawl](</d:/桌面文件下载/AI-hermes-agent/external/firecrawl>):

```powershell
docker compose up -d
docker compose down
```

## Shared Hermes config

Root [`.env`](</d:/桌面文件下载/AI-hermes-agent/.env>) includes:

```env
FIRECRAWL_BASE_URL=http://127.0.0.1:3003
FIRECRAWL_LOCAL_API_KEY=
FIRECRAWL_TIMEOUT_SECONDS=60
```

Shared settings are exposed through [shared/config/settings.py](</d:/桌面文件下载/AI-hermes-agent/shared/config/settings.py>) and the reusable client lives in [shared/clients/firecrawl.py](</d:/桌面文件下载/AI-hermes-agent/shared/clients/firecrawl.py>).

## Hermes usage

```python
from shared.clients import FirecrawlClient

client = FirecrawlClient()
response = client.scrape("https://example.com", formats=["markdown"])
data = response.json()
```

## Codex usage

If a Codex-side project reads the shared root `.env`, point it to:

```env
FIRECRAWL_BASE_URL=http://127.0.0.1:3003
```

If it needs direct HTTP calls:

```bash
curl http://127.0.0.1:3003/
curl -X POST http://127.0.0.1:3003/v2/scrape ^
  -H "Content-Type: application/json" ^
  -d "{\"url\":\"https://example.com\",\"formats\":[\"markdown\"]}"
```
