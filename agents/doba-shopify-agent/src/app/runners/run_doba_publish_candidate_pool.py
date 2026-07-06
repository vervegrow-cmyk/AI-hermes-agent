from __future__ import annotations

import argparse
import json
import sys

import bootstrap
from src.modules.shopify_listing.application.live_publish_runtime import (
    DEFAULT_CANDIDATE_POOL_PATH,
    build_doba_publish_candidate_pool,
)


def _print_json(payload: dict) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        print(text)
    except UnicodeEncodeError:
        print(text.encode("utf-8", errors="replace").decode("utf-8", errors="replace"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the archive-driven Doba publish candidate pool.")
    parser.add_argument(
        "--candidate-pool-path",
        default=str(DEFAULT_CANDIDATE_POOL_PATH),
        help="Output path for the qualified candidate pool JSON file.",
    )
    parser.add_argument(
        "--target-country",
        default="US",
        help="Target ship-to country used for candidate qualification.",
    )
    parser.add_argument(
        "--inventory-threshold",
        type=int,
        default=10,
        help="Only variants with available inventory strictly greater than this threshold are qualified.",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Refresh only changed archive groups when runtime state exists.",
    )
    args = parser.parse_args()

    result = build_doba_publish_candidate_pool(
        candidate_pool_path=args.candidate_pool_path,
        target_country=args.target_country,
        inventory_threshold=args.inventory_threshold,
        incremental=args.incremental,
    )
    _print_json(result)


if __name__ == "__main__":
    main()
