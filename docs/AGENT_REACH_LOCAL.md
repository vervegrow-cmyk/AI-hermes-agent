# Agent Reach Local Integration

This workspace keeps `Agent-Reach` under [external/Agent-Reach](</d:/桌面文件下载/AI-hermes-agent/external/Agent-Reach>).

## What is installed

- Source tree: [external/Agent-Reach](</d:/桌面文件下载/AI-hermes-agent/external/Agent-Reach>)
- Local venv: [external/Agent-Reach/.venv-agent-reach](</d:/桌面文件下载/AI-hermes-agent/external/Agent-Reach/.venv-agent-reach>)
- Hermes wrapper: [scripts/agent_reach.ps1](</d:/桌面文件下载/AI-hermes-agent/scripts/agent_reach.ps1>)
- Hermes Python client: [shared/clients/agent_reach.py](</d:/桌面文件下载/AI-hermes-agent/shared/clients/agent_reach.py>)

## Hermes usage

PowerShell:

```powershell
.\scripts\agent_reach.ps1 doctor --json
.\scripts\agent_reach.ps1 check-update
.\scripts\agent_reach.ps1 transcribe "https://www.youtube.com/watch?v=VIDEO_ID"
```

Python:

```python
from shared.clients import AgentReachClient

client = AgentReachClient()
status = client.doctor()
```

MCP server:

```powershell
python tools\mcp\agent_reach_mcp_server.py
python scripts\register_openhands_agent_reach_mcp.py
```

Registry entry:

- Hermes registry name: `agent-reach`
- Hermes MCP server name: `agent-reach`

## Current local status

Validated working channels on this machine:

- `exa_search`
- `web`
- `v2ex`
- `rss`
- `bilibili` via search API
- `youtube` routed through local `yt-dlp`, but doctor still wants the user-level JS runtime config file written once

Still optional / not configured:

- `github` via `gh`
- `twitter`
- `reddit`
- `xiaohongshu`
- `linkedin`
- `xiaoyuzhou`
- `xueqiu`

## Codex usage

Copy the Agent Reach skill folder into `C:\Users\Administrator\.codex\skills\agent-reach\`.
That allows future Codex sessions to discover and use the same routing guidance.

Codex MCP registration can also point to:

```toml
[mcp_servers.agent-reach]
command = "python"
args = ["D:\\桌面文件下载\\AI-hermes-agent\\tools\\mcp\\agent_reach_mcp_server.py"]
```

## Notes

- We keep upstream source inside `external/` and put Hermes-specific glue only in `shared/`, `scripts/`, and `docs/`.
- The wrapper script changes directory into `external/Agent-Reach` before execution so local `mcporter` config is picked up consistently.
