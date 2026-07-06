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

from shared.clients import BrowserHarnessClient  # noqa: E402


mcp = FastMCP("browser-harness")


@mcp.tool(
    name="browser_harness_get_version",
    description="Return the installed local browser-harness version.",
)
def browser_harness_get_version_tool() -> dict[str, Any]:
    client = BrowserHarnessClient()
    return {"version": client.version(), "root_dir": str(client.root_dir)}


@mcp.tool(
    name="browser_harness_get_skill",
    description="Return the installed browser-harness skill text.",
)
def browser_harness_get_skill_tool() -> dict[str, Any]:
    client = BrowserHarnessClient()
    return {"output": client.skill()}


@mcp.tool(
    name="browser_harness_doctor",
    description="Run browser-harness doctor to diagnose browser, daemon, and auth state.",
)
def browser_harness_doctor_tool(
    timeout_seconds: float = 60.0,
    check: bool = False,
) -> dict[str, Any]:
    client = BrowserHarnessClient()
    return client.doctor(timeout_seconds=timeout_seconds, check=check)


@mcp.tool(
    name="browser_harness_run_command",
    description="Run a raw browser-harness command by passing the positional arguments after `browser-harness`.",
)
def browser_harness_run_command_tool(
    args: list[str],
    timeout_seconds: float = 300.0,
    check: bool = True,
) -> dict[str, Any]:
    client = BrowserHarnessClient()
    return client.run_command(args, timeout_seconds=timeout_seconds, check=check)


@mcp.tool(
    name="browser_harness_run_script",
    description="Execute a browser-harness Python snippet through stdin.",
)
def browser_harness_run_script_tool(
    script: str,
    timeout_seconds: float = 300.0,
    check: bool = True,
) -> dict[str, Any]:
    client = BrowserHarnessClient()
    return client.run_script(script, timeout_seconds=timeout_seconds, check=check)


if __name__ == "__main__":
    transport = os.getenv("HERMES_MCP_TRANSPORT", "stdio").strip().lower() or "stdio"
    if transport in {"http", "streamable-http", "sse"}:
        host = os.getenv("HERMES_MCP_HOST", "0.0.0.0")
        port = int(os.getenv("HERMES_MCP_PORT", "8094"))
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
