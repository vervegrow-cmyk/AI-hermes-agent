from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
from typing import Any, Callable

import bootstrap
from shared.clients import DobaClient
from shared.clients.doba import DobaAPIError

from src.modules.shopify_listing.application.live_publish_runtime import (
    _build_archive_inputs_from_detail,
    _configure_doba_client,
    _fetch_platform_id,
    _fetch_seller_info,
    _fetch_shipping_map,
    _fetch_spu_details,
    _fetch_spu_page,
    _fetch_stock_map,
)
from src.modules.supplier_archive.application.ship_from_resolver import normalize_ship_from_country
from src.modules.supplier_archive.application.service import archive_supplier_products
from src.shared.repositories import LocalJsonSupplierArchiveRepository, SQLiteSupplierArchiveRepository


DEFAULT_ONLINE_ARCHIVE_REPORT_PATH = Path("docs/audits/doba-online-archive-report.json")
DEFAULT_ONLINE_ARCHIVE_CHECKPOINT_PATH = Path("data/runtime/supplier_archive/doba_online_archive_checkpoint.json")
DEFAULT_ONLINE_ARCHIVE_PAGE_SIZE = 20
DEFAULT_ONLINE_ARCHIVE_TARGET_COUNTRY = "US"
DEFAULT_ONLINE_ARCHIVE_ELIGIBLE_INVENTORY_THRESHOLD = 10


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _log(event: str, **payload: Any) -> None:
    parts = [f"[doba_online_archive] {event}"]
    for key, value in payload.items():
        parts.append(f'{key}={json.dumps(value, ensure_ascii=False)}')
    structured_line = " ".join(parts)
    chinese_line = _format_chinese_log(event, payload)
    if chinese_line:
        print(chinese_line, flush=True)
    print(structured_line, flush=True)


def _translate_reason(reason: str) -> str:
    mapping = {
        "not_us_or_inventory_below_threshold": "发货地不是美国或库存未达到门槛",
        "missing_detail": "缺少商品详情",
        "no_archive_inputs": "没有可归档变体",
    }
    normalized = str(reason or "").strip()
    return mapping.get(normalized, normalized or "无")


def _format_chinese_log(event: str, payload: dict[str, Any]) -> str:
    if event == "page_start":
        return (
            f"在线归档开始：第 {payload.get('page_number', '?')} 页，"
            f"本页数量 {payload.get('page_size', '?')}，"
            f"起始序号 {payload.get('start_index', 0)}，"
            f"候选总数 {payload.get('total_spu', '?')}。"
        )
    if event == "archive_result":
        action = str(payload.get("action") or "")
        title = str(payload.get("title") or "")
        spu_no = str(payload.get("doba_spu_no") or "")
        if action == "archived":
            return (
                f"归档成功：SPU {spu_no}，标题《{title}》，SKU {payload.get('sku', '')}，"
                f"发货地 {payload.get('ship_from_country', 'UNKNOWN')}，"
                f"库存 {payload.get('inventory', 0)}，"
                f"成本 {payload.get('cost', 0)}，运费 {payload.get('shipping_cost', 0)}。"
            )
        if action == "filtered":
            return (
                f"归档过滤：SPU {spu_no}，标题《{title}》，"
                f"候选变体 {payload.get('candidate_variant_count', 0)}，"
                f"合格变体 {payload.get('eligible_variant_count', 0)}，"
                f"原因 {_translate_reason(str(payload.get('reason') or ''))}。"
            )
        if action == "skipped":
            return f"归档跳过：SPU {spu_no}，标题《{title}》，原因 {_translate_reason(str(payload.get('reason') or ''))}。"
    return ""


def _load_json(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        return {}
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: str | Path, payload: dict[str, Any]) -> str:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    payload["updated_at"] = _now_iso()
    file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(file_path.resolve())


def _build_stop_reason_for_doba_error(exc: DobaAPIError) -> str:
    response_message = str(getattr(exc, "response_message", "") or "").strip().lower()
    if "ip whitelist check failed" in response_message:
        return "doba_ip_whitelist_check_failed"
    return "doba_api_error"


def _stop_archive_on_doba_error(
    *,
    state: dict[str, Any],
    checkpoint_path: str,
    report_path: str,
    exc: DobaAPIError,
    page_number: int,
    index_in_page: int,
    variant_index: int,
) -> dict[str, Any]:
    stopped_reason = _build_stop_reason_for_doba_error(exc)
    state["completed"] = False
    state["stopped_reason"] = stopped_reason
    state["progress"]["page_number"] = page_number
    state["progress"]["index_in_page"] = index_in_page
    state["progress"]["variant_index"] = variant_index
    state["last_failure"] = {
        "failed_reason": str(exc),
        "status_code": int(getattr(exc, "status_code", 0) or 0),
        "path": str(getattr(exc, "path", "") or ""),
        "response_code": str(getattr(exc, "response_code", "") or ""),
        "response_message": str(getattr(exc, "response_message", "") or ""),
        "resume_command": str(state.get("resume_command") or ""),
        "resume_position": {
            "page_number": page_number,
            "index_in_page": index_in_page,
            "variant_index": variant_index,
        },
        "completed_count": int((state.get("progress") or {}).get("processed_spu") or 0),
    }
    state["checkpoint_path"] = _write_json(checkpoint_path, state)
    state["report_path"] = _write_json(report_path, state)
    return state


def _build_resume_command(
    *,
    report_path: str,
    checkpoint_path: str,
    page_size: int,
    target_country: str,
    min_inventory: int | None,
    archive_eligible_only: bool,
    eligible_inventory_threshold: int | None,
) -> str:
    command = [
        "python -m src.app.runners.run_supplier_archive_online",
        f'--report-path "{report_path}"',
        f'--checkpoint-path "{checkpoint_path}"',
        f"--page-size {page_size}",
        f'--target-country "{target_country}"',
    ]
    if min_inventory is not None:
        command.append(f"--min-inventory {int(min_inventory)}")
    if archive_eligible_only:
        command.append("--archive-eligible-only")
    if archive_eligible_only and eligible_inventory_threshold is not None:
        command.append(f"--eligible-inventory-threshold {int(eligible_inventory_threshold)}")
    return " ".join(command)


def _initial_state(
    *,
    report_path: str,
    checkpoint_path: str,
    page_size: int,
    target_country: str,
    min_inventory: int | None,
    archive_eligible_only: bool,
    eligible_inventory_threshold: int | None,
) -> dict[str, Any]:
    return {
        "started_at": _now_iso(),
        "updated_at": _now_iso(),
        "completed": False,
        "report_path": report_path,
        "checkpoint_path": checkpoint_path,
        "resume_command": _build_resume_command(
            report_path=report_path,
            checkpoint_path=checkpoint_path,
            page_size=page_size,
            target_country=target_country,
            min_inventory=min_inventory,
            archive_eligible_only=archive_eligible_only,
            eligible_inventory_threshold=eligible_inventory_threshold,
        ),
        "config": {
            "page_size": page_size,
            "target_country": target_country,
            "min_inventory": min_inventory,
            "archive_eligible_only": archive_eligible_only,
            "eligible_inventory_threshold": eligible_inventory_threshold,
        },
        "progress": {
            "total_spu": 0,
            "processed_spu": 0,
            "archived_sku": 0,
            "skipped_spu": 0,
            "eligible_spu": 0,
            "eligible_sku": 0,
            "filtered_sku": 0,
            "page_number": 1,
            "index_in_page": 0,
            "variant_index": 0,
        },
        "warnings": [],
        "ship_from_summary": {
            "us": 0,
            "non_us": 0,
            "unknown": 0,
        },
        "last_event": {},
    }


def _state_matches_config(
    state: dict[str, Any],
    *,
    page_size: int,
    target_country: str,
    min_inventory: int | None,
    archive_eligible_only: bool,
    eligible_inventory_threshold: int | None,
) -> bool:
    config = dict(state.get("config") or {})
    return (
        int(config.get("page_size") or 0) == int(page_size)
        and str(config.get("target_country") or "").upper() == str(target_country).upper()
        and config.get("min_inventory") == min_inventory
        and bool(config.get("archive_eligible_only")) == bool(archive_eligible_only)
        and config.get("eligible_inventory_threshold") == eligible_inventory_threshold
    )


def _collect_item_nos(details_map: dict[str, dict[str, Any]]) -> list[str]:
    item_nos: list[str] = []
    seen: set[str] = set()
    for detail in details_map.values():
        for child in list((detail or {}).get("children") or []):
            for stock_row in list((child or {}).get("stocks") or []):
                item_no = str((stock_row or {}).get("itemNo") or (child or {}).get("itemNo") or "").strip()
                if not item_no or item_no in seen:
                    continue
                seen.add(item_no)
                item_nos.append(item_no)
    return item_nos


def _merge_archive_result(state: dict[str, Any], archive_result: dict[str, Any]) -> None:
    state["progress"]["archived_sku"] += int(archive_result.get("archived_products") or 0)
    warnings = list(state.get("warnings") or [])
    warnings.extend(list(archive_result.get("warnings") or []))
    state["warnings"] = warnings


def _is_us_ship_from(value: str) -> bool:
    return normalize_ship_from_country(value) == "United States"


def _update_ship_from_summary(state: dict[str, Any], products: list[Any]) -> None:
    summary = state.setdefault("ship_from_summary", {"us": 0, "non_us": 0, "unknown": 0})
    for product in products:
        ship_from_country = normalize_ship_from_country(str(getattr(product, "ship_from_country", "") or ""))
        if ship_from_country == "United States":
            summary["us"] += 1
        elif ship_from_country == "UNKNOWN":
            summary["unknown"] += 1
        else:
            summary["non_us"] += 1


def _is_archive_focus_eligible(
    product: Any,
    *,
    eligible_inventory_threshold: int | None,
) -> bool:
    if not _is_us_ship_from(str(getattr(product, "ship_from_country", "") or "")):
        return False
    if eligible_inventory_threshold is None:
        return True
    return int(getattr(product, "inventory", 0) or 0) > int(eligible_inventory_threshold)


def run_doba_online_archive(
    *,
    report_path: str = str(DEFAULT_ONLINE_ARCHIVE_REPORT_PATH),
    checkpoint_path: str = str(DEFAULT_ONLINE_ARCHIVE_CHECKPOINT_PATH),
    page_size: int = DEFAULT_ONLINE_ARCHIVE_PAGE_SIZE,
    target_country: str = DEFAULT_ONLINE_ARCHIVE_TARGET_COUNTRY,
    min_inventory: int | None = None,
    archive_eligible_only: bool = False,
    eligible_inventory_threshold: int | None = None,
    resume: bool = True,
    max_pages: int | None = None,
    post_archive_hook: Callable[[list[Any], dict[str, Any]], dict[str, Any] | None] | None = None,
) -> dict[str, Any]:
    state = _load_json(checkpoint_path) if resume else {}
    if not state or not _state_matches_config(
        state,
        page_size=page_size,
        target_country=target_country,
        min_inventory=min_inventory,
        archive_eligible_only=archive_eligible_only,
        eligible_inventory_threshold=eligible_inventory_threshold,
    ):
        state = _initial_state(
            report_path=report_path,
            checkpoint_path=checkpoint_path,
            page_size=page_size,
            target_country=target_country,
            min_inventory=min_inventory,
            archive_eligible_only=archive_eligible_only,
            eligible_inventory_threshold=eligible_inventory_threshold,
        )
    else:
        state["report_path"] = report_path
        state["checkpoint_path"] = checkpoint_path
        state["resume_command"] = _build_resume_command(
            report_path=report_path,
            checkpoint_path=checkpoint_path,
            page_size=page_size,
            target_country=target_country,
            min_inventory=min_inventory,
            archive_eligible_only=archive_eligible_only,
            eligible_inventory_threshold=eligible_inventory_threshold,
        )

    repository = SQLiteSupplierArchiveRepository()
    doba_client = _configure_doba_client(DobaClient.from_settings())

    page_number = int((state.get("progress") or {}).get("page_number") or 1)
    index_in_page = int((state.get("progress") or {}).get("index_in_page") or 0)
    variant_index = int((state.get("progress") or {}).get("variant_index") or 0)
    state.setdefault("progress", {})
    state["progress"].setdefault("eligible_spu", 0)
    state["progress"].setdefault("eligible_sku", 0)
    state["progress"].setdefault("filtered_sku", 0)
    try:
        platform_id = _fetch_platform_id(doba_client)
    except DobaAPIError as exc:
        return _stop_archive_on_doba_error(
            state=state,
            checkpoint_path=checkpoint_path,
            report_path=report_path,
            exc=exc,
            page_number=page_number,
            index_in_page=index_in_page,
            variant_index=variant_index,
        )
    seller_cache: dict[str, dict[str, Any]] = {}
    pages_processed = 0

    while True:
        try:
            total_spu, goods_list = _fetch_spu_page(
                doba_client,
                page_number=page_number,
                page_size=page_size,
                ship_to_country=target_country,
                min_inventory=min_inventory,
            )
        except DobaAPIError as exc:
            return _stop_archive_on_doba_error(
                state=state,
                checkpoint_path=checkpoint_path,
                report_path=report_path,
                exc=exc,
                page_number=page_number,
                index_in_page=index_in_page,
                variant_index=variant_index,
            )
        state["progress"]["total_spu"] = total_spu
        if not goods_list:
            state["completed"] = True
            state["progress"]["page_number"] = page_number
            state["progress"]["index_in_page"] = 0
            state["progress"]["variant_index"] = 0
            break

        summary_spu_nos = [
            str((item or {}).get("spuNo") or "").strip()
            for item in goods_list
            if str((item or {}).get("spuNo") or "").strip()
        ]
        try:
            details_map = _fetch_spu_details(doba_client, summary_spu_nos)
            item_nos = _collect_item_nos(details_map)
            stock_map = _fetch_stock_map(doba_client, item_nos)
            shipping_map = _fetch_shipping_map(
                doba_client,
                item_nos=item_nos,
                ship_to_country=target_country,
                platform_id=platform_id,
            )
        except DobaAPIError as exc:
            return _stop_archive_on_doba_error(
                state=state,
                checkpoint_path=checkpoint_path,
                report_path=report_path,
                exc=exc,
                page_number=page_number,
                index_in_page=index_in_page,
                variant_index=variant_index,
            )

        _log(
            "page_start",
            page_number=page_number,
            total_spu=total_spu,
            page_size=len(goods_list),
            start_index=index_in_page,
            archive_eligible_only=archive_eligible_only,
            eligible_inventory_threshold=eligible_inventory_threshold,
        )

        for summary_index in range(index_in_page, len(goods_list)):
            summary = goods_list[summary_index] or {}
            spu_no = str(summary.get("spuNo") or "").strip()
            spu_id = str(summary.get("spuId") or "").strip()
            title = str(summary.get("title") or "").strip()
            detail = details_map.get(spu_no) or {}

            if not detail:
                state["progress"]["processed_spu"] += 1
                state["progress"]["skipped_spu"] += 1
                state["progress"]["page_number"] = page_number
                state["progress"]["index_in_page"] = summary_index + 1
                state["progress"]["variant_index"] = 0
                state["last_event"] = {
                    "action": "skipped",
                    "reason": "missing_detail",
                    "spu_no": spu_no,
                    "spu_id": spu_id,
                    "title": title,
                }
                _write_json(checkpoint_path, state)
                _log(
                    "archive_result",
                    progress=dict(state["progress"]),
                    doba_product_id=spu_id,
                    doba_spu_no=spu_no,
                    title=title,
                    action="skipped",
                    reason="missing_detail",
                )
                continue

            archive_inputs = _build_archive_inputs_from_detail(
                detail=detail,
                stock_map=stock_map,
                shipping_map=shipping_map,
                target_country=target_country,
            )
            try:
                seller_info = _fetch_seller_info(
                    doba_client,
                    supplier_id=str(detail.get("busiId") or ""),
                    seller_cache=seller_cache,
                )
            except DobaAPIError as exc:
                return _stop_archive_on_doba_error(
                    state=state,
                    checkpoint_path=checkpoint_path,
                    report_path=report_path,
                    exc=exc,
                    page_number=page_number,
                    index_in_page=summary_index,
                    variant_index=variant_index,
                )
            for product in archive_inputs:
                if seller_info:
                    product.seller_info = dict(seller_info)
                    product.seller_name = str(seller_info.get("supplierName") or product.seller_name or "")
                    product.attributes = {
                        **dict(product.attributes),
                        "sellerName": product.seller_name,
                    }
            eligible_products = [
                product
                for product in archive_inputs
                if _is_archive_focus_eligible(
                    product,
                    eligible_inventory_threshold=eligible_inventory_threshold,
                )
            ]
            _update_ship_from_summary(state, archive_inputs)
            state["progress"]["eligible_sku"] += len(eligible_products)
            state["progress"]["filtered_sku"] += max(len(archive_inputs) - len(eligible_products), 0)
            if eligible_products:
                state["progress"]["eligible_spu"] += 1

            if not archive_inputs:
                state["progress"]["processed_spu"] += 1
                state["progress"]["skipped_spu"] += 1
                state["progress"]["page_number"] = page_number
                state["progress"]["index_in_page"] = summary_index + 1
                state["progress"]["variant_index"] = 0
                state["last_event"] = {
                    "action": "skipped",
                    "reason": "no_archive_inputs",
                    "spu_no": spu_no,
                    "spu_id": spu_id,
                    "title": title,
                }
                _write_json(checkpoint_path, state)
                _log(
                    "archive_result",
                    progress=dict(state["progress"]),
                    doba_product_id=spu_id,
                    doba_spu_no=spu_no,
                    title=title,
                    action="skipped",
                    reason="no_archive_inputs",
                )
                continue

            selected_products = eligible_products if archive_eligible_only else archive_inputs
            if archive_eligible_only and not selected_products:
                state["progress"]["processed_spu"] += 1
                state["progress"]["skipped_spu"] += 1
                state["progress"]["page_number"] = page_number
                state["progress"]["index_in_page"] = summary_index + 1
                state["progress"]["variant_index"] = 0
                state["last_event"] = {
                    "action": "filtered",
                    "reason": "not_us_or_inventory_below_threshold",
                    "spu_no": spu_no,
                    "spu_id": spu_id,
                    "title": title,
                }
                _write_json(checkpoint_path, state)
                _log(
                    "archive_result",
                    progress=dict(state["progress"]),
                    doba_product_id=spu_id,
                    doba_spu_no=spu_no,
                    title=title,
                    candidate_variant_count=len(archive_inputs),
                    eligible_variant_count=0,
                    ship_from_summary=dict(state.get("ship_from_summary") or {}),
                    action="filtered",
                    reason="not_us_or_inventory_below_threshold",
                )
                continue

            for product_index in range(variant_index, len(selected_products)):
                product = selected_products[product_index]
                archive_result = archive_supplier_products([product], repository).model_dump()
                _merge_archive_result(state, archive_result)
                state["progress"]["page_number"] = page_number
                state["progress"]["index_in_page"] = summary_index
                state["progress"]["variant_index"] = product_index + 1
                state["last_event"] = {
                    "action": "archived",
                    "reason": "",
                    "spu_no": spu_no,
                    "spu_id": spu_id,
                    "sku": product.sku,
                    "title": product.title,
                }
                _write_json(checkpoint_path, state)
                _log(
                    "archive_result",
                    progress=dict(state["progress"]),
                    doba_product_id=spu_id,
                    doba_spu_no=spu_no,
                    title=product.title,
                    sku=product.sku,
                    sku_code=product.sku_code,
                    candidate_variant_count=len(archive_inputs),
                    eligible_variant_count=len(eligible_products),
                    ship_from_country=product.ship_from_country or "UNKNOWN",
                    inventory=product.inventory,
                    cost=round(product.cost, 2),
                    shipping_cost=round(product.shipping_cost, 2),
                    seller_name=product.seller_name,
                    category_name=product.category_name,
                    action="archived",
                    reason="",
                )

            if selected_products and post_archive_hook is not None:
                try:
                    hook_result = post_archive_hook(
                        list(selected_products),
                        {
                            "spu_no": spu_no,
                            "spu_id": spu_id,
                            "title": title,
                            "page_number": page_number,
                            "index_in_page": summary_index,
                            "eligible_variant_count": len(eligible_products),
                        },
                    )
                    if hook_result:
                        state["last_stream_publish"] = hook_result
                        if bool(hook_result.get("stop_archive")):
                            state["completed"] = False
                            state["stopped_reason"] = str(hook_result.get("stop_reason") or "stream_publish_hook_stopped")
                            last_failure = dict(hook_result.get("last_failure") or {})
                            if last_failure:
                                state["last_failure"] = last_failure
                            state["progress"]["page_number"] = page_number
                            state["progress"]["index_in_page"] = summary_index
                            state["progress"]["variant_index"] = 0
                            _write_json(checkpoint_path, state)
                            state["checkpoint_path"] = _write_json(checkpoint_path, state)
                            state["report_path"] = _write_json(report_path, state)
                            return state
                        _write_json(checkpoint_path, state)
                except Exception as exc:
                    warnings = list(state.get("warnings") or [])
                    warnings.append(f"stream_publish_hook_failed:{spu_no}:{exc}")
                    state["warnings"] = warnings
                    _write_json(checkpoint_path, state)

            state["progress"]["processed_spu"] += 1
            state["progress"]["page_number"] = page_number
            state["progress"]["index_in_page"] = summary_index + 1
            state["progress"]["variant_index"] = 0
            _write_json(checkpoint_path, state)

        page_number += 1
        index_in_page = 0
        variant_index = 0
        state["progress"]["page_number"] = page_number
        state["progress"]["index_in_page"] = 0
        state["progress"]["variant_index"] = 0
        _write_json(checkpoint_path, state)
        pages_processed += 1
        if max_pages is not None and pages_processed >= max_pages:
            break

    state["checkpoint_path"] = _write_json(checkpoint_path, state)
    state["report_path"] = _write_json(report_path, state)
    return state
