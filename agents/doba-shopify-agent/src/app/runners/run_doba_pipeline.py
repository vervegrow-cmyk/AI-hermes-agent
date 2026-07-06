from __future__ import annotations

import argparse
import json
import sys

import bootstrap
from src.modules.doba_pipeline import run_doba_pipeline


def _print_json(payload: dict) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        print(text)
    except UnicodeEncodeError:
        print(text.encode("utf-8", errors="replace").decode("utf-8", errors="replace"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the unified Doba pipeline orchestration modes.")
    parser.add_argument("--mode", default="archive-and-publish")
    parser.add_argument("--archive-report-path", default="docs/audits/doba-online-archive-us-focus-report.json")
    parser.add_argument("--archive-checkpoint-path", default="data/runtime/supplier_archive/doba_online_archive_us_focus_checkpoint.json")
    parser.add_argument("--publish-report-path", default="docs/audits/doba-shopify-live-publish-candidate-only-report.json")
    parser.add_argument("--candidate-pool-path", default="data/runtime/shopify_listing/doba_publish_candidates.json")
    parser.add_argument("--target-country", default="US")
    parser.add_argument("--inventory-threshold", type=int, default=10)
    parser.add_argument("--list-min-inventory", type=int, default=11)
    parser.add_argument("--eligible-inventory-threshold", type=int, default=10)
    parser.add_argument("--page-size", type=int, default=20)
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument("--max-successes", type=int, default=None)
    parser.add_argument("--channels", nargs="*", default=["Inbox", "Shop", "Pinterest", "Facebook & Instagram"])
    parser.add_argument("--incremental", action="store_true")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--no-candidate-pool", action="store_true")
    parser.add_argument("--refresh-candidate-pool", action="store_true")
    parser.add_argument("--archive-eligible-only", action="store_true")
    parser.add_argument("--stream-publish", action="store_true")
    args = parser.parse_args()

    result = run_doba_pipeline(
        {
            "mode": args.mode,
            "archive_report_path": args.archive_report_path,
            "archive_checkpoint_path": args.archive_checkpoint_path,
            "publish_report_path": args.publish_report_path,
            "candidate_pool_path": args.candidate_pool_path,
            "target_country": args.target_country,
            "inventory_threshold": args.inventory_threshold,
            "list_min_inventory": args.list_min_inventory,
            "eligible_inventory_threshold": args.eligible_inventory_threshold,
            "page_size": args.page_size,
            "max_pages": args.max_pages,
            "max_successes": args.max_successes,
            "channels": args.channels,
            "incremental": args.incremental,
            "no_resume": args.no_resume,
            "no_candidate_pool": args.no_candidate_pool,
            "refresh_candidate_pool": args.refresh_candidate_pool,
            "archive_eligible_only": args.archive_eligible_only,
            "stream_publish": args.stream_publish,
        }
    )
    _print_json(result)


if __name__ == "__main__":
    main()
