from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from models.price_sync import DobaPriceSnapshot
from shared.clients import DobaClient as SharedDobaClient
from shared.clients.doba import build_doba_signature
from shared.config import get_settings


REASON_DOBA_API_ERROR = "doba_api_error"
REASON_DOBA_EMPTY_RESPONSE = "doba_empty_response"
REASON_DOBA_SCHEMA_UNKNOWN = "doba_schema_unknown"

RETAILER_CATEGORY_ENDPOINT = "/api/category/doba/list"
RETAILER_SPU_LIST_ENDPOINT = "/api/goods/doba/spu/list"
RETAILER_SPU_DETAIL_ENDPOINT = "/api/goods/doba/spu/detail"
RETAILER_UPDATED_ENDPOINT = "/api/goods/doba/updated"
RETAILER_STOCK_ENDPOINT = "/api/goods/doba/stock"
RETAILER_PLATFORM_ENDPOINT = "/api/platform/list"
RETAILER_SHIPPING_ENDPOINT = "/api/shipping/doba/cost/goods"

DEFAULT_PROBE_ENDPOINTS = (
    RETAILER_CATEGORY_ENDPOINT,
    RETAILER_SPU_LIST_ENDPOINT,
    RETAILER_UPDATED_ENDPOINT,
    RETAILER_STOCK_ENDPOINT,
    RETAILER_SHIPPING_ENDPOINT,
)


class DobaPriceSyncClient:
    def __init__(self, *, client: SharedDobaClient | None = None, http_client: Any | None = None) -> None:
        self.settings = get_settings()
        self.client = client
        self.http_client = http_client
        self._platform_id_cache = self.settings.doba_price_sync_platform_id

    def list_price_snapshots(
        self,
        *,
        store_name: str,
        sync_scope: str,
        updated_since: str = "",
        skus: list[str] | None = None,
        snapshots_override: list[DobaPriceSnapshot] | list[dict] | None = None,
    ) -> list[DobaPriceSnapshot]:
        if snapshots_override is not None:
            return [
                item if isinstance(item, DobaPriceSnapshot) else DobaPriceSnapshot.model_validate(item)
                for item in snapshots_override
            ]
        if self._should_use_retailer_mainline():
            return self._list_retailer_snapshots(
                store_name=store_name,
                sync_scope=sync_scope,
                updated_since=updated_since,
                skus=skus or [],
            )

        payload = self._request_payload(sync_scope=sync_scope, updated_since=updated_since, skus=skus or [])
        response = self._request(payload)
        data = self._extract_items(response)
        return [self._normalize_item(store_name=store_name, item=item) for item in data]

    def debug_price_snapshots(
        self,
        *,
        store_name: str,
        sync_scope: str,
        updated_since: str = "",
        endpoint_override: str = "",
        skus: list[str] | None = None,
    ) -> dict[str, Any]:
        endpoint = endpoint_override or self._debug_primary_endpoint(sync_scope=sync_scope, skus=skus or [])
        payload = self._request_payload(sync_scope=sync_scope, updated_since=updated_since, skus=skus or [])
        base_url = self.settings.doba_api_base_url.rstrip("/")
        retailer_strategy = self._build_retailer_strategy(sync_scope=sync_scope, updated_since=updated_since, skus=skus or [])
        probes = self.probe_endpoints(sync_scope=sync_scope, updated_since=updated_since, skus=skus or [])
        try:
            snapshots = self.list_price_snapshots(
                store_name=store_name,
                sync_scope=sync_scope,
                updated_since=updated_since,
                skus=skus or [],
            )
            return {
                "ok": True,
                "request": {
                    "base_url": base_url,
                    "endpoint": endpoint,
                    "auth_mode": self.settings.doba_auth_mode,
                    "params": payload,
                    "header_names": self._header_names(),
                    "token_loaded": bool(self.settings.doba_access_token),
                },
                "response": {
                    "status_code": 200,
                    "payload_top_level_keys": ["snapshots"],
                    "item_count": len(snapshots),
                    "normalized_preview": [item.model_dump(mode="json") for item in snapshots[:3]],
                    "error_message": "",
                },
                "retailer_strategy": retailer_strategy,
                "probe_results": probes,
            }
        except Exception as exc:
            return {
                "ok": False,
                "request": {
                    "base_url": base_url,
                    "endpoint": endpoint,
                    "auth_mode": self.settings.doba_auth_mode,
                    "params": payload,
                    "header_names": self._header_names(),
                    "token_loaded": bool(self.settings.doba_access_token),
                },
                "response": {
                    "status_code": getattr(getattr(exc, "response", None), "status_code", 0),
                    "payload_top_level_keys": [],
                    "item_count": 0,
                    "normalized_preview": [],
                    "error_message": str(exc),
                },
                "retailer_strategy": retailer_strategy,
                "probe_results": probes,
            }

    def probe_endpoints(
        self,
        *,
        sync_scope: str = "full",
        updated_since: str = "",
        skus: list[str] | None = None,
        candidates: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        item_no = self._discover_probe_item_no(sync_scope=sync_scope, updated_since=updated_since, skus=skus or [])
        for endpoint in candidates or list(DEFAULT_PROBE_ENDPOINTS):
            payload = self._endpoint_payload(
                endpoint,
                sync_scope=sync_scope,
                updated_since=updated_since,
                skus=skus or [],
                sample_item_no=item_no,
            )
            results.append(self._probe_single_endpoint(endpoint=endpoint, payload=payload))
        return results

    def _list_retailer_snapshots(
        self,
        *,
        store_name: str,
        sync_scope: str,
        updated_since: str,
        skus: list[str],
    ) -> list[DobaPriceSnapshot]:
        updated_rows: dict[str, dict[str, Any]] = {}
        detail_by_item: dict[str, dict[str, Any]] = {}

        if skus:
            item_nos = self._unique_preserve_order(skus)
            detail_by_item = self._fetch_detail_by_item_nos(item_nos)
        elif sync_scope == "incremental":
            updated_rows = self._fetch_updated_rows(updated_since=updated_since)
            item_nos = list(updated_rows.keys())
            detail_by_item = self._fetch_detail_by_item_nos(item_nos)
        else:
            if not self.settings.doba_allow_full_scan:
                raise RuntimeError("doba_full_scan_disabled")
            detail_by_item = self._fetch_full_catalog_detail_by_item()
            item_nos = list(detail_by_item.keys())

        if not item_nos:
            return []

        stock_rows = self._fetch_stock_rows(item_nos)
        if not stock_rows and sync_scope == "incremental" and updated_rows:
            stock_rows = {
                key: {"itemNo": key, "sellingPrice": value.get("updateDetail"), "availableNum": 0}
                for key, value in updated_rows.items()
            }

        shipping_rows = self._fetch_shipping_rows(item_nos)
        snapshots: list[DobaPriceSnapshot] = []
        for item_no in item_nos:
            stock_row = stock_rows.get(item_no, {"itemNo": item_no})
            detail_row = detail_by_item.get(item_no, {})
            updated_row = updated_rows.get(item_no, {})
            shipping_row = shipping_rows.get(item_no, {})
            snapshots.append(
                self._normalize_retailer_item(
                    store_name=store_name,
                    item_no=item_no,
                    stock_row=stock_row,
                    detail_row=detail_row,
                    updated_row=updated_row,
                    shipping_row=shipping_row,
                )
            )
        return snapshots

    def _fetch_full_catalog_detail_by_item(self) -> dict[str, dict[str, Any]]:
        page_size = min(max(int(self.settings.doba_price_sync_full_page_size), 1), 20)
        max_pages = max(int(self.settings.doba_price_sync_full_max_pages), 0)
        spu_nos: list[str] = []
        seen_spu_nos: set[str] = set()
        page_number = 1

        while True:
            response = self._request_endpoint(
                RETAILER_SPU_LIST_ENDPOINT,
                {
                    "pageNumber": page_number,
                    "pageSize": page_size,
                },
            )
            payload = self._unwrap_business_data(response.json())
            goods_list = list((payload or {}).get("goodsList") or [])
            if not goods_list:
                break
            page_new_count = 0
            for item in goods_list:
                spu_no = str((item or {}).get("spuNo") or "").strip()
                if not spu_no or spu_no in seen_spu_nos:
                    continue
                seen_spu_nos.add(spu_no)
                spu_nos.append(spu_no)
                page_new_count += 1
            if len(goods_list) < page_size:
                break
            if max_pages and page_number >= max_pages:
                break
            if page_new_count == 0:
                break
            page_number += 1

        if not spu_nos:
            return {}
        by_item: dict[str, dict[str, Any]] = {}
        for chunk in self._chunked(spu_nos, 20):
            detail_response = self._request_endpoint(
                RETAILER_SPU_DETAIL_ENDPOINT,
                {"spuNo": ",".join(chunk)},
            )
            detail_rows = self._unwrap_business_data(detail_response.json())
            for detail in list(detail_rows or []):
                meta = {
                    "spuId": str((detail or {}).get("spuId") or ""),
                    "spuNo": str((detail or {}).get("spuNo") or ""),
                    "title": str((detail or {}).get("title") or ""),
                    "sellerName": str((detail or {}).get("sellerName") or ""),
                }
                for child in list((detail or {}).get("children") or []):
                    for stock in list((child or {}).get("stocks") or []):
                        item_no = str((stock or {}).get("itemNo") or "").strip()
                        if not item_no:
                            continue
                        by_item[item_no] = {
                            **meta,
                            "skuId": str((child or {}).get("skuId") or ""),
                            "skuCode": str((child or {}).get("skuCode") or ""),
                            "currencyId": str((child or {}).get("currencyId") or "USD"),
                            "stockHint": stock,
                        }
        return by_item

    def _fetch_detail_by_item_nos(self, item_nos: list[str]) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for chunk in self._chunked(self._unique_preserve_order(item_nos), 20):
            response = self._request_endpoint(
                RETAILER_SPU_DETAIL_ENDPOINT,
                {"itemNo": ",".join(chunk)},
            )
            detail_rows = list(self._unwrap_business_data(response.json()) or [])
            for detail in detail_rows:
                meta = {
                    "spuId": str((detail or {}).get("spuId") or ""),
                    "spuNo": str((detail or {}).get("spuNo") or ""),
                    "title": str((detail or {}).get("title") or ""),
                    "sellerName": str((detail or {}).get("sellerName") or ""),
                }
                for child in list((detail or {}).get("children") or []):
                    for stock in list((child or {}).get("stocks") or []):
                        item_no = str((stock or {}).get("itemNo") or "").strip()
                        if not item_no:
                            continue
                        result[item_no] = {
                            **meta,
                            "skuId": str((child or {}).get("skuId") or ""),
                            "skuCode": str((child or {}).get("skuCode") or ""),
                            "currencyId": str((child or {}).get("currencyId") or "USD"),
                            "stockHint": stock,
                        }
        return result

    def _fetch_updated_rows(self, *, updated_since: str) -> dict[str, dict[str, Any]]:
        payload = self._endpoint_payload(
            RETAILER_UPDATED_ENDPOINT,
            sync_scope="incremental",
            updated_since=updated_since,
        )
        response = self._request_endpoint(RETAILER_UPDATED_ENDPOINT, payload)
        data = self._unwrap_business_data(response.json())
        rows = list((data or {}).get("productUpdateInfoList") or [])
        return {
            str((item or {}).get("itemNo") or "").strip(): item
            for item in rows
            if str((item or {}).get("itemNo") or "").strip()
        }

    def _fetch_stock_rows(self, item_nos: list[str]) -> dict[str, dict[str, Any]]:
        rows: dict[str, dict[str, Any]] = {}
        for chunk in self._chunked(self._unique_preserve_order(item_nos), 20):
            response = self._request_endpoint(
                RETAILER_STOCK_ENDPOINT,
                {"itemNo": ",".join(chunk)},
            )
            data = list(self._unwrap_business_data(response.json()) or [])
            for item in data:
                item_no = str((item or {}).get("itemNo") or "").strip()
                if item_no:
                    rows[item_no] = item
        return rows

    def _fetch_shipping_rows(self, item_nos: list[str]) -> dict[str, dict[str, Any]]:
        platform_id = self._resolve_platform_id()
        if not platform_id:
            return {}
        rows: dict[str, dict[str, Any]] = {}
        for chunk in self._chunked(self._unique_preserve_order(item_nos), 20):
            response = self._request_endpoint(
                RETAILER_SHIPPING_ENDPOINT,
                {
                    "shipToCountry": self.settings.doba_price_sync_ship_to_country,
                    "platformId": platform_id,
                    "goods": [{"itemNo": item_no, "quantity": 1} for item_no in chunk],
                },
            )
            data = list(self._unwrap_business_data(response.json()) or [])
            for item in data:
                detail = (item or {}).get("data") or {}
                item_no = str(detail.get("itemNo") or "").strip()
                if not item_no:
                    continue
                costs = list(detail.get("costs") or [])
                costs.sort(key=lambda cost: self._to_float((cost or {}).get("shipFee")) or 0.0)
                rows[item_no] = {
                    "itemNo": item_no,
                    "quantity": detail.get("quantity"),
                    "cost": costs[0] if costs else None,
                    "successful": bool((item or {}).get("successful")),
                    "businessMessage": str((item or {}).get("businessMessage") or ""),
                }
        return rows

    def _resolve_platform_id(self) -> str:
        if self._platform_id_cache:
            return self._platform_id_cache
        response = self._request_endpoint(RETAILER_PLATFORM_ENDPOINT, {})
        data = response.json().get("businessData")
        if not isinstance(data, list):
            return ""
        target_name = self.settings.doba_price_sync_platform_name.strip().lower()
        for row in data:
            if str((row or {}).get("platformName") or "").strip().lower() == target_name:
                self._platform_id_cache = str((row or {}).get("platformId") or "").strip()
                break
        return self._platform_id_cache

    def _normalize_retailer_item(
        self,
        *,
        store_name: str,
        item_no: str,
        stock_row: dict[str, Any],
        detail_row: dict[str, Any],
        updated_row: dict[str, Any],
        shipping_row: dict[str, Any],
    ) -> DobaPriceSnapshot:
        merged = {
            "itemNo": item_no,
            "stock": stock_row,
            "detail": detail_row,
            "updated": updated_row,
            "shipping": shipping_row,
        }
        shipping_cost = self._to_float(
            ((shipping_row.get("cost") or {}) if isinstance(shipping_row, dict) else {}).get("shipFee")
        )
        supplier_cost = self._to_float(
            self._pick_first(
                stock_row,
                "supplierCost",
                "cost",
                "price",
                "productPrice",
                "sellingPrice",
                "pickupSellingPrice",
            )
        )
        if supplier_cost is None:
            supplier_cost = self._to_float((updated_row or {}).get("updateDetail"))
        normalized_payload = json.dumps(merged, ensure_ascii=True, sort_keys=True)
        estimated_total_cost = sum(value for value in (supplier_cost, shipping_cost) if value is not None)
        return DobaPriceSnapshot(
            store_name=store_name,
            doba_product_id=str((detail_row or {}).get("spuId") or (detail_row or {}).get("spuNo") or ""),
            doba_sku=item_no,
            supplier_cost=supplier_cost,
            shipping_cost=shipping_cost,
            handling_fee=0.0,
            warehouse_fee=0.0,
            estimated_total_cost=round(estimated_total_cost, 2),
            currency=self._pick_first(stock_row, "currencyId", "currency", "currencyCode")
            or str((detail_row or {}).get("currencyId") or "USD"),
            inventory=int(self._to_float(self._pick_first(stock_row, "availableNum", "inventory", "stock")) or 0),
            status="active",
            source_updated_at=str((updated_row or {}).get("updateTime") or ""),
            raw_payload=merged,
            raw_hash=hashlib.sha256(normalized_payload.encode("utf-8")).hexdigest(),
        )

    def _request_payload(self, *, sync_scope: str, updated_since: str, skus: list[str]) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if skus:
            payload["skus"] = skus
            payload["itemNo"] = ",".join(skus[:20])
        if sync_scope == "incremental" and updated_since:
            payload["updated_since"] = updated_since
            payload["updateTimeAfter"] = updated_since
            payload["updateTimeBefore"] = self._format_updated_timestamp()
        if self.settings.doba_api_version:
            payload["version"] = self.settings.doba_api_version
        return payload

    def _request(self, payload: dict[str, Any], endpoint: str | None = None) -> Any:
        path = endpoint or self.settings.doba_price_endpoint
        return self._request_endpoint(path, payload)

    def _request_endpoint(self, path: str, payload: dict[str, Any]) -> Any:
        method = self._http_method_for_endpoint(path)
        url = f"{self.settings.doba_api_base_url.rstrip('/')}/{path.lstrip('/')}"
        headers = self._headers_for_http_client(path)
        params = self._query_params_for_endpoint(path, payload)
        json_body = None if method == "GET" else payload
        if self.http_client is not None:
            response = self.http_client.request(method, url, headers=headers, params=params, json=json_body)
            if hasattr(response, "raise_for_status"):
                response.raise_for_status()
            return response
        if self.settings.doba_auth_mode.strip().lower() == "access_token" and self.settings.doba_access_token:
            with httpx.Client(timeout=30.0, trust_env=False) as client:
                response = client.request(method, url, headers=headers, params=params, json=json_body)
                response.raise_for_status()
                return response
        if path.startswith("/api/"):
            with httpx.Client(timeout=30.0, trust_env=False) as client:
                response = client.request(method, url, headers=headers, params=params, json=json_body)
            response.raise_for_status()
            return response
        client = self.client or SharedDobaClient.from_settings()
        if method == "GET":
            return client.get(path, params=params)
        return client.post(path, params=params, json_body=payload)

    def _extract_items(self, payload_or_response: Any) -> list[dict[str, Any]]:
        payload = payload_or_response.json() if hasattr(payload_or_response, "json") else payload_or_response
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if not isinstance(payload, dict):
            raise ValueError(REASON_DOBA_SCHEMA_UNKNOWN)
        for key in ("items", "data", "result", "products", "rows"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
            if isinstance(value, dict):
                for nested_key in ("items", "rows", "list", "data"):
                    nested = value.get(nested_key)
                    if isinstance(nested, list):
                        return [item for item in nested if isinstance(item, dict)]
        raise ValueError(REASON_DOBA_EMPTY_RESPONSE if payload else REASON_DOBA_SCHEMA_UNKNOWN)

    def _normalize_item(self, *, store_name: str, item: dict[str, Any]) -> DobaPriceSnapshot:
        sku = self._pick_first(item, "dobaSku", "sku", "supplierSku", "productSku")
        if not sku:
            raise ValueError(REASON_DOBA_SCHEMA_UNKNOWN)
        supplier_cost = self._to_float(self._pick_first(item, "supplierCost", "cost", "price", "productPrice"))
        shipping_cost = self._to_float(self._pick_first(item, "shippingCost", "shipping_fee", "normalShippingFee", "shipping"))
        handling_fee = self._to_float(self._pick_first(item, "handlingFee", "handling_fee"))
        warehouse_fee = self._to_float(self._pick_first(item, "warehouseFee", "warehouse_fee"))
        estimated_total_cost = sum(value for value in (supplier_cost, shipping_cost, handling_fee, warehouse_fee) if value is not None)
        normalized_payload = json.dumps(item, ensure_ascii=True, sort_keys=True)
        return DobaPriceSnapshot(
            store_name=store_name,
            doba_product_id=self._pick_first(item, "dobaProductId", "productId", "spu", "product_id"),
            doba_sku=sku,
            supplier_cost=supplier_cost,
            shipping_cost=shipping_cost,
            handling_fee=handling_fee or 0.0,
            warehouse_fee=warehouse_fee or 0.0,
            estimated_total_cost=round(estimated_total_cost, 2),
            currency=self._pick_first(item, "currency", "currencyCode") or "USD",
            inventory=int(self._to_float(self._pick_first(item, "inventory", "stock", "availableStock")) or 0),
            status=self._pick_first(item, "status", "productStatus") or "active",
            source_updated_at=self._pick_first(item, "updatedAt", "updateTime", "modified", "modifiedAt") or "",
            raw_payload=item,
            raw_hash=hashlib.sha256(normalized_payload.encode("utf-8")).hexdigest(),
        )

    def _headers_for_http_client(self, path: str) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.settings.doba_access_token:
            headers["Authorization"] = f"Bearer {self.settings.doba_access_token}"
        if path.startswith("/api/") and self.settings.doba_auth_mode.strip().lower() == "signature" and self.settings.doba_app_key and self.settings.doba_private_key:
            headers.update(self._retailer_signature_headers())
        return headers

    def _header_names(self) -> list[str]:
        names = ["Content-Type"]
        if self.settings.doba_access_token:
            names.append("Authorization")
        if self.settings.doba_app_key:
            names.extend(["appKey", "signType", "timestamp", "sign"])
        if self.settings.doba_retailer_id:
            names.append("retailerId")
        return names

    def _http_method_for_endpoint(self, path: str) -> str:
        if path == RETAILER_SHIPPING_ENDPOINT:
            return "POST"
        if path.startswith("/api/"):
            return "GET"
        return "POST"

    def _query_params_for_endpoint(self, path: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        if not path.startswith("/api/"):
            return None
        if self._http_method_for_endpoint(path) == "POST":
            return None
        query_payload = dict(payload)
        query_payload.pop("skus", None)
        return {key: value for key, value in query_payload.items() if value not in (None, "", [], {})}

    def _retailer_signature_headers(self) -> dict[str, str]:
        timestamp_ms = int(time.time() * 1000)
        headers = {
            "appKey": self.settings.doba_app_key,
            "signType": self.settings.doba_sign_type,
            "timestamp": str(timestamp_ms),
            "sign": build_doba_signature(
                app_key=self.settings.doba_app_key,
                sign_type=self.settings.doba_sign_type,
                timestamp_ms=timestamp_ms,
                private_key=self.settings.doba_private_key,
            ),
        }
        if self.settings.doba_retailer_id:
            headers["retailerId"] = self.settings.doba_retailer_id
        return headers

    def _probe_single_endpoint(self, *, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.settings.doba_api_base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        method = self._http_method_for_endpoint(endpoint)
        headers = self._headers_for_http_client(endpoint)
        params = self._query_params_for_endpoint(endpoint, payload)
        result = {
            "endpoint": endpoint,
            "method": method,
            "header_names": sorted(headers.keys()),
            "query_keys": sorted((params or {}).keys()),
            "body_keys": sorted(payload.keys()) if method == "POST" else [],
        }
        try:
            if self.http_client is not None:
                response = self.http_client.request(method, url, headers=headers, params=params, json=None if method == "GET" else payload)
            else:
                with httpx.Client(timeout=20.0, trust_env=False) as client:
                    response = client.request(method, url, headers=headers, params=params, json=None if method == "GET" else payload)
            result["status_code"] = response.status_code
            try:
                body = response.json()
            except ValueError:
                body = {}
            if isinstance(body, dict):
                business = body.get("businessData")
                result["responseCode"] = str(body.get("responseCode") or "")
                result["responseMessage"] = str(body.get("responseMessage") or "")
                result["payload_top_level_keys"] = sorted(body.keys())
                if isinstance(business, dict):
                    result["businessStatus"] = str(business.get("businessStatus") or "")
                    result["businessMessage"] = str(business.get("businessMessage") or "")
                else:
                    result["businessStatus"] = ""
                    result["businessMessage"] = ""
            else:
                result["responseCode"] = ""
                result["responseMessage"] = ""
                result["payload_top_level_keys"] = []
                result["businessStatus"] = ""
                result["businessMessage"] = ""
            result["ok"] = response.is_success
        except Exception as exc:
            result["ok"] = False
            result["status_code"] = getattr(getattr(exc, "response", None), "status_code", 0)
            result["responseCode"] = ""
            result["responseMessage"] = str(exc)
            result["payload_top_level_keys"] = []
            result["businessStatus"] = ""
            result["businessMessage"] = ""
        return result

    def _endpoint_payload(
        self,
        endpoint: str,
        *,
        sync_scope: str,
        updated_since: str = "",
        skus: list[str] | None = None,
        sample_item_no: str = "",
    ) -> dict[str, Any]:
        if endpoint == RETAILER_CATEGORY_ENDPOINT:
            return {}
        if endpoint == RETAILER_SPU_LIST_ENDPOINT:
            return {
                "pageNumber": 1,
                "pageSize": min(max(int(self.settings.doba_price_sync_full_page_size), 1), 20),
            }
        if endpoint == RETAILER_SPU_DETAIL_ENDPOINT:
            chosen = sample_item_no or next(iter(skus or []), "")
            return {"itemNo": chosen} if chosen else {"spuNo": "D0100HHHD06"}
        if endpoint == RETAILER_UPDATED_ENDPOINT:
            return {
                "pageNo": 1,
                "pageSize": 5,
                "updateType": 1,
                "updateTimeAfter": self._format_updated_timestamp(updated_since, fallback_hours=48),
                "updateTimeBefore": self._format_updated_timestamp(),
            }
        if endpoint == RETAILER_STOCK_ENDPOINT:
            chosen = sample_item_no or next(iter(skus or []), "")
            return {"itemNo": chosen or "TEST"}
        if endpoint == RETAILER_SHIPPING_ENDPOINT:
            chosen = sample_item_no or next(iter(skus or []), "")
            platform_id = self._platform_id_cache or self.settings.doba_price_sync_platform_id or "unknown-platform"
            return {
                "shipToCountry": self.settings.doba_price_sync_ship_to_country,
                "platformId": platform_id,
                "goods": [{"itemNo": chosen or "TEST", "quantity": 1}],
            }
        return self._request_payload(sync_scope=sync_scope, updated_since=updated_since, skus=skus or [])

    def _build_retailer_strategy(self, *, sync_scope: str, updated_since: str, skus: list[str]) -> dict[str, Any]:
        platform_id = self._platform_id_cache or self.settings.doba_price_sync_platform_id
        if not platform_id:
            try:
                platform_id = self._resolve_platform_id()
            except Exception:
                platform_id = ""
        return {
            "enabled": self._should_use_retailer_mainline(),
            "platform_name": self.settings.doba_price_sync_platform_name,
            "platform_id": platform_id,
            "ship_to_country": self.settings.doba_price_sync_ship_to_country,
            "full_page_size": self.settings.doba_price_sync_full_page_size,
            "full_max_pages": self.settings.doba_price_sync_full_max_pages,
            "primary_endpoint": self._debug_primary_endpoint(sync_scope=sync_scope, skus=skus),
            "sync_scope": sync_scope,
            "updated_since": updated_since,
            "sku_count": len(skus),
            "default_endpoint": self.settings.doba_price_endpoint,
        }

    def _debug_primary_endpoint(self, *, sync_scope: str, skus: list[str]) -> str:
        if not self._should_use_retailer_mainline():
            return self.settings.doba_price_endpoint
        if skus or sync_scope == "single_sku":
            return RETAILER_SPU_DETAIL_ENDPOINT
        if sync_scope == "incremental":
            return RETAILER_UPDATED_ENDPOINT
        return RETAILER_SPU_LIST_ENDPOINT

    def _discover_probe_item_no(self, *, sync_scope: str, updated_since: str, skus: list[str]) -> str:
        if skus:
            return skus[0]
        try:
            rows = self._fetch_updated_rows(updated_since=updated_since) if sync_scope != "full" or updated_since else self._fetch_updated_rows(updated_since="")
            return next(iter(rows.keys()), "")
        except Exception:
            return ""

    def _unwrap_business_data(self, payload: Any) -> Any:
        if not isinstance(payload, dict):
            return payload
        business = payload.get("businessData")
        if isinstance(business, dict):
            return business.get("data")
        return business

    def _format_updated_timestamp(self, value: str = "", *, fallback_hours: int = 24) -> str:
        if value:
            text = value.strip()
            if text.endswith("Z"):
                return text
            try:
                parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
                return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                return text
        return (datetime.now(timezone.utc) - timedelta(hours=fallback_hours)).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _should_use_retailer_mainline(self) -> bool:
        endpoint = self.settings.doba_price_endpoint.strip()
        return self.settings.doba_auth_mode.strip().lower() == "signature" or endpoint.startswith("/api/")

    @staticmethod
    def _chunked(items: list[str], size: int) -> list[list[str]]:
        return [items[index : index + size] for index in range(0, len(items), size)]

    @staticmethod
    def _unique_preserve_order(items: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            value = str(item or "").strip()
            if not value or value in seen:
                continue
            seen.add(value)
            result.append(value)
        return result

    @staticmethod
    def _pick_first(payload: dict[str, Any], *keys: str) -> str:
        for key in keys:
            value = payload.get(key)
            if value not in (None, ""):
                return str(value)
        return ""

    @staticmethod
    def _to_float(value: Any) -> float | None:
        if value in (None, ""):
            return None
        try:
            return round(float(value), 2)
        except (TypeError, ValueError):
            return None
