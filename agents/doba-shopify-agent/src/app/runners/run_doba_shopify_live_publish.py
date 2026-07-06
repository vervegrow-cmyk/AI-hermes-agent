from __future__ import annotations

import argparse
import json
import sys

import bootstrap
import httpx
from shared.clients.doba import DobaAPIError
from src.modules.shopify_listing.application.live_publish_runtime import (
    DEFAULT_CANDIDATE_POOL_PATH,
    DEFAULT_LIST_MIN_INVENTORY,
    publish_doba_products_live,
)


def _print_json(payload: dict) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        print(text)
    except UnicodeEncodeError:
        print(text.encode("utf-8", errors="replace").decode("utf-8", errors="replace"))


def _print_doba_connectivity_hint(exc: Exception) -> None:
    if isinstance(exc, DobaAPIError):
        payload = {
            "ok": False,
            "error_type": "doba_api_error",
            "status_code": exc.status_code,
            "path": exc.path,
            "response_code": exc.response_code,
            "response_message": exc.response_message,
            "hint": (
                "Doba API reached the server but rejected the request. "
                "If responseMessage contains 'IP whitelist check failed', the current outbound IP is not yet accepted by Doba."
            ),
        }
        _print_json(payload)
        return
    if isinstance(exc, httpx.ConnectError):
        payload = {
            "ok": False,
            "error_type": "network_connect_error",
            "message": str(exc),
            "hint": (
                "The local process could not open an outbound connection. "
                "Check Windows firewall, proxy/VPN policy, endpoint protection, or corporate network restrictions before re-testing Doba."
            ),
        }
        _print_json(payload)
        return
    raise exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan Doba candidate products and publish them to Shopify one by one.")
    parser.add_argument(
        "--report-path",
        default="docs/audits/doba-shopify-live-publish-report.json",
        help="Checkpoint and result report path.",
    )
    parser.add_argument(
        "--target-country",
        default="US",
        help="Target destination country for Doba shipping cost estimation.",
    )
    parser.add_argument(
        "--channels",
        nargs="*",
        default=None,
        help="Shopify publication names to publish into.",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=20,
        help="Doba scan page size. Keep at 20 to align with detail and stock batch limits.",
    )
    parser.add_argument(
        "--inventory-threshold",
        type=int,
        default=10,
        help="Only variants with available inventory strictly greater than this threshold are publishable.",
    )
    parser.add_argument(
        "--list-min-inventory",
        type=int,
        default=DEFAULT_LIST_MIN_INVENTORY,
        help="Doba server-side minInventory filter to reduce low-stock scan noise.",
    )
    parser.add_argument(
        "--candidate-pool-path",
        default=str(DEFAULT_CANDIDATE_POOL_PATH),
        help="Qualified archive-driven publish candidate pool path.",
    )
    parser.add_argument(
        "--no-candidate-pool",
        action="store_true",
        help="Disable archive-driven candidate pool consumption and fall back to direct Doba scan.",
    )
    parser.add_argument(
        "--refresh-candidate-pool",
        action="store_true",
        help="Rebuild the local archive-driven candidate pool before publish.",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Ignore existing checkpoint and start from the beginning.",
    )
    parser.add_argument(
        "--max-successes",
        type=int,
        default=None,
        help="Optional safety valve for validation runs. Omit to scan until completion.",
    )
    args = parser.parse_args()

    try:
        result = publish_doba_products_live(
            report_path=args.report_path,
            target_country=args.target_country,
            channels=args.channels,
            page_size=args.page_size,
            inventory_threshold=args.inventory_threshold,
            list_min_inventory=args.list_min_inventory,
            candidate_pool_path=args.candidate_pool_path,
            prefer_candidate_pool=not args.no_candidate_pool,
            refresh_candidate_pool=args.refresh_candidate_pool,
            resume=not args.no_resume,
            max_successes=args.max_successes,
        )
        _print_json(result)
    except (DobaAPIError, httpx.ConnectError) as exc:
        _print_doba_connectivity_hint(exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
