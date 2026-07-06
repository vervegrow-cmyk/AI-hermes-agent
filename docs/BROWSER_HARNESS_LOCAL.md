# Browser Harness Local Integration

This repository exposes the local `browser-use/browser-harness` install to Hermes and Codex through a shared PowerShell wrapper, Python client, and local MCP server.

## Installed source

- Local working directory: [external/browser-harness](</d:/桌面文件下载/AI-hermes-agent/external/browser-harness>)
- Shared wrapper: [scripts/browser-harness.ps1](</d:/桌面文件下载/AI-hermes-agent/scripts/browser-harness.ps1>)
- Hermes client: [shared/clients/browser_harness.py](</d:/桌面文件下载/AI-hermes-agent/shared/clients/browser_harness.py>)
- MCP server: [tools/mcp/browser_harness_mcp_server.py](</d:/桌面文件下载/AI-hermes-agent/tools/mcp/browser_harness_mcp_server.py>)
- OpenHands registration: [scripts/register_openhands_browser_harness_mcp.py](</d:/桌面文件下载/AI-hermes-agent/scripts/register_openhands_browser_harness_mcp.py>)
- One-shot starter: [scripts/start_browser_harness_integration.ps1](</d:/桌面文件下载/AI-hermes-agent/scripts/start_browser_harness_integration.ps1>)

The wrapper always changes into `external/browser-harness`, prepends the local `uv` tool binary directory to `PATH`, imports the root [`.env`](</d:/桌面文件下载/AI-hermes-agent/.env>), and sets `BH_AGENT_WORKSPACE` to the parent `AI-hermes-agent` repository so browser-harness inherits the full Hermes runtime context.

## Installation status

The official package was installed with:

```powershell
uv tool install --python 3.12 --upgrade --force browser-harness
```

Installed version:

```text
browser-harness 0.1.3
```

## Local usage

```powershell
scripts\browser-harness.ps1 --version
scripts\browser-harness.ps1 skill
scripts\browser-harness.ps1 --doctor
@'
ensure_real_tab()
print(page_info())
'@ | scripts\browser-harness.ps1
```

## Hermes usage

Python services can call:

```python
from shared.clients import BrowserHarnessClient

client = BrowserHarnessClient()
version = client.version()
skill = client.skill()
doctor = client.doctor()
result = client.run_script("print(page_info())")
```

## Codex and OpenHands usage

Start the MCP bridge locally:

```powershell
$env:HERMES_MCP_TRANSPORT="http"
$env:HERMES_MCP_PORT="8094"
python tools/mcp/browser_harness_mcp_server.py
```

Or start and register it in one step:

```powershell
scripts\start_browser_harness_integration.ps1
```

Register it into OpenHands:

```powershell
python scripts/register_openhands_browser_harness_mcp.py
```

After registration, Codex and OpenHands can call:

- `browser_harness_get_version`
- `browser_harness_get_skill`
- `browser_harness_doctor`
- `browser_harness_run_command`
- `browser_harness_run_script`

## Optional env overrides

Root [`.env`](</d:/桌面文件下载/AI-hermes-agent/.env>) can override:

```text
BROWSER_HARNESS_ROOT=D:\桌面文件下载\AI-hermes-agent\external\browser-harness
BROWSER_HARNESS_CLI=D:\桌面文件下载\AI-hermes-agent\scripts\browser-harness.ps1
BROWSER_HARNESS_EXE=C:\Users\Administrator\.local\bin\browser-harness.exe
```
