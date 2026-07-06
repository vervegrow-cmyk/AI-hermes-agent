from __future__ import annotations

from typing import Any

from shared.clients import OpenHandsClient


def openhands_conversation(
    *,
    prompt: str,
    conversation_id: str | None = None,
    title: str | None = None,
    run: bool = True,
    wait_for_ready: bool = True,
    ready_timeout_seconds: float = 180.0,
    poll_interval_seconds: float = 2.0,
    llm_model: str | None = None,
    agent_type: str | None = None,
) -> dict[str, Any]:
    client = OpenHandsClient()

    if conversation_id:
        response = client.send_message(conversation_id, text=prompt, run=run)
        response.raise_for_status()
        payload = response.json()
        return {
            "agent": "hermes-trendforge-agent",
            "tool": "openhands",
            "action": "send-message",
            "conversation_id": conversation_id,
            "run": run,
            "response": payload,
            "summary": f"Sent follow-up message to OpenHands conversation {conversation_id}.",
        }

    response = client.start_conversation(
        initial_user_text=prompt,
        title=title,
        run=run,
        llm_model=llm_model,
        agent_type=agent_type,
        trigger="automation",
    )
    response.raise_for_status()
    start_task = response.json()
    resolved_task = start_task

    if wait_for_ready and start_task.get("status") != "READY":
        resolved_task = client.wait_for_start_task(
            str(start_task["id"]),
            timeout_seconds=ready_timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
        )

    resolved_conversation_id = resolved_task.get("app_conversation_id")
    return {
        "agent": "hermes-trendforge-agent",
        "tool": "openhands",
        "action": "start-conversation",
        "conversation_id": resolved_conversation_id,
        "title": title,
        "run": run,
        "wait_for_ready": wait_for_ready,
        "start_task": resolved_task,
        "summary": (
            f"Started OpenHands conversation {resolved_conversation_id}."
            if resolved_conversation_id
            else "Started OpenHands conversation task."
        ),
    }
