from __future__ import annotations

from typing import Any

from shared.clients import OpenHandsClient
from shared.config import get_settings


def get_openhands_status() -> dict[str, Any]:
    settings = get_settings()
    client = OpenHandsClient()

    status: dict[str, Any] = {
        "agent": "hermes-trendforge-agent",
        "tool": "openhands",
        "base_url": settings.openhands_base_url,
        "service_reachable": False,
        "service_status_code": None,
        "mcp_registered": False,
        "registered_server_names": [],
        "registered_server": "hermes-trendforge",
        "connected": False,
        "summary": "OpenHands is not connected yet.",
    }

    health_response = client.health()
    status["service_status_code"] = health_response.status_code
    status["service_reachable"] = health_response.is_success

    if not health_response.is_success:
        status["summary"] = (
            f"OpenHands health check failed with status {health_response.status_code}."
        )
        return status

    settings_response = client.get_settings()
    settings_response.raise_for_status()
    payload = settings_response.json()
    servers = (
        (((payload.get("agent_settings") or {}).get("mcp_config") or {}).get("mcpServers"))
        or {}
    )
    server_names = sorted(servers.keys())
    status["registered_server_names"] = server_names
    status["mcp_registered"] = "hermes-trendforge" in servers
    status["connected"] = bool(status["service_reachable"] and status["mcp_registered"])
    status["summary"] = (
        "OpenHands is connected locally and Hermes MCP is registered."
        if status["connected"]
        else "OpenHands is reachable, but Hermes MCP is not registered yet."
    )
    return status
