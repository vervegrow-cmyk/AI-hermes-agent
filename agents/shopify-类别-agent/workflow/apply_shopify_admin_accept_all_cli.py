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

from workflow.batch_io import append_jsonl, read_json, write_json
from workflow.capture_shopify_admin_suggestions_cli import (
    _build_cloned_user_data_dir,
    _build_urls_from_shopify,
    _cooldown_after_item,
    _extract_product_gid,
    _open_product_page,
    _require_playwright,
)


def _now_label() -> str:
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _print_line(message: str) -> None:
    print(f"[{_now_label()}] {message}", flush=True)


def _slugify(value: str) -> str:
    import re

    return re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower()).strip("-")


def _default_checkpoint_file(args: argparse.Namespace) -> Path:
    runs_dir = AGENT_ROOT / "workflow" / "runs"
    if args.store_handle:
        scope = _slugify(args.product_query) if args.product_query else "all-products"
    elif args.product_url:
        scope = f"manual-{len(args.product_url)}-products"
    elif args.product_urls_file:
        scope = f"manual-file-{Path(args.product_urls_file).stem}"
    else:
        scope = "manual-run"
    return runs_dir / f"shopify-admin-accept-all-{scope}.checkpoint.json"


class CheckpointStore:
    def __init__(
        self,
        checkpoint_file: Path,
        *,
        store_handle: str,
        product_query: str,
        max_items: int,
        output_file: Path,
    ) -> None:
        self.checkpoint_file = checkpoint_file
        self.result_file = output_file
        self.store_handle = store_handle
        self.product_query = product_query
        self.max_items = max_items
        self.data: dict[str, Any] = {}

    def reset(self) -> None:
        for path in [self.checkpoint_file, self.result_file]:
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
            "store_handle": self.store_handle,
            "product_query": self.product_query,
            "max_items": self.max_items,
            "started_at": _now_label(),
            "updated_at": _now_label(),
            "processed_count": 0,
            "saved_count": 0,
            "skipped_count": 0,
            "failed_count": 0,
            "processed_product_ids": [],
            "files": {
                "checkpoint": str(self.checkpoint_file),
                "results_jsonl": str(self.result_file),
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
        if status in {"applied", "category_suggestion_applied"}:
            self.data["saved_count"] = int(self.data.get("saved_count", 0)) + 1
        elif status in {
            "no_accept_button",
            "accepted_not_saved",
            "category_suggestion_clicked_not_saved",
            "category_suggestion_save_not_completed",
            "category_suggestion_refreshed_value_unchanged",
        }:
            self.data["skipped_count"] = int(self.data.get("skipped_count", 0)) + 1
        elif status == "open_failed":
            self.data["failed_count"] = int(self.data.get("failed_count", 0)) + 1

        self.data["updated_at"] = _now_label()
        append_jsonl(self.result_file, item)
        self._save()

    def mark_interrupted(self) -> None:
        self.data["status"] = "interrupted"
        self.data["updated_at"] = _now_label()
        self.data["summary"] = (
            f"任务已中断，当前已处理 {self.data.get('processed_count', 0)} 个商品，"
            f"保存成功 {self.data.get('saved_count', 0)} 个，"
            f"跳过 {self.data.get('skipped_count', 0)} 个，失败 {self.data.get('failed_count', 0)} 个。"
        )
        self._save()

    def mark_finished(self) -> None:
        self.data["status"] = "completed"
        self.data["updated_at"] = _now_label()
        self.data["summary"] = (
            f"任务完成：共处理 {self.data.get('processed_count', 0)} 个商品，"
            f"保存成功 {self.data.get('saved_count', 0)} 个，"
            f"跳过 {self.data.get('skipped_count', 0)} 个，失败 {self.data.get('failed_count', 0)} 个。"
        )
        self._save()

    def _validate_compatibility(self) -> None:
        mismatches = []
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

    def _save(self) -> None:
        write_json(self.checkpoint_file, self.data)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Accept Shopify admin suggestions by clicking the visible '全部接受' button and saving the product page."
    )
    parser.add_argument("--product-url", action="append", default=[], help="单个 Shopify 商品编辑页 URL，可重复传入")
    parser.add_argument("--product-urls-file", default="", help="包含多个 Shopify 商品编辑页 URL 的文本文件")
    parser.add_argument("--store-handle", default="", help="Shopify Admin store handle，例如 getbulkdeals")
    parser.add_argument("--product-query", default="", help="自动扫描商品页时使用的 Shopify query")
    parser.add_argument("--max-items", type=int, default=0, help="最大处理商品数，0 表示不限")
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
    parser.add_argument("--retry-count", type=int, default=3, help="打开商品页失败时的重试次数")
    parser.add_argument("--retry-backoff-ms", type=int, default=15000, help="每次重试前的等待时间")
    parser.add_argument("--page-delay-ms", type=int, default=12000, help="每个商品完成后的常规等待时间")
    parser.add_argument("--batch-size", type=int, default=5, help="连续处理多少个商品后进入一轮冷却")
    parser.add_argument("--batch-cooldown-ms", type=int, default=120000, help="批次冷却时间")
    parser.add_argument("--post-click-wait-ms", type=int, default=1500, help="点击全部接受后等待时间")
    parser.add_argument("--post-save-wait-ms", type=int, default=4000, help="点击提交/保存后等待时间")
    parser.add_argument("--save-settle-timeout-ms", type=int, default=30000, help="点击保存后等待未保存状态消失的最长时间")
    parser.add_argument("--checkpoint-file", default="", help="检查点文件路径，默认自动生成")
    parser.add_argument("--reset-checkpoint", action="store_true", help="执行前重置检查点和结果文件")
    parser.add_argument("--no-resume", action="store_true", help="禁用断点续跑，每次都从头开始")
    parser.add_argument("--output-file", default="workflow/runs/shopify-admin-accept-all-results.jsonl", help="结果 JSONL 文件")
    parser.add_argument("--headed", action="store_true", help="使用有头浏览器")
    return parser


def _load_urls(args: argparse.Namespace) -> list[str]:
    urls = list(args.product_url or [])
    if args.product_urls_file:
        file_path = Path(args.product_urls_file).expanduser()
        if not file_path.is_absolute():
            file_path = (AGENT_ROOT / file_path).resolve()
        urls.extend([line.strip() for line in file_path.read_text(encoding="utf-8").splitlines() if line.strip()])
    if args.store_handle:
        urls.extend(_build_urls_from_shopify(args.store_handle, args.product_query, args.max_items))
    deduped: list[str] = []
    seen: set[str] = set()
    for url in urls:
        if url and url not in seen:
            seen.add(url)
            deduped.append(url)
    if not deduped:
        raise SystemExit("请至少提供 --product-url、--product-urls-file 或 --store-handle 其中之一。")
    if args.max_items and args.max_items > 0:
        return deduped[: args.max_items]
    return deduped


def _open_browser_runtime(args: argparse.Namespace) -> tuple[Any, Any, Any, Path | None]:
    sync_playwright, _ = _require_playwright()
    playwright = sync_playwright().start()
    cloned_user_data_dir: Path | None = None

    if args.cdp_url:
        try:
            browser = playwright.chromium.connect_over_cdp(args.cdp_url)
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.new_page()
            return playwright, browser, page, None
        except Exception as exc:
            playwright.stop()
            raise SystemExit(
                "未能连接到已打开浏览器的 CDP 地址："
                f"{args.cdp_url}。请先启动带 `--remote-debugging-port` 的 Chrome / Edge，"
                "并确认该端口仍可访问后再重试。"
                f" 原始错误：{exc}"
            ) from exc

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
        raise SystemExit("未提供可用的浏览器登录态。请提供 --cdp-url、--chrome-user-data-dir 或 --storage-state。")
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


def _click_accept_all(page, *, post_click_wait_ms: int) -> bool:
    candidates = [
        page.get_by_text("全部接受", exact=True).first,
        page.locator('button:has-text("全部接受")').first,
        page.locator('text="全部接受"').first,
    ]
    for locator in candidates:
        try:
            if locator.count() == 0 or not locator.is_visible(timeout=1000):
                continue
            locator.scroll_into_view_if_needed(timeout=2000)
            locator.click(timeout=3000, force=True)
            page.wait_for_timeout(post_click_wait_ms)
            return True
        except Exception:
            continue
    return False


def _click_accept_all(page, *, post_click_wait_ms: int) -> bool:
    before_unsaved = _has_unsaved_changes(page)
    before_snapshot = page.evaluate(
        """
        () => {
          const clean = (value) => (value || '').replace(/\\s+/g, ' ').trim();
          return Array.from(document.querySelectorAll('button, [role="button"]'))
            .map((node) => clean(node.innerText || node.textContent || node.getAttribute?.('aria-label') || ''))
            .filter((text) => text && text.includes('全部接受'))
            .join(' | ');
        }
        """
    )

    clicked = False
    candidates = [
        page.locator('button[aria-label*="全部接受"]').first,
        page.locator('[role="button"][aria-label*="全部接受"]').first,
        page.get_by_text("鍏ㄩ儴鎺ュ彈", exact=True).first,
        page.locator('button:has-text("鍏ㄩ儴鎺ュ彈")').first,
        page.locator('text="鍏ㄩ儴鎺ュ彈"').first,
    ]
    for locator in candidates:
        try:
            if locator.count() == 0 or not locator.is_visible(timeout=1000):
                continue
            locator.scroll_into_view_if_needed(timeout=2000)
            try:
                locator.hover(timeout=1500)
            except Exception:
                pass
            locator.click(timeout=3000, force=True)
            clicked = True
            break
        except Exception:
            continue

    if not clicked:
        clicked = bool(
            page.evaluate(
                """
                () => {
                  const clean = (value) => (value || '').replace(/\\s+/g, ' ').trim();
                  const isVisible = (node) => {
                    if (!node) return false;
                    const style = window.getComputedStyle(node);
                    if (style.visibility === 'hidden' || style.display === 'none') return false;
                    const rect = node.getBoundingClientRect();
                    return rect.width > 0 && rect.height > 0;
                  };
                  const robustClick = (node) => {
                    try { node.scrollIntoView({ block: 'center', inline: 'center' }); } catch (error) {}
                    try { node.focus?.(); } catch (error) {}
                    for (const [eventName, Ctor] of [
                      ['pointerdown', PointerEvent],
                      ['mousedown', MouseEvent],
                      ['pointerup', PointerEvent],
                      ['mouseup', MouseEvent],
                      ['click', MouseEvent],
                    ]) {
                      try {
                        node.dispatchEvent(new Ctor(eventName, { bubbles: true, cancelable: true, view: window }));
                      } catch (error) {}
                    }
                    try { node.click?.(); } catch (error) {}
                    return true;
                  };
                  const nodes = Array.from(document.querySelectorAll('button, [role="button"]'))
                    .filter((node) => isVisible(node))
                    .filter((node) => clean(node.innerText || node.textContent || node.getAttribute('aria-label') || '').includes('全部接受'));
                  if (!nodes.length) return false;
                  return robustClick(nodes[0]);
                }
                """
            )
        )

    if not clicked:
        return False

    page.wait_for_timeout(post_click_wait_ms)
    after_unsaved = _has_unsaved_changes(page)
    after_snapshot = page.evaluate(
        """
        () => {
          const clean = (value) => (value || '').replace(/\\s+/g, ' ').trim();
          return Array.from(document.querySelectorAll('button, [role="button"]'))
            .map((node) => clean(node.innerText || node.textContent || node.getAttribute?.('aria-label') || ''))
            .filter((text) => text && text.includes('全部接受'))
            .join(' | ');
        }
        """
    )
    return after_unsaved or (not before_unsaved and after_snapshot != before_snapshot)


def _click_submit_or_save(page, *, post_save_wait_ms: int) -> bool:
    def _try_locator_click(locator) -> bool:
        try:
            if locator.count() == 0 or not locator.is_visible(timeout=1000):
                return False
            locator.scroll_into_view_if_needed(timeout=2000)
            locator.hover(timeout=2000)
            locator.click(timeout=3000, force=True)
            page.wait_for_timeout(post_save_wait_ms)
            return True
        except Exception:
            return False

    top_bar_candidates = [
        page.locator('button:has-text("保存")').first,
        page.get_by_text("保存", exact=True).first,
        page.locator('button:has-text("提交")').first,
        page.get_by_text("提交", exact=True).first,
    ]
    for locator in top_bar_candidates:
        if _try_locator_click(locator):
            return True

    js_clicked = page.evaluate(
        """
        () => {
          const clean = (value) => (value || '').replace(/\\s+/g, ' ').trim();
          const isVisible = (node) => {
            if (!node) return false;
            const style = window.getComputedStyle(node);
            if (style.visibility === 'hidden' || style.display === 'none') return false;
            const rect = node.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0;
          };
          const buttons = Array.from(document.querySelectorAll('button, [role="button"]'))
            .filter((node) => isVisible(node))
            .map((node) => ({ node, text: clean(node.innerText || node.textContent || '') }))
            .filter((item) => item.text === '保存' || item.text === '提交');
          if (!buttons.length) {
            return false;
          }
          buttons.sort((a, b) => {
            const rectA = a.node.getBoundingClientRect();
            const rectB = b.node.getBoundingClientRect();
            return (rectA.top - rectB.top) || (rectB.right - rectA.right);
          });
          const target = buttons[0].node;
          target.scrollIntoView({ block: 'center', inline: 'center' });
          target.focus?.();
          target.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true, view: window }));
          target.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true, view: window }));
          target.click?.();
          return true;
        }
        """
    )
    if js_clicked:
        page.wait_for_timeout(post_save_wait_ms)
        return True

    keyboard_clicked = page.evaluate(
        """
        () => {
          const clean = (value) => (value || '').replace(/\\s+/g, ' ').trim();
          const isVisible = (node) => {
            if (!node) return false;
            const style = window.getComputedStyle(node);
            if (style.visibility === 'hidden' || style.display === 'none') return false;
            const rect = node.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0;
          };
          const buttons = Array.from(document.querySelectorAll('button, [role="button"]'))
            .filter((node) => isVisible(node))
            .map((node) => ({ node, text: clean(node.innerText || node.textContent || '') }))
            .filter((item) => item.text === '保存' || item.text === '提交');
          if (!buttons.length) {
            return false;
          }
          buttons.sort((a, b) => {
            const rectA = a.node.getBoundingClientRect();
            const rectB = b.node.getBoundingClientRect();
            return (rectA.top - rectB.top) || (rectB.right - rectA.right);
          });
          buttons[0].node.focus?.();
          return true;
        }
        """
    )
    if keyboard_clicked:
        try:
            page.keyboard.press("Enter")
            page.wait_for_timeout(post_save_wait_ms)
            return True
        except Exception:
            pass
    return False


def _has_unsaved_changes(page) -> bool:
    candidates = [
        page.get_by_text("未保存的更改", exact=True).first,
        page.locator('text="未保存的更改"').first,
    ]
    for locator in candidates:
        try:
            if locator.count() > 0 and locator.is_visible(timeout=500):
                return True
        except Exception:
            continue
    return False


def _wait_for_save_settle(page, *, timeout_ms: int) -> bool:
    deadline = __import__("time").time() + max(timeout_ms, 0) / 1000
    while __import__("time").time() < deadline:
        if not _has_unsaved_changes(page):
            return True
        page.wait_for_timeout(1000)
    return not _has_unsaved_changes(page)


def _extract_category_section_state(page) -> dict[str, str]:
    return page.evaluate(
        """
        () => {
          const clean = (value) => (value || '').replace(/\\s+/g, ' ').trim();
          const normalizeSuggestionText = (value) => {
            let text = clean(value);
            if (!text) {
              return '';
            }
            text = text
              .replace(/^\\d+\\s*条可用建议\\s*/i, '')
              .replace(/^\\d+\\s*条建议\\s*/i, '')
              .replace(/^接受建议的类别[:：]\\s*/i, '')
              .replace(/\\s*建议\\s*[×xX✕✖]?\\s*$/i, '')
              .replace(/[×xX✕✖]$/g, '')
              .trim();
            if (/^\\d+\\s*条(可用)?建议$/i.test(text)) {
              return '';
            }
            return text;
          };
          const linesFromSection = (section) => {
            const lines = clean(section?.innerText || '')
              .split(/\\n+/)
              .map((item) => clean(item))
              .filter(Boolean);
            return lines;
          };

          const findCategorySection = () => {
            const all = Array.from(document.querySelectorAll('div, section, form'));
            let best = null;
            let bestScore = -1;
            for (const node of all) {
              const text = clean(node.innerText || '');
              if (!text || !text.includes('类别')) {
                continue;
              }
              let score = 0;
              if (text.includes('选择产品类别')) score += 10;
              if (text.includes('建议')) score += 20;
              if (text.includes('元字段')) score -= 25;
              if (text.includes('确定税率并添加元字段')) score += 5;
              if (text.length > 800) score -= 10;
              if (score > bestScore) {
                best = node;
                bestScore = score;
              }
            }
            return best;
          };

          const section = findCategorySection();
          if (!section) {
            return { current_value: '', suggestion_text: '', section_text: '' };
          }

          const lines = linesFromSection(section);
          let currentValue = '';
          let suggestionText = '';

          const currentSelectors = [
            's-internal-single-picker-field-value',
            '[class*="SinglePickerFieldValue"]',
            '[class*="ValueWrapper"]',
            '[class*="CurrentValue"]',
            '[role="combobox"]',
            'button[aria-haspopup="listbox"]',
            'input',
          ];
          for (const selector of currentSelectors) {
            const nodes = Array.from(section.querySelectorAll(selector));
            for (const node of nodes) {
              const text = clean(
                node.value ||
                node.innerText ||
                node.textContent ||
                node.getAttribute?.('value') ||
                node.getAttribute?.('aria-label') ||
                ''
              );
              if (
                text &&
                text !== '类别' &&
                text !== '选择产品类别' &&
                !/条(可用)?建议/i.test(text) &&
                !text.includes('建议')
              ) {
                currentValue = text;
                break;
              }
            }
            if (currentValue) {
              break;
            }
          }

          const suggestionSelectors = [
            '[class*="SuggestionButtonStack"]',
            '[class*="MagicFieldSuggestion"]',
            '[class*="SuggestionButton"]',
            's-internal-picker-option[value^="gid://shopify/ProductTaxonomyNode/"]',
            '[role="option"]',
          ];
          for (const selector of suggestionSelectors) {
            const nodes = Array.from(section.querySelectorAll(selector));
            for (const node of nodes) {
              const text = normalizeSuggestionText(
                clean(node.innerText || node.textContent || node.getAttribute?.('aria-label') || '')
              );
              if (
                text &&
                text !== currentValue &&
                !text.includes('全部接受') &&
                !text.includes('确定税率并添加元字段')
              ) {
                suggestionText = text;
                break;
              }
            }
            if (suggestionText) {
              break;
            }
          }

          for (const line of lines) {
            if (!currentValue && line !== '类别' && !line.includes('建议') && !line.includes('确定税率并添加元字段')) {
              currentValue = line;
              continue;
            }
            if (!suggestionText && (line.includes('建议') || /条(可用)?建议/i.test(line)) && !line.includes('全部接受')) {
              const normalized = normalizeSuggestionText(line);
              if (normalized && normalized !== currentValue) {
                suggestionText = normalized;
              }
            }
          }
          return {
            current_value: currentValue,
            suggestion_text: suggestionText,
            section_text: clean(section.innerText || ''),
          };
        }
        """
    )


def _click_category_suggestion(page, *, post_click_wait_ms: int) -> dict[str, Any]:
    before = _extract_category_section_state(page)
    click_result = page.evaluate(
        """
        () => {
          const clean = (value) => (value || '').replace(/\\s+/g, ' ').trim();
          const normalizeSuggestionText = (value) => {
            let text = clean(value);
            if (!text) {
              return '';
            }
            text = text
              .replace(/^\\d+\\s*条可用建议\\s*/i, '')
              .replace(/^\\d+\\s*条建议\\s*/i, '')
              .replace(/^接受建议的类别[:：]\\s*/i, '')
              .replace(/\\s*建议\\s*[×xX✕✖]?\\s*$/i, '')
              .replace(/[×xX✕✖]$/g, '')
              .trim();
            if (/^\\d+\\s*条(可用)?建议$/i.test(text)) {
              return '';
            }
            return text;
          };

          const findCategorySection = () => {
            const all = Array.from(document.querySelectorAll('div, section, form'));
            let best = null;
            let bestScore = -1;
            for (const node of all) {
              const text = clean(node.innerText || '');
              if (!text || !text.includes('类别')) {
                continue;
              }
              let score = 0;
              if (text.includes('选择产品类别')) score += 10;
              if (text.includes('建议')) score += 20;
              if (text.includes('元字段')) score -= 25;
              if (text.includes('确定税率并添加元字段')) score += 5;
              if (text.length > 800) score -= 10;
              if (score > bestScore) {
                best = node;
                bestScore = score;
              }
            }
            return best;
          };

          const section = findCategorySection();
          if (!section) {
            return { clicked: false, clicked_text: '', reason: 'category_section_not_found' };
          }

          const candidates = [];
          const pushCandidate = (node, source) => {
            if (!node) {
              return;
            }
            const rawText = clean(node.innerText || node.textContent || node.getAttribute?.('aria-label') || '');
            const text = normalizeSuggestionText(rawText);
            if (!text || text === '类别' || text === '建议' || text.includes('全部接受')) {
              return;
            }
            if (/^\\d+\\s*条(可用)?建议$/i.test(rawText)) {
              return;
            }

            let clickable = node;
            for (let i = 0; i < 8 && clickable; i += 1) {
              const role = clickable.getAttribute?.('role') || '';
              const tag = (clickable.tagName || '').toLowerCase();
              const style = window.getComputedStyle(clickable);
              if (
                tag === 'button' ||
                tag === 'a' ||
                role === 'button' ||
                role === 'option' ||
                clickable.hasAttribute?.('tabindex') ||
                style.cursor === 'pointer'
              ) {
                break;
              }
              clickable = clickable.parentElement;
            }
            clickable = clickable || node;
            const html = clickable.outerHTML || node.outerHTML || '';
            let score = 0;
            if (source === 'suggestion-stack') score += 100;
            if (source === 'picker-option') score += 90;
            if (source === 'generic-suggestion') score += 40;
            if ((clickable.className || '').toString().includes('Suggestion')) score += 60;
            if ((node.className || '').toString().includes('Suggestion')) score += 40;
            if (/接受建议的类别/i.test(rawText)) score += 60;
            if (/gid:\\/\\/shopify\\/ProductTaxonomyNode\\//i.test(html)) score += 30;
            if (/tone=["']ai["']/i.test(html)) score += 20;
            if (/条可用建议|条建议/i.test(rawText)) score -= 100;
            candidates.push({ node, clickable, text, source, score });
          };

          for (const node of Array.from(section.querySelectorAll('[class*="SuggestionButtonStack"], [class*="MagicFieldSuggestion"], [class*="SuggestionButton"]'))) {
            pushCandidate(node, 'suggestion-stack');
          }
          for (const node of Array.from(section.querySelectorAll('s-internal-picker-option[value^="gid://shopify/ProductTaxonomyNode/"], [role="option"]'))) {
            pushCandidate(node, 'picker-option');
          }
          for (const node of Array.from(section.querySelectorAll('button, div, span, p, li'))) {
            const text = clean(node.innerText || node.textContent || '');
            if (text.includes('建议') || /接受建议的类别|条可用建议|条建议/i.test(text)) {
              pushCandidate(node, 'generic-suggestion');
            }
          }

          candidates.sort((a, b) => b.score - a.score || b.text.length - a.text.length);
          const target = candidates[0];
          if (!target) {
            return { clicked: false, clicked_text: '', reason: 'category_suggestion_not_found' };
          }

          target.clickable.scrollIntoView({ block: 'center', inline: 'center' });
          target.clickable.click();
          return {
            clicked: true,
            clicked_text: target.text,
            reason: `clicked:${target.source}`,
          };
        }
        """
    )
    page.wait_for_timeout(post_click_wait_ms)
    after = _extract_category_section_state(page)
    changed = bool(after.get("current_value")) and after.get("current_value") != before.get("current_value")
    suggestion_disappeared = bool(before.get("suggestion_text")) and after.get("suggestion_text") != before.get("suggestion_text")
    click_result["before_value"] = before.get("current_value", "")
    click_result["after_value"] = after.get("current_value", "")
    click_result["changed"] = changed or suggestion_disappeared
    click_result["after_suggestion_text"] = after.get("suggestion_text", "")
    return click_result


def _click_category_suggestion(page, *, post_click_wait_ms: int) -> dict[str, Any]:
    before = _extract_category_section_state(page)
    click_result = page.evaluate(
        """
        () => {
          const clean = (value) => (value || '').replace(/\\s+/g, ' ').trim();
          const normalizeSuggestionText = (value) => {
            let text = clean(value);
            if (!text) {
              return '';
            }
            text = text
              .replace(/^\\d+\\s*条可用建议[:：]?\\s*/i, '')
              .replace(/^\\d+\\s*条建议[:：]?\\s*/i, '')
              .replace(/^接受建议的类别[:：]\\s*/i, '')
              .replace(/\\s*建议\\s*[×xX]?\\s*$/i, '')
              .replace(/[×xX]$/g, '')
              .trim();
            if (/^\\d+\\s*条(可用)?建议$/i.test(text)) {
              return '';
            }
            return text;
          };

          const findCategorySection = () => {
            const all = Array.from(document.querySelectorAll('div, section, form'));
            let best = null;
            let bestScore = -1;
            for (const node of all) {
              const text = clean(node.innerText || '');
              if (!text || !text.includes('类别')) {
                continue;
              }
              let score = 0;
              if (text.includes('选择产品类别')) score += 10;
              if (text.includes('建议')) score += 20;
              if (text.includes('元字段')) score -= 25;
              if (text.includes('确定税率并添加元字段')) score += 5;
              if (text.length > 800) score -= 10;
              if (score > bestScore) {
                best = node;
                bestScore = score;
              }
            }
            return best;
          };

          const robustClick = (node) => {
            if (!node) return false;
            try { node.scrollIntoView({ block: 'center', inline: 'center' }); } catch (error) {}
            try { node.focus?.(); } catch (error) {}
            const events = [
              ['pointerdown', PointerEvent],
              ['mousedown', MouseEvent],
              ['pointerup', PointerEvent],
              ['mouseup', MouseEvent],
              ['click', MouseEvent],
            ];
            for (const [eventName, Ctor] of events) {
              try {
                node.dispatchEvent(new Ctor(eventName, { bubbles: true, cancelable: true, view: window }));
              } catch (error) {}
            }
            try { node.click?.(); } catch (error) {}
            return true;
          };

          const section = findCategorySection();
          if (!section) {
            return { clicked: false, clicked_text: '', reason: 'category_section_not_found' };
          }

          const candidates = [];
          const pushCandidate = (node, source) => {
            if (!node) return;
            const ariaLabel = clean(node.getAttribute?.('aria-label') || '');
            const rawText = clean(node.innerText || node.textContent || ariaLabel || '');
            const text = normalizeSuggestionText(rawText);
            if (!text || text === '类别' || text === '建议' || text.includes('全部接受')) {
              return;
            }
            if (/^\\d+\\s*条(可用)?建议$/i.test(rawText)) {
              return;
            }

            let clickable = node;
            for (let i = 0; i < 8 && clickable; i += 1) {
              const role = clickable.getAttribute?.('role') || '';
              const tag = (clickable.tagName || '').toLowerCase();
              const style = window.getComputedStyle(clickable);
              if (
                tag === 'button' ||
                tag === 'a' ||
                role === 'button' ||
                role === 'option' ||
                clickable.hasAttribute?.('tabindex') ||
                style.cursor === 'pointer'
              ) {
                break;
              }
              clickable = clickable.parentElement;
            }
            clickable = clickable || node;
            const html = clickable.outerHTML || node.outerHTML || '';
            let score = 0;
            if (source === 'accept-button') score += 1000;
            if (source === 'suggestion-stack') score += 100;
            if (source === 'picker-option') score += 90;
            if (source === 'generic-suggestion') score += 40;
            if ((clickable.className || '').toString().includes('Suggestion')) score += 60;
            if ((node.className || '').toString().includes('Suggestion')) score += 40;
            if (/接受建议的类别/i.test(rawText) || /接受建议的类别/i.test(ariaLabel)) score += 200;
            if (/gid:\\/\\/shopify\\/ProductTaxonomyNode\\//i.test(html)) score += 30;
            if (/tone=["']ai["']/i.test(html)) score += 20;
            if (/条可用建议|条建议/i.test(rawText)) score -= 100;
            candidates.push({ clickable, text, source, score, ariaLabel });
          };

          for (const node of Array.from(section.querySelectorAll('button[aria-label^="接受建议的类别"], [role="button"][aria-label^="接受建议的类别"]'))) {
            pushCandidate(node, 'accept-button');
          }
          for (const node of Array.from(section.querySelectorAll('[class*="SuggestionButtonStack"], [class*="MagicFieldSuggestion"], [class*="SuggestionButton"]'))) {
            pushCandidate(node, 'suggestion-stack');
          }
          for (const node of Array.from(section.querySelectorAll('s-internal-picker-option[value^="gid://shopify/ProductTaxonomyNode/"], [role="option"]'))) {
            pushCandidate(node, 'picker-option');
          }
          for (const node of Array.from(section.querySelectorAll('button, div, span, p, li'))) {
            const text = clean(node.innerText || node.textContent || '');
            if (text.includes('建议') || /接受建议的类别|条可用建议|条建议/i.test(text)) {
              pushCandidate(node, 'generic-suggestion');
            }
          }

          candidates.sort((a, b) => b.score - a.score || b.text.length - a.text.length);
          const target = candidates[0];
          if (!target) {
            return { clicked: false, clicked_text: '', reason: 'category_suggestion_not_found' };
          }

          const clicked = robustClick(target.clickable);
          return {
            clicked,
            clicked_text: target.text,
            clicked_aria_label: target.ariaLabel,
            reason: clicked ? `clicked:${target.source}` : `click_failed:${target.source}`,
          };
        }
        """
    )
    page.wait_for_timeout(post_click_wait_ms)
    after = _extract_category_section_state(page)
    changed = bool(after.get("current_value")) and after.get("current_value") != before.get("current_value")
    suggestion_disappeared = bool(before.get("suggestion_text")) and after.get("suggestion_text") != before.get("suggestion_text")
    unsaved_appeared = _has_unsaved_changes(page)
    click_result["before_value"] = before.get("current_value", "")
    click_result["after_value"] = after.get("current_value", "")
    click_result["changed"] = changed or suggestion_disappeared or unsaved_appeared
    click_result["after_suggestion_text"] = after.get("suggestion_text", "")
    click_result["unsaved_appeared"] = unsaved_appeared
    return click_result


def _click_accept_all(page, *, post_click_wait_ms: int) -> bool:
    before_unsaved = _has_unsaved_changes(page)
    before_snapshot = page.evaluate(
        """
        () => {
          const clean = (value) => (value || '').replace(/\\s+/g, ' ').trim();
          return Array.from(document.querySelectorAll('button, [role="button"]'))
            .map((node) => clean(node.innerText || node.textContent || node.getAttribute?.('aria-label') || ''))
            .filter((text) => text && text.includes('全部接受'))
            .join(' | ');
        }
        """
    )

    constClicked = []
    candidates = [
        page.locator('button[aria-label*="全部接受"]').first,
        page.locator('[role="button"][aria-label*="全部接受"]').first,
        page.get_by_text("全部接受", exact=True).first,
        page.locator('button:has-text("全部接受")').first,
        page.locator('[role="button"]:has-text("全部接受")').first,
        page.locator('text="全部接受"').first,
    ]
    for locator in candidates:
        try:
            if locator.count() == 0 or not locator.is_visible(timeout=1000):
                continue
            locator.scroll_into_view_if_needed(timeout=2000)
            try:
                locator.hover(timeout=1500)
            except Exception:
                pass
            locator.click(timeout=3000, force=True)
            constClicked.append("locator")
            break
        except Exception:
            continue

    if not constClicked:
        js_clicked = bool(
            page.evaluate(
                """
                () => {
                  const clean = (value) => (value || '').replace(/\\s+/g, ' ').trim();
                  const isVisible = (node) => {
                    if (!node) return false;
                    const style = window.getComputedStyle(node);
                    if (style.visibility === 'hidden' || style.display === 'none') return false;
                    const rect = node.getBoundingClientRect();
                    return rect.width > 0 && rect.height > 0;
                  };
                  const robustClick = (node) => {
                    try { node.scrollIntoView({ block: 'center', inline: 'center' }); } catch (error) {}
                    try { node.focus?.(); } catch (error) {}
                    for (const [eventName, Ctor] of [
                      ['pointerdown', PointerEvent],
                      ['mousedown', MouseEvent],
                      ['pointerup', PointerEvent],
                      ['mouseup', MouseEvent],
                      ['click', MouseEvent],
                    ]) {
                      try {
                        node.dispatchEvent(new Ctor(eventName, { bubbles: true, cancelable: true, view: window }));
                      } catch (error) {}
                    }
                    try { node.click?.(); } catch (error) {}
                    return true;
                  };
                  const nodes = Array.from(document.querySelectorAll('button, [role="button"]'))
                    .filter((node) => isVisible(node))
                    .filter((node) => clean(node.innerText || node.textContent || node.getAttribute('aria-label') || '').includes('全部接受'));
                  if (!nodes.length) return false;
                  return robustClick(nodes[0]);
                }
                """
            )
        )
        if js_clicked:
            constClicked.append("js")

    if not constClicked:
        return False

    page.wait_for_timeout(post_click_wait_ms)
    after_unsaved = _has_unsaved_changes(page)
    after_snapshot = page.evaluate(
        """
        () => {
          const clean = (value) => (value || '').replace(/\\s+/g, ' ').trim();
          return Array.from(document.querySelectorAll('button, [role="button"]'))
            .map((node) => clean(node.innerText || node.textContent || node.getAttribute?.('aria-label') || ''))
            .filter((text) => text && text.includes('全部接受'))
            .join(' | ');
        }
        """
    )
    return after_unsaved or (not before_unsaved and after_snapshot != before_snapshot)


def _click_submit_or_save(page, *, post_save_wait_ms: int) -> bool:
    def _try_locator_click(locator) -> bool:
        try:
            if locator.count() == 0 or not locator.is_visible(timeout=1000):
                return False
            locator.scroll_into_view_if_needed(timeout=2000)
            try:
                locator.hover(timeout=1500)
            except Exception:
                pass
            locator.click(timeout=3000, force=True)
            page.wait_for_timeout(post_save_wait_ms)
            return True
        except Exception:
            return False

    top_bar_candidates = [
        page.locator('button[aria-label="保存"]').first,
        page.locator('button[aria-label*="保存"]').first,
        page.locator('button:has-text("保存")').first,
        page.get_by_text("保存", exact=True).first,
        page.locator('button:has-text("提交")').first,
        page.get_by_text("提交", exact=True).first,
    ]
    for locator in top_bar_candidates:
        if _try_locator_click(locator):
            return True

    js_clicked = bool(
        page.evaluate(
            """
            () => {
              const clean = (value) => (value || '').replace(/\\s+/g, ' ').trim();
              const isVisible = (node) => {
                if (!node) return false;
                const style = window.getComputedStyle(node);
                if (style.visibility === 'hidden' || style.display === 'none') return false;
                const rect = node.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
              };
              const robustClick = (node) => {
                try { node.scrollIntoView({ block: 'center', inline: 'center' }); } catch (error) {}
                try { node.focus?.(); } catch (error) {}
                for (const [eventName, Ctor] of [
                  ['pointerdown', PointerEvent],
                  ['mousedown', MouseEvent],
                  ['pointerup', PointerEvent],
                  ['mouseup', MouseEvent],
                  ['click', MouseEvent],
                ]) {
                  try {
                    node.dispatchEvent(new Ctor(eventName, { bubbles: true, cancelable: true, view: window }));
                  } catch (error) {}
                }
                try { node.click?.(); } catch (error) {}
                return true;
              };
              const buttons = Array.from(document.querySelectorAll('button, [role="button"]'))
                .filter((node) => isVisible(node))
                .map((node) => ({ node, text: clean(node.innerText || node.textContent || node.getAttribute('aria-label') || '') }))
                .filter((item) => item.text === '保存' || item.text === '提交');
              if (!buttons.length) return false;
              buttons.sort((a, b) => {
                const rectA = a.node.getBoundingClientRect();
                const rectB = b.node.getBoundingClientRect();
                return (rectA.top - rectB.top) || (rectB.right - rectA.right);
              });
              return robustClick(buttons[0].node);
            }
            """
        )
    )
    if js_clicked:
        page.wait_for_timeout(post_save_wait_ms)
        return True

    keyboard_targeted = bool(
        page.evaluate(
            """
            () => {
              const clean = (value) => (value || '').replace(/\\s+/g, ' ').trim();
              const isVisible = (node) => {
                if (!node) return false;
                const style = window.getComputedStyle(node);
                if (style.visibility === 'hidden' || style.display === 'none') return false;
                const rect = node.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
              };
              const buttons = Array.from(document.querySelectorAll('button, [role="button"]'))
                .filter((node) => isVisible(node))
                .map((node) => ({ node, text: clean(node.innerText || node.textContent || node.getAttribute('aria-label') || '') }))
                .filter((item) => item.text === '保存' || item.text === '提交');
              if (!buttons.length) return false;
              buttons.sort((a, b) => {
                const rectA = a.node.getBoundingClientRect();
                const rectB = b.node.getBoundingClientRect();
                return (rectA.top - rectB.top) || (rectB.right - rectA.right);
              });
              try { buttons[0].node.focus?.(); } catch (error) {}
              return true;
            }
            """
        )
    )
    if keyboard_targeted:
        try:
            page.keyboard.press("Enter")
            page.wait_for_timeout(post_save_wait_ms)
            return True
        except Exception:
            pass
    return False


def _has_unsaved_changes(page) -> bool:
    candidates = [
        page.locator('text="未保存的更改"').first,
        page.get_by_text("未保存的更改", exact=True).first,
        page.locator('[aria-label*="未保存的更改"]').first,
    ]
    for locator in candidates:
        try:
            if locator.count() > 0 and locator.is_visible(timeout=500):
                return True
        except Exception:
            continue
    return False


def _verify_saved_category_change(
    page,
    *,
    url: str,
    previous_value: str,
    expected_value: str,
    wait_until: str,
    goto_timeout_ms: int,
    save_settle_timeout_ms: int,
) -> dict[str, Any]:
    save_completed = _wait_for_save_settle(page, timeout_ms=save_settle_timeout_ms)
    if not save_completed:
        second_try_saved = _click_submit_or_save(page, post_save_wait_ms=4000)
        if second_try_saved:
            save_completed = _wait_for_save_settle(page, timeout_ms=save_settle_timeout_ms)
    try:
        page.reload(wait_until=wait_until, timeout=goto_timeout_ms)
    except Exception as exc:
        return {
            "save_completed": save_completed,
            "refreshed_value": "",
            "matched_expected": False,
            "changed_from_previous": False,
            "verification_status": "reload_failed",
            "verification_error": str(exc),
        }
    refreshed = _extract_category_section_state(page)
    refreshed_value = refreshed.get("current_value", "")
    expected_norm = (expected_value or "").strip()
    previous_norm = (previous_value or "").strip()
    matched_expected = bool(expected_norm) and refreshed_value == expected_norm
    changed_from_previous = bool(refreshed_value) and refreshed_value != previous_norm
    return {
        "save_completed": save_completed,
        "refreshed_value": refreshed_value,
        "matched_expected": matched_expected,
        "changed_from_previous": changed_from_previous,
        "verification_status": (
            "saved_successfully"
            if save_completed and (matched_expected or changed_from_previous)
            else ("save_not_completed" if not save_completed else "refreshed_value_unchanged")
        ),
    }


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    output_file = Path(args.output_file).expanduser()
    if not output_file.is_absolute():
        output_file = (AGENT_ROOT / output_file).resolve()
    checkpoint_file = Path(args.checkpoint_file).expanduser() if args.checkpoint_file else _default_checkpoint_file(args)
    if not checkpoint_file.is_absolute():
        checkpoint_file = (AGENT_ROOT / checkpoint_file).resolve()
    checkpoint = CheckpointStore(
        checkpoint_file,
        store_handle=args.store_handle,
        product_query=args.product_query,
        max_items=args.max_items,
        output_file=output_file,
    )
    if args.reset_checkpoint:
        checkpoint.reset()
    checkpoint.load_or_initialize(resume=not args.no_resume)
    resumed_ids = set(checkpoint.processed_product_ids())
    urls = _load_urls(args)
    if resumed_ids:
        urls = [url for url in urls if _extract_product_gid(url) not in resumed_ids]

    _print_line(f"检查点文件：{checkpoint.checkpoint_file}")
    _print_line(f"结果明细文件：{checkpoint.result_file}")
    if resumed_ids:
        _print_line(f"检测到历史进度，已完成 {len(resumed_ids)} 个商品，本次将从断点继续执行。")
    else:
        _print_line("未检测到可恢复进度，本次将从头开始执行。")

    _print_line(f"开始执行 Shopify 后台建议全量采纳，目标商品数：{len(urls)}。")
    if args.cdp_url:
        _print_line(f"当前使用已打开浏览器连接：{args.cdp_url}")

    playwright = None
    holder = None
    page = None
    temp_dir = None

    try:
        playwright, holder, page, temp_dir = _open_browser_runtime(args)
        for index, url in enumerate(urls, start=1):
            product_gid = _extract_product_gid(url)
            try:
                _open_product_page(
                    page,
                    url,
                    progress_label=f"第 {index}/{len(urls)} 个商品",
                    wait_until=args.wait_until,
                    goto_timeout_ms=args.goto_timeout_ms,
                    retry_count=args.retry_count,
                    retry_backoff_ms=args.retry_backoff_ms,
                )

                accepted = _click_accept_all(page, post_click_wait_ms=args.post_click_wait_ms)
                category_suggestion = {
                    "clicked": False,
                    "clicked_text": "",
                    "changed": False,
                    "before_value": "",
                    "after_value": "",
                    "reason": "not_attempted",
                }
                if not accepted:
                    category_suggestion = _click_category_suggestion(page, post_click_wait_ms=args.post_click_wait_ms)
                saved = _click_submit_or_save(page, post_save_wait_ms=args.post_save_wait_ms) if (accepted or category_suggestion["clicked"]) else False
                category_applied = bool(category_suggestion["clicked"] and category_suggestion["changed"])
                accepted_all_applied = bool(accepted and saved)
                verification = {
                    "save_completed": False,
                    "refreshed_value": "",
                    "matched_expected": False,
                    "changed_from_previous": False,
                    "verification_status": "not_applicable",
                }
                if category_suggestion["clicked"] and saved:
                    verification = _verify_saved_category_change(
                        page,
                        url=url,
                        previous_value=category_suggestion["before_value"],
                        expected_value=category_suggestion["clicked_text"],
                        wait_until=args.wait_until,
                        goto_timeout_ms=args.goto_timeout_ms,
                        save_settle_timeout_ms=args.save_settle_timeout_ms,
                    )
                status = "applied" if accepted_all_applied else (
                    "category_suggestion_applied" if verification["verification_status"] == "saved_successfully" else (
                        "category_suggestion_save_not_completed" if verification["verification_status"] == "save_not_completed" else (
                            "category_suggestion_refreshed_value_unchanged" if verification["verification_status"] == "refreshed_value_unchanged" else (
                        "category_suggestion_clicked_not_saved" if category_suggestion["clicked"] else (
                            "accepted_not_saved" if accepted else "no_accept_button"
                        )
                    ))
                    )
                )

                result = {
                    "product_id": product_gid,
                    "admin_url": url,
                    "accepted": accepted,
                    "category_suggestion_clicked": category_suggestion["clicked"],
                    "category_suggestion_text": category_suggestion["clicked_text"],
                    "category_value_before": category_suggestion["before_value"],
                    "category_value_after": category_suggestion["after_value"],
                    "category_changed": category_suggestion["changed"],
                    "saved": saved,
                    "save_completed": verification["save_completed"],
                    "category_value_refreshed": verification["refreshed_value"],
                    "category_refresh_matched_expected": verification["matched_expected"],
                    "category_refresh_changed_from_previous": verification["changed_from_previous"],
                    "verification_status": verification["verification_status"],
                    "status": status,
                }
                checkpoint.record_item(result)

                if accepted and saved:
                    _print_line(f"第 {index}/{len(urls)} 个商品已执行“全部接受”并提交保存。")
                elif category_suggestion["clicked"] and saved:
                    if verification["verification_status"] == "saved_successfully":
                        _print_line(
                            f"第 {index}/{len(urls)} 个商品保存成功。"
                            f"建议：{category_suggestion['clicked_text']}；原类别：{category_suggestion['before_value']}；"
                            f"点击后类别：{category_suggestion['after_value']}；刷新后类别：{verification['refreshed_value']}。"
                        )
                    elif verification["verification_status"] == "save_not_completed":
                        _print_line(
                            f"第 {index}/{len(urls)} 个商品保存未完成。"
                            f"建议：{category_suggestion['clicked_text']}；原类别：{category_suggestion['before_value']}；"
                            f"点击后类别：{category_suggestion['after_value']}；刷新后类别：{verification['refreshed_value']}。"
                        )
                    else:
                        _print_line(
                            f"第 {index}/{len(urls)} 个商品刷新后类别未变化。"
                            f"建议：{category_suggestion['clicked_text']}；原类别：{category_suggestion['before_value']}；"
                            f"点击后类别：{category_suggestion['after_value']}；刷新后类别：{verification['refreshed_value']}。"
                        )
                elif category_suggestion["clicked"]:
                    _print_line(
                        f"第 {index}/{len(urls)} 个商品已点击类别建议，但未确认到提交保存按钮。"
                        f"建议：{category_suggestion['clicked_text']}；原类别：{category_suggestion['before_value']}；"
                        f"现类别：{category_suggestion['after_value']}。"
                    )
                elif accepted:
                    _print_line(f"第 {index}/{len(urls)} 个商品已点击“全部接受”，但未确认到提交保存按钮。")
                else:
                    _print_line(f"第 {index}/{len(urls)} 个商品未发现可点击的“全部接受”按钮，已跳过。")
            except Exception as exc:
                result = {
                    "product_id": product_gid,
                    "admin_url": url,
                    "accepted": False,
                    "saved": False,
                    "status": "open_failed",
                    "error": str(exc),
                }
                checkpoint.record_item(result)
                _print_line(f"第 {index}/{len(urls)} 个商品处理失败，已记录错误并继续后续商品。原因：{exc}")

            _cooldown_after_item(
                page,
                index=index,
                page_delay_ms=args.page_delay_ms,
                batch_size=args.batch_size,
                batch_cooldown_ms=args.batch_cooldown_ms,
            )
    except KeyboardInterrupt:
        checkpoint.mark_interrupted()
        _print_line("任务已中断，检查点已保存。下次直接运行同一命令即可从断点继续。")
        raise
    finally:
        if playwright is not None and holder is not None:
            _close_browser_runtime(playwright, holder, temp_dir)

    checkpoint.mark_finished()
    _print_line(checkpoint.data.get("summary", ""))
    _print_line("检查点已更新完成。如需重新从头跑，请在命令后加 --reset-checkpoint。")


if __name__ == "__main__":
    main()
