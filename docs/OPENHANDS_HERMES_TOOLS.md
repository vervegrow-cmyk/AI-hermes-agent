# OpenHands Hermes Tool Registration

This repository exposes local Hermes tools to OpenHands and Codex through local MCP bridges.

## Registered tool servers

- Server name: `hermes-trendforge`
- MCP script: [tools/mcp/hermes_trendforge_mcp_server.py](</d:/桌面文件下载/AI-hermes-agent/tools/mcp/hermes_trendforge_mcp_server.py>)
- Registration script: [scripts/register_openhands_mcp.py](</d:/桌面文件下载/AI-hermes-agent/scripts/register_openhands_mcp.py>)

- Server name: `yt-dlp`
- MCP script: [tools/mcp/yt_dlp_mcp_server.py](</d:/桌面文件下载/AI-hermes-agent/tools/mcp/yt_dlp_mcp_server.py>)
- Registration script: [scripts/register_openhands_yt_dlp_mcp.py](</d:/桌面文件下载/AI-hermes-agent/scripts/register_openhands_yt_dlp_mcp.py>)

- Server name: `opencli`
- MCP script: [tools/mcp/opencli_mcp_server.py](</d:/桌面文件下载/AI-hermes-agent/tools/mcp/opencli_mcp_server.py>)
- Registration script: [scripts/register_openhands_opencli_mcp.py](</d:/桌面文件下载/AI-hermes-agent/scripts/register_openhands_opencli_mcp.py>)

- Server name: `browser-harness`
- MCP script: [tools/mcp/browser_harness_mcp_server.py](</d:/桌面文件下载/AI-hermes-agent/tools/mcp/browser_harness_mcp_server.py>)
- Registration script: [scripts/register_openhands_browser_harness_mcp.py](</d:/桌面文件下载/AI-hermes-agent/scripts/register_openhands_browser_harness_mcp.py>)

- Combined registration script: [scripts/register_openhands_local_tools.py](</d:/桌面文件下载/AI-hermes-agent/scripts/register_openhands_local_tools.py>)
- Registration status script: [scripts/check_openhands_local_tools.py](</d:/桌面文件下载/AI-hermes-agent/scripts/check_openhands_local_tools.py>)

## Exposed OpenHands tools

- `hermes_trendforge_discover_insights`
- `hermes_trendforge_firecrawl_scrape`
- `hermes_trendforge_discover_insights_web`
- `yt_dlp_get_version`
- `yt_dlp_extract_info`
- `yt_dlp_download`
- `opencli_get_version`
- `opencli_list_commands`
- `opencli_doctor`
- `opencli_run_command`
- `browser_harness_get_version`
- `browser_harness_get_skill`
- `browser_harness_doctor`
- `browser_harness_run_command`
- `browser_harness_run_script`

## How it works

OpenHands stores HTTP MCP servers in user settings and connects to local bridges such as:

```text
http://host.docker.internal:8091/mcp
http://host.docker.internal:8092/mcp
http://host.docker.internal:8093/mcp
http://host.docker.internal:8094/mcp
```

Typical local processes receive:

- `PYTHONPATH=/workspace/project:/workspace/project/agents/hermes-trendforge-agent`
- `FIRECRAWL_BASE_URL=http://host.docker.internal:3003`

That keeps OpenHands on `3002`, Hermes MCP on `8091`, `yt-dlp` MCP on `8092`, OpenCLI MCP on `8093`, browser-harness MCP on `8094`, and the shared Firecrawl service on `3003`.

## Re-register

```powershell
python scripts/register_openhands_mcp.py
python scripts/register_openhands_yt_dlp_mcp.py
python scripts/register_openhands_opencli_mcp.py
python scripts/register_openhands_browser_harness_mcp.py
python scripts/register_openhands_local_tools.py
```

## Check registration

```powershell
python scripts/check_openhands_local_tools.py
```
