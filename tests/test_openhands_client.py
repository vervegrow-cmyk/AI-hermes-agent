import json

import httpx
import pytest

from shared.clients import OpenHandsClient


def test_start_conversation_builds_openhands_payload():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["url"] = str(request.url)
        captured["json"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(200, json={"id": "task-1", "status": "WORKING"})

    client = OpenHandsClient(
        base_url="http://localhost:3002",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    response = client.start_conversation(
        initial_user_text="Fix this repo",
        title="Codex handoff",
        run=True,
        llm_model="openai/gpt-4.1",
        agent_type="default",
        trigger="automation",
    )

    assert response.status_code == 200
    assert captured == {
        "method": "POST",
        "url": "http://localhost:3002/api/v1/app-conversations",
        "json": {
            "initial_message": {
                "role": "user",
                "content": [{"type": "text", "text": "Fix this repo"}],
                "run": True,
            },
            "title": "Codex handoff",
            "llm_model": "openai/gpt-4.1",
            "agent_type": "default",
            "trigger": "automation",
        },
    }


def test_send_message_builds_openhands_payload():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["url"] = str(request.url)
        captured["json"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(200, json={"success": True, "sandbox_status": "RUNNING"})

    client = OpenHandsClient(
        base_url="http://localhost:3002",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    response = client.send_message("conv-123", text="Continue the task", run=False)

    assert response.status_code == 200
    assert captured == {
        "method": "POST",
        "url": "http://localhost:3002/api/v1/app-conversations/conv-123/send-message",
        "json": {
            "role": "user",
            "content": [{"type": "text", "text": "Continue the task"}],
            "run": False,
        },
    }


def test_wait_for_start_task_returns_ready_payload():
    responses = iter(
        [
            httpx.Response(200, json=[{"id": "task-1", "status": "WORKING"}]),
            httpx.Response(
                200,
                json=[
                    {
                        "id": "task-1",
                        "status": "READY",
                        "app_conversation_id": "conv-123",
                    }
                ],
            ),
        ]
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return next(responses)

    client = OpenHandsClient(
        base_url="http://localhost:3002",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    payload = client.wait_for_start_task("task-1", timeout_seconds=1.0, poll_interval_seconds=0.0)

    assert payload["status"] == "READY"
    assert payload["app_conversation_id"] == "conv-123"


def test_wait_for_start_task_raises_on_error_status():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=[{"id": "task-1", "status": "ERROR", "detail": "sandbox failed"}],
        )

    client = OpenHandsClient(
        base_url="http://localhost:3002",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(RuntimeError, match="sandbox failed"):
        client.wait_for_start_task("task-1", timeout_seconds=0.1, poll_interval_seconds=0.0)
