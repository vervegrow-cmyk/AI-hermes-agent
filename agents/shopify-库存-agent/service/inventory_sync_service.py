from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from models.inventory_sync import (
    ConnectionCheckResult,
    InventorySyncBatch,
    InventorySyncItem,
    InventorySyncRequest,
)
from service.giga_inventory_client import GigaInventoryClient, GigaInventoryClientError
from shared.clients import ShopifyAuthClient
from shared.clients.shopify import ShopifyGraphQLError, normalize_shop_domain
from shared.config import get_settings


class InventorySyncStartupError(RuntimeError):
    """Raised when startup validation fails and the job must stop."""


class InventorySyncService:
    DEKUCH_VENDOR = "dekuch"
    GIGA_DELIST_REASON = "该 SKU 未加入 Saved Items，或当前没有备货库存"
    LOW_INVENTORY_DRAFT_THRESHOLD = 5
    LOW_INVENTORY_DRAFT_REASON = "库存低于 5，商品改为草稿"
    SHOPIFY_DELIST_STATUS = "DRAFT"

    def __init__(
        self,
        *,
        shopify_client: ShopifyAuthClient | None = None,
        giga_client: GigaInventoryClient | None = None,
    ) -> None:
        self.settings = get_settings()
        self.shopify_client = shopify_client or ShopifyAuthClient.from_settings(self.settings)
        self.giga_client = giga_client or GigaInventoryClient()
        self.agent_root = Path(__file__).resolve().parents[1]
        self.runtime_dir = self.agent_root / "runtime"
        self.report_dir = self.runtime_dir / "reports"
        self.export_dir = self.runtime_dir / "exports"

    def run(
        self,
        request: InventorySyncRequest,
        *,
        progress_callback: Any | None = None,
    ) -> InventorySyncBatch:
        mode = request.mode or ("dry-run" if self.settings.inventory_sync_dry_run else "apply")
        batch = InventorySyncBatch(
            batch_id=str(uuid4()),
            store_name=request.store_name or self.shopify_client.store_domain,
            mode=mode,
        )
        self._emit(
            progress_callback,
            {
                "event": "stage",
                "stage": "start",
                "batch_id": batch.batch_id,
                "mode": batch.mode,
                "store_name": batch.store_name,
            },
        )

        location_id = self._resolve_location_id(request.location_id)
        batch.location_id = location_id

        batch.shopify_connection = self._validate_shopify_connection(request, location_id)
        self._emit(
            progress_callback,
            {
                "event": "stage",
                "stage": "shopify_validated",
                "store_name": batch.shopify_connection.details.get("myshopify_domain", ""),
                "location_id": location_id,
            },
        )

        batch.giga_connection = self._validate_giga_connection()
        self._emit(
            progress_callback,
            {
                "event": "stage",
                "stage": "giga_validated",
                "base_url": batch.giga_connection.details.get("base_url", ""),
                "endpoint": batch.giga_connection.details.get("endpoint", ""),
            },
        )

        variants = self._collect_target_variants(request, progress_callback=progress_callback)
        total = len(variants)
        if total == 0:
            batch.status = "completed"
            batch.finished_at = self._utc_now_iso()
            batch.artifact_paths = self._persist_artifacts(batch)
            self._emit(
                progress_callback,
                {
                    "event": "stage",
                    "stage": "finished",
                    "processed_count": 0,
                    "updated_count": 0,
                    "skipped_count": 0,
                    "failed_count": 0,
                },
            )
            return batch

        duplicate_counts = Counter(item["normalized_sku"] for item in variants if item["normalized_sku"])
        for index, variant in enumerate(variants, start=1):
            item = self._process_variant(
                variant=variant,
                location_id=location_id,
                mode=batch.mode,
                duplicate_counts=duplicate_counts,
            )
            batch.items.append(item)
            batch.processed_count += 1
            if item.status == "updated":
                batch.updated_count += 1
            elif item.status == "failed":
                batch.failed_count += 1
            else:
                batch.skipped_count += 1

            self._emit(
                progress_callback,
                {
                    "event": "item",
                    "index": index,
                    "total": total,
                    "item": item.model_dump(mode="json"),
                },
            )

        batch.status = "completed"
        batch.finished_at = self._utc_now_iso()
        batch.missing_sku_count = sum(1 for item in batch.items if item.reason == "SKU 为空")
        batch.artifact_paths = self._persist_artifacts(batch)
        self._emit(
            progress_callback,
            {
                "event": "stage",
                "stage": "finished",
                "processed_count": batch.processed_count,
                "updated_count": batch.updated_count,
                "skipped_count": batch.skipped_count,
                "failed_count": batch.failed_count,
            },
        )
        return batch

    def _validate_shopify_connection(
        self,
        request: InventorySyncRequest,
        location_id: str,
    ) -> ConnectionCheckResult:
        try:
            shop = self.shopify_client.query_shop_info()
            if not shop:
                raise InventorySyncStartupError("Shopify 未返回店铺信息。")

            actual_domain = normalize_shop_domain(str(shop.get("myshopifyDomain", "")))
            expected_domain = normalize_shop_domain(request.store_name or self.shopify_client.store_domain)
            if actual_domain != expected_domain:
                raise InventorySyncStartupError(
                    f"Shopify 店铺不匹配，期望 {expected_domain}，实际 {actual_domain}。"
                )
            return ConnectionCheckResult(
                ok=True,
                system="shopify",
                message="Shopify 连接验证成功。",
                details={
                    "shop_id": shop.get("id", ""),
                    "shop_name": shop.get("name", ""),
                    "myshopify_domain": actual_domain,
                    "location_id": location_id,
                },
            )
        except Exception as exc:
            raise InventorySyncStartupError(f"Shopify 连接验证失败: {exc}") from exc

    def _validate_giga_connection(self) -> ConnectionCheckResult:
        try:
            details = self.giga_client.validate_connection()
            return ConnectionCheckResult(
                ok=True,
                system="giga",
                message="Giga OpenAPI 连接验证成功。",
                details=details,
            )
        except GigaInventoryClientError as exc:
            raise InventorySyncStartupError(str(exc)) from exc

    def _resolve_location_id(self, request_location_id: str) -> str:
        location_id = (
            (request_location_id or "").strip()
            or (self.settings.shopify_inventory_location_id or "").strip()
        )
        if location_id:
            return location_id

        primary_location = self.shopify_client.get_primary_location()
        if not primary_location or not primary_location.get("id"):
            raise InventorySyncStartupError("未找到可用的 Shopify inventory location。")
        return str(primary_location["id"])

    def _collect_target_variants(
        self,
        request: InventorySyncRequest,
        *,
        progress_callback: Any | None = None,
    ) -> list[dict[str, Any]]:
        limit = request.max_items or self.settings.inventory_sync_max_items
        if request.sku_list:
            variants: list[dict[str, Any]] = []
            total = len(request.sku_list)
            for index, sku in enumerate(request.sku_list, start=1):
                matches = self._find_variants_by_exact_sku(sku)
                self._emit(
                    progress_callback,
                    {
                        "event": "stage",
                        "stage": "shopify_scan_progress",
                        "current": index,
                        "total": total,
                        "fetched_total": len(variants) + len(matches),
                        "sku": sku,
                    },
                )
                variants.extend(matches)
                if limit and len(variants) >= limit:
                    break
            self._emit(
                progress_callback,
                {
                    "event": "stage",
                    "stage": "shopify_scan_finished",
                    "variant_count": len(variants),
                },
            )
            return variants[:limit] if limit else variants

        query = request.shopify_query or self.settings.shopify_inventory_sync_query
        cursor: str | None = None
        page = 0
        variants: list[dict[str, Any]] = []
        while True:
            page += 1
            data = self.shopify_client.graphql(
                """
                query ProductVariantsPage($first: Int!, $after: String, $query: String!) {
                  productVariants(first: $first, after: $after, query: $query) {
                    edges {
                      cursor
                      node {
                        id
                        sku
                        inventoryQuantity
                        inventoryItem {
                          id
                        }
                        product {
                          id
                          title
                          status
                          vendor
                        }
                      }
                    }
                    pageInfo {
                      hasNextPage
                      endCursor
                    }
                  }
                }
                """,
                {"first": 100, "after": cursor, "query": query},
            )
            connection = data.get("productVariants", {}) or {}
            edges = connection.get("edges", []) or []
            for edge in edges:
                node = edge.get("node") or {}
                variants.append({**node, "normalized_sku": self._normalize_sku(node.get("sku", ""))})
                if limit and len(variants) >= limit:
                    break
            self._emit(
                progress_callback,
                {
                    "event": "stage",
                    "stage": "shopify_scan_progress",
                    "page": page,
                    "fetched_in_page": len(edges),
                    "fetched_total": len(variants),
                    "query": query,
                },
            )
            if limit and len(variants) >= limit:
                break
            page_info = connection.get("pageInfo", {}) or {}
            if not page_info.get("hasNextPage"):
                break
            cursor = page_info.get("endCursor")
            if not cursor:
                break

        self._emit(
            progress_callback,
            {
                "event": "stage",
                "stage": "shopify_scan_finished",
                "variant_count": len(variants),
            },
        )
        return variants

    def _find_variants_by_exact_sku(self, sku: str) -> list[dict[str, Any]]:
        clean_sku = self._normalize_sku(sku)
        if not clean_sku:
            return []
        data = self.shopify_client.graphql(
            """
            query VariantsBySku($query: String!) {
              productVariants(first: 10, query: $query) {
                edges {
                  node {
                    id
                    sku
                    inventoryQuantity
                    inventoryItem {
                      id
                    }
                    product {
                      id
                      title
                      status
                      vendor
                    }
                  }
                }
              }
            }
            """,
            {"query": f"sku:{clean_sku}"},
        )
        edges = data.get("productVariants", {}).get("edges", []) or []
        matches = []
        for edge in edges:
            node = edge.get("node") or {}
            if self._normalize_sku(node.get("sku", "")) == clean_sku:
                matches.append({**node, "normalized_sku": clean_sku})
        return matches

    def _process_variant(
        self,
        *,
        variant: dict[str, Any],
        location_id: str,
        mode: str,
        duplicate_counts: Counter,
    ) -> InventorySyncItem:
        sku = self._normalize_sku(variant.get("sku", ""))
        product = variant.get("product") or {}
        item = InventorySyncItem(
            sku=sku,
            shopify_variant_id=str(variant.get("id", "")),
            shopify_product_id=str(product.get("id", "")),
            shopify_product_title=str(product.get("title", "")),
            shopify_product_vendor=str(product.get("vendor", "")),
            shopify_product_status_before=str(product.get("status", "")),
            shopify_inventory_item_id=str((variant.get("inventoryItem") or {}).get("id", "")),
            shopify_inventory_before=variant.get("inventoryQuantity"),
        )
        if not sku:
            item.reason = "SKU 为空"
            return item

        if duplicate_counts.get(sku, 0) > 1:
            item.reason = "Shopify 中存在重复 SKU，已跳过"
            return item

        try:
            matches = self.giga_client.fetch_inventory_by_sku(sku)
        except Exception as exc:
            item.error_message = str(exc)
            item.reason = self._extract_giga_reason(exc)
            if self._should_delist_by_giga_reason(item):
                return self._delist_product(
                    item=item,
                    mode=mode,
                    reason=f"已下架：{self.GIGA_DELIST_REASON}",
                    dry_run_reason="命中 Dekuch 下架规则，dry-run 未实际下架",
                    already_draft_reason="命中 Dekuch 下架规则，但商品已是下架状态",
                )
            item.status = "failed"
            return item

        if not matches:
            item.reason = "Giga 未找到对应 SKU"
            return item

        if len(matches) > 1:
            item.reason = "Giga 返回多个同 SKU 记录，已跳过"
            return item

        giga_record = matches[0]
        target_inventory = giga_record.available_inventory
        item.giga_inventory = target_inventory
        if target_inventory < 0:
            item.reason = "Giga 库存为负数，已跳过"
            return item

        current_inventory = int(item.shopify_inventory_before or 0)
        inventory_changed = current_inventory != target_inventory
        needs_low_inventory_draft = target_inventory < self.LOW_INVENTORY_DRAFT_THRESHOLD

        if inventory_changed:
            if not item.shopify_inventory_item_id:
                item.reason = "缺少 Shopify inventoryItemId"
                item.status = "failed"
                item.error_message = "当前变体未返回 inventoryItemId，无法更新库存"
                return item

            item.action = "update_inventory"
            if mode == "dry-run":
                item.status = "dry_run"
                item.reason = "dry-run 模式，未实际更新库存"
            else:
                try:
                    self.shopify_client.set_inventory_quantity(
                        inventory_item_id=item.shopify_inventory_item_id,
                        location_id=location_id,
                        quantity=target_inventory,
                        change_from_quantity=current_inventory,
                    )
                    item.status = "updated"
                    item.reason = "库存已更新"
                except ShopifyGraphQLError as exc:
                    item.status = "failed"
                    item.reason = "Shopify 更新失败"
                    item.error_message = str(exc)
                    return item
        else:
            item.reason = "库存一致，无需更新"

        if needs_low_inventory_draft:
            return self._delist_product(
                item=item,
                mode=mode,
                reason=f"已下架：{self.LOW_INVENTORY_DRAFT_REASON}",
                dry_run_reason="库存低于 5，dry-run 未实际下架",
                already_draft_reason="库存低于 5，但商品已是下架状态",
            )

        return item

    def _persist_artifacts(self, batch: InventorySyncBatch) -> dict[str, str]:
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.export_dir.mkdir(parents=True, exist_ok=True)

        report_path = self.report_dir / f"{batch.batch_id}.json"
        missing_sku_path = self.export_dir / f"{batch.batch_id}-missing-skus.json"
        retry_path = self.export_dir / f"{batch.batch_id}-retry-items.json"
        artifact_paths = {
            "report": str(report_path),
            "missing_skus": str(missing_sku_path),
            "retry_items": str(retry_path),
        }

        missing_items = [
            {
                "shopify_variant_id": item.shopify_variant_id,
                "shopify_product_id": item.shopify_product_id,
                "shopify_product_title": item.shopify_product_title,
                "shopify_product_vendor": item.shopify_product_vendor,
                "shopify_inventory_before": item.shopify_inventory_before,
            }
            for item in batch.items
            if item.reason == "SKU 为空"
        ]
        retry_items = [
            {
                "sku": item.sku,
                "shopify_variant_id": item.shopify_variant_id,
                "shopify_product_id": item.shopify_product_id,
                "shopify_product_title": item.shopify_product_title,
                "shopify_product_vendor": item.shopify_product_vendor,
                "reason": item.reason,
                "error_message": item.error_message,
                "status": item.status,
                "action": item.action,
            }
            for item in batch.items
            if item.status == "failed"
            or item.reason in {"SKU 为空", "Giga 未找到对应 SKU", "Giga 返回多个同 SKU 记录，已跳过"}
        ]

        report_payload = batch.model_dump(mode="json")
        report_payload["artifact_paths"] = artifact_paths
        report_path.write_text(json.dumps(report_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        missing_sku_path.write_text(json.dumps(missing_items, ensure_ascii=False, indent=2), encoding="utf-8")
        retry_path.write_text(json.dumps(retry_items, ensure_ascii=False, indent=2), encoding="utf-8")
        return artifact_paths

    def _normalize_sku(self, value: str) -> str:
        return (value or "").strip()

    def _normalize_vendor(self, value: str) -> str:
        return (value or "").strip().lower()

    def _should_delist_by_giga_reason(self, item: InventorySyncItem) -> bool:
        return (
            self._normalize_vendor(item.shopify_product_vendor) == self.DEKUCH_VENDOR
            and self.GIGA_DELIST_REASON in item.reason
            and bool(item.shopify_product_id)
        )

    def _delist_product(
        self,
        *,
        item: InventorySyncItem,
        mode: str,
        reason: str,
        dry_run_reason: str,
        already_draft_reason: str,
    ) -> InventorySyncItem:
        if item.action in {"skip", ""}:
            item.action = "delist_product"
        else:
            item.action = f"{item.action}_and_delist"

        if item.shopify_product_status_before.upper() in {"DRAFT", "ARCHIVED"}:
            item.reason = already_draft_reason
            item.shopify_product_status_after = item.shopify_product_status_before
            return item

        if mode == "dry-run":
            item.status = "dry_run"
            item.reason = dry_run_reason
            item.shopify_product_status_after = self.SHOPIFY_DELIST_STATUS
            return item

        try:
            product = self.shopify_client.update_product_status(
                product_id=item.shopify_product_id,
                status=self.SHOPIFY_DELIST_STATUS,
            )
            item.status = "updated"
            item.reason = reason
            item.shopify_product_status_after = str(product.get("status", self.SHOPIFY_DELIST_STATUS))
            return item
        except ShopifyGraphQLError as exc:
            item.status = "failed"
            item.reason = "Shopify 下架失败"
            item.error_message = str(exc)
            return item

    def _extract_giga_reason(self, exc: Exception) -> str:
        message = str(exc).strip()
        if not message:
            return "Giga 查询失败"
        if "|" in message:
            message = message.split("|", 1)[0].strip()
        if ":" in message:
            prefix, remainder = message.split(":", 1)
            if "Giga" in prefix and remainder.strip():
                return remainder.strip()
        return message

    def _emit(self, progress_callback: Any | None, event: dict[str, Any]) -> None:
        if progress_callback is not None:
            progress_callback(event)

    def _utc_now_iso(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_inventory_sync(
    command: InventorySyncRequest,
    *,
    progress_callback: Any | None = None,
    service: InventorySyncService | None = None,
) -> InventorySyncBatch:
    sync_service = service or InventorySyncService()
    return sync_service.run(command, progress_callback=progress_callback)
