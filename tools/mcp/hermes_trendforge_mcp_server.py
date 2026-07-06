from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from pydantic import Field


REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_ROOT = REPO_ROOT / "agents" / "hermes-trendforge-agent"

for path in (REPO_ROOT, AGENT_ROOT):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from service.intelligence_service import (  # noqa: E402
    discover_insights,
    discover_insights_from_urls,
    scrape_urls,
)


mcp = FastMCP("hermes-trendforge")


@mcp.tool(
    name="hermes_trendforge_discover_insights",
    description=(
        "Analyze search queries and customer comments into demand signals, "
        "pain points, topic clusters, intent scores, and opportunity briefs."
    ),
)
def discover_insights_tool(
    search_queries: list[str] = Field(default_factory=list),
    comments: list[str] = Field(default_factory=list),
    market: str = "US",
    audience: str = "general",
) -> dict[str, Any]:
    return discover_insights(
        search_queries=search_queries,
        comments=comments,
        market=market,
        audience=audience,
    )


@mcp.tool(
    name="hermes_trendforge_firecrawl_scrape",
    description=(
        "Scrape one or more URLs via the shared Firecrawl service and return "
        "per-URL structured results."
    ),
)
def firecrawl_scrape_tool(
    urls: list[str] = Field(default_factory=list),
    formats: list[str] = Field(default_factory=lambda: ["markdown"]),
    only_main_content: bool = True,
) -> dict[str, Any]:
    return scrape_urls(
        urls=urls,
        formats=formats,
        only_main_content=only_main_content,
    )


@mcp.tool(
    name="hermes_trendforge_discover_insights_web",
    description=(
        "Scrape URLs via Firecrawl, then summarize them into market demand "
        "signals, customer needs, topic clusters, and opportunity briefs."
    ),
)
def discover_insights_web_tool(
    urls: list[str] = Field(default_factory=list),
    market: str = "US",
    audience: str = "general",
    formats: list[str] = Field(default_factory=lambda: ["markdown"]),
) -> dict[str, Any]:
    return discover_insights_from_urls(
        urls=urls,
        market=market,
        audience=audience,
        formats=formats,
    )


if __name__ == "__main__":
    transport = os.getenv("HERMES_MCP_TRANSPORT", "stdio").strip().lower() or "stdio"
    if transport in {"http", "streamable-http", "sse"}:
        host = os.getenv("HERMES_MCP_HOST", "0.0.0.0")
        port = int(os.getenv("HERMES_MCP_PORT", "8091"))
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
