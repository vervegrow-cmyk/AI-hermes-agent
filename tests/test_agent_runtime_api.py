from __future__ import annotations

from fastapi.testclient import TestClient

from shared.agent_runtime import create_agent_app
from shared.schemas import ExecuteRequest


def _executor(request: ExecuteRequest) -> dict:
    return {
        "summary": f"Handled {request.task}",
        "data": {"echo": request.payload},
    }


def test_runtime_health_includes_capabilities():
    app = create_agent_app(
        agent_name="trend-agent",
        description="test",
        executor=_executor,
        capabilities=["trend-discovery", "keyword-analysis"],
    )
    client = TestClient(app)
    response = client.get("/health")
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "ok"
    assert body["capabilities"] == ["trend-discovery", "keyword-analysis"]


def test_runtime_execute_returns_normalized_payload():
    app = create_agent_app(
        agent_name="trend-agent",
        description="test",
        executor=_executor,
        capabilities=["trend-discovery"],
    )
    client = TestClient(app)
    response = client.post(
        "/execute",
        json={
            "request_id": "req-1",
            "task": "Analyze TikTok trends",
            "capability": "trend-discovery",
            "payload": {"market": "US"},
            "metadata": {"source": "test"},
        },
    )
    body = response.json()
    assert response.status_code == 200
    assert body["ok"] is True
    assert body["agent"] == "trend-agent"
    assert body["capability"] == "trend-discovery"
    assert body["request_id"] == "req-1"
    assert body["data"]["echo"]["market"] == "US"
