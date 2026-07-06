# OpenCLI Local Integration

This repository keeps the local OpenCLI install in [external/OpenCLI](</d:/桌面文件下载/AI-hermes-agent/external/OpenCLI>) and exposes it to Hermes and Codex through a shared wrapper, Python client, and MCP server.

## Installed source

- Local package root: [external/OpenCLI](</d:/桌面文件下载/AI-hermes-agent/external/OpenCLI>)
- Shared wrapper: [scripts/opencli.ps1](</d:/桌面文件下载/AI-hermes-agent/scripts/opencli.ps1>)
- Hermes client: [shared/clients/opencli.py](</d:/桌面文件下载/AI-hermes-agent/shared/clients/opencli.py>)
- MCP server: [tools/mcp/opencli_mcp_server.py](</d:/桌面文件下载/AI-hermes-agent/tools/mcp/opencli_mcp_server.py>)
- OpenHands registration: [scripts/register_openhands_opencli_mcp.py](</d:/桌面文件下载/AI-hermes-agent/scripts/register_openhands_opencli_mcp.py>)

The wrapper always changes into `external/OpenCLI`, prepends `node_modules/.bin` to `PATH`, and imports the root [`.env`](</d:/桌面文件下载/AI-hermes-agent/.env>) so the full Hermes environment is available to OpenCLI, Codex, and Hermes-triggered subprocesses.

## Local usage

```powershell
scripts\opencli.ps1 --version
scripts\opencli.ps1 doctor
scripts\opencli.ps1 list
scripts\opencli.ps1 codex status
```

## Hermes usage

Python services can call:

```python
from shared.clients import OpenCLIClient

client = OpenCLIClient()
version = client.version()
commands = client.list_commands()
result = client.run_command(["codex", "status"], check=False)
```

## Codex and OpenHands usage

Start the MCP bridge locally:

```powershell
$env:HERMES_MCP_TRANSPORT="http"
$env:HERMES_MCP_PORT="8093"
python tools/mcp/opencli_mcp_server.py
```

Register it into OpenHands:

```powershell
python scripts/register_openhands_opencli_mcp.py
```

After registration, Codex and OpenHands can call:

- `opencli_get_version`
- `opencli_list_commands`
- `opencli_doctor`
- `opencli_run_command`

## Optional env overrides

Root [`.env`](</d:/桌面文件下载/AI-hermes-agent/.env>) can override:

```text
OPENCLI_ROOT=D:\桌面文件下载\AI-hermes-agent\external\OpenCLI
OPENCLI_CLI=D:\桌面文件下载\AI-hermes-agent\scripts\opencli.ps1
```
