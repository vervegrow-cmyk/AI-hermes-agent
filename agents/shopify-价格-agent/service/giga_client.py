from __future__ import annotations

import base64
import hashlib
import hmac
import random
import string
import time
from collections.abc import Callable
from urllib.parse import urljoin
from urllib.parse import urlparse

import httpx

from models.price_sync import GigaPriceSnapshot
from shared.config import get_settings


class GigaClient:
    def __init__(self, http_client: httpx.Client | None = None) -> None:
        self.settings = get_settings()
        self.http_client = http_client or httpx.Client(timeout=self.settings.giga_timeout_seconds)
        self.last_failed_skus: list[dict[str, str]] = []

    def list_price_snapshots(
        self,
        *,
        store_name: str,
        sync_scope: str,
        updated_since: str = "",
        endpoint_override: str = "",
        skus: list[str] | None = None,
        snapshots_override: list[GigaPriceSnapshot] | list[dict] | None = None,
        progress_callback=None,
    ) -> list[GigaPriceSnapshot]:
        self.last_failed_skus = []
        if snapshots_override is not None:
            items = [
                item if isinstance(item, GigaPriceSnapshot) else GigaPriceSnapshot.model_validate(item)
                for item in snapshots_override
            ]
            return [self._with_hash(item, store_name) for item in items]

        if not self._resolved_base_url() or not self._resolved_client_id() or not self._resolved_client_secret():
            return []

        endpoint = endpoint_override or self.settings.giga_price_endpoint
        sku_list = [sku.strip() for sku in (skus or []) if sku and sku.strip()]
        if not sku_list:
            return []

        items: list[dict] = []
        chunks = self._chunked(sku_list, 200)
        for index, chunk in enumerate(chunks, start=1):
            extracted = self._fetch_chunk_with_recovery(
                endpoint=endpoint,
                chunk=chunk,
                progress_callback=progress_callback,
                chunk_index=index,
                chunk_count=len(chunks),
            )
            items.extend(extracted)
            if progress_callback is not None:
                progress_callback(
                    {
                        "chunk_index": index,
                        "chunk_count": len(chunks),
                        "requested_sku_count": len(chunk),
                        "received_item_count": len(extracted),
                        "received_total": len(items),
                        "failed_sku_count": len(self.last_failed_skus),
                    }
                )
        return [self._with_hash(self._normalize_snapshot(item, store_name), store_name) for item in items]

    def debug_price_snapshots(
        self,
        *,
        store_name: str,
        sync_scope: str,
        updated_since: str = "",
        endpoint_override: str = "",
        skus: list[str] | None = None,
    ) -> dict:
        if not self._resolved_base_url() or not self._resolved_client_id() or not self._resolved_client_secret():
            return {
                "ok": False,
                "error": "missing_giga_runtime_config",
                "request": {
                    "base_url": self._resolved_base_url(),
                    "endpoint": self.settings.giga_price_endpoint,
                    "sync_scope": sync_scope,
                    "updated_since": updated_since,
                },
            }

        params = {
            "store_name": store_name,
            "page_size": self.settings.giga_page_size,
            "sync_scope": sync_scope,
        }
        if updated_since:
            params["updated_since"] = updated_since
        endpoint = endpoint_override or self.settings.giga_price_endpoint
        headers = self._build_headers(endpoint)
        sku_list = [sku.strip() for sku in (skus or []) if sku and sku.strip()]
        body = {"skus": sku_list} if sku_list else None
        try:
            if body:
                response, payload = self._post_json_with_response(endpoint=endpoint, body=body)
            else:
                response = self.http_client.get(
                    urljoin(self._resolved_base_url().rstrip("/") + "/", endpoint.lstrip("/")),
                    params=params,
                    headers=headers,
                )
                response.raise_for_status()
                payload = response.json()
            raw_text = response.text[:2000]
            items = self._extract_items(payload)
            normalized = [
                self._with_hash(self._normalize_snapshot(item, store_name), store_name).model_dump(mode="json")
                for item in items[:5]
            ]
            return {
                "ok": True,
                "request": {
                    "base_url": self._resolved_base_url(),
                    "endpoint": endpoint,
                    "params": params,
                    "body": body,
                    "header_names": sorted(headers.keys()),
                    "header_preview": {
                        "client-id": headers.get("client-id", ""),
                        "timestamp": headers.get("timestamp", ""),
                        "nonce": headers.get("nonce", ""),
                        "content-type": headers.get("Content-Type", ""),
                    },
                },
                "response": {
                    "status_code": response.status_code,
                    "item_count": len(items),
                    "payload_type": type(payload).__name__,
                    "payload_keys": sorted(payload.keys()) if isinstance(payload, dict) else [],
                    "success": payload.get("success") if isinstance(payload, dict) else None,
                    "code": payload.get("code") if isinstance(payload, dict) else None,
                    "msg": payload.get("msg") if isinstance(payload, dict) else None,
                    "raw_preview": raw_text,
                    "normalized_preview": normalized,
                },
            }
        except Exception as exc:
            return {
                "ok": False,
                "error": str(exc),
                "request": {
                    "base_url": self._resolved_base_url(),
                    "endpoint": endpoint,
                    "params": params,
                    "body": body,
                    "header_names": sorted(headers.keys()),
                    "header_preview": {
                        "client-id": headers.get("client-id", ""),
                        "timestamp": headers.get("timestamp", ""),
                        "nonce": headers.get("nonce", ""),
                        "content-type": headers.get("Content-Type", ""),
                    },
                },
            }

    def debug_frontend_access(self) -> dict:
        base_url = self.settings.giga_buyer_site_base_url
        route = self.settings.giga_frontend_product_list_route
        if not base_url or not route:
            return {
                "ok": False,
                "error": "missing_frontend_runtime_config",
            }
        target_url = urljoin(base_url.rstrip("/") + "/", route.lstrip("/"))
        headers = {
            "User-Agent": self.settings.giga_buyer_user_agent or "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml",
        }
        if self.settings.giga_buyer_session_cookie:
            headers["Cookie"] = self.settings.giga_buyer_session_cookie
        if self.settings.giga_buyer_csrf_token and self.settings.giga_buyer_csrf_token != "none":
            headers["X-CSRF-TOKEN"] = self.settings.giga_buyer_csrf_token
        try:
            response = self.http_client.get(target_url, headers=headers, follow_redirects=True)
            body = response.text[:2000]
            parsed = urlparse(str(response.url))
            blocked = ("safe/captcha" in str(response.url)) or ("Verification" in body and "AliyunCaptcha" in body)
            return {
                "ok": True,
                "request": {
                    "target_url": target_url,
                    "header_names": sorted(headers.keys()),
                },
                "response": {
                    "status_code": response.status_code,
                    "final_url": str(response.url),
                    "final_path": parsed.path,
                    "blocked_by_captcha": blocked,
                    "body_preview": body,
                },
            }
        except Exception as exc:
            return {
                "ok": False,
                "error": str(exc),
                "request": {
                    "target_url": target_url,
                    "header_names": sorted(headers.keys()),
                },
            }

    def _resolved_base_url(self) -> str:
        return (
            self.settings.giga_api_base_url
            or self.settings.giga_production_base_url
            or self.settings.giga_sandbox_base_url
        )

    def _resolved_client_id(self) -> str:
        return (
            self.settings.giga_api_key
            or self.settings.giga_production_client_id
            or self.settings.giga_sandbox_client_id
        )

    def _resolved_client_secret(self) -> str:
        return (
            self.settings.giga_api_secret
            or self.settings.giga_production_app_secret
            or self.settings.giga_sandbox_app_secret
            or self.settings.giga_sandbox_client_secret
        )

    def _build_headers(self, endpoint: str) -> dict[str, str]:
        nonce = self._generate_nonce()
        timestamp = str(int(time.time() * 1000))
        uri = endpoint
        client_id = self._resolved_client_id()
        client_secret = self._resolved_client_secret()
        message = f"{client_id}&{uri}&{timestamp}&{nonce}"
        secret_key = f"{client_id}&{client_secret}&{nonce}"
        hex_digest = hmac.new(
            secret_key.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        signature = base64.b64encode(hex_digest.encode("utf-8")).decode("utf-8")
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "client-id": client_id,
            "timestamp": timestamp,
            "nonce": nonce,
            "sign": signature,
        }

    def _generate_nonce(self, length: int = 10) -> str:
        alphabet = string.ascii_letters + string.digits
        return "".join(random.choice(alphabet) for _ in range(length))

    def probe_endpoints(
        self,
        *,
        store_name: str,
        sync_scope: str,
        candidates: list[str] | None = None,
    ) -> dict:
        candidate_paths = candidates or [
            self.settings.giga_price_endpoint,
            self.settings.giga_product_list_endpoint,
            "/b2b-overseas-api/v1/buyer/product/detailInfo/v1",
            "/b2b-overseas-api/v1/buyer/inventory/quantity/v1",
        ]
        results: list[dict[str, object]] = []
        for endpoint in candidate_paths:
            path = (endpoint or "").strip()
            if not path:
                continue
            params = {
                "store_name": store_name,
                "page_size": self.settings.giga_page_size,
                "sync_scope": sync_scope,
            }
            headers = self._build_headers(path)
            url = urljoin(self._resolved_base_url().rstrip("/") + "/", path.lstrip("/"))
            try:
                response = self.http_client.get(url, params=params, headers=headers)
                results.append(
                    {
                        "endpoint": path,
                        "status_code": response.status_code,
                        "ok": response.is_success,
                        "raw_preview": response.text[:500],
                    }
                )
            except Exception as exc:
                results.append(
                    {
                        "endpoint": path,
                        "ok": False,
                        "error": str(exc),
                    }
                )
        return {
            "base_url": self._resolved_base_url(),
            "results": results,
        }

    def _post_json(self, *, endpoint: str, body: dict) -> dict:
        _, payload = self._post_json_with_response(endpoint=endpoint, body=body)
        return payload

    def _post_json_with_response(self, *, endpoint: str, body: dict) -> tuple[httpx.Response, dict]:
        last_error: Exception | None = None
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            headers = self._build_headers(endpoint)
            try:
                response = self.http_client.post(
                    urljoin(self._resolved_base_url().rstrip("/") + "/", endpoint.lstrip("/")),
                    headers=headers,
                    json=body,
                )
                response.raise_for_status()
                return response, response.json()
            except httpx.HTTPStatusError as exc:
                last_error = exc
                status_code = exc.response.status_code if exc.response is not None else 0
                if status_code < 500 or attempt >= max_attempts:
                    raise
                time.sleep(min(2**attempt, 5))
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt >= max_attempts:
                    raise
                time.sleep(min(2**attempt, 5))
        if last_error is not None:
            raise last_error
        raise RuntimeError("giga_request_failed_without_error")

    def _fetch_chunk_with_recovery(
        self,
        *,
        endpoint: str,
        chunk: list[str],
        progress_callback: Callable[[dict], None] | None,
        chunk_index: int,
        chunk_count: int,
    ) -> list[dict]:
        try:
            payload = self._post_json(
                endpoint=endpoint,
                body={"skus": chunk},
            )
            return self._extract_items(payload)
        except Exception as exc:
            if len(chunk) == 1:
                self.last_failed_skus.append(
                    {
                        "sku": chunk[0],
                        "error": str(exc),
                    }
                )
                if progress_callback is not None:
                    progress_callback(
                        {
                            "event": "stage",
                            "stage": "giga_chunk_failed",
                            "chunk_index": chunk_index,
                            "chunk_count": chunk_count,
                            "failed_skus": chunk,
                            "error": str(exc),
                        }
                    )
                return []

            midpoint = max(1, len(chunk) // 2)
            left = chunk[:midpoint]
            right = chunk[midpoint:]
            if progress_callback is not None:
                progress_callback(
                    {
                        "event": "stage",
                        "stage": "giga_chunk_split_retry",
                        "chunk_index": chunk_index,
                        "chunk_count": chunk_count,
                        "requested_sku_count": len(chunk),
                        "left_size": len(left),
                        "right_size": len(right),
                        "error": str(exc),
                    }
                )
            return self._fetch_chunk_with_recovery(
                endpoint=endpoint,
                chunk=left,
                progress_callback=progress_callback,
                chunk_index=chunk_index,
                chunk_count=chunk_count,
            ) + self._fetch_chunk_with_recovery(
                endpoint=endpoint,
                chunk=right,
                progress_callback=progress_callback,
                chunk_index=chunk_index,
                chunk_count=chunk_count,
            )

    def _chunked(self, values: list[str], size: int) -> list[list[str]]:
        return [values[index : index + size] for index in range(0, len(values), size)]

    def _extract_items(self, payload: object) -> list[dict]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if not isinstance(payload, dict):
            return []

        data = payload.get("data")
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            nested = data.get("items")
            if isinstance(nested, list):
                return [item for item in nested if isinstance(item, dict)]

        items = payload.get("items")
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]

        return []

    def _with_hash(self, snapshot: GigaPriceSnapshot, store_name: str) -> GigaPriceSnapshot:
        if snapshot.raw_hash:
            return snapshot.model_copy(update={"store_name": store_name or snapshot.store_name})
        raw = "|".join(
            [
                store_name or snapshot.store_name,
                snapshot.giga_sku,
                f"{snapshot.supplier_cost:.2f}",
                f"{snapshot.shipping_cost:.2f}",
                str(snapshot.inventory),
                snapshot.status,
                snapshot.source_updated_at,
            ]
        )
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return snapshot.model_copy(update={"store_name": store_name or snapshot.store_name, "raw_hash": digest})

    def _normalize_snapshot(self, payload: dict, store_name: str) -> GigaPriceSnapshot:
        def pick(*keys: str, default=None):
            for key in keys:
                if key in payload and payload[key] not in (None, ""):
                    return payload[key]
            return default

        return GigaPriceSnapshot(
            store_name=store_name or str(pick("store_name", default="")),
            giga_product_id=str(pick("giga_product_id", "product_id", "goods_id", "spu_id", default="")),
            giga_sku=str(pick("giga_sku", "sku", "sku_code", "variant_sku", default="")),
            supplier_cost=float(pick("supplier_cost", "cost", "supply_price", "price", "unit_price", default=0) or 0),
            shipping_cost=float(
                pick(
                    "shipping_cost",
                    "shippingFee",
                    "logistics_fee",
                    "normal_shipping_fee",
                    "delivery_fee",
                    default=0,
                )
                or 0
            ),
            currency=str(pick("currency", "currency_code", default="USD")),
            inventory=int(pick("inventory", "stock", "available_stock", default=0) or 0),
            status=str(pick("status", "product_status", default="active")),
            source_updated_at=str(pick("source_updated_at", "updated_at", "modify_time", "last_modified_at", default="")),
            raw_hash=str(pick("raw_hash", default="")),
        )
