from __future__ import annotations

from typing import Any

import httpx

from shared.config import get_settings


class FirecrawlClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        settings = get_settings()
        self.base_url = (base_url or settings.firecrawl_base_url).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.firecrawl_api_key
        self.timeout = timeout or settings.firecrawl_timeout_seconds
        self._http_client = http_client

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _client(self) -> httpx.Client:
        return self._http_client or httpx.Client(timeout=self.timeout)

    def health(self) -> httpx.Response:
        client = self._client()
        return client.get(f"{self.base_url}/", headers=self._headers())

    def scrape(
        self,
        url: str,
        *,
        formats: list[str | dict[str, Any]] | None = None,
        timeout: int | None = None,
        only_main_content: bool | None = None,
    ) -> httpx.Response:
        payload: dict[str, Any] = {"url": url}
        if formats is not None:
            payload["formats"] = formats
        if timeout is not None:
            payload["timeout"] = timeout
        if only_main_content is not None:
            payload["onlyMainContent"] = only_main_content

        client = self._client()
        return client.post(
            f"{self.base_url}/v2/scrape",
            headers=self._headers(),
            json=payload,
        )
