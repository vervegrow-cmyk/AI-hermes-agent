from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys
from typing import Any

AGENT_ROOT = Path(__file__).resolve().parents[1]
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from models.category_sync import CategorySyncRequest
from service.category_optimization_service import get_category_optimization_service
from workflow.batch_io import read_json, write_json
from workflow.capture_shopify_admin_suggestions_cli import (
    _build_cloned_user_data_dir,
    _build_urls_from_shopify,
    _cooldown_after_item,
    _extract_product_gid,
    _extract_suggestions,
    _open_product_page,
    _require_playwright,
)
from workflow.run_category_optimization_cli import (
    CheckpointStore,
    ProgressPrinter,
    _print_line,
    _slugify,
)


def _default_checkpoint_file(args: argparse.Namespace) -> Path:
    runs_dir = AGENT_ROOT / "workflow" / "runs"
    if args.store_handle and not args.product_query and not args.product_id and not args.product_url and not args.product_urls_file:
        scope = "all-products"
    else:
        scope = _slugify(args.product_query) if args.product_query else "streaming"
    return runs_dir / f"category-optimization-streaming-{args.mode}-{scope}.checkpoint.json"


def _default_suggestions_file(args: argparse.Namespace) -> Path:
    runs_dir = AGENT_ROOT / "workflow" / "runs"
    if args.store_handle and not args.product_query and not args.product_id and not args.product_url and not args.product_urls_file:
        scope = "all-products"
    else:
        scope = _slugify(args.product_query) if args.product_query else "streaming"
    return runs_dir / f"shopify-admin-suggestions-streaming-{scope}.json"


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
    if explicit_product_ids:
        if not args.store_handle:
            raise SystemExit("使用 --product-id 进行前端建议抓取时，必须同时提供 --store-handle。")
        for product_gid in explicit_product_ids:
            urls.append(_product_gid_to_admin_url(product_gid, args.store_handle))

    if args.store_handle:
        urls.extend(_build_urls_from_shopify(args.store_handle, args.product_query, args.max_items))

    deduped: list[str] = []
    seen: set[str] = set()
    for url in urls:
        if url not in seen:
            seen.add(url)
            deduped.append(url)

    if not deduped:
        raise SystemExit("请至少提供 --store-handle、--product-url、--product-urls-file 或 --product-id 其中之一。")

    if args.max_items and args.max_items > 0:
        return deduped[: args.max_items]
    return deduped


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


def _build_fetch_failed_item(product_id: str, error_message: str, mode: str) -> dict[str, Any]:
    return {
        "product_id": product_id,
        "title": "",
        "vendor": "",
        "product_type": "",
        "current_category": {"id": "", "name": "", "full_name": ""},
        "current_metafields": [],
        "rollback_snapshot": {"category": {"id": "", "name": "", "full_name": ""}, "metafields": []},
        "suggested_category": {"id": "", "name": "", "full_name": ""},
        "suggested_metafields": [],
        "source": "system",
        "risk_level": "high",
        "needs_review": False,
        "decision_reason": "无法从 Shopify 读取该商品，已记录失败并继续处理后续商品。",
        "candidate_categories": [],
        "apply_result": {
            "mode": mode,
            "category_updated": False,
            "metafields_updated": 0,
            "skipped_metafields": [],
            "errors": [
                {
                    "scope": "product_fetch",
                    "reason": "shopify_product_not_found",
                    "detail": error_message,
                }
            ],
            "written_metafields": [],
            "rollback_ready": False,
            "status": "apply_failed",
        },
    }


def _capture_single_suggestion(
    page,
    *,
    url: str,
    index: int,
    total: int,
    args: argparse.Namespace,
) -> dict[str, Any]:
    _open_product_page(
        page,
        url,
        progress_label=f"第 {index}/{total} 个商品",
        wait_until=args.wait_until,
        goto_timeout_ms=args.goto_timeout_ms,
        retry_count=args.retry_count,
        retry_backoff_ms=args.retry_backoff_ms,
    )
    suggestion = _extract_suggestions(page)
    suggestion["admin_url"] = url
    return suggestion


def _open_browser_runtime(args: argparse.Namespace) -> tuple[Any, Any, Any, Path | None]:
    sync_playwright, _ = _require_playwright()
    playwright = sync_playwright().start()
    cloned_user_data_dir: Path | None = None

    if args.cdp_url:
        browser = playwright.chromium.connect_over_cdp(args.cdp_url)
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.new_page()
        return playwright, browser, page, None

    if args.chrome_user_data_dir:
        user_data_dir = Path(args.chrome_user_data_dir).expanduser()
        if not user_data_dir.is_absolute():
            user_data_dir = (AGENT_ROOT / user_data_dir).resolve()
        if not user_data_dir.exists():
            playwright.stop()
            raise SystemExit(f"未找到浏览器用户数据目录：{user_data_dir}")
        cloned_user_data_dir = _build_cloned_user_data_dir(user_data_dir, args.chrome_profile_directory)
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(cloned_user_data_dir),
            channel=args.browser_channel,
            headless=not args.headed,
            args=[f"--profile-directory={args.chrome_profile_directory}"],
        )
        page = context.new_page()
        return playwright, context, page, cloned_user_data_dir

    storage_state = Path(args.storage_state).expanduser()
    if not storage_state.is_absolute():
        storage_state = (AGENT_ROOT / storage_state).resolve()
    if not storage_state.exists():
        playwright.stop()
        raise SystemExit(
            "未提供可用的浏览器登录态。请提供 --cdp-url、--chrome-user-data-dir 或 --storage-state。"
        )
    browser = playwright.chromium.launch(headless=not args.headed)
    context = browser.new_context(storage_state=str(storage_state))
    page = context.new_page()
    return playwright, context, page, None


def _close_browser_runtime(playwright: Any, holder: Any, temp_dir: Path | None) -> None:
    try:
        holder.close()
    finally:
        try:
            playwright.stop()
        finally:
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture Shopify admin suggestions and execute category optimization one product at a time."
    )
    parser.add_argument("--mode", choices=["dry-run", "apply"], default="dry-run", help="执行模式")
    parser.add_argument("--store-handle", default="", help="Shopify Admin store handle，例如 getbulkdeals")
    parser.add_argument("--product-query", default="", help="按 Shopify 商品 query 逐个抓取并执行")
    parser.add_argument("--candidate-category", default="", help="可选候选类目提示")
    parser.add_argument("--max-items", type=int, default=0, help="最大处理商品数，0 表示不限")
    parser.add_argument("--product-id", action="append", default=[], help="指定 Shopify Product GID，可重复传入")
    parser.add_argument("--product-url", action="append", default=[], help="指定单个 Shopify 商品编辑页 URL，可重复传入")
    parser.add_argument("--product-urls-file", default="", help="包含多个 Shopify 商品编辑页 URL 的文本文件")
    parser.add_argument("--store-name", default="", help="店铺域名，默认使用共享环境变量")
    parser.add_argument("--no-apply-metafields", action="store_true", help="apply 模式下不写回元字段")
    parser.add_argument("--force-apply-review-items", action="store_true", help="高风险或原本待人工复核的后端决策也直接写回 Shopify，不再进入人工复核")
    parser.add_argument("--checkpoint-file", default="", help="检查点文件路径，默认自动生成")
    parser.add_argument("--no-resume", action="store_true", help="本次执行不读取已有检查点")
    parser.add_argument("--reset-checkpoint", action="store_true", help="执行前重置检查点和结果文件")
    parser.add_argument(
        "--captured-suggestions-file",
        default="",
        help="流式抓取过程中持续落盘的 Shopify 前端建议 JSON 文件",
    )
    parser.add_argument("--storage-state", default="", help="Playwright 登录态文件路径")
    parser.add_argument("--chrome-user-data-dir", default="", help="本地浏览器用户数据目录")
    parser.add_argument("--chrome-profile-directory", default="Default", help="浏览器 Profile 名称")
    parser.add_argument("--browser-channel", default="chrome", choices=["chrome", "msedge"], help="浏览器通道")
    parser.add_argument("--cdp-url", default="", help="连接已打开浏览器的 CDP 地址，例如 http://127.0.0.1:9222")
    parser.add_argument("--goto-timeout-ms", type=int, default=120000, help="商品页打开超时时间")
    parser.add_argument(
        "--wait-until",
        default="domcontentloaded",
        choices=["domcontentloaded", "load", "networkidle", "commit"],
        help="页面跳转等待策略",
    )
    parser.add_argument("--page-delay-ms", type=int, default=8000, help="每个商品完成后的常规等待时间")
    parser.add_argument("--retry-count", type=int, default=3, help="打开商品页失败时的重试次数")
    parser.add_argument("--retry-backoff-ms", type=int, default=15000, help="每次重试前的等待时间")
    parser.add_argument("--batch-size", type=int, default=20, help="连续处理多少个商品后进入一轮冷却")
    parser.add_argument("--batch-cooldown-ms", type=int, default=60000, help="批次冷却时间")
    parser.add_argument("--headed", action="store_true", help="使用有头浏览器")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    checkpoint_file = Path(args.checkpoint_file).expanduser() if args.checkpoint_file else _default_checkpoint_file(args)
    if not checkpoint_file.is_absolute():
        checkpoint_file = (AGENT_ROOT / checkpoint_file).resolve()
    checkpoint = CheckpointStore(
        checkpoint_file,
        mode=args.mode,
        product_query=args.product_query,
        max_items=args.max_items,
        apply_metafields=not args.no_apply_metafields,
        store_name=args.store_name,
    )
    if args.reset_checkpoint:
        checkpoint.reset()

    checkpoint.load_or_initialize(resume=not args.no_resume)
    resumed_ids = set(checkpoint.processed_product_ids())

    suggestions_file = (
        Path(args.captured_suggestions_file).expanduser()
        if args.captured_suggestions_file
        else _default_suggestions_file(args)
    )
    if not suggestions_file.is_absolute():
        suggestions_file = (AGENT_ROOT / suggestions_file).resolve()
    captured_suggestions = read_json(suggestions_file) if suggestions_file.exists() else {}

    _print_line(f"检查点文件：{checkpoint.checkpoint_file}")
    _print_line(f"结果明细文件：{checkpoint.result_file}")
    _print_line(f"复核清单文件：{checkpoint.review_csv_file}")
    _print_line(f"失败清单文件：{checkpoint.failed_csv_file}")
    _print_line(f"审计报告文件：{checkpoint.audit_report_file}")
    _print_line(f"流式建议文件：{suggestions_file}")
    if resumed_ids:
        _print_line(f"检测到历史进度，已完成 {len(resumed_ids)} 个商品，本次将从断点继续执行。")
    else:
        _print_line("未检测到可恢复进度，本次将从头开始执行。")

    all_urls = _load_urls(args)
    pending_urls: list[str] = []
    skipped_without_gid = 0
    for url in all_urls:
        product_gid = _extract_product_gid(url)
        if not product_gid:
            skipped_without_gid += 1
            continue
        if product_gid in resumed_ids:
            continue
        pending_urls.append(url)

    if skipped_without_gid:
        _print_line(f"有 {skipped_without_gid} 个商品链接未能解析出 product gid，已自动跳过。")

    total_overall = len(resumed_ids) + len(pending_urls)
    _print_line(
        f"开始执行流式分类优化任务，模式：{args.mode}，待处理商品：{len(pending_urls)} 个，"
        f"累计目标商品：{total_overall} 个。"
    )

    if not pending_urls:
        summary = (
            f"本次以 {args.mode} 模式处理了 {checkpoint.data.get('processed_count', 0)} 个 Shopify 商品，"
            f"其中 {checkpoint.data.get('applied_count', 0)} 个已修改，"
            f"{checkpoint.data.get('review_count', 0)} 个需要人工复核。"
        )
        checkpoint.mark_finished(summary)
        _print_line("没有新的待处理商品，本次无需继续执行。")
        _print_line(f"任务摘要：{summary}")
        return

    service = get_category_optimization_service()
    printer = ProgressPrinter(checkpoint=checkpoint)

    if args.cdp_url:
        _print_line(f"当前使用已打开浏览器连接：{args.cdp_url}")
    elif args.chrome_user_data_dir:
        _print_line(
            f"当前使用浏览器资料目录：{args.chrome_user_data_dir}；"
            f"Profile：{args.chrome_profile_directory}；通道：{args.browser_channel}"
        )
    else:
        _print_line(f"当前使用 Playwright 登录态文件：{args.storage_state}")

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

            suggestion_payload: dict[str, Any] = {}
            try:
                suggestion_payload = _capture_single_suggestion(
                    page,
                    url=url,
                    index=overall_index,
                    total=total_overall,
                    args=args,
                )
                captured_suggestions[product_gid] = suggestion_payload
                write_json(suggestions_file, captured_suggestions)
                _print_line(
                    f"第 {overall_index}/{total_overall} 个商品前端建议抓取完成："
                    f"类别建议：{suggestion_payload.get('category_suggestion_text') or suggestion_payload.get('category_full_name') or '未识别'}；"
                    f"类别元字段建议数：{len(suggestion_payload.get('metafields') or [])}。"
                )
            except Exception as exc:
                _print_line(
                    f"第 {overall_index}/{total_overall} 个商品前端建议抓取失败，"
                    f"本次将自动回退到 Shopify 数据 + DeepSeek 决策链。原因：{exc}"
                )
                suggestion_payload = {}

            request = _build_request(args, product_id=product_gid, suggestion=suggestion_payload)
            item = service.run_single_product(request, product_id=product_gid)
            if item is None:
                item = _build_fetch_failed_item(product_gid, "product lookup returned empty result", args.mode)

            printer(
                {
                    "event": "item",
                    "index": overall_index,
                    "total": total_overall,
                    "item": item,
                }
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
        _print_line("用户已中断流式执行，检查点已保存，下次可直接续跑。")
        raise SystemExit(130)
    finally:
        if playwright is not None and holder is not None:
            _close_browser_runtime(playwright, holder, temp_dir)

    summary = (
        f"本次以 {args.mode} 模式处理了 {checkpoint.data.get('processed_count', 0)} 个 Shopify 商品，"
        f"其中 {checkpoint.data.get('applied_count', 0)} 个已修改，"
        f"{checkpoint.data.get('review_count', 0)} 个需要人工复核。"
    )
    checkpoint.mark_finished(summary)
    _print_line(
        f"任务完成：共处理 {checkpoint.data.get('processed_count', 0)} 个商品，"
        f"成功修改 {checkpoint.data.get('applied_count', 0)} 个，"
        f"需要人工复核 {checkpoint.data.get('review_count', 0)} 个。"
    )
    _print_line(f"任务摘要：{summary}")
    _print_line("检查点已更新完成。如需重新从头跑，请在命令后加 --reset-checkpoint。")


if __name__ == "__main__":
    main()
