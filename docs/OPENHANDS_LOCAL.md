# OpenHands Local Integration

## Local service

- Base URL: `http://127.0.0.1:3002`
- Health check: `GET /`
- OpenAPI docs: `GET /docs`

## Start and stop

From [external/OpenHands](</d:/桌面文件下载/AI-hermes-agent/external/OpenHands>):

```powershell
$env:OPENHANDS_HOST_PORT='3002'
$env:WORKSPACE_BASE='D:\桌面文件下载\AI-hermes-agent'
$env:PWD='D:\桌面文件下载\AI-hermes-agent\external\OpenHands'
$env:DATE=(Get-Date -Format 'yyyyMMddHHmmss')
docker compose up -d

docker compose down
```

`WORKSPACE_BASE` points OpenHands at the top-level Hermes repository, so local sessions can read and write the shared root files, agent folders, and the root `.env`.

## Shared Hermes config

Root [`.env`](</d:/桌面文件下载/AI-hermes-agent/.env>) should include:

```env
OPENHANDS_BASE_URL=http://127.0.0.1:3002
```

Shared settings expose this through [shared/config/settings.py](</d:/桌面文件下载/AI-hermes-agent/shared/config/settings.py>).

## Hermes usage

```python
from shared.config.settings import get_settings

settings = get_settings()
openhands_url = settings.openhands_base_url
```

## Codex usage

If a Codex-side project reads the shared root `.env`, point it to:

```env
OPENHANDS_BASE_URL=http://127.0.0.1:3002
```

If it needs direct HTTP calls:

```powershell
curl http://127.0.0.1:3002/
curl http://127.0.0.1:3002/docs
```
