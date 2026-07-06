from __future__ import annotations

import argparse
import json
import sys

import bootstrap
from src.modules.doba_pipeline.application.production_runtime import (
    DEFAULT_ARCHIVE_CHECKPOINT_PATH,
    DEFAULT_ARCHIVE_REPORT_PATH,
    DEFAULT_CANDIDATE_POOL_PATH,
    DEFAULT_PUBLISH_CHECKPOINT_PATH,
    DEFAULT_PUBLISH_REPORT_PATH,
    DEFAULT_RUNTIME_REPORT_PATH,
    _write_console_line,
    run_doba_shopify_runtime,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Doba-Shopify-Agent V2 Production Runtime Pipeline.")
    parser.add_argument("--mode", default="full-runtime")
    parser.add_argument("--target-country", default="US")
    parser.add_argument("--inventory-threshold", type=int, default=10)
    parser.add_argument("--list-min-inventory", type=int, default=11)
    parser.add_argument("--eligible-inventory-threshold", type=int, default=10)
    parser.add_argument("--page-size", type=int, default=20)
    parser.add_argument("--stream-publish", action="store_true")
    parser.add_argument("--incremental", action="store_true")
    parser.add_argument("--archive-eligible-only", action="store_true")
    parser.add_argument("--channels", default="shop,inbox,pinterest,facebook")
    parser.add_argument("--archive-report-path", default=DEFAULT_ARCHIVE_REPORT_PATH)
    parser.add_argument("--archive-checkpoint-path", default=DEFAULT_ARCHIVE_CHECKPOINT_PATH)
    parser.add_argument("--publish-report-path", default=DEFAULT_PUBLISH_REPORT_PATH)
    parser.add_argument("--publish-checkpoint-path", default=DEFAULT_PUBLISH_CHECKPOINT_PATH)
    parser.add_argument("--candidate-pool-path", default=DEFAULT_CANDIDATE_POOL_PATH)
    parser.add_argument("--runtime-report-path", default=DEFAULT_RUNTIME_REPORT_PATH)
    parser.add_argument("--no-resume", action="store_true")
    return parser


def _print_json(payload: dict) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        _write_console_line(line)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    result = run_doba_shopify_runtime(
        {
            "mode": args.mode,
            "target_country": args.target_country,
            "inventory_threshold": args.inventory_threshold,
            "list_min_inventory": args.list_min_inventory,
            "eligible_inventory_threshold": args.eligible_inventory_threshold,
            "page_size": args.page_size,
            "stream_publish": args.stream_publish,
            "incremental": args.incremental,
            "archive_eligible_only": args.archive_eligible_only,
            "channels": args.channels,
            "archive_report_path": args.archive_report_path,
            "archive_checkpoint_path": args.archive_checkpoint_path,
            "publish_report_path": args.publish_report_path,
            "publish_checkpoint_path": args.publish_checkpoint_path,
            "candidate_pool_path": args.candidate_pool_path,
            "runtime_report_path": args.runtime_report_path,
            "no_resume": args.no_resume,
        }
    )
    _print_json(result)


if __name__ == "__main__":
    main()
