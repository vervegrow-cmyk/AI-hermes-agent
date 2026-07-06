from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from fastmcp import FastMCP


REPO_ROOT = Path(__file__).resolve().parents[2]

path_str = str(REPO_ROOT)
if path_str not in sys.path:
    sys.path.insert(0, path_str)

from shared.clients import OpenCLIClient  # noqa: E402


mcp = FastMCP("opencli")


@mcp.tool(
    name="opencli_get_version",
    description="Return the installed local OpenCLI version from external/OpenCLI.",
)
def opencli_get_version_tool() -> dict[str, Any]:
    client = OpenCLIClient()
    return {"version": client.version(), "root_dir": str(client.root_dir)}


@mcp.tool(
    name="opencli_list_commands",
    description="List installed OpenCLI commands and adapters from the local OpenCLI integration.",
)
def opencli_list_commands_tool() -> dict[str, Any]:
    client = OpenCLIClient()
    output = client.list_commands()
    return {"output": output}


@mcp.tool(
    name="opencli_doctor",
    description="Run OpenCLI doctor to check local browser bridge and CLI health.",
)
def opencli_doctor_tool() -> dict[str, Any]:
    client = OpenCLIClient()
    return client.doctor()


@mcp.tool(
    name="opencli_run_command",
    description="Run a local OpenCLI command by passing the positional arguments after `opencli`.",
)
def opencli_run_command_tool(
    args: list[str],
    timeout_seconds: float = 300.0,
    check: bool = True,
) -> dict[str, Any]:
    client = OpenCLIClient()
    return client.run_command(args, timeout_seconds=timeout_seconds, check=check)


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
