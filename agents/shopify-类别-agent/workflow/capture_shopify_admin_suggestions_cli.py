from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from typing import Any

AGENT_ROOT = Path(__file__).resolve().parents[1]
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from shared.clients import ShopifyAuthClient
from shared.config import get_settings


def _now_label() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _print_line(message: str) -> None:
    print(f"[{_now_label()}] {message}", flush=True)


def _require_playwright():
    try:
        from playwright.sync_api import Error as PlaywrightError  # type: ignore
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise SystemExit(
            "当前环境未安装 Playwright，无法自动抓取 Shopify 后台建议框。"
            " 请先执行：python -m pip install playwright && python -m playwright install chromium"
        ) from exc
    return sync_playwright, PlaywrightError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Capture Shopify admin category suggestions from product edit pages.")
    parser.add_argument("--product-url", action="append", default=[], help="单个 Shopify 商品编辑页 URL，可重复传入")
    parser.add_argument("--product-urls-file", default="", help="包含多个 Shopify 商品编辑页 URL 的文本文件")
    parser.add_argument("--store-handle", default="", help="Shopify Admin store handle，例如 getbulkdeals")
    parser.add_argument("--product-query", default="", help="自动扫描商品页时使用的 Shopify query")
    parser.add_argument("--max-items", type=int, default=0, help="自动扫描时最大商品数，0 表示不限")
    parser.add_argument("--storage-state", default="", help="Playwright 登录态文件路径")
    parser.add_argument("--chrome-user-data-dir", default="", help="本机浏览器用户数据目录")
    parser.add_argument("--chrome-profile-directory", default="Default", help="浏览器 Profile 名称，例如 Default 或 Profile 1")
    parser.add_argument("--browser-channel", default="chrome", choices=["chrome", "msedge"], help="浏览器通道")
    parser.add_argument("--cdp-url", default="", help="连接已打开浏览器的 CDP 地址，例如 http://127.0.0.1:9222")
    parser.add_argument("--goto-timeout-ms", type=int, default=120000, help="打开商品页超时时间")
    parser.add_argument(
        "--wait-until",
        default="domcontentloaded",
        choices=["domcontentloaded", "load", "networkidle", "commit"],
        help="页面跳转等待策略",
    )
    parser.add_argument("--page-delay-ms", type=int, default=8000, help="每个商品处理后的常规等待时间")
    parser.add_argument("--retry-count", type=int, default=3, help="打开商品页失败时的重试次数")
    parser.add_argument("--retry-backoff-ms", type=int, default=15000, help="每次重试前的等待时间")
    parser.add_argument("--batch-size", type=int, default=20, help="连续抓取多少个商品后进入一次冷却")
    parser.add_argument("--batch-cooldown-ms", type=int, default=60000, help="批次冷却时间")
    parser.add_argument("--output-file", required=True, help="输出 JSON 文件路径")
    parser.add_argument("--headed", action="store_true", help="使用有头浏览器")
    return parser


def _load_urls(args: argparse.Namespace) -> list[str]:
    urls = list(args.product_url or [])
    if args.product_urls_file:
        file_path = Path(args.product_urls_file).expanduser()
        urls.extend([line.strip() for line in file_path.read_text(encoding="utf-8").splitlines() if line.strip()])
    if args.store_handle:
        urls.extend(_build_urls_from_shopify(args.store_handle, args.product_query, args.max_items))
    if not urls:
        raise SystemExit("请至少提供 --product-url、--product-urls-file 或 --store-handle 其中之一。")
    return urls


def _build_urls_from_shopify(store_handle: str, product_query: str, max_items: int) -> list[str]:
    client = ShopifyAuthClient.from_settings(get_settings())
    limit = max_items if max_items and max_items > 0 else None
    cursor = None
    urls: list[str] = []
    page = 0
    while True:
        page += 1
        data = client.graphql(
            """
            query ProductsPage($first: Int!, $after: String, $query: String!) {
              products(first: $first, after: $after, query: $query) {
                edges {
                  cursor
                  node {
                    id
                  }
                }
                pageInfo {
                  hasNextPage
                  endCursor
                }
              }
            }
            """,
            {
                "first": min(50, max(1, (limit - len(urls)) if limit else 50)),
                "after": cursor,
                "query": product_query,
            },
        )
        connection = data.get("products", {}) or {}
        for edge in connection.get("edges", []) or []:
            product_gid = ((edge.get("node") or {}).get("id") or "")
            numeric_id = product_gid.rsplit("/", 1)[-1]
            if numeric_id:
                urls.append(f"https://admin.shopify.com/store/{store_handle}/products/{numeric_id}")
            if limit and len(urls) >= limit:
                break
        _print_line(f"商品链接扫描中：第 {page} 页，当前累计 {len(urls)} 个商品链接。")
        page_info = connection.get("pageInfo", {}) or {}
        if (limit and len(urls) >= limit) or not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
        if not cursor:
            break
    return urls


def _extract_product_gid(url: str) -> str:
    match = re.search(r"/products/(\d+)", url)
    if not match:
        return ""
    return f"gid://shopify/Product/{match.group(1)}"


def _extract_suggestions(page) -> dict[str, Any]:
    return page.evaluate(
        """
        () => {
          const clean = (value) => (value || '').replace(/\\s+/g, ' ').trim();

          const unique = (values) => {
            const seen = new Set();
            const output = [];
            for (const value of values || []) {
              const item = clean(value);
              if (!item || seen.has(item)) continue;
              seen.add(item);
              output.push(item);
            }
            return output;
          };

          const slugify = (value) =>
            clean(value)
              .toLowerCase()
              .replace(/[^a-z0-9\u4e00-\u9fff]+/g, '-')
              .replace(/^-+|-+$/g, '');

          const isVisible = (element) => {
            if (!element || !element.getBoundingClientRect) {
              return false;
            }
            const rect = element.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0;
          };

          const elementAttributes = (element) => {
            const output = {};
            if (!element || !element.getAttributeNames) {
              return output;
            }
            for (const name of element.getAttributeNames()) {
              const value = clean(element.getAttribute(name) || '');
              if (value) {
                output[name] = value;
              }
            }
            return output;
          };

          const stripSuggestionDecorations = (text) => {
            return clean(
              (text || '')
                .replace(/(^|\\s)建议(\\s|$)/g, ' ')
                .replace(/(^|\\s)全部接受(\\s|$)/g, ' ')
                .replace(/[×✕✖xX]$/g, ' ')
            );
          };

          const normalizeRowText = (text) => {
            return clean(
              stripSuggestionDecorations(text)
                .replace(/^类别\\s+/, '')
                .replace(/^类别元字段\\s+/, '')
            );
          };

          const findCategorySection = () => {
            const all = Array.from(document.querySelectorAll('div, section, label, span, p, h2, h3'));
            const exactLabel = all.find((node) => clean(node.innerText) === '类别');
            if (!exactLabel) {
              return null;
            }
            let best = null;
            let current = exactLabel;
            for (let depth = 0; depth < 8 && current; depth += 1) {
              const text = clean(current.innerText || '');
              const score =
                (text.includes('建议') ? 20 : 0) +
                (text.includes('选择产品类别') ? 10 : 0) +
                (text.includes('类别') ? 5 : 0) -
                Math.max(0, Math.floor(text.length / 300));
              if (!best || score > best.score) {
                best = { element: current, score };
              }
              current = current.parentElement;
            }
            return best ? best.element : exactLabel.parentElement;
          };

          const findMetafieldSuggestionSection = () => {
            const getAncestors = (node) => {
              const ancestors = [];
              let current = node;
              while (current) {
                ancestors.push(current);
                current = current.parentElement;
              }
              return ancestors;
            };

            const lowestCommonAncestor = (left, right) => {
              if (!left || !right) {
                return null;
              }
              const leftAncestors = getAncestors(left);
              const rightAncestors = new Set(getAncestors(right));
              for (const node of leftAncestors) {
                if (rightAncestors.has(node)) {
                  return node;
                }
              }
              return null;
            };

            const countNodes = Array.from(document.querySelectorAll('div, span, p, h2, h3, button'))
              .filter((node) => isVisible(node))
              .filter((node) => /^\\d+\\s*条可用建议$/.test(clean(node.innerText || '')));

            const acceptNodes = Array.from(document.querySelectorAll('button, div, span'))
              .filter((node) => isVisible(node))
              .filter((node) => clean(node.innerText || '') === '全部接受');

            let best = null;
            for (const countNode of countNodes) {
              for (const acceptNode of acceptNodes) {
                const ancestor = lowestCommonAncestor(countNode, acceptNode);
                if (!ancestor || !isVisible(ancestor)) {
                  continue;
                }
                const text = clean(ancestor.innerText || '');
                if (!text) {
                  continue;
                }
                const score =
                  (/\\d+\\s*条可用建议/.test(text) ? 60 : 0) +
                  (text.includes('全部接受') ? 50 : 0) +
                  (text.includes('类别元字段') ? 25 : 0) +
                  (text.includes('建议') ? 10 : 0) -
                  Math.max(0, Math.floor(text.length / 180));
                if (score <= 0) {
                  continue;
                }
                if (!best || score > best.score) {
                  best = { element: ancestor, score };
                }
              }
            }

            if (best) {
              return best.element;
            }

            const candidates = Array.from(document.querySelectorAll('div, section, aside'));
            for (const node of candidates) {
              if (!isVisible(node)) {
                continue;
              }
              const text = clean(node.innerText || '');
              if (!text) {
                continue;
              }
              const score =
                (/\\d+\\s*条可用建议/.test(text) ? 35 : 0) +
                (text.includes('全部接受') ? 25 : 0) +
                (text.includes('类别元字段') ? 20 : 0) +
                (text.includes('建议') ? 5 : 0) -
                Math.max(0, Math.floor(text.length / 220));
              if (score <= 0) {
                continue;
              }
              if (!best || score > best.score) {
                best = { element: node, score };
              }
            }
            return best ? best.element : null;
          };

          const findCategoryMetafieldFieldsSection = () => {
            const candidates = Array.from(document.querySelectorAll('div, section, aside'));
            let best = null;
            for (const node of candidates) {
              if (!isVisible(node)) {
                continue;
              }
              const text = clean(node.innerText || '');
              if (!text) {
                continue;
              }
              const score =
                (text.includes('类别 元字段') ? 50 : 0) +
                (text.includes('类别元字段') ? 40 : 0) +
                (/中的\\s+.+/.test(text) ? 15 : 0) +
                (text.includes('颜色') ? 10 : 0) +
                (text.includes('家具/固定装置材质') ? 10 : 0) +
                (text.includes('床/床架特点') ? 10 : 0) -
                Math.max(0, Math.floor(text.length / 260));
              if (score <= 0) {
                continue;
              }
              if (!best || score > best.score) {
                best = { element: node, score };
              }
            }
            return best ? best.element : null;
          };

          const collectSuggestionRows = (section) => {
            if (!section) {
              return [];
            }
            const rows = [];
            const nodes = Array.from(section.querySelectorAll('*'));
            for (const node of nodes) {
              const text = clean(node.innerText || '');
              if (!text || !text.includes('建议')) {
                continue;
              }
              let row = node;
              while (row && row !== section && clean(row.innerText || '').length < text.length + 4) {
                row = row.parentElement;
              }
              row = row || node;
              const rowText = clean(row.innerText || '');
              const normalizedText = normalizeRowText(rowText);
              if (!normalizedText || normalizedText === '类别') {
                continue;
              }
              rows.push({
                text: normalizedText,
                raw_text: rowText,
                tag: row.tagName || '',
                attributes: elementAttributes(row),
                html: (row.outerHTML || '').slice(0, 2000),
              });
            }
            return rows;
          };

          const collectLeafTextEntries = (root) => {
            if (!root) {
              return [];
            }
            const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
            const entries = [];
            while (walker.nextNode()) {
              const textNode = walker.currentNode;
              const text = clean(textNode.textContent || '');
              if (!text) {
                continue;
              }
              const parent = textNode.parentElement;
              if (!parent || !isVisible(parent)) {
                continue;
              }
              const rect = parent.getBoundingClientRect();
              entries.push({
                text,
                x: rect.left,
                y: rect.top,
                width: rect.width,
                height: rect.height,
                tag: parent.tagName || '',
                attributes: elementAttributes(parent),
              });
            }
            return entries;
          };

          const collectAttributeValueEntries = (root) => {
            if (!root) {
              return [];
            }
            const entries = [];
            const addEntry = (node, value, source) => {
              const text = clean(value || '');
              if (!text) {
                return;
              }
              const rect = node.getBoundingClientRect();
              entries.push({
                text,
                x: rect.left,
                y: rect.top,
                width: rect.width,
                height: rect.height,
                tag: node.tagName || '',
                attributes: elementAttributes(node),
                source,
              });
            };

            for (const node of Array.from(root.querySelectorAll('*'))) {
              if (!isVisible(node)) {
                continue;
              }
              const attrNames = ['value', 'aria-label', 'title', 'data-value', 'label'];
              for (const attrName of attrNames) {
                const attrValue = node.getAttribute ? node.getAttribute(attrName) : '';
                addEntry(node, attrValue, `attr:${attrName}`);
              }
              if (typeof node.value === 'string') {
                addEntry(node, node.value, 'dom:value');
              }
            }

            return entries;
          };

          const collectShadowValueEntries = (root) => {
            if (!root) {
              return [];
            }

            const entries = [];
            const visitedRoots = new Set();

            const addEntry = (node, value, source) => {
              const text = clean(value || '');
              if (!text) {
                return;
              }
              const rect = node.getBoundingClientRect ? node.getBoundingClientRect() : { left: 0, top: 0, width: 0, height: 0 };
              entries.push({
                text,
                x: rect.left,
                y: rect.top,
                width: rect.width,
                height: rect.height,
                tag: node.tagName || '',
                attributes: elementAttributes(node),
                source,
              });
            };

            const walkRoot = (container) => {
              if (!container || visitedRoots.has(container)) {
                return;
              }
              visitedRoots.add(container);

              const nodes = container.querySelectorAll ? Array.from(container.querySelectorAll('*')) : [];
              for (const node of nodes) {
                if (node.shadowRoot) {
                  walkRoot(node.shadowRoot);
                }
                if (!isVisible(node) && !node.shadowRoot) {
                  continue;
                }
                addEntry(node, node.innerText || node.textContent || '', 'shadow:text');
                const attrNames = ['value', 'aria-label', 'title', 'data-value', 'label'];
                for (const attrName of attrNames) {
                  const attrValue = node.getAttribute ? node.getAttribute(attrName) : '';
                  addEntry(node, attrValue, `shadow:attr:${attrName}`);
                }
                if (typeof node.value === 'string') {
                  addEntry(node, node.value, 'shadow:dom:value');
                }
              }
            };

            walkRoot(root);
            for (const node of Array.from(root.querySelectorAll('*'))) {
              if (node.shadowRoot) {
                walkRoot(node.shadowRoot);
              }
            }
            return entries;
          };

          const collectKeyCandidatesFromRow = (elements) => {
            const raw = [];
            const addTokens = (value) => {
              const text = clean(value || '');
              if (!text) {
                return;
              }
              const matches = text.match(/[a-z][a-z0-9_-]{2,}/gi) || [];
              for (const match of matches) {
                raw.push(match.toLowerCase().replace(/_/g, '-'));
              }
            };
            for (const entry of elements) {
              for (const [name, value] of Object.entries(entry.attributes || {})) {
                if (['id', 'name', 'for'].includes(name) || name.startsWith('data-') || name.startsWith('aria-')) {
                  addTokens(value);
                }
              }
            }
            return unique(
              raw.filter((item) =>
                ![
                  'polaris', 'shopify', 'internal', 'label', 'value', 'button', 'small', 'medium',
                  'base', 'text', 'suggestion', 'accept', 'field', 'content', 'secondary', 'search',
                  'picker', 'action', 'tone', 'fontweight', 'exclusive', 'outside'
                ].includes(item)
              )
            );
          };

          const extractMetafields = (section) => {
            if (!section) {
              return { metafields: [], rows: [] };
            }

            const ignoredTexts = new Set([
              '类别元字段',
              '全部接受',
              '建议',
              '查看全部',
              '添加定义',
            ]);

            const ignoredLabels = new Set([
              '富文本编辑器',
              '描述',
              '段落',
              '媒体文件',
              '类别',
              '类别元字段',
              '建议',
              '保存',
            ]);

            const entries = collectLeafTextEntries(section)
              .filter((entry) => {
                if (ignoredTexts.has(entry.text)) {
                  return false;
                }
                if (/^\\d+\\s*条可用建议$/.test(entry.text)) {
                  return false;
                }
                if (entry.text.includes('Google:')) {
                  return false;
                }
                if (entry.text.includes('确定税率并添加元字段')) {
                  return false;
                }
                return true;
              })
              .sort((a, b) => (a.y - b.y) || (a.x - b.x));

            const rows = [];
            for (const entry of entries) {
              let row = rows.find((item) => Math.abs(item.y - entry.y) <= 18);
              if (!row) {
                row = { y: entry.y, items: [] };
                rows.push(row);
              }
              row.items.push(entry);
            }

            const metafields = [];
            const rowDebug = [];
            for (const row of rows) {
              const items = row.items.sort((a, b) => a.x - b.x);
              const texts = unique(items.map((item) => item.text));
              if (texts.length < 2) {
                rowDebug.push({ texts, skipped: true });
                continue;
              }
              const label = texts[0];
              if (!label || ignoredLabels.has(label) || /^\\d+\\s*条可用建议$/.test(label)) {
                rowDebug.push({ texts, skipped: true });
                continue;
              }
              const values = texts.slice(1).filter((value) => !ignoredTexts.has(value));
              if (!label || !values.length) {
                rowDebug.push({ texts, skipped: true });
                continue;
              }
              const keyCandidates = collectKeyCandidatesFromRow(items);
              metafields.push({
                key: keyCandidates[0] || '',
                label,
                name: label,
                key_candidates: keyCandidates,
                values: unique(values).slice(0, 12),
              });
              rowDebug.push({
                label,
                values: unique(values),
                key_candidates: keyCandidates,
              });
            }

            return { metafields, rows: rowDebug };
          };

          const extractRenderedMetafields = (section) => {
            if (!section) {
              return { metafields: [], rows: [] };
            }

            const ignoredTexts = new Set([
              '类别元字段',
              '类别 元字段',
              '全部接受',
              '建议',
              '查看全部',
              '添加定义',
              '产品元字段',
              '多属性元字段',
              'Google: Custom Product',
            ]);

            const noiseMatchers = [
              /^\\d+\\s*个元字段$/,
              /^\\d+\\s*条可用建议$/,
              /^Google:/,
              /^中的\\s+/,
            ];

            const allEntries = [
              ...collectLeafTextEntries(section).map((entry) => ({ ...entry, source: 'text' })),
              ...collectAttributeValueEntries(section),
              ...collectShadowValueEntries(section),
            ]
              .filter((entry) => {
                const text = entry.text;
                if (!text) {
                  return false;
                }
                if (ignoredTexts.has(text)) {
                  return false;
                }
                if (text.includes('确定税率并添加元字段')) {
                  return false;
                }
                if (text === '保存' || text === '提交' || text === '更多操作') {
                  return false;
                }
                if (text.startsWith('编辑 ') && text.endsWith(' 元字段')) {
                  return false;
                }
                if (noiseMatchers.some((pattern) => pattern.test(text))) {
                  return false;
                }
                return true;
              })
              .sort((a, b) => (a.y - b.y) || (a.x - b.x));

            const rows = [];
            for (const entry of allEntries) {
              let row = rows.find((item) => Math.abs(item.y - entry.y) <= 18);
              if (!row) {
                row = { y: entry.y, items: [] };
                rows.push(row);
              }
              row.items.push(entry);
            }

            const labelAliases = new Map();
            for (const label of [
              '颜色',
              '床上用品尺寸',
              '家具/固定装置材质',
              '床/床架特点',
              '木材类型',
              '木材饰面',
              '兼容的床垫尺寸',
              '床体收纳类型',
              '床头板款式',
            ]) {
              labelAliases.set(label, slugify(label));
            }

            const metafields = [];
            const rowDebug = [];
            for (const row of rows) {
              const items = row.items.sort((a, b) => a.x - b.x);
              const leftmost = items[0];
              const label = clean(leftmost ? leftmost.text : '');
              if (
                !label ||
                ignoredTexts.has(label) ||
                noiseMatchers.some((pattern) => pattern.test(label)) ||
                label.length > 40 ||
                label.includes('中的') ||
                label.includes('元字段')
              ) {
                rowDebug.push({ texts: unique(items.map((item) => item.text)), skipped: true });
                continue;
              }
              const keyCandidates = collectKeyCandidatesFromRow(items);
              const values = unique(
                items
                  .filter((item) => item.x > leftmost.x + Math.max(80, leftmost.width))
                  .map((item) => item.text)
                  .filter((value) => {
                    if (!value || value === label || ignoredTexts.has(value)) {
                      return false;
                    }
                    if (noiseMatchers.some((pattern) => pattern.test(value))) {
                      return false;
                    }
                    return true;
                  })
              );
              if (!values.length) {
                rowDebug.push({ label, values: [], skipped: true });
                continue;
              }
              metafields.push({
                key: '',
                label,
                name: label,
                key_candidates: unique([slugify(label), ...keyCandidates]).slice(0, 8),
                values: values.slice(0, 12),
              });
              rowDebug.push({
                label,
                values,
                key_candidates: unique([slugify(label), ...keyCandidates]).slice(0, 8),
              });
            }

            return { metafields, rows: rowDebug };
          };

          const bodyText = clean(document.body ? document.body.innerText : '');
          const categorySection = findCategorySection();
          const categorySectionText = categorySection ? clean(categorySection.innerText || '') : '';
          const categorySuggestionRows = collectSuggestionRows(categorySection);
          const normalizeCategorySuggestion = (value) => {
            let text = normalizeRowText(clean(value || ''));
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

          const acceptSuggestionLabels = (() => {
            if (!categorySection) {
              return [];
            }
            return unique(
              Array.from(categorySection.querySelectorAll('button[aria-label]'))
                .map((node) => clean(node.getAttribute('aria-label') || ''))
                .filter((text) => text.startsWith('接受建议的类别'))
                .map((text) => normalizeCategorySuggestion(text))
                .filter(Boolean)
            );
          })();

          const frontendSuggestionNodes = (() => {
            if (!categorySection) {
              return [];
            }
            return unique(
              Array.from(
                categorySection.querySelectorAll(
                  '[class*="SuggestionButtonStack"], [class*="MagicFieldSuggestion"], [class*="SuggestionButton"]'
                )
              )
                .map((node) => normalizeCategorySuggestion(node.innerText || node.textContent || ''))
                .filter((text) => text && !/^\d+\s*条(可用)?建议$/i.test(text))
                .filter(Boolean)
            );
          })();

          const aiSuggestionOptions = (() => {
            if (!categorySection) {
              return [];
            }
            return Array.from(
              categorySection.querySelectorAll('s-internal-picker-option[value^="gid://shopify/ProductTaxonomyNode/"]')
            )
              .map((node) => {
                const text = normalizeRowText(clean(node.innerText || ''));
                const nodeId = clean(node.getAttribute('value') || '');
                const rawHtml = (node.outerHTML || '').slice(0, 2000);
                const hasAiBadge =
                  /tone=["']ai["']/i.test(rawHtml) ||
                  /建议|寤鸿/.test(clean(node.textContent || '')) ||
                  /建议|寤鸿/.test(rawHtml);
                return {
                  text,
                  node_id: nodeId,
                  has_ai_badge: hasAiBadge,
                };
              })
              .filter((item) => item.has_ai_badge && item.text);
          })();

          const categoryTextFromBody = (() => {
            const match = bodyText.match(/类别\\s+(.+?)\\s+建议\\s+/);
            const value = match ? normalizeRowText(clean(match[1])) : '';
            return value && !value.includes('纭畾绋庣巼') ? value : '';
          })();

          const suggestionNodeIds = (() => {
            return unique(aiSuggestionOptions.map((item) => item.node_id));
          })();

          const currentCategoryValue = (() => {
            if (!categorySection) {
              return '';
            }
            const selectors = [
              's-internal-single-picker-field-value',
              '[class*="SinglePickerFieldValue"]',
              '[class*="ValueWrapper"]',
              '[class*="CurrentValue"]',
              'input',
              '[role="combobox"]',
              'button[aria-haspopup="listbox"]',
              'button',
            ];
            for (const selector of selectors) {
              const candidates = Array.from(categorySection.querySelectorAll(selector));
              for (const node of candidates) {
                const text = clean(node.value || node.innerText || node.getAttribute('aria-label') || '');
                if (text && !text.includes('建议') && !/条(可用)?建议/i.test(text) && text !== '类别' && text !== '选择产品类别') {
                  return text;
                }
              }
            }
            return '';
          })();

          const categoryLikeTexts = (() => {
            if (!categorySection) {
              return [];
            }
            const texts = Array.from(categorySection.querySelectorAll('div, span, button, p, li'))
              .map((node) => clean(node.innerText || ''))
              .filter(Boolean)
              .filter((text) => {
                if (text === '类别' || text === '建议' || text === '选择产品类别') {
                  return false;
                }
                if (text === currentCategoryValue) {
                  return false;
                }
                return (
                  text.includes(' > ') ||
                  /（在.+中）/.test(text) ||
                  /\\(in .+\\)/i.test(text) ||
                  text.includes('全部接受')
                );
              });
            return unique(texts.map(normalizeRowText));
          })();

          const categoryAttributeCandidates = (() => {
            if (!categorySection) {
              return [];
            }
            const values = [];
            const nodes = Array.from(categorySection.querySelectorAll('*'));
            for (const node of nodes) {
              for (const [name, value] of Object.entries(elementAttributes(node))) {
                if (
                  value.includes(' > ') ||
                  /（在.+中）/.test(value) ||
                  /\\(in .+\\)/i.test(value) ||
                  name.includes('aria') ||
                  name.startsWith('data-')
                ) {
                  values.push(value);
                }
              }
            }
            return unique(values);
          })();

          const bestCategorySuggestion =
            acceptSuggestionLabels.find(Boolean) ||
            frontendSuggestionNodes.find(Boolean) ||
            aiSuggestionOptions.map((item) => item.text).find(Boolean) ||
            categoryTextFromBody ||
            categorySuggestionRows.map((item) => item.text).find((text) => text && !text.startsWith('类别 ') && !text.includes('确定税率')) ||
            categorySuggestionRows.map((item) => item.text).find(Boolean) ||
            categoryLikeTexts.find(Boolean) ||
            '';

          const metafieldSuggestionSection = findMetafieldSuggestionSection();
          const metafieldSuggestionSectionText = metafieldSuggestionSection
            ? clean(metafieldSuggestionSection.innerText || '')
            : '';
          const metafieldFieldsSection = findCategoryMetafieldFieldsSection();
          const metafieldFieldsSectionText = metafieldFieldsSection
            ? clean(metafieldFieldsSection.innerText || '')
            : '';
          const metafieldSuggestionExtraction = extractMetafields(metafieldSuggestionSection);
          const metafieldRenderedExtraction = extractRenderedMetafields(metafieldFieldsSection);
          const metafieldExtraction =
            metafieldSuggestionExtraction.metafields.length > 0
              ? metafieldSuggestionExtraction
              : metafieldRenderedExtraction;
          const metafieldExtractionSource =
            metafieldSuggestionExtraction.metafields.length > 0
              ? 'suggestion'
              : (metafieldRenderedExtraction.metafields.length > 0 ? 'rendered' : '');

          return {
            category_full_name: bestCategorySuggestion,
            category_suggestion_text: bestCategorySuggestion,
            category_suggestion_node_ids: suggestionNodeIds,
            category_suggestion_candidates: unique([
              ...acceptSuggestionLabels,
              ...frontendSuggestionNodes,
              ...aiSuggestionOptions.map((item) => item.text),
              categoryTextFromBody,
              ...categorySuggestionRows.map((item) => item.text),
              ...categoryLikeTexts,
              ...categoryAttributeCandidates,
            ]),
            current_category_value: currentCategoryValue,
            category_section_text: categorySectionText,
            category_section_found: Boolean(categorySection),
            category_suggestion_rows: categorySuggestionRows,
            category_attribute_candidates: categoryAttributeCandidates,
            metafield_suggestion_section_found: Boolean(metafieldSuggestionSection),
            metafield_suggestion_section_text: metafieldSuggestionSectionText,
            metafield_suggestion_rows: metafieldExtraction.rows,
            metafield_fields_section_found: Boolean(metafieldFieldsSection),
            metafield_fields_section_text: metafieldFieldsSectionText,
            metafields_source: metafieldExtractionSource,
            metafield_suggestion_count: metafieldSuggestionExtraction.metafields.length,
            metafield_rendered_count: metafieldRenderedExtraction.metafields.length,
            metafields: metafieldExtraction.metafields,
            raw_text_excerpt: bodyText.slice(0, 5000),
          };
        }
        """
    )


def _page_has_shopify_error(page) -> bool:
    body_text = str(page.evaluate("() => document.body ? document.body.innerText : ''") or "")
    lowered = body_text.lower()
    return (
        "加载此页面时出现问题" in body_text
        or "请尝试重新加载此页面" in body_text
        or ("500" in body_text and "shopify" in lowered)
        or "there's a problem loading this page" in lowered
    )


def _prime_page_for_suggestions(page, *, goto_timeout_ms: int) -> None:
    try:
        page.wait_for_timeout(2000)
        page.evaluate(
            """
            async () => {
              const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
              const maxScroll = Math.max(
                document.documentElement ? document.documentElement.scrollHeight : 0,
                document.body ? document.body.scrollHeight : 0
              );
              const viewport = window.innerHeight || 900;
              let current = 0;
              while (current < maxScroll) {
                window.scrollTo({ top: current, behavior: 'instant' });
                await sleep(350);
                current += Math.max(500, Math.floor(viewport * 0.7));
              }
              window.scrollTo({ top: 0, behavior: 'instant' });
              await sleep(500);
            }
            """
        )
        page.wait_for_function(
            """
            () => {
              const text = document.body ? document.body.innerText : '';
              return /\\d+\\s*条可用建议/.test(text) || text.includes('全部接受');
            }
            """,
            timeout=min(goto_timeout_ms, 30000),
        )
    except Exception:
        page.wait_for_timeout(2500)


def _open_product_page(
    page,
    url: str,
    *,
    progress_label: str,
    wait_until: str,
    goto_timeout_ms: int,
    retry_count: int,
    retry_backoff_ms: int,
) -> None:
    last_error: Exception | None = None
    for attempt in range(1, retry_count + 1):
        try:
            _print_line(f"{progress_label} 开始打开页面，第 {attempt}/{retry_count} 次尝试：{url}")
            page.goto(url, wait_until=wait_until, timeout=goto_timeout_ms)
            try:
                page.wait_for_function(
                    """
                    () => {
                      const text = document.body ? document.body.innerText : '';
                      return text.includes('类别') && (
                        text.includes('建议') ||
                        text.includes('选择产品类别') ||
                        text.includes('确定税率并添加元字段')
                      );
                    }
                    """,
                    timeout=min(goto_timeout_ms, 20000),
                )
            except Exception:
                page.wait_for_timeout(8000)
            _prime_page_for_suggestions(page, goto_timeout_ms=goto_timeout_ms)
            if _page_has_shopify_error(page):
                raise RuntimeError("Shopify 后台返回了 500 或页面加载异常。")
            _print_line(f"{progress_label} 页面已打开，准备解析建议。")
            return
        except Exception as exc:
            last_error = exc
            if attempt >= retry_count:
                raise
            _print_line(f"{progress_label} 页面打开失败，将在 {retry_backoff_ms} 毫秒后重试。原因：{exc}")
            page.wait_for_timeout(retry_backoff_ms)
    if last_error:
        raise last_error


INTERACTIVE_METAFIELD_LABELS = [
    "颜色",
    "床上用品尺寸",
    "家具/固定装置材质",
    "床/床架特点",
    "木材类型",
    "木材饰面",
    "兼容的床垫尺寸",
    "床体收纳类型",
    "床头板款式",
]


def _extract_visible_overlay_values(page, label: str) -> list[str]:
    return page.evaluate(
        """
        (label) => {
          const clean = (value) => (value || '').replace(/\\s+/g, ' ').trim();
          const unique = (values) => {
            const seen = new Set();
            const output = [];
            for (const value of values || []) {
              const item = clean(value);
              if (!item || seen.has(item)) continue;
              seen.add(item);
              output.push(item);
            }
            return output;
          };
          const isVisible = (element) => {
            if (!element || !element.getBoundingClientRect) return false;
            const rect = element.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0;
          };
          const ignored = new Set([
            label,
            `编辑 ${label} 元字段`,
            '建议',
            '全部接受',
            '查看全部',
            '添加定义',
            '搜索',
            '保存',
            '关闭',
            '返回',
          ]);

          const overlaySelectors = [
            '[role="dialog"]',
            'dialog',
            's-popover',
            '.Polaris-PositionedOverlay',
            '.Polaris-Popover',
            '.Polaris-Portal',
          ];

          const candidates = [];
          for (const selector of overlaySelectors) {
            for (const node of Array.from(document.querySelectorAll(selector))) {
              if (!isVisible(node)) continue;
              const text = clean(node.innerText || node.textContent || '');
              if (!text) continue;
              candidates.push({ node, text, len: text.length });
            }
          }

          const overlay = candidates.sort((a, b) => b.len - a.len)[0]?.node || null;
          if (!overlay) {
            return [];
          }

          const values = [];
          const nodes = Array.from(overlay.querySelectorAll('*'));
          for (const node of nodes) {
            if (!isVisible(node)) continue;
            const attrPairs = [
              ['innerText', node.innerText || node.textContent || ''],
              ['value', typeof node.value === 'string' ? node.value : ''],
              ['aria-label', node.getAttribute ? node.getAttribute('aria-label') : ''],
              ['title', node.getAttribute ? node.getAttribute('title') : ''],
              ['data-value', node.getAttribute ? node.getAttribute('data-value') : ''],
            ];
            const isSelected =
              (node.getAttribute && (
                node.getAttribute('selected') !== null ||
                node.getAttribute('aria-selected') === 'true' ||
                node.getAttribute('aria-pressed') === 'true' ||
                node.getAttribute('aria-checked') === 'true'
              )) ||
              false;
            for (const [, rawValue] of attrPairs) {
              const text = clean(rawValue || '');
              if (!text || ignored.has(text)) continue;
              if (text.includes('元字段') || text.includes('确定税率并添加元字段')) continue;
              if (/^\\d+\\s*(个元字段|条可用建议)$/.test(text)) continue;
              if (text.length > 80) continue;
              if (isSelected || /badge|chip|tag|token/i.test(node.className || '')) {
                values.push(text);
              }
            }
          }

          return unique(values).slice(0, 12);
        }
        """,
        label,
    )


def _extract_interactive_metafields(page) -> list[dict[str, Any]]:
    metafields: list[dict[str, Any]] = []
    for label in INTERACTIVE_METAFIELD_LABELS:
        values: list[str] = []
        candidates = [
            page.locator(f'[aria-label="编辑 {label} 元字段"]').first,
            page.locator(f'[title="编辑 {label} 元字段"]').first,
            page.get_by_text(label, exact=True).first,
        ]
        for locator in candidates:
            try:
                if locator.count() == 0 or not locator.is_visible(timeout=1000):
                    continue
                locator.scroll_into_view_if_needed(timeout=2000)
                locator.click(timeout=3000, force=True)
                page.wait_for_timeout(900)
                values = _extract_visible_overlay_values(page, label)
                try:
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(300)
                except Exception:
                    pass
                if values:
                    break
            except Exception:
                continue
        if values:
            metafields.append(
                {
                    "key": "",
                    "label": label,
                    "name": label,
                    "key_candidates": [],
                    "values": values,
                }
            )
    return metafields


def _enrich_suggestions_with_interaction(page, suggestion: dict[str, Any]) -> dict[str, Any]:
    if suggestion.get("metafields"):
        return suggestion
    if not suggestion.get("metafield_fields_section_found"):
        return suggestion
    interactive_metafields = _extract_interactive_metafields(page)
    if not interactive_metafields:
        return suggestion
    suggestion["metafields"] = interactive_metafields
    suggestion["metafields_source"] = "interactive"
    suggestion["metafield_rendered_count"] = len(interactive_metafields)
    suggestion["metafield_suggestion_rows"] = (
        suggestion.get("metafield_suggestion_rows", [])
        + [
            {
                "label": item.get("label", ""),
                "values": item.get("values", []),
                "key_candidates": item.get("key_candidates", []),
                "source": "interactive",
            }
            for item in interactive_metafields
        ]
    )
    return suggestion


def _cooldown_after_item(page, *, index: int, page_delay_ms: int, batch_size: int, batch_cooldown_ms: int) -> None:
    if page_delay_ms > 0:
        _print_line(f"第 {index} 个商品解析完成，常规降速等待 {page_delay_ms} 毫秒。")
        page.wait_for_timeout(page_delay_ms)
    if batch_size > 0 and index % batch_size == 0 and batch_cooldown_ms > 0:
        _print_line(f"已完成 {index} 个商品，进入批次冷却，等待 {batch_cooldown_ms} 毫秒。")
        page.wait_for_timeout(batch_cooldown_ms)


def _build_cloned_user_data_dir(user_data_dir: Path, profile_directory: str) -> Path:
    temp_root = Path(tempfile.mkdtemp(prefix="shopify-admin-profile-"))
    source_local_state = user_data_dir / "Local State"
    source_profile_dir = user_data_dir / profile_directory
    if not source_profile_dir.exists():
        raise SystemExit(f"未找到浏览器 Profile 目录：{source_profile_dir}")

    if source_local_state.exists():
        shutil.copy2(source_local_state, temp_root / "Local State")

    target_profile_dir = temp_root / profile_directory
    _copy_profile_tree(source_profile_dir, target_profile_dir)
    return temp_root


def _copy_profile_tree(source_profile_dir: Path, target_profile_dir: Path) -> None:
    ignored_dir_names = {
        "Cache",
        "Code Cache",
        "GPUCache",
        "DawnGraphiteCache",
        "DawnWebGPUCache",
        "GrShaderCache",
        "GraphiteDawnCache",
        "ShaderCache",
        "Safe Browsing",
        "Safe Browsing Network",
        "Crashpad",
    }
    ignored_file_names = {
        "LOCK",
        "lockfile",
        "chrome_debug.log",
        "Cookies-journal",
        "Safe Browsing Cookies-journal",
    }
    critical_locked_markers = {
        os.path.join("Network", "Cookies"),
        os.path.join("Sessions", ""),
        "Cookies",
        "Login Data",
        "Web Data",
    }
    permission_denied_paths: list[str] = []

    for root, dirs, files in os.walk(source_profile_dir):
        relative_root = Path(root).relative_to(source_profile_dir)
        dirs[:] = [item for item in dirs if item not in ignored_dir_names and not item.startswith("Singleton")]
        destination_root = target_profile_dir / relative_root
        destination_root.mkdir(parents=True, exist_ok=True)
        for file_name in files:
            if file_name in ignored_file_names or file_name.startswith("Singleton"):
                continue
            source_file = Path(root) / file_name
            destination_file = destination_root / file_name
            try:
                shutil.copy2(source_file, destination_file)
            except (PermissionError, OSError):
                permission_denied_paths.append(str(source_file))

    critical_hits = [path for path in permission_denied_paths if any(marker in path for marker in critical_locked_markers)]
    if critical_hits:
        raise SystemExit(
            "浏览器登录资料仍被占用，无法复制关键登录文件。"
            " 请先彻底关闭所有 Chrome / Edge 窗口后重试。"
            f" 关键占用文件示例：{critical_hits[0]}"
        )


def _capture_loop(page, urls: list[str], args: argparse.Namespace, suggestions: dict[str, Any], output_file: Path) -> None:
    total = len(urls)
    for index, url in enumerate(urls, start=1):
        _open_product_page(
            page,
            url,
            progress_label=f"第 {index}/{total} 个商品",
            wait_until=args.wait_until,
            goto_timeout_ms=args.goto_timeout_ms,
            retry_count=args.retry_count,
            retry_backoff_ms=args.retry_backoff_ms,
        )
        product_gid = _extract_product_gid(url)
        if not product_gid:
            _print_line(f"第 {index}/{total} 个商品未能解析出 product gid，已跳过。")
            continue
        suggestions[product_gid] = _enrich_suggestions_with_interaction(page, _extract_suggestions(page))
        suggestions[product_gid]["admin_url"] = url
        output_file.write_text(json.dumps(suggestions, ensure_ascii=False, indent=2), encoding="utf-8")
        _print_line(f"第 {index}/{total} 个商品建议抓取完成，已落盘：{output_file}")
        _cooldown_after_item(
            page,
            index=index,
            page_delay_ms=args.page_delay_ms,
            batch_size=args.batch_size,
            batch_cooldown_ms=args.batch_cooldown_ms,
        )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    urls = _load_urls(args)
    output_file = Path(args.output_file).expanduser()
    output_file.parent.mkdir(parents=True, exist_ok=True)

    _print_line(f"开始抓取 Shopify 前端建议框，目标商品数：{len(urls)}。")
    if args.cdp_url:
        _print_line(f"当前使用已打开浏览器连接：{args.cdp_url}")
    elif args.chrome_user_data_dir:
        _print_line(
            f"当前使用浏览器资料目录：{args.chrome_user_data_dir}，"
            f"Profile：{args.chrome_profile_directory}，"
            f"通道：{args.browser_channel}"
        )
    else:
        _print_line(f"当前使用 Playwright 登录态文件：{args.storage_state}")

    sync_playwright, PlaywrightError = _require_playwright()
    suggestions: dict[str, Any] = {}
    cloned_user_data_dir: Path | None = None
    try:
        with sync_playwright() as playwright:  # pragma: no cover
            if args.cdp_url:
                browser = playwright.chromium.connect_over_cdp(args.cdp_url)
                context = browser.contexts[0] if browser.contexts else browser.new_context()
                page = context.new_page()
                _capture_loop(page, urls, args, suggestions, output_file)
                browser.close()
            elif args.chrome_user_data_dir:
                user_data_dir = Path(args.chrome_user_data_dir).expanduser()
                if not user_data_dir.exists():
                    raise SystemExit(f"未找到浏览器用户数据目录：{user_data_dir}")
                cloned_user_data_dir = _build_cloned_user_data_dir(user_data_dir, args.chrome_profile_directory)
                context = playwright.chromium.launch_persistent_context(
                    user_data_dir=str(cloned_user_data_dir),
                    channel=args.browser_channel,
                    headless=not args.headed,
                    args=[f"--profile-directory={args.chrome_profile_directory}"],
                )
                page = context.new_page()
                _capture_loop(page, urls, args, suggestions, output_file)
                context.close()
            else:
                storage_state = Path(args.storage_state).expanduser()
                if not storage_state.exists():
                    raise SystemExit(
                        "未提供可用的浏览器登录态。"
                        " 请二选一：1) 传 --chrome-user-data-dir 复用本机已登录浏览器；"
                        " 2) 传 --storage-state 指向 Playwright 登录态文件。"
                    )
                browser = playwright.chromium.launch(headless=not args.headed)
                context = browser.new_context(storage_state=str(storage_state))
                page = context.new_page()
                _capture_loop(page, urls, args, suggestions, output_file)
                context.close()
                browser.close()
    except PlaywrightError as exc:  # pragma: no cover
        raise SystemExit(
            "浏览器启动或页面抓取失败。请检查 Shopify 后台是否可正常访问，并优先使用减速参数重试。"
            f" 原始错误：{exc}"
        ) from exc
    finally:
        if cloned_user_data_dir and cloned_user_data_dir.exists():  # pragma: no cover
            shutil.rmtree(cloned_user_data_dir, ignore_errors=True)

    output_file.write_text(json.dumps(suggestions, ensure_ascii=False, indent=2), encoding="utf-8")
    _print_line(f"Shopify 前端建议抓取完成，共写入 {len(suggestions)} 个商品：{output_file}")


if __name__ == "__main__":
    main()
