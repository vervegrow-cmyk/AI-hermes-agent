from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import shutil
import sys
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

AGENT_ROOT = Path(__file__).resolve().parents[1]
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from models.category_sync import CategorySyncRequest
from service.category_optimization_service import get_category_optimization_service
from workflow.apply_shopify_admin_accept_all_cli import (
    _click_accept_all,
    _click_category_suggestion,
    _click_submit_or_save,
    _default_checkpoint_file as _default_frontend_checkpoint_file,
    _extract_category_section_state,
    _has_unsaved_changes,
    _open_browser_runtime,
    _slugify,
    _verify_saved_category_change,
)
from workflow.batch_io import append_jsonl, read_json, read_jsonl, write_csv, write_json
from workflow.capture_shopify_admin_suggestions_cli import (
    _build_urls_from_shopify,
    _cooldown_after_item,
    _extract_product_gid,
    _extract_suggestions,
    _open_product_page,
)


def _now_label() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _print_line(message: str) -> None:
    print(f"[{_now_label()}] {message}", flush=True)


def _normalize_product_id(product_id: str) -> str:
    cleaned = str(product_id or "").strip()
    if not cleaned:
        return ""
    if cleaned.startswith("gid://shopify/Product/"):
        return cleaned
    numeric = cleaned.rsplit("/", 1)[-1]
    return f"gid://shopify/Product/{numeric}"


def _product_gid_to_admin_url(product_gid: str, store_handle: str) -> str:
    numeric_id = product_gid.rsplit("/", 1)[-1]
    return f"https://admin.shopify.com/store/{store_handle}/products/{numeric_id}"


def _default_checkpoint_file(args: argparse.Namespace) -> Path:
    if args.checkpoint_file:
        return Path(args.checkpoint_file).expanduser()
    tmp = argparse.Namespace(
        store_handle=args.store_handle,
        product_query=args.product_query,
        product_url=args.product_url,
        product_urls_file=args.product_urls_file,
    )
    path = _default_frontend_checkpoint_file(tmp)
    return path.with_name(path.stem.replace("shopify-admin-accept-all", "shopify-category-governance") + path.suffix)


def _default_suggestions_file(args: argparse.Namespace) -> Path:
    runs_dir = AGENT_ROOT / "workflow" / "runs"
    if args.store_handle and not args.product_query and not args.product_id and not args.product_url and not args.product_urls_file:
        scope = "all-products"
    else:
        scope = _slugify(args.product_query) if args.product_query else "governance"
    return runs_dir / f"shopify-admin-suggestions-governance-{scope}.jsonl"


def _resolve_suggestions_log_file(path: Path) -> Path:
    if path.suffix.lower() == ".jsonl":
        return path
    return path.with_suffix(path.suffix + ".jsonl")


def _append_captured_suggestion(log_file: Path, product_gid: str, suggestion: dict[str, Any]) -> None:
    payload = {
        "product_id": product_gid,
        "captured_at": _now_label(),
        **suggestion,
    }
    append_jsonl(log_file, payload)


def _preflight_cdp_url(cdp_url: str) -> None:
    target = str(cdp_url or "").strip()
    if not target:
        return
    probe_url = target.rstrip("/") + "/json/version"
    try:
        with urlopen(probe_url, timeout=3) as response:
            if getattr(response, "status", 200) >= 400:
                raise URLError(f"HTTP {response.status}")
    except Exception as exc:
        raise SystemExit(
            f"未能连接到已打开浏览器的 CDP 地址：{target}。"
            f" 请先启动带 `--remote-debugging-port` 的 Chrome / Edge，"
            f"并确认该端口仍可访问后再重试。原始错误：{exc}"
        ) from exc


class CheckpointStore:
    def __init__(
        self,
        checkpoint_file: Path,
        *,
        mode: str,
        store_handle: str,
        product_query: str,
        max_items: int,
    ) -> None:
        self.checkpoint_file = checkpoint_file
        self.result_file = checkpoint_file.with_suffix(".results.jsonl")
        self.review_csv_file = checkpoint_file.with_suffix(".review.csv")
        self.failed_csv_file = checkpoint_file.with_suffix(".failed.csv")
        self.audit_report_file = checkpoint_file.with_suffix(".audit.json")
        self.mode = mode
        self.store_handle = store_handle
        self.product_query = product_query
        self.max_items = max_items
        self.data: dict[str, Any] = {}

    def reset(self) -> None:
        for path in [
            self.checkpoint_file,
            self.result_file,
            self.review_csv_file,
            self.failed_csv_file,
            self.audit_report_file,
        ]:
            if path.exists():
                path.unlink()

    def load_or_initialize(self, *, resume: bool) -> dict[str, Any]:
        if resume and self.checkpoint_file.exists():
            self.data = read_json(self.checkpoint_file)
            self._validate_compatibility()
            self.data["status"] = "running"
            self.data["updated_at"] = _now_label()
            self._save()
            return self.data

        self.data = {
            "version": 1,
            "status": "running",
            "mode": self.mode,
            "store_handle": self.store_handle,
            "product_query": self.product_query,
            "max_items": self.max_items,
            "started_at": _now_label(),
            "updated_at": _now_label(),
            "processed_count": 0,
            "frontend_saved_count": 0,
            "backend_saved_count": 0,
            "unchanged_count": 0,
            "review_count": 0,
            "failed_count": 0,
            "processed_product_ids": [],
            "files": {
                "checkpoint": str(self.checkpoint_file),
                "results_jsonl": str(self.result_file),
                "review_csv": str(self.review_csv_file),
                "failed_csv": str(self.failed_csv_file),
                "audit_report": str(self.audit_report_file),
            },
        }
        self._save()
        return self.data

    def processed_product_ids(self) -> list[str]:
        return list(self.data.get("processed_product_ids", []))

    def record_item(self, item: dict[str, Any]) -> None:
        product_id = item.get("product_id", "")
        processed = self.data.setdefault("processed_product_ids", [])
        if product_id and product_id not in processed:
            processed.append(product_id)
        self.data["processed_count"] = len(processed)

        status = item.get("status", "")
        if status in {"shopify_accept_all_saved", "shopify_category_suggestion_saved"}:
            self.data["frontend_saved_count"] = int(self.data.get("frontend_saved_count", 0)) + 1
        elif status in {"deepseek_suggestion_applied", "forced_review_applied"}:
            self.data["backend_saved_count"] = int(self.data.get("backend_saved_count", 0)) + 1
        elif status in {"no_suggestion_no_change", "shopify_frontend_detected_but_not_applied", "forced_review_unchanged"}:
            self.data["unchanged_count"] = int(self.data.get("unchanged_count", 0)) + 1
        elif status == "needs_manual_review":
            self.data["review_count"] = int(self.data.get("review_count", 0)) + 1
        elif status in {"open_failed", "apply_failed"}:
            self.data["failed_count"] = int(self.data.get("failed_count", 0)) + 1

        self.data["updated_at"] = _now_label()
        append_jsonl(self.result_file, item)
        self._save()

    def mark_interrupted(self) -> None:
        self.data["status"] = "interrupted"
        self.data["updated_at"] = _now_label()
        self.data["summary"] = self._summary_text(prefix="任务已中断")
        self._build_exports()
        self._save()

    def mark_finished(self) -> None:
        self.data["status"] = "completed"
        self.data["updated_at"] = _now_label()
        self.data["summary"] = self._summary_text(prefix="任务完成")
        self._build_exports()
        self._save()

    def _summary_text(self, *, prefix: str) -> str:
        return (
            f"{prefix}：共处理 {self.data.get('processed_count', 0)} 个商品，"
            f"前端建议保存成功 {self.data.get('frontend_saved_count', 0)} 个，"
            f"后端回退写回成功 {self.data.get('backend_saved_count', 0)} 个，"
            f"无需修改 {self.data.get('unchanged_count', 0)} 个，"
            f"待人工复核 {self.data.get('review_count', 0)} 个，"
            f"失败 {self.data.get('failed_count', 0)} 个。"
        )

    def _validate_compatibility(self) -> None:
        mismatches = []
        if (self.data.get("mode") or "") != self.mode:
            mismatches.append("mode")
        if (self.data.get("store_handle") or "") != self.store_handle:
            mismatches.append("store_handle")
        if (self.data.get("product_query") or "") != self.product_query:
            mismatches.append("product_query")
        if int(self.data.get("max_items", 0)) != int(self.max_items):
            mismatches.append("max_items")
        if mismatches:
            mismatch_text = ", ".join(mismatches)
            raise SystemExit(
                f"检查点文件与当前命令不匹配，冲突字段：{mismatch_text}。"
                f" 如需重跑，请加 --reset-checkpoint，或改用新的 --checkpoint-file。"
            )

    def _build_exports(self) -> None:
        items = read_jsonl(self.result_file) if self.result_file.exists() else []
        latest_by_product: dict[str, dict[str, Any]] = {}
        for item in items:
            product_id = str(item.get("product_id", "")).strip()
            if not product_id:
                continue
            latest_by_product[product_id] = item
        latest_items = list(latest_by_product.values())
        self.data["processed_product_ids"] = sorted(latest_by_product.keys())
        self.data["processed_count"] = len(latest_items)
        self.data["frontend_saved_count"] = sum(
            1 for item in latest_items if item.get("status") in {"shopify_accept_all_saved", "shopify_category_suggestion_saved"}
        )
        self.data["backend_saved_count"] = sum(
            1 for item in latest_items if item.get("status") in {"deepseek_suggestion_applied", "forced_review_applied"}
        )
        self.data["unchanged_count"] = sum(
            1
            for item in latest_items
            if item.get("status") in {"no_suggestion_no_change", "shopify_frontend_detected_but_not_applied", "forced_review_unchanged"}
        )
        self.data["review_count"] = sum(1 for item in latest_items if item.get("status") == "needs_manual_review")
        self.data["failed_count"] = sum(1 for item in latest_items if item.get("status") in {"open_failed", "apply_failed"})

        review_rows = []
        failed_rows = []
        for item in latest_items:
            if item.get("status") == "needs_manual_review":
                review_rows.append(
                    {
                        "product_id": item.get("product_id", ""),
                        "title": item.get("title", ""),
                        "source": item.get("source", ""),
                        "status": item.get("status", ""),
                        "decision_reason": item.get("decision_reason", ""),
                        "admin_url": item.get("admin_url", ""),
                    }
                )
            if item.get("status") in {"open_failed", "apply_failed"}:
                failed_rows.append(
                    {
                        "product_id": item.get("product_id", ""),
                        "title": item.get("title", ""),
                        "status": item.get("status", ""),
                        "error": item.get("error", "") or self._collapse_apply_errors(item),
                        "admin_url": item.get("admin_url", ""),
                    }
                )

        write_csv(self.review_csv_file, review_rows, ["product_id", "title", "source", "status", "decision_reason", "admin_url"])
        write_csv(self.failed_csv_file, failed_rows, ["product_id", "title", "status", "error", "admin_url"])
        write_json(
            self.audit_report_file,
            {
                "generated_at": _now_label(),
                "summary": self.data.get("summary", ""),
                "counts": {
                    "processed": self.data.get("processed_count", 0),
                    "frontend_saved": self.data.get("frontend_saved_count", 0),
                    "backend_saved": self.data.get("backend_saved_count", 0),
                    "unchanged": self.data.get("unchanged_count", 0),
                    "review": self.data.get("review_count", 0),
                    "failed": self.data.get("failed_count", 0),
                },
                "files": self.data.get("files", {}),
            },
        )

    def _collapse_apply_errors(self, item: dict[str, Any]) -> str:
        apply_result = item.get("apply_result") or {}
        errors = apply_result.get("errors") or []
        if not errors:
            return ""
        parts = []
        for error in errors:
            scope = str(error.get("scope", "") or "").strip()
            reason = str(error.get("reason", "") or "").strip()
            detail = str(error.get("detail", "") or "").strip()
            parts.append(" / ".join(part for part in [scope, reason, detail] if part))
        return "; ".join(parts)

    def _save(self) -> None:
        write_json(self.checkpoint_file, self.data)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Shopify category governance main chain one product at a time.")
    parser.add_argument("--mode", choices=["dry-run", "apply"], default="apply", help="执行模式")
    parser.add_argument("--store-handle", required=True, help="Shopify Admin store handle，例如 getbulkdeals")
    parser.add_argument("--store-name", default="", help="店铺域名，后端 API 回退时使用共享环境变量中的默认值")
    parser.add_argument("--product-query", default="", help="按 Shopify query 过滤商品；为空时跑全店")
    parser.add_argument("--max-items", type=int, default=0, help="最大处理商品数，0 表示不限")
    parser.add_argument("--product-id", action="append", default=[], help="指定 Shopify Product GID，可重复传入")
    parser.add_argument("--product-url", action="append", default=[], help="指定单个 Shopify 商品编辑页 URL，可重复传入")
    parser.add_argument("--product-urls-file", default="", help="包含多个 Shopify 商品编辑页 URL 的文本文件")
    parser.add_argument("--candidate-category", default="", help="DeepSeek 回退时可选候选类目提示")
    parser.add_argument("--no-apply-metafields", action="store_true", help="后端回退 apply 模式下不写回元字段")
    parser.add_argument("--force-apply-review-items", action="store_true", help="高风险或原本待人工复核的后端决策也直接写回 Shopify，不再进入人工复核")
    parser.add_argument("--captured-suggestions-file", default="", help="逐商品落盘的前端建议 JSON 文件")
    parser.add_argument("--checkpoint-file", default="", help="检查点文件路径，默认自动生成")
    parser.add_argument("--reset-checkpoint", action="store_true", help="执行前重置检查点和结果文件")
    parser.add_argument("--no-resume", action="store_true", help="禁用断点续跑，每次都从头开始")
    parser.add_argument("--storage-state", default="", help="Playwright 登录态文件路径")
    parser.add_argument("--chrome-user-data-dir", default="", help="本地浏览器用户数据目录")
    parser.add_argument("--chrome-profile-directory", default="Default", help="浏览器 Profile 名称")
    parser.add_argument("--browser-channel", default="chrome", choices=["chrome", "msedge"], help="浏览器通道")
    parser.add_argument("--cdp-url", default="", help="连接已打开浏览器的 CDP 地址，例如 http://127.0.0.1:9222")
    parser.add_argument("--goto-timeout-ms", type=int, default=120000, help="商品页打开超时时间")
    parser.add_argument("--wait-until", default="domcontentloaded", choices=["domcontentloaded", "load", "networkidle", "commit"], help="页面跳转等待策略")
    parser.add_argument("--retry-count", type=int, default=4, help="打开商品页失败时的重试次数")
    parser.add_argument("--retry-backoff-ms", type=int, default=30000, help="每次重试前的等待时间")
    parser.add_argument("--page-delay-ms", type=int, default=12000, help="每个商品完成后的常规等待时间")
    parser.add_argument("--batch-size", type=int, default=5, help="连续处理多少个商品后进入一轮冷却")
    parser.add_argument("--batch-cooldown-ms", type=int, default=120000, help="批次冷却时间")
    parser.add_argument("--post-click-wait-ms", type=int, default=1500, help="点击建议后的等待时间")
    parser.add_argument("--post-save-wait-ms", type=int, default=4000, help="点击保存后的等待时间")
    parser.add_argument("--save-settle-timeout-ms", type=int, default=30000, help="点击保存后等待未保存状态消失的最长时间")
    parser.add_argument("--headed", action="store_true", help="使用有头浏览器")
    return parser


def _load_urls(args: argparse.Namespace) -> list[str]:
    urls: list[str] = []

    for item in args.product_url or []:
        cleaned = str(item or "").strip()
        if cleaned:
            urls.append(cleaned)

    if args.product_urls_file:
        file_path = Path(args.product_urls_file).expanduser()
        if not file_path.is_absolute():
            file_path = (AGENT_ROOT / file_path).resolve()
        urls.extend([line.strip() for line in file_path.read_text(encoding="utf-8").splitlines() if line.strip()])

    explicit_product_ids = [_normalize_product_id(item) for item in (args.product_id or []) if _normalize_product_id(item)]
    for product_gid in explicit_product_ids:
        urls.append(_product_gid_to_admin_url(product_gid, args.store_handle))

    urls.extend(_build_urls_from_shopify(args.store_handle, args.product_query, args.max_items))

    deduped: list[str] = []
    seen: set[str] = set()
    for url in urls:
        if url and url not in seen:
            seen.add(url)
            deduped.append(url)
    if not deduped:
        raise SystemExit("未找到可处理的商品链接，请检查店铺、筛选条件或手工输入参数。")
    if args.max_items and args.max_items > 0:
        return deduped[: args.max_items]
    return deduped


def _has_frontend_signal(suggestion: dict[str, Any]) -> bool:
    metafield_source = str(suggestion.get("metafields_source", "") or "").strip().lower()
    has_metafield_suggestion = metafield_source == "suggestion" or bool(suggestion.get("metafield_suggestion_count"))
    return bool(
        suggestion.get("category_suggestion_text")
        or suggestion.get("category_full_name")
        or has_metafield_suggestion
        or (suggestion.get("metafield_suggestion_section_found") and suggestion.get("metafield_suggestion_rows"))
        or suggestion.get("metafield_suggestion_section_found")
    )


def _is_clean_frontend_category_text(value: str) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    noise_markers = ["确定税率", "全部接受", "Google:", "false", "搜索类别", "可用建议"]
    if any(marker.lower() in text.lower() for marker in noise_markers):
        return False
    if text.startswith("接受建议的类别：") or text.startswith("忽略建议的类别："):
        return False
    if "条建议" in text or "个元字段" in text:
        return False
    if text.count("（在") > 1 or text.count("(in ") > 1:
        return False
    if "；" in text or ";" in text:
        return False
    return len(text) <= 140


def _is_reliable_frontend_signal(suggestion: dict[str, Any]) -> bool:
    category_text = str(suggestion.get("category_suggestion_text", "") or "")
    metafields = suggestion.get("metafields") or []
    metafield_source = str(suggestion.get("metafields_source", "") or "").strip().lower()
    if category_text and _is_clean_frontend_category_text(category_text):
        return True
    if metafield_source == "suggestion" and metafields and not category_text:
        return True
    return False


def _normalize_category_display_text(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    for marker in ["（在", "(在", " (in ", "（in "]:
        if marker in text:
            text = text.split(marker, 1)[0].strip()
    return " ".join(text.split()).lower()


def _category_value_matches_expected(actual_value: str, expected_value: str) -> bool:
    actual_norm = _normalize_category_display_text(actual_value)
    expected_norm = _normalize_category_display_text(expected_value)
    if not actual_norm or not expected_norm:
        return False
    return actual_norm == expected_norm or actual_norm in expected_norm or expected_norm in actual_norm


def _build_request(args: argparse.Namespace, *, product_id: str, suggestion: dict[str, Any]) -> CategorySyncRequest:
    shopify_suggestions = {product_id: suggestion} if suggestion else {}
    return CategorySyncRequest(
        store_name=args.store_name,
        mode=args.mode,
        product_query=args.product_query,
        candidate_category=args.candidate_category,
        max_items=1,
        product_ids=[product_id],
        shopify_suggestions=shopify_suggestions,
        apply_metafields=not args.no_apply_metafields,
        force_apply_review_items=args.force_apply_review_items,
    )


def _build_review_item(
    product_gid: str,
    url: str,
    reason: str,
    suggestion: dict[str, Any],
    backend_item: dict[str, Any] | None = None,
    frontend_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    title = ""
    if backend_item:
        title = backend_item.get("title", "")
    verification = (frontend_result or {}).get("verification") or {}
    category_suggestion = (frontend_result or {}).get("category_suggestion") or {}
    return {
        "product_id": product_gid,
        "title": title,
        "admin_url": url,
        "source": "shopify_frontend" if suggestion else "system",
        "status": "needs_manual_review",
        "decision_reason": reason,
        "frontend_suggestion": suggestion,
        "frontend_result": frontend_result or {},
        "frontend_accepted": (frontend_result or {}).get("accepted"),
        "frontend_saved": (frontend_result or {}).get("saved"),
        "frontend_verification_status": verification.get("verification_status", ""),
        "frontend_verification_error": verification.get("verification_error", ""),
        "frontend_refreshed_value": verification.get("refreshed_value", ""),
        "frontend_category_clicked_text": category_suggestion.get("clicked_text", ""),
        "frontend_category_before": category_suggestion.get("before_value", ""),
        "frontend_category_after": category_suggestion.get("after_value", ""),
        "backend_item": backend_item or {},
    }


def _build_open_failed_item(product_gid: str, url: str, error_message: str) -> dict[str, Any]:
    return {
        "product_id": product_gid,
        "title": "",
        "admin_url": url,
        "source": "system",
        "status": "open_failed",
        "error": error_message,
        "decision_reason": "商品页打开失败，已记录错误并继续后续商品。",
    }


def _build_backend_result_item(item: dict[str, Any], *, url: str) -> dict[str, Any]:
    apply_result = item.get("apply_result") or {}
    review_bypassed = bool(item.get("review_bypassed") or apply_result.get("review_bypassed"))
    if apply_result.get("status") == "applied":
        status = "forced_review_applied" if review_bypassed else "deepseek_suggestion_applied"
    elif apply_result.get("status") == "unchanged":
        status = "forced_review_unchanged" if review_bypassed else "no_suggestion_no_change"
    elif apply_result.get("status") == "apply_failed":
        status = "apply_failed"
    elif item.get("needs_review"):
        status = "needs_manual_review"
    elif apply_result.get("status") == "dry_run":
        status = "no_suggestion_no_change"
    else:
        status = apply_result.get("status", "no_suggestion_no_change")
    item["status"] = status
    item["admin_url"] = url
    return item


def _build_frontend_chain_status(frontend_result: dict[str, Any]) -> str:
    verification = frontend_result.get("verification") or {}
    status = str(verification.get("verification_status", "") or "").strip()
    if status == "saved_successfully":
        if frontend_result.get("accepted"):
            return "shopify_accept_all_saved"
        if (frontend_result.get("category_suggestion") or {}).get("clicked"):
            return "shopify_category_suggestion_saved"
        return "shopify_frontend_saved"
    if status == "save_not_completed":
        return "shopify_save_not_completed"
    if status == "refreshed_value_unchanged":
        return "shopify_refresh_unchanged"
    if status == "reload_failed":
        return "shopify_reload_failed"
    return "shopify_frontend_not_applied"


def _print_frontend_diagnostics(*, overall_index: int, total_target: int, frontend_result: dict[str, Any]) -> None:
    category = frontend_result.get("category_suggestion") or {}
    verification = frontend_result.get("verification") or {}
    _print_line(
        f"第 {overall_index}/{total_target} 个商品前端诊断："
        f"全部接受={'是' if frontend_result.get('accepted') else '否'}；"
        f"类别建议点击={'是' if category.get('clicked') else '否'}；"
        f"类别建议文本：{category.get('clicked_text') or '无'}；"
        f"出现未保存更改={'是' if category.get('unsaved_appeared') or verification.get('save_completed') or frontend_result.get('accepted') else '否'}；"
        f"保存点击={'是' if frontend_result.get('saved') else '否'}；"
        f"刷新后类别：{verification.get('refreshed_value') or '未读取到'}；"
        f"刷新后前端建议仍存在={'是' if verification.get('frontend_signal_after_reload') else '否'}；"
        f"前端状态：{_build_frontend_chain_status(frontend_result)}。"
    )


def _build_frontend_failure_reason(frontend_result: dict[str, Any]) -> str:
    verification = frontend_result.get("verification") or {}
    status = _build_frontend_chain_status(frontend_result)
    refreshed_value = verification.get("refreshed_value") or "未读取到"
    if status == "shopify_save_not_completed":
        return "存在 Shopify 前端建议，但页面未完成保存提交，已回退到后端链且未形成有效变更。"
    if status == "shopify_refresh_unchanged":
        return f"存在 Shopify 前端建议，已尝试采纳并保存，但刷新后类别未变化，当前刷新值：{refreshed_value}。"
    if status == "shopify_reload_failed":
        return f"存在 Shopify 前端建议，已尝试采纳并保存，但刷新复核失败：{verification.get('verification_error', 'unknown error')}。"
    return "存在 Shopify 前端建议，但前端采纳未形成稳定闭环且后端回退未形成有效变更，需人工复核。"


def _attempt_frontend_chain(page, *, url: str, args: argparse.Namespace, suggestion: dict[str, Any]) -> dict[str, Any]:
    before_accept_state = _extract_category_section_state(page)
    expected_category_value = str(
        suggestion.get("category_suggestion_text")
        or suggestion.get("category_full_name")
        or ""
    ).strip()
    before_metafield_suggestion_count = int(suggestion.get("metafield_suggestion_count") or 0)
    before_metafield_source = str(suggestion.get("metafields_source", "") or "").strip().lower()
    accepted = _click_accept_all(page, post_click_wait_ms=args.post_click_wait_ms)
    after_accept_state = _extract_category_section_state(page)
    accept_unsaved_appeared = _has_unsaved_changes(page)
    accept_effective = bool(
        accepted and (
            accept_unsaved_appeared
            or (
                after_accept_state.get("current_value", "")
                and after_accept_state.get("current_value", "") != before_accept_state.get("current_value", "")
            )
            or (
                before_accept_state.get("suggestion_text", "")
                and after_accept_state.get("suggestion_text", "") != before_accept_state.get("suggestion_text", "")
            )
            or before_metafield_suggestion_count > 0
        )
    )
    category_suggestion = {
        "clicked": False,
        "clicked_text": "",
        "changed": False,
        "before_value": "",
        "after_value": "",
        "reason": "not_attempted",
        "unsaved_appeared": accept_unsaved_appeared,
    }
    if not accepted or (expected_category_value and not _category_value_matches_expected(after_accept_state.get("current_value", ""), expected_category_value)):
        category_suggestion = _click_category_suggestion(page, post_click_wait_ms=args.post_click_wait_ms)
    save_needed = bool(
        accepted
        or category_suggestion["clicked"]
        or _has_unsaved_changes(page)
        or accept_effective
    )
    saved = _click_submit_or_save(page, post_save_wait_ms=args.post_save_wait_ms) if save_needed else False

    verification = {
        "save_completed": False,
        "refreshed_value": "",
        "matched_expected": False,
        "changed_from_previous": False,
        "verification_status": "not_attempted",
        "frontend_signal_after_reload": False,
        "metafield_verification_passed": False,
    }
    if save_needed and saved:
        save_completed = not _has_unsaved_changes(page)
        if not save_completed:
            from workflow.apply_shopify_admin_accept_all_cli import _wait_for_save_settle

            save_completed = _wait_for_save_settle(
                page,
                timeout_ms=args.save_settle_time_out_ms if hasattr(args, "save_settle_time_out_ms") else args.save_settle_timeout_ms,
            )
        try:
            page.reload(wait_until=args.wait_until, timeout=args.goto_timeout_ms)
            refreshed = _extract_suggestions(page)
            refreshed_state = _extract_category_section_state(page)
            previous_value = before_accept_state.get("current_value", "")
            refreshed_value = refreshed_state.get("current_value", "")
            refreshed_suggestion_text = refreshed_state.get("suggestion_text", "")
            expected_value = str(category_suggestion.get("clicked_text") or expected_category_value or "").strip()
            category_changed = bool(refreshed_value) and refreshed_value != previous_value
            category_matches_expected = _category_value_matches_expected(refreshed_value, expected_value)
            refreshed_metafield_suggestion_count = int(refreshed.get("metafield_suggestion_count") or 0)
            refreshed_metafield_source = str(refreshed.get("metafields_source", "") or "").strip().lower()
            metafield_verification_passed = True
            if before_metafield_source == "suggestion" or before_metafield_suggestion_count > 0:
                metafield_verification_passed = (
                    refreshed_metafield_suggestion_count == 0
                    and refreshed_metafield_source != "suggestion"
                    and not refreshed.get("metafield_suggestion_section_found")
                )
            no_frontend_signal = not _has_frontend_signal(refreshed)
            category_verification_passed = True
            if expected_value:
                category_verification_passed = category_matches_expected or (
                    category_changed and not refreshed_suggestion_text
                )
            verification = {
                "save_completed": save_completed,
                "previous_value": previous_value,
                "expected_value": expected_value,
                "refreshed_value": refreshed_value,
                "refreshed_suggestion_text": refreshed_suggestion_text,
                "frontend_signal_after_reload": not no_frontend_signal,
                "matched_expected": category_matches_expected,
                "changed_from_previous": category_changed,
                "before_metafield_suggestion_count": before_metafield_suggestion_count,
                "refreshed_metafield_suggestion_count": refreshed_metafield_suggestion_count,
                "refreshed_metafield_source": refreshed_metafield_source,
                "metafield_verification_passed": metafield_verification_passed,
                "verification_status": (
                    "saved_successfully"
                    if save_completed and category_verification_passed and metafield_verification_passed and (no_frontend_signal or category_changed or category_matches_expected)
                    else ("save_not_completed" if not save_completed else "refreshed_value_unchanged")
                ),
            }
        except Exception as exc:
            verification = {
                "save_completed": save_completed,
                "previous_value": before_accept_state.get("current_value", ""),
                "expected_value": str(category_suggestion.get("clicked_text") or expected_category_value or "").strip(),
                "refreshed_value": "",
                "matched_expected": False,
                "changed_from_previous": False,
                "frontend_signal_after_reload": True,
                "metafield_verification_passed": False,
                "verification_status": "reload_failed",
                "verification_error": str(exc),
            }

    return {
        "accepted": accepted,
        "accept_effective": accept_effective,
        "accept_unsaved_appeared": accept_unsaved_appeared,
        "category_suggestion": category_suggestion,
        "save_needed": save_needed,
        "saved": saved,
        "verification": verification,
    }


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    _preflight_cdp_url(args.cdp_url)

    checkpoint_file = _default_checkpoint_file(args)
    if not checkpoint_file.is_absolute():
        checkpoint_file = (AGENT_ROOT / checkpoint_file).resolve()
    suggestions_file = Path(args.captured_suggestions_file).expanduser() if args.captured_suggestions_file else _default_suggestions_file(args)
    if not suggestions_file.is_absolute():
        suggestions_file = (AGENT_ROOT / suggestions_file).resolve()
    suggestions_log_file = _resolve_suggestions_log_file(suggestions_file)

    checkpoint = CheckpointStore(
        checkpoint_file,
        mode=args.mode,
        store_handle=args.store_handle,
        product_query=args.product_query,
        max_items=args.max_items,
    )
    if args.reset_checkpoint:
        checkpoint.reset()
    checkpoint.load_or_initialize(resume=not args.no_resume)
    resumed_ids = set(checkpoint.processed_product_ids())
    review_retry_ids: set[str] = set()
    if args.force_apply_review_items and checkpoint.result_file.exists():
        review_retry_ids = {
            str(item.get("product_id", "")).strip()
            for item in read_jsonl(checkpoint.result_file)
            if str(item.get("status", "")).strip() == "needs_manual_review"
        }
        review_retry_ids.discard("")
        if review_retry_ids:
            resumed_ids -= review_retry_ids

    urls = _load_urls(args)
    pending_urls = [url for url in urls if _extract_product_gid(url) not in resumed_ids]
    total_target = len(resumed_ids) + len(pending_urls)

    _print_line(f"检查点文件：{checkpoint.checkpoint_file}")
    _print_line(f"结果明细文件：{checkpoint.result_file}")
    _print_line(f"复核清单文件：{checkpoint.review_csv_file}")
    _print_line(f"失败清单文件：{checkpoint.failed_csv_file}")
    _print_line(f"审计报告文件：{checkpoint.audit_report_file}")
    _print_line(f"前端建议文件：{suggestions_log_file}")
    if resumed_ids:
        _print_line(f"检测到历史进度，已完成 {len(resumed_ids)} 个商品，本次将从断点继续执行。")
    else:
        _print_line("未检测到可恢复进度，本次将从头开始执行。")
    _print_line(
        f"开始执行 Shopify 全店商品分类建议闭环治理主链，模式：{args.mode}，"
        f"待处理商品：{len(pending_urls)} 个，累计目标商品：{total_target} 个。"
    )

    service = get_category_optimization_service()
    playwright = None
    holder = None
    page = None
    temp_dir = None
    try:
        playwright, holder, page, temp_dir = _open_browser_runtime(args)
        for offset, url in enumerate(pending_urls, start=1):
            overall_index = len(resumed_ids) + offset
            product_gid = _extract_product_gid(url)
            if not product_gid:
                continue

            _print_line(f"第 {overall_index}/{total_target} 个商品开始处理：{url}")
            try:
                _open_product_page(
                    page,
                    url,
                    progress_label=f"第 {overall_index}/{total_target} 个商品",
                    wait_until=args.wait_until,
                    goto_timeout_ms=args.goto_timeout_ms,
                    retry_count=args.retry_count,
                    retry_backoff_ms=args.retry_backoff_ms,
                )
            except Exception as exc:
                item = _build_open_failed_item(product_gid, url, str(exc))
                checkpoint.record_item(item)
                _print_line(f"第 {overall_index}/{total_target} 个商品页面打开失败，已记失败并继续。原因：{exc}")
                _cooldown_after_item(page, index=overall_index, page_delay_ms=args.page_delay_ms, batch_size=args.batch_size, batch_cooldown_ms=args.batch_cooldown_ms)
                continue

            suggestion = _extract_suggestions(page)
            suggestion["admin_url"] = url
            _append_captured_suggestion(suggestions_log_file, product_gid, suggestion)
            metafield_suggestion_count = int(
                suggestion.get("metafield_suggestion_count")
                or (
                    len(suggestion.get("metafields") or [])
                    if str(suggestion.get("metafields_source", "") or "").strip().lower() == "suggestion"
                    else 0
                )
            )
            _print_line(
                f"第 {overall_index}/{total_target} 个商品建议识别完成："
                f"类别建议：{suggestion.get('category_suggestion_text') or suggestion.get('category_full_name') or '无'}；"
                f"元字段建议数：{metafield_suggestion_count}。"
            )

            frontend_signal = _has_frontend_signal(suggestion)
            reliable_frontend_signal = _is_reliable_frontend_signal(suggestion)
            if frontend_signal and reliable_frontend_signal:
                _print_line(f"第 {overall_index}/{total_target} 个商品命中 Shopify 前端建议，优先走前端采纳链。")
                frontend_result = _attempt_frontend_chain(page, url=url, args=args, suggestion=suggestion)
                accepted = frontend_result["accepted"]
                category_suggestion = frontend_result["category_suggestion"]
                verification = frontend_result["verification"]
                saved = frontend_result["saved"]
                _print_frontend_diagnostics(
                    overall_index=overall_index,
                    total_target=total_target,
                    frontend_result=frontend_result,
                )

                if accepted and verification["verification_status"] == "saved_successfully":
                    item = {
                        "product_id": product_gid,
                        "title": "",
                        "admin_url": url,
                        "source": "shopify_frontend",
                        "status": "shopify_accept_all_saved",
                        "decision_reason": "已命中 Shopify 前端“全部接受”，保存成功并完成刷新复核。",
                        "save_completed": verification["save_completed"],
                        "category_value_refreshed": verification["refreshed_value"],
                    }
                    checkpoint.record_item(item)
                    _print_line(f"第 {overall_index}/{total_target} 个商品保存成功：已通过 Shopify 前端“全部接受”完成采纳并复核。")
                    _cooldown_after_item(page, index=overall_index, page_delay_ms=args.page_delay_ms, batch_size=args.batch_size, batch_cooldown_ms=args.batch_cooldown_ms)
                    continue

                if category_suggestion["clicked"] and verification["verification_status"] == "saved_successfully":
                    item = {
                        "product_id": product_gid,
                        "title": "",
                        "admin_url": url,
                        "source": "shopify_frontend",
                        "status": "shopify_category_suggestion_saved",
                        "decision_reason": "已命中 Shopify 类别建议条，保存成功并完成刷新复核。",
                        "category_suggestion_text": category_suggestion["clicked_text"],
                        "category_value_before": category_suggestion["before_value"],
                        "category_value_after": category_suggestion["after_value"],
                        "category_value_refreshed": verification["refreshed_value"],
                        "save_completed": verification["save_completed"],
                    }
                    checkpoint.record_item(item)
                    _print_line(
                        f"第 {overall_index}/{total_target} 个商品保存成功：类别建议 {category_suggestion['clicked_text']} 已采纳；"
                        f"刷新后类别：{verification['refreshed_value']}。"
                    )
                    _cooldown_after_item(page, index=overall_index, page_delay_ms=args.page_delay_ms, batch_size=args.batch_size, batch_cooldown_ms=args.batch_cooldown_ms)
                    continue

                if verification["verification_status"] == "reload_failed":
                    _print_line(
                        f"第 {overall_index}/{total_target} 个商品前端建议已执行，但刷新复核失败："
                        f"{verification.get('verification_error', 'unknown error')}；"
                        "将自动回退到 Shopify 数据 + DeepSeek 决策链。"
                    )
                else:
                    _print_line(
                        f"第 {overall_index}/{total_target} 个商品前端建议未形成稳定闭环，"
                        f"将自动回退到 Shopify 数据 + DeepSeek 决策链。"
                    )
            else:
                _print_line(f"第 {overall_index}/{total_target} 个商品未识别到 Shopify 前端建议，回退到 Shopify 数据 + DeepSeek 决策链。")

            if frontend_signal and not reliable_frontend_signal:
                _print_line(
                    f"第 {overall_index}/{total_target} 个商品识别到前端建议，但建议文本不够干净，"
                    "已跳过前端自动采纳，直接回退到 Shopify 数据 + DeepSeek 复判链。"
                )

            request = _build_request(args, product_id=product_gid, suggestion=suggestion if frontend_signal else {})
            try:
                backend_item = service.run_single_product(request, product_id=product_gid)
            except Exception as exc:
                item = _build_open_failed_item(product_gid, url, f"backend_fallback_failed: {exc}")
                checkpoint.record_item(item)
                _print_line(f"第 {overall_index}/{total_target} 个商品后端回退失败，已记录失败并继续：{exc}")
            else:
                if backend_item is None:
                    item = _build_open_failed_item(product_gid, url, "run_single_product returned empty result")
                    checkpoint.record_item(item)
                    _print_line(f"第 {overall_index}/{total_target} 个商品后端回退失败，未读到商品对象。")
                else:
                    item = _build_backend_result_item(backend_item, url=url)
                    if frontend_signal and item["status"] == "no_suggestion_no_change" and not args.force_apply_review_items:
                        item = _build_review_item(
                            product_gid,
                            url,
                            "存在 Shopify 前端建议，但前端采纳未闭环且后端回退未形成有效变更，需人工复核。",
                            suggestion,
                            backend_item=item,
                            frontend_result=frontend_result if frontend_signal and reliable_frontend_signal else None,
                        )
                    checkpoint.record_item(item)
                    _print_line(
                        f"第 {overall_index}/{total_target} 个商品后端链处理完成："
                        f"来源：{item.get('source', '')}；状态：{item.get('status', '')}；"
                        f"说明：{item.get('decision_reason', '') or '无'}。"
                    )

            _cooldown_after_item(
                page,
                index=overall_index,
                page_delay_ms=args.page_delay_ms,
                batch_size=args.batch_size,
                batch_cooldown_ms=args.batch_cooldown_ms,
            )
    except KeyboardInterrupt:
        checkpoint.mark_interrupted()
        _print_line("用户已中断主链执行，检查点已保存。下次运行同一命令即可从断点继续。")
        raise SystemExit(130)
    finally:
        if playwright is not None and holder is not None:
            try:
                holder.close()
            finally:
                try:
                    playwright.stop()
                finally:
                    if temp_dir and temp_dir.exists():
                        shutil.rmtree(temp_dir, ignore_errors=True)

    checkpoint.mark_finished()
    _print_line(checkpoint.data.get("summary", ""))
    _print_line("主链检查点、结果明细、复核清单和审计报告已更新完成。")


if __name__ == "__main__":
    main()
