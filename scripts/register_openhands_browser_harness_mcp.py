from __future__ import annotations

import json
import urllib.error
import urllib.request
from copy import deepcopy


OPENHANDS_BASE_URL = "http://127.0.0.1:3002"
SETTINGS_URL = f"{OPENHANDS_BASE_URL}/api/v1/settings"
SERVER_NAME = "browser-harness"
MCP_URL = "http://host.docker.internal:8094/mcp"


def _http_json(method: str, url: str, payload: dict | None = None) -> tuple[int, dict]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8") or "{}"
            return resp.status, json.loads(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8") or "{}"
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = {"raw": body}
        return exc.code, parsed


def load_settings() -> dict:
    status, body = _http_json("GET", SETTINGS_URL)
    if status == 404:
        return {}
    if status != 200:
        raise RuntimeError(f"Failed to load OpenHands settings: {status} {body}")
    return body


def main() -> None:
    settings = load_settings()
    existing_agent_settings = deepcopy(settings.get("agent_settings") or {})
    mcp_config = deepcopy(existing_agent_settings.get("mcp_config") or {})
    servers = deepcopy(mcp_config.get("mcpServers") or {})

    servers[SERVER_NAME] = {
        "transport": "http",
        "url": MCP_URL,
    }
    payload = {
        "agent_settings_diff": {
            "mcp_config": {
                "mcpServers": servers,
            }
        }
    }

    status, body = _http_json("POST", SETTINGS_URL, payload)
    if status != 200:
        raise RuntimeError(f"Failed to save OpenHands settings: {status} {body}")

    print(
        json.dumps(
            {
                "status": "ok",
                "registered_server": SERVER_NAME,
                "settings_url": SETTINGS_URL,
            }
        )
    )


if __name__ == "__main__":
    main()
