from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import ctypes
import json
import msvcrt
import re
import sys
from typing import Any

from src.modules.inventory_sync.application.service import (
    REPORT_PATH as INVENTORY_REPORT_PATH,
    build_inventory_sync_command_from_archive,
    run_inventory_sync_runtime,
)
from src.modules.price_sync.application.service import (
    REPORT_PATH as PRICE_REPORT_PATH,
    build_price_sync_command_from_archive,
    run_price_sync_runtime,
)
from src.modules.product_screening.application.service import (
    run_candidate_pool,
    run_deepseek_scoring,
    run_rule_engine,
)
from src.modules.risk_control.application.service import (
    REPORT_PATH as RISK_REPORT_PATH,
    build_risk_control_command_from_archive,
    run_risk_control,
)
from src.modules.shopify_listing.application.live_publish_runtime import (
    build_doba_publish_candidate_pool,
    publish_doba_products_live,
    rollback_shopify_product_publications,
)
from src.modules.supplier_archive.application.online_archive_runtime import run_doba_online_archive
from src.shared.contracts.inventory import ShopifyInventoryState
from src.shared.contracts.pricing import ShopifyPriceState
from src.shared.repositories import (
    InMemoryProductScreeningRepository,
    SQLitePublishMappingRepository,
    SQLiteSupplierArchiveRepository,
)


DEFAULT_ARCHIVE_REPORT_PATH = "docs/audits/doba-online-archive-us-focus-report.json"
DEFAULT_ARCHIVE_CHECKPOINT_PATH = "data/runtime/supplier_archive/doba_online_archive_us_focus_checkpoint.json"
DEFAULT_PUBLISH_REPORT_PATH = "docs/audits/doba-shopify-live-publish-candidate-only-report.json"
DEFAULT_PUBLISH_CHECKPOINT_PATH = "data/runtime/shopify_listing/doba_live_publish_checkpoint.json"
DEFAULT_CANDIDATE_POOL_PATH = "data/runtime/shopify_listing/doba_publish_candidates.json"
DEFAULT_RUNTIME_REPORT_PATH = "docs/audits/doba-shopify-runtime-report.md"


CHANNEL_LABELS = {
    "shop": "Shop",
    "inbox": "Inbox",
    "pinterest": "Pinterest",
    "facebook": "Facebook & Instagram",
    "facebook & instagram": "Facebook & Instagram",
    "facebook_and_instagram": "Facebook & Instagram",
    "online_store": "\u5728\u7ebf\u5546\u5e97",
}


def _load_json(path: str) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        return {}
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: str, payload: dict[str, Any]) -> str:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(output_path.resolve())


def _configure_stdout_utf8() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def _write_console_line(message: str) -> None:
    text = f"{message}\n"
    if sys.platform == "win32":
        try:
            handle = msvcrt.get_osfhandle(sys.stdout.fileno())
            written = ctypes.c_ulong(0)
            ok = ctypes.windll.kernel32.WriteConsoleW(
                ctypes.c_void_p(handle),
                ctypes.c_wchar_p(text),
                len(text),
                ctypes.byref(written),
                None,
            )
            if ok:
                return
        except OSError:
            pass
        except Exception:
            pass
    print(message, flush=True)


def _parse_markdown_metric(path: Path, label: str) -> int:
    if not path.exists():
        return 0
    text = path.read_text(encoding="utf-8", errors="replace")
    pattern = rf"- {re.escape(label)}: `([^`]+)`"
    match = re.search(pattern, text)
    if not match:
        return 0
    raw = match.group(1).strip()
    try:
        return int(float(raw))
    except ValueError:
        return 0


@dataclass
class RuntimeConsoleLogger:
    mode: str
    target_country: str

    def _emit(self, message: str) -> None:
        _write_console_line(message)

    def banner(self) -> None:
        self._emit("========================================================")
        self._emit("Doba-Shopify-Agent V2 Commerce Runtime")
        self._emit(f"\u76ee\u6807\u5e02\u573a\uff1a{self.target_country}")
        self._emit(f"\u8fd0\u884c\u6a21\u5f0f\uff1a{self.mode}")
        self._emit(f"\u5f00\u59cb\u65f6\u95f4\uff1a{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._emit("========================================================")

    def progress(self, *, current: int, total: int, success: int, skipped: int, failed: int) -> None:
        self._emit(
            f"\u3010\u8fdb\u5ea6\u3011\u5f53\u524d\u5546\u54c1\uff1a{current} / {total} | "
            f"\u6210\u529f\uff1a{success} | \u8df3\u8fc7\uff1a{skipped} | \u5931\u8d25\uff1a{failed}"
        )

    def archive(self, *, title: str, sku_count: int, inventory: int, status: str) -> None:
        self._emit(f"\u3010\u5f52\u6863\u3011{title} | SKU\u6570\uff1a{sku_count} | \u5e93\u5b58\uff1a{inventory} | \u72b6\u6001\uff1a{status}")

    def normalization(self, *, variant_count: int) -> None:
        self._emit(f"\u3010\u6807\u51c6\u5316\u3011SPU \u5408\u5e76\u5b8c\u6210 | Variant \u6570\uff1a{variant_count}")

    def validation(self, *, category_mapped: bool, ship_from_us: bool) -> None:
        category_text = "\u7c7b\u76ee\u5df2\u6620\u5c04" if category_mapped else "\u7c7b\u76ee\u672a\u6620\u5c04"
        ship_text = "\u662f" if ship_from_us else "\u5426"
        self._emit(f"\u3010\u6821\u9a8c\u3011\u5b57\u6bb5\u5b8c\u6574 | {category_text} | US\u53d1\u8d27\uff1a{ship_text}")

    def rule_engine(self, *, status: str) -> None:
        self._emit(f"\u3010\u89c4\u5219\u3011\u5e93\u5b58\u901a\u8fc7 | \u7c7b\u76ee\u901a\u8fc7 | \u72b6\u6001\uff1a{status}")

    def ai(self, *, score: int | float, status: str) -> None:
        self._emit(f"\u3010AI\u3011DeepSeek\u8bc4\u5206\uff1a{score} | \u72b6\u6001\uff1a{status}")

    def content(self) -> None:
        self._emit("\u3010\u5185\u5bb9\u3011\u6807\u9898/\u63cf\u8ff0/FAQ/SEO/ALT \u5df2\u751f\u6210")

    def geo(self, *, score: int | float, eligible: bool) -> None:
        status = "\u901a\u8fc7" if eligible else "\u963b\u65ad"
        self._emit(f"\u3010GEO\u3011\u8bc4\u5206\uff1a{score} | \u72b6\u6001\uff1a{status}")

    def shopify_creating(self, *, title: str) -> None:
        self._emit(f"\u3010Shopify\u3011\u6b63\u5728\u521b\u5efa\u5546\u54c1\uff1a{title}")

    def shopify_success(self, *, product_id: str, variant_count: int) -> None:
        self._emit(f"\u3010Shopify\u3011\u521b\u5efa\u6210\u529f | Product ID\uff1a{product_id} | Variant \u6570\uff1a{variant_count}")

    def mapping(self, *, variant_count: int) -> None:
        self._emit(f"\u3010\u6620\u5c04\u3011SKU Mapping \u5df2\u5199\u5165 | Variant \u6570\uff1a{variant_count}")

    def inventory(self, *, synced: bool, inventory: int) -> None:
        if synced:
            self._emit(f"\u3010\u5e93\u5b58\u3011\u540c\u6b65\u6210\u529f | Shopify\u5e93\u5b58\uff1a{inventory}")
        else:
            self._emit("\u3010\u5e93\u5b58\u3011\u5e93\u5b58\u65e0\u53d8\u5316\uff0c\u8df3\u8fc7")

    def price(self, *, cost: float, sale_price: float, margin_rate: float, synced: bool) -> None:
        status = "\u6210\u529f" if synced else "\u8df3\u8fc7"
        self._emit(
            f"\u3010\u4ef7\u683c\u3011\u6210\u672c\uff1a{cost:.2f} | \u552e\u4ef7\uff1a{sale_price:.2f} | "
            f"\u5229\u6da6\u7387\uff1a{margin_rate:.0%} | \u72b6\u6001\uff1a{status}"
        )

    def risk(self, *, level: str, blocked: bool, reason: str = "") -> None:
        if blocked:
            safe_reason = reason or "\u672a\u77e5"
            self._emit(
                f"\u3010\u98ce\u63a7\u3011\u98ce\u9669\u7b49\u7ea7\uff1a{level.upper()} | "
                f"\u539f\u56e0\uff1a{safe_reason} | \u72b6\u6001\uff1a\u5df2\u963b\u65ad"
            )
        else:
            self._emit(f"\u3010\u98ce\u63a7\u3011\u98ce\u9669\u7b49\u7ea7\uff1a{level.upper()} | \u72b6\u6001\uff1a\u901a\u8fc7")

    def channels(self, published_channels: list[str]) -> None:
        targets = ["Shop", "Inbox", "Pinterest", "Facebook & Instagram"]
        statuses = []
        for name in targets:
            status = "\u6210\u529f" if name in published_channels else "\u672a\u53d1\u5e03"
            statuses.append(f"{name}\uff1a{status}")
        self._emit(f"\u3010\u6e20\u9053\u3011{' | '.join(statuses)}")

    def skip(self, *, reason: str, doba_product_id: str = "") -> None:
        suffix = f" | Doba Product ID\uff1a{doba_product_id}" if doba_product_id else ""
        self._emit(f"\u3010\u8df3\u8fc7\u3011{reason}{suffix}")

    def error(self, *, title: str, sku: str, reason: str) -> None:
        self._emit(f"\u3010\u9519\u8bef\u3011\u5546\u54c1\uff1a{title} | SKU\uff1a{sku} | \u539f\u56e0\uff1a{reason}")

    def stop(self, *, next_position: str) -> None:
        self._emit(
            f"\u3010\u505c\u6b62\u3011\u811a\u672c\u5df2\u505c\u6b62\uff0c\u65ad\u70b9\u5df2\u4fdd\u5b58\uff0c"
            f"\u53ef\u76f4\u63a5\u91cd\u8dd1\u540c\u4e00\u547d\u4ee4\u7eed\u8dd1 | {next_position}"
        )

    def checkpoint(self, *, next_position: str) -> None:
        self._emit(f"\u3010\u65ad\u70b9\u3011\u5df2\u4fdd\u5b58 | \u4e0b\u6b21\u4ece {next_position} \u7ee7\u7eed")

    def completion(self, *, summary: dict[str, Any], report_paths: list[str]) -> None:
        self._emit("========================================================")
        self._emit("\u672c\u6b21\u8fd0\u884c\u5b8c\u6210")
        self._emit(f"\u626b\u63cf\u5546\u54c1\uff1a{summary.get('scanned', 0)}")
        self._emit(f"\u6210\u529f\u53d1\u5e03\uff1a{summary.get('published', 0)}")
        self._emit(f"\u8df3\u8fc7\uff1a{summary.get('skipped', 0)}")
        self._emit(f"\u5931\u8d25\uff1a{summary.get('failed', 0)}")
        self._emit(f"\u62a5\u544a\uff1a{' | '.join(report_paths)}")
        self._emit("========================================================")


def normalize_channels(channels: str | list[str] | None) -> list[str]:
    if channels is None:
        return ["Shop", "Inbox", "Pinterest", "Facebook & Instagram"]
    if isinstance(channels, str):
        raw_values = [item.strip() for item in channels.split(",")]
    else:
        raw_values = []
        for item in channels:
            raw_values.extend([part.strip() for part in str(item).split(",")])
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in raw_values:
        if not raw:
            continue
        mapped = CHANNEL_LABELS.get(raw.lower(), raw)
        if mapped in seen:
            continue
        seen.add(mapped)
        normalized.append(mapped)
    return normalized or ["Shop", "Inbox", "Pinterest", "Facebook & Instagram"]


def _latest_result_for_spu(publish_result: dict[str, Any], spu_no: str) -> dict[str, Any] | None:
    for item in reversed(list(publish_result.get("results") or [])):
        if str(item.get("doba_spu_no") or "").strip() == spu_no:
            return item
    return None


def _shopify_states_from_result(result: dict[str, Any], sku_mappings: list[dict[str, Any]]) -> tuple[list[ShopifyInventoryState], list[ShopifyPriceState]]:
    mapping_by_sku = {
        str(item.get("supplier_sku") or item.get("sku") or "").strip(): item
        for item in sku_mappings
        if str(item.get("supplier_sku") or item.get("sku") or "").strip()
    }
    inventory_states: list[ShopifyInventoryState] = []
    price_states: list[ShopifyPriceState] = []
    for variant in list(result.get("variant_details") or []):
        sku = str(variant.get("sku") or "").strip()
        if not sku:
            continue
        mapping = mapping_by_sku.get(sku) or {}
        variant_id = str(mapping.get("shopify_variant_id") or "")
        inventory = int(variant.get("inventory") or 0)
        sale_price = float(variant.get("sale_price") or 0)
        timestamp = str(result.get("timestamp") or "")
        inventory_states.append(
            ShopifyInventoryState(
                supplier_sku=sku,
                shopify_variant_id=variant_id,
                inventory=inventory,
                updated_at=timestamp,
            )
        )
        price_states.append(
            ShopifyPriceState(
                supplier_sku=sku,
                shopify_variant_id=variant_id,
                current_price=sale_price,
                inventory=inventory,
                updated_at=timestamp,
            )
        )
    return inventory_states, price_states


def _collect_spu_context(
    *,
    archive_repository: SQLiteSupplierArchiveRepository,
    supplier_spu_no: str,
) -> dict[str, Any]:
    products = archive_repository.list_supplier_products_by_spu_nos([supplier_spu_no])
    sku_set = {product.sku for product in products if str(product.sku or "").strip()}
    screening_inputs = [item for item in archive_repository.list_screening_inputs() if item.supplier_sku in sku_set]
    return {
        "products": products,
        "screening_inputs": screening_inputs,
    }


def _merge_resume_summaries(runtime_state: dict[str, Any], archive_result: dict[str, Any], publish_report_path: str) -> None:
    publish_report = _load_json(publish_report_path)
    publish_summary = dict(publish_report.get("summary") or {})
    stream_publish = dict(archive_result.get("last_stream_publish") or {})
    stream_publish_summary = dict(stream_publish.get("publish_summary") or {})
    stream_candidate_summary = dict(stream_publish.get("candidate_pool_summary") or {})

    runtime_state["summary"]["published"] = max(
        runtime_state["summary"]["published"],
        int(publish_summary.get("published_count") or 0),
        int(stream_publish_summary.get("published_count") or 0),
    )
    runtime_state["summary"]["skipped"] = max(
        runtime_state["summary"]["skipped"],
        int(publish_summary.get("skipped_count") or 0),
        int(stream_publish_summary.get("skipped_count") or 0),
    )
    runtime_state["summary"]["failed"] = max(
        runtime_state["summary"]["failed"],
        int(publish_summary.get("failed_count") or 0),
        int(stream_publish_summary.get("failed_count") or 0),
    )
    runtime_state["summary"]["candidates"] = max(
        runtime_state["summary"]["candidates"],
        int(stream_candidate_summary.get("qualified_count") or 0),
    )
    runtime_state["summary"]["duplicate_skipped"] = max(
        runtime_state["summary"]["duplicate_skipped"],
        int((stream_candidate_summary.get("skipped_by_reason") or {}).get("already_successfully_published") or 0),
    )
    runtime_state["summary"]["active_skipped"] = max(
        runtime_state["summary"]["active_skipped"],
        int((stream_candidate_summary.get("skipped_by_reason") or {}).get("active_product_exists") or 0),
    )
    if runtime_state["summary"]["published"] > 0 and not runtime_state["channel_distribution_summary"]:
        runtime_state["channel_distribution_summary"] = {
            "Inbox": runtime_state["summary"]["published"],
            "Shop": runtime_state["summary"]["published"],
            "Pinterest": runtime_state["summary"]["published"],
            "Facebook & Instagram": runtime_state["summary"]["published"],
        }
        runtime_state["summary"]["channel_published"] = runtime_state["summary"]["published"] * 4

    runtime_state["inventory_sync_summary"]["successful_syncs"] = max(
        runtime_state["inventory_sync_summary"]["successful_syncs"],
        _parse_markdown_metric(INVENTORY_REPORT_PATH, "Successful syncs"),
    )
    runtime_state["inventory_sync_summary"]["failed_syncs"] = max(
        runtime_state["inventory_sync_summary"]["failed_syncs"],
        _parse_markdown_metric(INVENTORY_REPORT_PATH, "Failed syncs"),
    )
    runtime_state["price_sync_summary"]["successful_syncs"] = max(
        runtime_state["price_sync_summary"]["successful_syncs"],
        _parse_markdown_metric(PRICE_REPORT_PATH, "Successful syncs"),
    )
    runtime_state["price_sync_summary"]["failed_syncs"] = max(
        runtime_state["price_sync_summary"]["failed_syncs"],
        _parse_markdown_metric(PRICE_REPORT_PATH, "Failed syncs"),
    )
    runtime_state["risk_control_summary"]["total_events"] = max(
        runtime_state["risk_control_summary"]["total_events"],
        _parse_markdown_metric(RISK_REPORT_PATH, "Total risk events"),
    )
    runtime_state["risk_control_summary"]["approval_queue_count"] = max(
        runtime_state["risk_control_summary"]["approval_queue_count"],
        _parse_markdown_metric(RISK_REPORT_PATH, "Approval queue count"),
    )
    runtime_state["risk_control_summary"]["blocked_product_count"] = max(
        runtime_state["risk_control_summary"]["blocked_product_count"],
        _parse_markdown_metric(RISK_REPORT_PATH, "Blocked product count"),
    )


def _build_runtime_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Doba-Shopify-Agent V2 Runtime Report",
        "",
        "## Summary",
        f"- Total scanned: `{payload['summary'].get('scanned', 0)}`",
        f"- Total archived: `{payload['summary'].get('archived', 0)}`",
        f"- Total eligible: `{payload['summary'].get('eligible', 0)}`",
        f"- Total scored: `{payload['summary'].get('scored', 0)}`",
        f"- Total candidates: `{payload['summary'].get('candidates', 0)}`",
        f"- Total created: `{payload['summary'].get('published', 0)}`",
        f"- Total channel published: `{payload['summary'].get('channel_published', 0)}`",
        f"- Total skipped: `{payload['summary'].get('skipped', 0)}`",
        f"- Total failed: `{payload['summary'].get('failed', 0)}`",
        "",
        "## Failure Reasons",
    ]
    failure_reasons = payload.get("failure_reasons") or {}
    if failure_reasons:
        lines.extend(f"- `{reason}`: `{count}`" for reason, count in sorted(failure_reasons.items()))
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Duplicate Detection Summary",
            f"- Already published skipped: `{payload['summary'].get('duplicate_skipped', 0)}`",
            f"- Active product skipped: `{payload['summary'].get('active_skipped', 0)}`",
            "",
            "## Checkpoint Summary",
            f"- Archive checkpoint: `{payload.get('archive_checkpoint_path', '')}`",
            f"- Publish checkpoint: `{payload.get('publish_checkpoint_path', '')}`",
            f"- Last processed Doba product id: `{payload.get('last_processed_doba_product_id', '')}`",
            f"- Last processed SPU: `{payload.get('last_processed_spu', '')}`",
            "",
            "## Channel Distribution Summary",
        ]
    )
    channel_summary = payload.get("channel_distribution_summary") or {}
    if channel_summary:
        lines.extend(f"- `{channel}`: `{count}`" for channel, count in sorted(channel_summary.items()))
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Inventory Sync Summary",
            f"- Successful syncs: `{payload['inventory_sync_summary'].get('successful_syncs', 0)}`",
            f"- Failed syncs: `{payload['inventory_sync_summary'].get('failed_syncs', 0)}`",
            "",
            "## Price Sync Summary",
            f"- Successful syncs: `{payload['price_sync_summary'].get('successful_syncs', 0)}`",
            f"- Failed syncs: `{payload['price_sync_summary'].get('failed_syncs', 0)}`",
            "",
            "## Risk Control Summary",
            f"- Total events: `{payload['risk_control_summary'].get('total_events', 0)}`",
            f"- Approval queue: `{payload['risk_control_summary'].get('approval_queue_count', 0)}`",
            f"- Blocked products: `{payload['risk_control_summary'].get('blocked_product_count', 0)}`",
            "",
        ]
    )
    return "\n".join(lines)


def _write_runtime_report(path: str, payload: dict[str, Any]) -> str:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_build_runtime_report(payload) + "\n", encoding="utf-8")
    return str(output_path.resolve())


def run_doba_shopify_runtime(payload: dict[str, Any]) -> dict[str, Any]:
    _configure_stdout_utf8()
    mode = str(payload.get("mode") or "full-runtime").strip().lower()
    target_country = str(payload.get("target_country") or "US").strip().upper()
    inventory_threshold = int(payload.get("inventory_threshold") or 10)
    list_min_inventory = payload.get("list_min_inventory", 11)
    eligible_inventory_threshold = int(payload.get("eligible_inventory_threshold") or 10)
    page_size = int(payload.get("page_size") or 20)
    stream_publish = bool(payload.get("stream_publish", False))
    incremental = bool(payload.get("incremental", False))
    archive_eligible_only = bool(payload.get("archive_eligible_only", False))
    channels = normalize_channels(payload.get("channels"))
    archive_report_path = str(payload.get("archive_report_path") or DEFAULT_ARCHIVE_REPORT_PATH)
    archive_checkpoint_path = str(payload.get("archive_checkpoint_path") or DEFAULT_ARCHIVE_CHECKPOINT_PATH)
    publish_report_path = str(payload.get("publish_report_path") or DEFAULT_PUBLISH_REPORT_PATH)
    publish_checkpoint_path = str(payload.get("publish_checkpoint_path") or DEFAULT_PUBLISH_CHECKPOINT_PATH)
    candidate_pool_path = str(payload.get("candidate_pool_path") or DEFAULT_CANDIDATE_POOL_PATH)
    runtime_report_path = str(payload.get("runtime_report_path") or DEFAULT_RUNTIME_REPORT_PATH)
    resume_enabled = not bool(payload.get("no_resume", False))

    logger = RuntimeConsoleLogger(mode=mode, target_country=target_country)
    logger.banner()

    runtime_state: dict[str, Any] = {
        "ok": True,
        "mode": mode,
        "archive_checkpoint_path": archive_checkpoint_path,
        "publish_checkpoint_path": publish_checkpoint_path,
        "archive_report_path": archive_report_path,
        "publish_report_path": publish_report_path,
        "candidate_pool_path": candidate_pool_path,
        "runtime_report_path": runtime_report_path,
        "summary": {
            "scanned": 0,
            "archived": 0,
            "eligible": 0,
            "scored": 0,
            "candidates": 0,
            "published": 0,
            "channel_published": 0,
            "skipped": 0,
            "failed": 0,
            "duplicate_skipped": 0,
            "active_skipped": 0,
        },
        "failure_reasons": {},
        "channel_distribution_summary": {},
        "inventory_sync_summary": {"successful_syncs": 0, "failed_syncs": 0},
        "price_sync_summary": {"successful_syncs": 0, "failed_syncs": 0},
        "risk_control_summary": {"total_events": 0, "approval_queue_count": 0, "blocked_product_count": 0},
        "events": [],
    }

    archive_repository = SQLiteSupplierArchiveRepository()
    publish_mapping_repository = SQLitePublishMappingRepository()

    if mode == "archive-only":
        archive_result = run_doba_online_archive(
            report_path=archive_report_path,
            checkpoint_path=archive_checkpoint_path,
            page_size=page_size,
            target_country=target_country,
            min_inventory=(int(list_min_inventory) if list_min_inventory is not None else None),
            archive_eligible_only=archive_eligible_only,
            eligible_inventory_threshold=eligible_inventory_threshold,
            resume=resume_enabled,
        )
        runtime_state["archive_result"] = archive_result
        runtime_state["summary"]["scanned"] = int((archive_result.get("progress") or {}).get("processed_spu") or 0)
        runtime_state["summary"]["archived"] = int((archive_result.get("progress") or {}).get("archived_sku") or 0)
        runtime_state["summary"]["eligible"] = int((archive_result.get("progress") or {}).get("eligible_spu") or 0)
        runtime_state["runtime_report_path"] = _write_runtime_report(runtime_report_path, runtime_state)
        logger.completion(
            summary=runtime_state["summary"],
            report_paths=[archive_report_path, publish_report_path, runtime_state["runtime_report_path"]],
        )
        return runtime_state

    enable_publish = mode in {"archive-and-publish", "full-runtime"} and stream_publish

    def _hook(products: list[Any], context: dict[str, Any]) -> dict[str, Any]:
        spu_no = str(context.get("spu_no") or "").strip()
        spu_id = str(context.get("spu_id") or "").strip()
        title = str(context.get("title") or "").strip()
        total_spu = int(context.get("total_spu") or runtime_state["summary"]["scanned"] or 0)

        runtime_state["summary"]["scanned"] += 1
        runtime_state["summary"]["archived"] += len(products)
        runtime_state["summary"]["eligible"] += 1
        runtime_state["last_processed_doba_product_id"] = spu_id
        runtime_state["last_processed_spu"] = spu_no

        logger.progress(
            current=runtime_state["summary"]["scanned"],
            total=max(total_spu, runtime_state["summary"]["scanned"]),
            success=runtime_state["summary"]["published"],
            skipped=runtime_state["summary"]["skipped"],
            failed=runtime_state["summary"]["failed"],
        )
        logger.archive(
            title=title,
            sku_count=len(products),
            inventory=max(int(getattr(product, "inventory", 0) or 0) for product in products),
            status="\u6210\u529f",
        )
        logger.normalization(variant_count=len(products))

        screening_context = _collect_spu_context(archive_repository=archive_repository, supplier_spu_no=spu_no)
        screening_inputs = list(screening_context["screening_inputs"])
        screening_repository = InMemoryProductScreeningRepository()
        rule_result = run_rule_engine(screening_inputs, screening_repository)
        logger.validation(
            category_mapped=any(bool(getattr(product, "category_metafields", {})) for product in products),
            ship_from_us=all(str(getattr(product, "ship_from_country", "") or "").strip() == "United States" for product in products),
        )
        logger.rule_engine(status="\u8fdb\u5165 AI \u8bc4\u5206" if rule_result.pre_filtered_products else "\u88ab\u89c4\u5219\u62e6\u622a")
        if not rule_result.pre_filtered_products:
            runtime_state["summary"]["skipped"] += 1
            logger.skip(reason="\u89c4\u5219\u5f15\u64ce\u672a\u901a\u8fc7", doba_product_id=spu_id)
            return {"spu_no": spu_no, "rule_engine_summary": rule_result.model_dump()}

        deepseek_result = run_deepseek_scoring(rule_result.pre_filtered_products, screening_repository)
        runtime_state["summary"]["scored"] += deepseek_result.total_scored_products
        candidate_pool_result = run_candidate_pool(deepseek_result.ai_product_scores, screening_repository)
        runtime_state["summary"]["candidates"] += candidate_pool_result.approved_for_listing_count
        approved_candidate = next(
            (candidate for candidate in candidate_pool_result.listing_candidates if candidate.status == "approved_for_listing"),
            None,
        )
        logger.ai(
            score=(approved_candidate.overall_score if approved_candidate is not None else 0),
            status=(approved_candidate.status if approved_candidate is not None else "rejected"),
        )

        candidate_build_result = build_doba_publish_candidate_pool(
            candidate_pool_path=candidate_pool_path,
            target_country=target_country,
            inventory_threshold=inventory_threshold,
            incremental=incremental,
            incremental_spu_nos=[spu_no],
        )
        current_candidate_payload = next(
            (
                item
                for item in list(candidate_build_result.get("qualified_candidates") or [])
                if str((item or {}).get("spu_no") or "").strip() == spu_no
            ),
            {},
        )
        enrichment = dict((current_candidate_payload or {}).get("content_enrichment") or {})
        geo_score = dict(enrichment.get("geo_score") or {})
        logger.content()
        logger.geo(score=int(geo_score.get("score") or 0), eligible=bool(geo_score.get("eligible", False)))

        if mode == "archive-and-candidate" or not enable_publish:
            return {
                "spu_no": spu_no,
                "candidate_pool_summary": dict(candidate_build_result.get("summary") or {}),
                "publish_completed": False,
            }

        if not current_candidate_payload:
            skipped_by_reason = dict((candidate_build_result.get("summary") or {}).get("skipped_by_reason") or {})
            inferred_reason = "not_qualified_for_candidate_pool"
            if sum(int(value or 0) for value in skipped_by_reason.values()) == 1 and len(skipped_by_reason) == 1:
                inferred_reason = str(next(iter(skipped_by_reason.keys())) or inferred_reason)
            runtime_state["summary"]["skipped"] += 1
            if inferred_reason == "already_successfully_published":
                runtime_state["summary"]["duplicate_skipped"] += 1
            if inferred_reason == "active_product_exists":
                runtime_state["summary"]["active_skipped"] += 1
            skip_reason_map = {
                "already_successfully_published": "该商品之前已经成功发布",
                "active_product_exists": "Shopify 已存在 ACTIVE 商品",
                "missing_shopify_category": "类目无法映射到 Shopify",
                "missing_variant_pricing_data": "变体缺少有效定价数据",
                "not_qualified_for_candidate_pool": "未进入候选池，已跳过发布",
            }
            logger.skip(reason=skip_reason_map.get(inferred_reason, inferred_reason), doba_product_id=spu_id)
            return {
                "spu_no": spu_no,
                "candidate_pool_summary": dict(candidate_build_result.get("summary") or {}),
                "publish_completed": False,
                "publish_skipped_before_shopify": True,
                "skip_reason": inferred_reason,
            }

        logger.shopify_creating(title=title)
        publish_result = publish_doba_products_live(
            report_path=publish_report_path,
            target_country=target_country,
            channels=channels,
            page_size=page_size,
            inventory_threshold=inventory_threshold,
            list_min_inventory=(int(list_min_inventory) if list_min_inventory is not None else None),
            candidate_pool_path=candidate_pool_path,
            prefer_candidate_pool=True,
            refresh_candidate_pool=False,
            resume=resume_enabled,
            candidate_spu_nos=[spu_no],
            max_successes=1,
        )
        _write_json(publish_checkpoint_path, publish_result)
        latest_result = _latest_result_for_spu(publish_result, spu_no) or {}
        action = str(latest_result.get("action") or "").strip()
        reason = str(latest_result.get("reason") or "").strip()
        sku_list = list(latest_result.get("sku_list") or [])

        if action == "published":
            runtime_state["summary"]["published"] += 1
            published_channels = list(latest_result.get("published_channels") or [])
            runtime_state["summary"]["channel_published"] += len(published_channels)
            for channel in published_channels:
                runtime_state["channel_distribution_summary"][channel] = runtime_state["channel_distribution_summary"].get(channel, 0) + 1
            logger.shopify_success(
                product_id=str(latest_result.get("shopify_product_id") or ""),
                variant_count=int(latest_result.get("variant_count") or 0),
            )
            logger.mapping(variant_count=int(latest_result.get("variant_count") or 0))

            sku_mappings = [
                item.model_dump()
                for item in publish_mapping_repository.list_publish_mappings()
                if str(item.supplier_spu_no or "").strip() == spu_no
            ]
            inventory_states, price_states = _shopify_states_from_result(latest_result, sku_mappings)

            inventory_command = build_inventory_sync_command_from_archive(
                archive_repository=archive_repository,
                shopify_inventory_states=inventory_states,
                sku_mappings=sku_mappings,
                supplier_skus=sku_list,
                target_market=target_country,
            )
            inventory_sync_result = run_inventory_sync_runtime(inventory_command)
            runtime_state["inventory_sync_summary"]["successful_syncs"] += int(inventory_sync_result.report.successful_syncs or 0)
            runtime_state["inventory_sync_summary"]["failed_syncs"] += int(inventory_sync_result.report.failed_syncs or 0)
            logger.inventory(
                synced=bool(inventory_sync_result.report.successful_syncs),
                inventory=max([state.inventory for state in inventory_states] or [0]),
            )

            price_command = build_price_sync_command_from_archive(
                archive_repository=archive_repository,
                shopify_price_states=price_states,
                sku_mappings=sku_mappings,
                supplier_skus=sku_list,
                target_market=target_country,
            )
            price_sync_result = run_price_sync_runtime(price_command)
            runtime_state["price_sync_summary"]["successful_syncs"] += int(price_sync_result.report.successful_syncs or 0)
            runtime_state["price_sync_summary"]["failed_syncs"] += int(price_sync_result.report.failed_syncs or 0)
            variant_costs = list(latest_result.get("cost_prices") or [0])
            variant_sales = list(latest_result.get("sale_prices") or [0])
            top_cost = float(variant_costs[0] if variant_costs else 0)
            top_sale = float(variant_sales[0] if variant_sales else 0)
            margin_rate = ((top_sale - top_cost) / top_sale) if top_sale else 0
            logger.price(
                cost=top_cost,
                sale_price=top_sale,
                margin_rate=margin_rate,
                synced=bool(price_sync_result.report.successful_syncs),
            )

            risk_command = build_risk_control_command_from_archive(
                archive_repository=archive_repository,
                listing_candidates=screening_repository.list_listing_candidates(),
                inventory_sync_logs=inventory_sync_result.records,
                price_sync_logs=price_sync_result.records,
                pricing_decisions=price_sync_result.decisions,
                sku_mappings=sku_mappings,
                supplier_skus=sku_list,
            )
            risk_result = run_risk_control(risk_command)
            runtime_state["risk_control_summary"]["total_events"] += len(risk_result.risk_events)
            runtime_state["risk_control_summary"]["approval_queue_count"] += len(risk_result.approval_queue)
            runtime_state["risk_control_summary"]["blocked_product_count"] += len(risk_result.blocked_products)
            blocked_current = [item for item in risk_result.blocked_products if str(item.supplier_sku or "").strip() in set(sku_list)]
            if blocked_current:
                reason_text = str(blocked_current[0].reason or "critical_risk_detected")
                runtime_state["summary"]["failed"] += 1
                runtime_state["failure_reasons"][reason_text] = runtime_state["failure_reasons"].get(reason_text, 0) + 1
                rollback_summary: dict[str, Any] = {}
                product_id = str(latest_result.get("shopify_product_id") or "")
                if product_id:
                    try:
                        rollback_summary = rollback_shopify_product_publications(
                            product_id=product_id,
                            channels=published_channels,
                            set_draft=True,
                        )
                    except Exception as rollback_exc:
                        rollback_summary = {
                            "shopify_product_id": product_id,
                            "rollback_error": str(rollback_exc),
                        }
                logger.risk(level="high", blocked=True, reason=reason_text)
                next_position = f"Doba Product ID：{spu_id} / SPU：{spu_no}"
                logger.checkpoint(next_position=next_position)
                logger.stop(next_position=next_position)
                return {
                    "spu_no": spu_no,
                    "candidate_pool_summary": dict(candidate_build_result.get("summary") or {}),
                    "publish_summary": dict(publish_result.get("summary") or {}),
                    "publish_completed": False,
                    "stop_archive": True,
                    "stop_reason": "critical_risk_detected",
                    "last_failure": {
                        "failed_spu_no": spu_no,
                        "failed_doba_product_id": spu_id,
                        "failed_sku": sku_list[0] if sku_list else "",
                        "failed_sku_list": sku_list,
                        "failed_reason": reason_text,
                        "rollback_summary": rollback_summary,
                        "completed_count": runtime_state["summary"]["published"],
                        "resume_position": {"doba_product_id": spu_id, "spu_no": spu_no},
                    },
                }

            logger.risk(level="low", blocked=False)
            logger.channels(published_channels=published_channels)
            logger.checkpoint(next_position=f"Doba Product ID：{spu_id} / SPU：{spu_no}")
            return {
                "spu_no": spu_no,
                "candidate_pool_summary": dict(candidate_build_result.get("summary") or {}),
                "publish_summary": dict(publish_result.get("summary") or {}),
                "publish_completed": bool(publish_result.get("completed")),
            }

        runtime_state["summary"]["skipped"] += 1
        if reason == "already_successfully_published":
            runtime_state["summary"]["duplicate_skipped"] += 1
        if reason == "active_product_exists":
            runtime_state["summary"]["active_skipped"] += 1
        if action == "failed":
            runtime_state["summary"]["failed"] += 1
            runtime_state["failure_reasons"][reason or "unknown"] = runtime_state["failure_reasons"].get(reason or "unknown", 0) + 1
            logger.error(title=title, sku=(sku_list[0] if sku_list else ""), reason=reason or "unknown")
            next_position = f"Doba Product ID：{spu_id} / SPU：{spu_no}"
            logger.checkpoint(next_position=next_position)
            logger.stop(next_position=next_position)
            return {
                "spu_no": spu_no,
                "candidate_pool_summary": dict(candidate_build_result.get("summary") or {}),
                "publish_summary": dict(publish_result.get("summary") or {}),
                "publish_completed": False,
                "stop_archive": True,
                "stop_reason": "publish_failed",
                "last_failure": {
                    "failed_spu_no": spu_no,
                    "failed_doba_product_id": spu_id,
                    "failed_sku": sku_list[0] if sku_list else "",
                    "failed_sku_list": sku_list,
                    "failed_reason": reason or "unknown",
                    "completed_count": runtime_state["summary"]["published"],
                    "resume_position": {"doba_product_id": spu_id, "spu_no": spu_no},
                },
            }

        skip_reason_map = {
            "already_successfully_published": "\u8be5\u5546\u54c1\u4e4b\u524d\u5df2\u7ecf\u6210\u529f\u53d1\u5e03",
            "active_product_exists": "Shopify \u5df2\u5b58\u5728 ACTIVE \u5546\u54c1",
            "all_variants_inventory_below_threshold": "\u6240\u6709\u53d8\u4f53\u5e93\u5b58\u90fd\u672a\u8fbe\u5230\u95e8\u69db",
        }
        logger.skip(reason=skip_reason_map.get(reason, reason or "\u672a\u901a\u8fc7\u53d1\u5e03\u6761\u4ef6"), doba_product_id=spu_id)
        return {
            "spu_no": spu_no,
            "candidate_pool_summary": dict(candidate_build_result.get("summary") or {}),
            "publish_summary": dict(publish_result.get("summary") or {}),
            "publish_completed": bool(publish_result.get("completed")),
        }

    archive_result = run_doba_online_archive(
        report_path=archive_report_path,
        checkpoint_path=archive_checkpoint_path,
        page_size=page_size,
        target_country=target_country,
        min_inventory=(int(list_min_inventory) if list_min_inventory is not None else None),
        archive_eligible_only=archive_eligible_only,
        eligible_inventory_threshold=eligible_inventory_threshold,
        resume=resume_enabled,
        post_archive_hook=_hook if mode != "archive-only" else None,
    )

    runtime_state["archive_result"] = archive_result
    progress = dict(archive_result.get("progress") or {})
    runtime_state["summary"]["scanned"] = max(runtime_state["summary"]["scanned"], int(progress.get("processed_spu") or 0))
    runtime_state["summary"]["archived"] = max(runtime_state["summary"]["archived"], int(progress.get("archived_sku") or 0))
    runtime_state["summary"]["eligible"] = max(runtime_state["summary"]["eligible"], int(progress.get("eligible_spu") or 0))
    _merge_resume_summaries(runtime_state, archive_result, publish_report_path)
    runtime_state["ok"] = not bool(archive_result.get("stopped_reason"))
    if archive_result.get("last_failure"):
        runtime_state["last_failure"] = dict(archive_result.get("last_failure") or {})
        if str(runtime_state["last_failure"].get("response_message") or "").strip() == "IP whitelist check failed":
            logger.error(
                title="Doba API",
                sku="",
                reason="\u767d\u540d\u5355 IP \u6821\u9a8c\u5931\u8d25\uff0c\u8bf7\u68c0\u67e5\u5f53\u524d\u51fa\u53e3 IP \u548c Doba \u767d\u540d\u5355",
            )
            logger.stop(
                next_position=(
                    f"page={runtime_state['last_failure'].get('resume_position', {}).get('page_number', 0)}, "
                    f"index={runtime_state['last_failure'].get('resume_position', {}).get('index_in_page', 0)}"
                )
            )
    runtime_state["runtime_report_path"] = _write_runtime_report(runtime_report_path, runtime_state)
    logger.completion(
        summary=runtime_state["summary"],
        report_paths=[archive_report_path, publish_report_path, runtime_state["runtime_report_path"]],
    )
    return runtime_state
