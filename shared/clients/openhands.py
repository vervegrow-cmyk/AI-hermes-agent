from __future__ import annotations

import time
from typing import Any

import httpx

from shared.config import get_settings


class OpenHandsClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        settings = get_settings()
        self.base_url = (base_url or settings.openhands_base_url).rstrip("/")
        self.timeout = timeout or 300.0
        self._http_client = http_client

    def _headers(self) -> dict[str, str]:
        return {"Content-Type": "application/json"}

    def _client(self) -> httpx.Client:
        return self._http_client or httpx.Client(timeout=self.timeout)

    def health(self) -> httpx.Response:
        client = self._client()
        return client.get(f"{self.base_url}/", headers=self._headers())

    def get_settings(self) -> httpx.Response:
        client = self._client()
        return client.get(f"{self.base_url}/api/v1/settings", headers=self._headers())

    def start_conversation(
        self,
        *,
        initial_user_text: str | None = None,
        title: str | None = None,
        run: bool = True,
        llm_model: str | None = None,
        agent_type: str | None = None,
        trigger: str | None = None,
        selected_repository: str | None = None,
        selected_branch: str | None = None,
        git_provider: str | None = None,
        plugins: list[dict[str, Any]] | None = None,
    ) -> httpx.Response:
        payload: dict[str, Any] = {}
        if initial_user_text is not None:
            payload["initial_message"] = {
                "role": "user",
                "content": [{"type": "text", "text": initial_user_text}],
                "run": run,
            }
        if title is not None:
            payload["title"] = title
        if llm_model is not None:
            payload["llm_model"] = llm_model
        if agent_type is not None:
            payload["agent_type"] = agent_type
        if trigger is not None:
            payload["trigger"] = trigger
        if selected_repository is not None:
            payload["selected_repository"] = selected_repository
        if selected_branch is not None:
            payload["selected_branch"] = selected_branch
        if git_provider is not None:
            payload["git_provider"] = git_provider
        if plugins is not None:
            payload["plugins"] = plugins

        client = self._client()
        return client.post(
            f"{self.base_url}/api/v1/app-conversations",
            headers=self._headers(),
            json=payload,
        )

    def get_start_task(self, task_id: str) -> httpx.Response:
        client = self._client()
        return client.get(
            f"{self.base_url}/api/v1/app-conversations/start-tasks",
            headers=self._headers(),
            params={"ids": task_id},
        )

    def wait_for_start_task(
        self,
        task_id: str,
        *,
        timeout_seconds: float = 180.0,
        poll_interval_seconds: float = 2.0,
    ) -> dict[str, Any]:
        deadline = time.monotonic() + timeout_seconds

        while True:
            response = self.get_start_task(task_id)
            response.raise_for_status()
            payload = response.json()
            task = payload[0] if isinstance(payload, list) and payload else None
            if task is None:
                raise RuntimeError(f"OpenHands start task not found: {task_id}")

            status = str(task.get("status", ""))
            if status == "READY":
                return task
            if status == "ERROR":
                detail = task.get("detail") or "OpenHands start task failed."
                raise RuntimeError(str(detail))
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Timed out waiting for OpenHands start task {task_id} to become READY."
                )
            time.sleep(poll_interval_seconds)

    def send_message(
        self,
        conversation_id: str,
        *,
        text: str,
        run: bool = True,
    ) -> httpx.Response:
        payload = {
            "role": "user",
            "content": [{"type": "text", "text": text}],
            "run": run,
        }
        client = self._client()
        return client.post(
            f"{self.base_url}/api/v1/app-conversations/{conversation_id}/send-message",
            headers=self._headers(),
            json=payload,
        )
