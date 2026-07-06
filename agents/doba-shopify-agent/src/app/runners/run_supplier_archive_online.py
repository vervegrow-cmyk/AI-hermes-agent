from __future__ import annotations

import argparse
import json
import sys

import bootstrap
import httpx
from shared.clients.doba import DobaAPIError
from src.modules.supplier_archive.application.online_archive_runtime import (
    DEFAULT_ONLINE_ARCHIVE_CHECKPOINT_PATH,
    DEFAULT_ONLINE_ARCHIVE_ELIGIBLE_INVENTORY_THRESHOLD,
    DEFAULT_ONLINE_ARCHIVE_PAGE_SIZE,
    DEFAULT_ONLINE_ARCHIVE_REPORT_PATH,
    DEFAULT_ONLINE_ARCHIVE_TARGET_COUNTRY,
    run_doba_online_archive,
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
    parser = argparse.ArgumentParser(description="Archive Doba online catalog pages into the local supplier archive runtime.")
    parser.add_argument(
        "--report-path",
        default=str(DEFAULT_ONLINE_ARCHIVE_REPORT_PATH),
        help="JSON report path for archive progress and summary.",
    )
    parser.add_argument(
        "--checkpoint-path",
        default=str(DEFAULT_ONLINE_ARCHIVE_CHECKPOINT_PATH),
        help="Checkpoint path for resumable online archive progress.",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=DEFAULT_ONLINE_ARCHIVE_PAGE_SIZE,
        help="Doba page size. Keep at 20 to align with detail, stock, and shipping batch limits.",
    )
    parser.add_argument(
        "--target-country",
        default=DEFAULT_ONLINE_ARCHIVE_TARGET_COUNTRY,
        help="Ship-to country used for Doba shipping cost estimation while archiving.",
    )
    parser.add_argument(
        "--min-inventory",
        type=int,
        default=None,
        help="Optional Doba list minInventory server-side filter. Omit to continue full online archive.",
    )
    parser.add_argument(
        "--archive-eligible-only",
        action="store_true",
        help="Only persist variants whose ship-from resolves to United States and whose inventory is above the eligible threshold.",
    )
    parser.add_argument(
        "--eligible-inventory-threshold",
        type=int,
        default=DEFAULT_ONLINE_ARCHIVE_ELIGIBLE_INVENTORY_THRESHOLD,
        help="Archive focus inventory threshold used with --archive-eligible-only. Publish-equivalent rule is strictly greater than this value.",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Ignore existing online archive checkpoint and start from the beginning.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Optional limit for validation runs. Omit to continue until Doba list scan completes.",
    )
    args = parser.parse_args()

    try:
        result = run_doba_online_archive(
            report_path=args.report_path,
            checkpoint_path=args.checkpoint_path,
            page_size=args.page_size,
            target_country=args.target_country,
            min_inventory=args.min_inventory,
            archive_eligible_only=args.archive_eligible_only,
            eligible_inventory_threshold=(args.eligible_inventory_threshold if args.archive_eligible_only else None),
            resume=not args.no_resume,
            max_pages=args.max_pages,
        )
        _print_json(result)
    except (DobaAPIError, httpx.ConnectError) as exc:
        _print_doba_connectivity_hint(exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
