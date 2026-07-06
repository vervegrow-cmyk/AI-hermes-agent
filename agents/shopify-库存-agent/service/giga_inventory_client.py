from __future__ import annotations

import base64
import hashlib
import hmac
import json
import random
import string
import time
from urllib.parse import urljoin

import httpx

from models.inventory_sync import GigaInventoryRecord
from shared.config import get_settings


class GigaInventoryClientError(RuntimeError):
    """Raised when Giga OpenAPI validation or inventory queries fail."""


class GigaInventoryClient:
    MIN_REQUEST_INTERVAL_SECONDS = 1.0

    def __init__(self, http_client: httpx.Client | None = None) -> None:
        self.settings = get_settings()
        timeout = self.settings.inventory_sync_request_timeout_seconds or self.settings.giga_timeout_seconds
        self.http_client = http_client or httpx.Client(timeout=timeout)
        self._last_request_at = 0.0

    def validate_connection(self) -> dict:
        base_url = self._resolved_base_url()
        client_id = self._resolved_client_id()
        client_secret = self._resolved_client_secret()
        if not base_url or not client_id or not client_secret:
            raise GigaInventoryClientError(
                "缺少 Giga 运行配置，请检查 GIGA_API_BASE_URL、GIGA_API_KEY、GIGA_API_SECRET。"
            )

        endpoint = (
            self.settings.giga_validation_endpoint
            or self.settings.giga_product_list_endpoint
            or self.settings.giga_inventory_endpoint
        )
        try:
            body = self._build_validation_body(endpoint)
            response = self._post_with_throttle(endpoint=endpoint, body=body)
            payload = response.json()
            if response.status_code >= 400:
                self._raise_for_business_error(payload, endpoint=endpoint, body=body)
                response.raise_for_status()
            self._raise_for_business_error(payload, endpoint=endpoint, body=body)
        except Exception as exc:
            raise GigaInventoryClientError(f"Giga 连接验证失败: {exc}") from exc

        return {
            "base_url": base_url,
            "endpoint": endpoint,
            "validation_body": body,
            "response_type": type(payload).__name__,
            "payload_keys": sorted(payload.keys()) if isinstance(payload, dict) else [],
        }

    def fetch_inventory_by_sku(self, sku: str) -> list[GigaInventoryRecord]:
        clean_sku = (sku or "").strip()
        if not clean_sku:
            return []

        endpoint = self.settings.giga_inventory_endpoint
        if not endpoint:
            raise GigaInventoryClientError("缺少 GIGA_INVENTORY_ENDPOINT 配置。")

        payload = self._post_json(endpoint=endpoint, body={"skus": [clean_sku]})
        items = self._extract_items(payload)
        matches: list[GigaInventoryRecord] = []
        for item in items:
            normalized = self._normalize_inventory(item)
            if normalized.sku == clean_sku:
                matches.append(normalized)
        return matches

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
        client_id = self._resolved_client_id()
        client_secret = self._resolved_client_secret()
        message = f"{client_id}&{endpoint}&{timestamp}&{nonce}"
        secret_key = f"{client_id}&{client_secret}&{nonce}"
        digest = hmac.new(secret_key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()
        signature = base64.b64encode(digest.encode("utf-8")).decode("utf-8")
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

    def _post_json(self, *, endpoint: str, body: dict) -> dict | list:
        attempts = max(1, int(self.settings.inventory_sync_retry_attempts))
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                response = self._post_with_throttle(endpoint=endpoint, body=body)
                payload = response.json()
                if response.status_code >= 400:
                    self._raise_for_business_error(payload, endpoint=endpoint, body=body)
                    response.raise_for_status()
                self._raise_for_business_error(payload, endpoint=endpoint, body=body)
                return payload
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if attempt == attempts:
                    break
                time.sleep(0.5 * attempt)
            except GigaInventoryClientError as exc:
                last_error = exc
                if attempt == attempts:
                    break
                time.sleep(0.5 * attempt)
            except Exception as exc:
                last_error = exc
                if attempt == attempts:
                    break
                time.sleep(0.5 * attempt)
        raise GigaInventoryClientError(f"Giga 库存请求失败: {last_error}") from last_error

    def _post_with_throttle(self, *, endpoint: str, body: dict) -> httpx.Response:
        self._sleep_for_rate_limit()
        response = self.http_client.post(
            urljoin(self._resolved_base_url().rstrip("/") + "/", endpoint.lstrip("/")),
            headers=self._build_headers(endpoint),
            json=body,
        )
        self._last_request_at = time.monotonic()
        return response

    def _sleep_for_rate_limit(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_request_at
        remaining = self.MIN_REQUEST_INTERVAL_SECONDS - elapsed
        if remaining > 0:
            time.sleep(remaining)

    def _raise_for_business_error(self, payload: object, *, endpoint: str, body: dict) -> None:
        if not isinstance(payload, dict):
            return
        success = payload.get("success")
        code = str(payload.get("code", "")).strip()
        if success is True or code == "200":
            return

        msg = str(payload.get("msg", "")).strip()
        sub_msg = str(payload.get("subMsg", "")).strip()
        business_message = self._translate_business_error(code=code, msg=msg, sub_msg=sub_msg, endpoint=endpoint)
        details = {
            "code": code,
            "msg": msg,
            "subMsg": sub_msg,
            "endpoint": endpoint,
            "body": body,
        }
        raise GigaInventoryClientError(
            f"{business_message} | 响应详情: {json.dumps(details, ensure_ascii=False)}"
        )

    def _translate_business_error(self, *, code: str, msg: str, sub_msg: str, endpoint: str) -> str:
        lower_msg = msg.lower()
        lower_sub = sub_msg.lower()
        if code == "401" and "interface not available" in lower_msg:
            return f"当前 API Key 未开通库存接口权限，无法访问 {endpoint}"
        if code == "B50003" and ("收藏夹" in sub_msg or "saved items" in lower_sub or "无库存" in sub_msg):
            return "该 SKU 未加入 Saved Items，或当前没有备货库存"
        if code == "B20003" and ("saved items" in lower_sub or "stockpiled inventory" in lower_sub):
            return "该 SKU 未加入 Saved Items，或当前没有备货库存"
        if "too many requests" in lower_msg or "rate limit exceeded" in lower_msg or "rate limit exceeded" in lower_sub:
            return "Giga 返回业务错误：Too many requests. Rate limit exceeded；无附加说明"
        if code == "B50001" and "sku" in lower_sub:
            return "Giga 请求缺少 SKU 参数"
        if code in {"B50002", "B20002"}:
            return f"Giga 请求参数格式错误：{sub_msg or msg}"
        if code == "B50004":
            return "该 SKU 在 Giga 平台不存在，或返回了重复数据"
        if msg or sub_msg:
            return f"Giga 返回业务错误：{msg or '未知错误'}；{sub_msg or '无附加说明'}"
        return "Giga 返回未知业务错误"

    def _build_validation_body(self, endpoint: str) -> dict:
        if endpoint == self.settings.giga_inventory_endpoint:
            return {"skus": [""]}
        if endpoint == self.settings.giga_price_endpoint:
            return {"skus": [""]}
        return {"skus": [""]}

    def _extract_items(self, payload: object) -> list[dict]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if not isinstance(payload, dict):
            return []
        data = payload.get("data")
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            nested_items = data.get("items")
            if isinstance(nested_items, list):
                return [item for item in nested_items if isinstance(item, dict)]
            records = data.get("records")
            if isinstance(records, list):
                return [item for item in records if isinstance(item, dict)]
        if isinstance(payload.get("items"), list):
            return [item for item in payload["items"] if isinstance(item, dict)]
        return []

    def _normalize_inventory(self, payload: dict) -> GigaInventoryRecord:
        sku = str(
            payload.get("sku")
            or payload.get("sku_code")
            or payload.get("giga_sku")
            or payload.get("variant_sku")
            or ""
        ).strip()

        seller_info = payload.get("sellerInventoryInfo") or {}
        buyer_info = payload.get("buyerInventoryInfo") or {}

        quantity = seller_info.get("sellerAvailableInventory")
        if quantity in (None, ""):
            quantity = payload.get("available_inventory")
        if quantity in (None, ""):
            quantity = payload.get("inventory")
        if quantity in (None, ""):
            quantity = payload.get("stock")
        if quantity in (None, ""):
            quantity = payload.get("available_stock")
        if quantity in (None, ""):
            quantity = buyer_info.get("totalBuyerAvailableInventory")

        return GigaInventoryRecord(
            sku=sku,
            available_inventory=int(quantity or 0),
            raw=dict(payload),
        )
