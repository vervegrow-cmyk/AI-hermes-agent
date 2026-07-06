from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.clients import OpenHandsClient
from shared.config import get_settings


EXPECTED_SERVERS = ("hermes-trendforge", "yt-dlp", "opencli", "browser-harness")


def main() -> None:
    settings = get_settings()
    client = OpenHandsClient()
    status = {
        "base_url": settings.openhands_base_url,
        "service_reachable": False,
        "registered_server_names": [],
        "expected_servers": list(EXPECTED_SERVERS),
        "missing_servers": list(EXPECTED_SERVERS),
    }

    try:
        health_response = client.health()
        status["service_reachable"] = health_response.is_success
        status["health_status_code"] = health_response.status_code
        if not health_response.is_success:
            print(json.dumps(status, ensure_ascii=False, indent=2))
            return

        settings_response = client.get_settings()
        settings_response.raise_for_status()
        payload = settings_response.json()
        servers = (
            (((payload.get("agent_settings") or {}).get("mcp_config") or {}).get("mcpServers"))
            or {}
        )
        server_names = sorted(servers.keys())
        status["registered_server_names"] = server_names
        status["missing_servers"] = [name for name in EXPECTED_SERVERS if name not in servers]
    except Exception as exc:
        status["error"] = str(exc)

    print(json.dumps(status, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
