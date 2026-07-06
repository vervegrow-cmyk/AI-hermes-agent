import importlib.util
import sys
from pathlib import Path

from fastapi.testclient import TestClient

AGENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = AGENT_ROOT.parents[1]

for path in (REPO_ROOT, AGENT_ROOT):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


def _load_app_module():
    for module_name in [
        "api",
        "api.app",
        "runtime",
        "schemas",
        "service",
        "service.executor",
        "service.intelligence_service",
    ]:
        sys.modules.pop(module_name, None)

    spec = importlib.util.spec_from_file_location(
        "hermes_trendforge_agent_app",
        AGENT_ROOT / "api" / "app.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_discover_insights_endpoint_calls_service(monkeypatch):
    module = _load_app_module()
    captured: dict = {}

    def fake_discover_insights(*, search_queries, comments, market, audience):
        captured.update(
            {
                "search_queries": search_queries,
                "comments": comments,
                "market": market,
                "audience": audience,
            }
        )
        return {
            "agent": "hermes-trendforge-agent",
            "market": market,
            "audience": audience,
            "keywords": ["alpha"],
            "pain_points": ["beta"],
            "opportunities": [{"title": "gamma"}],
        }

    monkeypatch.setattr(module, "discover_insights_service", fake_discover_insights)
    client = TestClient(module.app)

    response = client.post(
        "/discover-insights",
        json={
            "search_queries": ["best ai product research workflow"],
            "comments": ["I hate how confusing product research tools are."],
            "market": "US",
            "audience": "operators",
        },
    )

    assert response.status_code == 200
    assert captured == {
        "search_queries": ["best ai product research workflow"],
        "comments": ["I hate how confusing product research tools are."],
        "market": "US",
        "audience": "operators",
    }
    assert response.json() == {
        "agent": "hermes-trendforge-agent",
        "market": "US",
        "audience": "operators",
        "keywords": ["alpha"],
        "pain_points": ["beta"],
        "opportunities": [{"title": "gamma"}],
    }


def test_execute_endpoint_uses_local_runtime_contract():
    module = _load_app_module()
    client = TestClient(module.app)

    response = client.post(
        "/execute",
        json={
            "request_id": "req-1",
            "task": "discover insights",
            "capability": "topic-discovery",
            "payload": {
                "search_queries": ["best ai product research workflow"],
                "comments": ["Need a better comparison before I buy anything."],
                "market": "US",
                "audience": "operators",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["agent"] == "hermes-trendforge-agent"
    assert body["request_id"] == "req-1"
    assert body["data"]["keywords"]
    assert body["data"]["opportunities"]


def test_firecrawl_scrape_route_calls_service(monkeypatch):
    module = _load_app_module()
    captured: dict = {}

    def fake_scrape_urls(*, urls, formats, only_main_content):
        captured.update(
            {
                "urls": urls,
                "formats": formats,
                "only_main_content": only_main_content,
            }
        )
        return {
            "agent": "hermes-trendforge-agent",
            "tool": "firecrawl",
            "results": [{"url": urls[0], "success": True}],
        }

    monkeypatch.setattr(module, "scrape_urls_service", fake_scrape_urls)
    client = TestClient(module.app)

    response = client.post(
        "/tools/firecrawl/scrape",
        json={
            "urls": ["https://example.com"],
            "formats": ["markdown"],
            "only_main_content": True,
        },
    )

    assert response.status_code == 200
    assert captured == {
        "urls": ["https://example.com"],
        "formats": ["markdown"],
        "only_main_content": True,
    }
    assert response.json()["tool"] == "firecrawl"


def test_execute_endpoint_supports_firecrawl_scrape_capability(monkeypatch):
    module = _load_app_module()
    client = TestClient(module.app)

    def fake_scrape_urls(*, urls, formats, only_main_content):
        return {
            "agent": "hermes-trendforge-agent",
            "tool": "firecrawl",
            "summary": "Scraped 1/1 urls with Firecrawl.",
            "results": [{"url": urls[0], "success": True, "status_code": 200}],
        }

    monkeypatch.setattr(sys.modules["service.executor"], "scrape_urls", fake_scrape_urls)

    response = client.post(
        "/execute",
        json={
            "request_id": "req-firecrawl-1",
            "task": "scrape a page",
            "capability": "firecrawl-scrape",
            "payload": {
                "urls": ["https://example.com"],
                "formats": ["markdown"],
                "only_main_content": True,
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["agent"] == "hermes-trendforge-agent"
    assert body["capability"] == "firecrawl-scrape"
    assert body["data"]["tool"] == "firecrawl"


def test_openhands_conversation_route_calls_service(monkeypatch):
    module = _load_app_module()
    captured: dict = {}

    def fake_openhands_conversation(
        *,
        prompt,
        conversation_id,
        title,
        run,
        wait_for_ready,
        ready_timeout_seconds,
        poll_interval_seconds,
        llm_model,
        agent_type,
    ):
        captured.update(
            {
                "prompt": prompt,
                "conversation_id": conversation_id,
                "title": title,
                "run": run,
                "wait_for_ready": wait_for_ready,
                "ready_timeout_seconds": ready_timeout_seconds,
                "poll_interval_seconds": poll_interval_seconds,
                "llm_model": llm_model,
                "agent_type": agent_type,
            }
        )
        return {
            "agent": "hermes-trendforge-agent",
            "tool": "openhands",
            "conversation_id": "conv-123",
        }

    monkeypatch.setattr(module, "openhands_conversation_service", fake_openhands_conversation)
    client = TestClient(module.app)

    response = client.post(
        "/tools/openhands/conversation",
        json={
            "prompt": "Open the repo and inspect startup failures",
            "title": "Startup triage",
            "run": True,
            "wait_for_ready": True,
            "ready_timeout_seconds": 30.0,
            "poll_interval_seconds": 1.0,
            "llm_model": "openai/gpt-4.1",
            "agent_type": "default",
        },
    )

    assert response.status_code == 200
    assert captured == {
        "prompt": "Open the repo and inspect startup failures",
        "conversation_id": None,
        "title": "Startup triage",
        "run": True,
        "wait_for_ready": True,
        "ready_timeout_seconds": 30.0,
        "poll_interval_seconds": 1.0,
        "llm_model": "openai/gpt-4.1",
        "agent_type": "default",
    }
    assert response.json()["tool"] == "openhands"


def test_execute_endpoint_supports_openhands_conversation_capability(monkeypatch):
    module = _load_app_module()
    client = TestClient(module.app)

    def fake_openhands_conversation(
        *,
        prompt,
        conversation_id,
        title,
        run,
        wait_for_ready,
        ready_timeout_seconds,
        poll_interval_seconds,
        llm_model,
        agent_type,
    ):
        return {
            "agent": "hermes-trendforge-agent",
            "tool": "openhands",
            "summary": "Started OpenHands conversation conv-123.",
            "conversation_id": "conv-123",
            "prompt": prompt,
        }

    monkeypatch.setattr(
        sys.modules["service.executor"],
        "openhands_conversation",
        fake_openhands_conversation,
    )

    response = client.post(
        "/execute",
        json={
            "request_id": "req-openhands-1",
            "task": "start openhands",
            "capability": "openhands-conversation",
            "payload": {
                "prompt": "Investigate the repo and report blockers",
                "title": "Repo investigation",
                "wait_for_ready": True,
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["agent"] == "hermes-trendforge-agent"
    assert body["capability"] == "openhands-conversation"
    assert body["data"]["tool"] == "openhands"
    assert body["data"]["conversation_id"] == "conv-123"


def test_openhands_status_route_calls_service(monkeypatch):
    module = _load_app_module()

    def fake_get_openhands_status():
        return {
            "agent": "hermes-trendforge-agent",
            "tool": "openhands",
            "base_url": "http://127.0.0.1:3002",
            "service_reachable": True,
            "service_status_code": 200,
            "mcp_registered": True,
            "registered_server_names": ["hermes-trendforge"],
            "registered_server": "hermes-trendforge",
            "connected": True,
            "summary": "OpenHands is connected locally and Hermes MCP is registered.",
        }

    monkeypatch.setattr(module, "get_openhands_status_service", fake_get_openhands_status)
    client = TestClient(module.app)

    response = client.get("/tools/openhands/status")

    assert response.status_code == 200
    body = response.json()
    assert body["connected"] is True
    assert body["mcp_registered"] is True
    assert body["registered_server_names"] == ["hermes-trendforge"]
