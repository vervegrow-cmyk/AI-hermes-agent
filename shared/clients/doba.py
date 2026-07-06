from __future__ import annotations

import base64
from dataclasses import dataclass
from time import sleep, time
from typing import Any

import httpx

from shared.config import get_settings


class DobaAPIError(RuntimeError):
    def __init__(
        self,
        *,
        status_code: int,
        path: str,
        response_code: str = "",
        response_message: str = "",
        response_text: str = "",
    ) -> None:
        details: list[str] = [f"Doba API request failed with status {status_code}", f"path={path}"]
        if response_code:
            details.append(f"responseCode={response_code}")
        if response_message:
            details.append(f"responseMessage={response_message}")
        elif response_text:
            details.append(f"response={response_text[:500]}")
        super().__init__(", ".join(details))
        self.status_code = status_code
        self.path = path
        self.response_code = response_code
        self.response_message = response_message
        self.response_text = response_text


def _extract_doba_error(response: httpx.Response) -> tuple[str, str, str]:
    response_text = response.text or ""
    try:
        payload = response.json()
    except ValueError:
        return "", "", response_text
    if not isinstance(payload, dict):
        return "", "", response_text
    return (
        str(payload.get("responseCode") or "").strip(),
        str(payload.get("responseMessage") or "").strip(),
        response_text,
    )


def _to_pem_block(key_body: str, kind: str) -> bytes:
    cleaned = key_body.strip().replace("\\n", "\n")
    if "BEGIN " in cleaned:
        return cleaned.encode("utf-8")
    return f"-----BEGIN {kind}-----\n{cleaned}\n-----END {kind}-----".encode("utf-8")


def build_doba_signing_string(app_key: str, sign_type: str, timestamp_ms: int) -> str:
    return f"appKey={app_key}&signType={sign_type}&timestamp={timestamp_ms}"


def build_doba_signature(app_key: str, sign_type: str, timestamp_ms: int, private_key: str) -> str:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding

    pem = _to_pem_block(private_key, "PRIVATE KEY")
    signer = serialization.load_pem_private_key(pem, password=None)
    payload = build_doba_signing_string(app_key, sign_type, timestamp_ms).encode("utf-8")
    signature = signer.sign(payload, padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(signature).decode("utf-8")


@dataclass
class DobaClient:
    base_url: str
    app_key: str
    sign_type: str
    private_key: str
    public_key: str = ""
    timeout: float = 30.0
    trust_env: bool = False
    retry_attempts: int = 3
    retry_backoff_seconds: float = 1.5

    @classmethod
    def from_settings(cls) -> "DobaClient":
        settings = get_settings()
        return cls(
            base_url=settings.doba_api_base_url.rstrip("/"),
            app_key=settings.doba_app_key,
            sign_type=settings.doba_sign_type,
            private_key=settings.doba_private_key,
            public_key=settings.doba_public_key,
        )

    def build_headers(self, timestamp_ms: int | None = None) -> dict[str, str]:
        ts = int(timestamp_ms if timestamp_ms is not None else time() * 1000)
        return {
            "appKey": self.app_key,
            "signType": self.sign_type,
            "timestamp": str(ts),
            "sign": build_doba_signature(
                app_key=self.app_key,
                sign_type=self.sign_type,
                timestamp_ms=ts,
                private_key=self.private_key,
            ),
        }

    def build_url(self, path: str) -> str:
        normalized = path if path.startswith("/") else f"/{path}"
        return f"{self.base_url}{normalized}"

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | list[Any] | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(1, self.retry_attempts + 1):
            try:
                with httpx.Client(timeout=timeout or self.timeout, trust_env=self.trust_env) as client:
                    response = client.request(
                        method=method.upper(),
                        url=self.build_url(path),
                        headers=self.build_headers(),
                        params=params,
                        json=json_body,
                    )
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as exc:
                last_error = exc
                status_code = exc.response.status_code
                if status_code not in {408, 425, 429, 500, 502, 503, 504} or attempt == self.retry_attempts:
                    response_code, response_message, response_text = _extract_doba_error(exc.response)
                    raise DobaAPIError(
                        status_code=status_code,
                        path=path,
                        response_code=response_code,
                        response_message=response_message,
                        response_text=response_text,
                    ) from exc
            except (httpx.TimeoutException, httpx.NetworkError, httpx.ProtocolError) as exc:
                last_error = exc
                if attempt == self.retry_attempts:
                    raise
            if attempt < self.retry_attempts:
                sleep(self.retry_backoff_seconds * attempt)
        if last_error:
            raise last_error
        raise RuntimeError("Doba request failed without a concrete error.")

    def get(self, path: str, *, params: dict[str, Any] | None = None) -> httpx.Response:
        return self.request("GET", path, params=params)

    def post(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | list[Any] | None = None,
    ) -> httpx.Response:
        return self.request("POST", path, params=params, json_body=json_body)
