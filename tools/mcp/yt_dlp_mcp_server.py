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

from shared.clients import YtDlpClient  # noqa: E402


mcp = FastMCP("yt-dlp")


@mcp.tool(
    name="yt_dlp_get_version",
    description="Return the installed local yt-dlp version from external/yt-dlp.",
)
def yt_dlp_get_version_tool() -> dict[str, Any]:
    client = YtDlpClient()
    return {"version": client.version(), "root_dir": str(client.root_dir)}


@mcp.tool(
    name="yt_dlp_extract_info",
    description=(
        "Extract video or playlist metadata from a URL without downloading media."
    ),
)
def yt_dlp_extract_info_tool(
    url: str,
    flat_playlist: bool = True,
) -> dict[str, Any]:
    client = YtDlpClient()
    payload = client.extract_info(url, flat_playlist=flat_playlist)
    return {"url": url, "info": payload}


@mcp.tool(
    name="yt_dlp_download",
    description=(
        "Download media from a supported URL into the local yt-dlp downloads directory."
    ),
)
def yt_dlp_download_tool(
    url: str,
    destination_dir: str | None = None,
    output_template: str | None = None,
    format_selector: str | None = None,
    audio_only: bool = False,
    write_info_json: bool = True,
    write_thumbnail: bool = False,
) -> dict[str, Any]:
    client = YtDlpClient()
    return client.download(
        url,
        destination_dir=destination_dir,
        output_template=output_template,
        format_selector=format_selector,
        audio_only=audio_only,
        write_info_json=write_info_json,
        write_thumbnail=write_thumbnail,
    )


if __name__ == "__main__":
    transport = os.getenv("HERMES_MCP_TRANSPORT", "stdio").strip().lower() or "stdio"
    if transport in {"http", "streamable-http", "sse"}:
        host = os.getenv("HERMES_MCP_HOST", "0.0.0.0")
        port = int(os.getenv("HERMES_MCP_PORT", "8092"))
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
