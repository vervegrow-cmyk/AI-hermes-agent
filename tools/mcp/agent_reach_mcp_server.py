from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from pydantic import Field


REPO_ROOT = Path(__file__).resolve().parents[2]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.clients import AgentReachClient  # noqa: E402


mcp = FastMCP("agent-reach")
client = AgentReachClient()


@mcp.tool(
    name="agent_reach_doctor",
    description=(
        "Inspect the local Agent Reach channel registry and return which "
        "internet channels are available, misconfigured, or missing."
    ),
)
def doctor_tool() -> dict[str, Any]:
    return client.doctor()


@mcp.tool(
    name="agent_reach_check_update",
    description="Check whether a newer Agent Reach version is available.",
)
def check_update_tool() -> dict[str, Any]:
    return client.check_update()


@mcp.tool(
    name="agent_reach_transcribe",
    description=(
        "Transcribe a YouTube URL or local audio file through Agent Reach's "
        "transcription pipeline."
    ),
)
def transcribe_tool(
    source: str,
    provider: str = "auto",
    output_path: str = "",
) -> dict[str, Any]:
    transcript = client.transcribe(
        source,
        provider=provider,
        output_path=output_path or None,
    )
    return {
        "source": source,
        "provider": provider,
        "output_path": output_path or None,
        "transcript": transcript,
    }


@mcp.tool(
    name="agent_reach_version",
    description="Return the locally installed Agent Reach version.",
)
def version_tool() -> dict[str, str]:
    return {"version": client.version()}


if __name__ == "__main__":
    transport = os.getenv("HERMES_MCP_TRANSPORT", "stdio").strip().lower() or "stdio"
    if transport in {"http", "streamable-http", "sse"}:
        host = os.getenv("HERMES_MCP_HOST", "0.0.0.0")
        port = int(os.getenv("HERMES_MCP_PORT", "8093"))
        path = os.getenv("HERMES_MCP_PATH", "/mcp")
        mcp.run(
            transport=transport,
            host=host,
            port=port,
            path=path,
            show_banner=False,
        )
    else:
        mcp.run(show_banner=False)
