# YT-DLP Local Integration

This repository keeps the upstream `yt-dlp` source in `external/yt-dlp` and exposes it to Hermes and Codex through a shared client plus a local MCP server.

## Installed source

- Upstream source root: `external/yt-dlp`
- Hermes wrapper client: `shared/clients/yt_dlp.py`
- MCP server: `tools/mcp/yt_dlp_mcp_server.py`
- OpenHands registration script: `scripts/register_openhands_yt_dlp_mcp.py`

## Hermes usage

Python services can call:

```python
from shared.clients import YtDlpClient

client = YtDlpClient()
version = client.version()
info = client.extract_info("https://www.youtube.com/watch?v=BaW_jenozKc")
```

Downloads default to `external/yt-dlp/downloads`.

## Codex and OpenHands usage

Start the MCP bridge locally:

```powershell
$env:HERMES_MCP_TRANSPORT="http"
$env:HERMES_MCP_PORT="8092"
python tools/mcp/yt_dlp_mcp_server.py
```

Register it into OpenHands:

```powershell
python scripts/register_openhands_yt_dlp_mcp.py
```

After registration, Codex and OpenHands can call:

- `yt_dlp_get_version`
- `yt_dlp_extract_info`
- `yt_dlp_download`

## Optional env overrides

Root `.env` can override:

```text
YT_DLP_ROOT=D:\桌面文件下载\AI-hermes-agent\external\yt-dlp
YT_DLP_DOWNLOADS_DIR=D:\桌面文件下载\AI-hermes-agent\external\yt-dlp\downloads
YT_DLP_PYTHON=python
```
