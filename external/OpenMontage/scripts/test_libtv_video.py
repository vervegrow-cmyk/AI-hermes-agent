from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.tool_registry import registry


def main() -> int:
    parser = argparse.ArgumentParser(description="Test the LibTV video provider tool.")
    parser.add_argument("--prompt", required=True, help="Prompt for the LibTV session.")
    parser.add_argument("--duration", default="10", help="Desired duration hint in seconds.")
    parser.add_argument("--aspect-ratio", default="9:16", help="Aspect ratio hint.")
    parser.add_argument(
        "--product-image",
        action="append",
        dest="product_images",
        default=[],
        help="Optional product image path. Repeat for multiple images.",
    )
    parser.add_argument(
        "--style-notes",
        default="High-energy TikTok UGC with real product fidelity.",
        help="Optional style notes appended to the prompt.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(ROOT_DIR / "outputs" / "libtv_test"),
        help="Where to store downloaded LibTV outputs.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=1800,
        help="Maximum time to wait for LibTV generation, in seconds.",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=10,
        help="Polling interval for LibTV node status, in seconds.",
    )
    args = parser.parse_args()

    registry.ensure_discovered()
    tool = registry.get("libtv_video")
    if tool is None:
        print("libtv_video tool was not discovered.", file=sys.stderr)
        return 1

    result = tool.execute(
        {
            "prompt": args.prompt,
            "duration": args.duration,
            "aspect_ratio": args.aspect_ratio,
            "product_images": args.product_images,
            "style_notes": args.style_notes,
            "output_dir": args.output_dir,
            "timeout": args.timeout,
            "poll_interval": args.poll_interval,
        }
    )
    print(json.dumps(
        {
            "success": result.success,
            "error": result.error,
            "data": result.data,
            "artifacts": result.artifacts,
            "cost_usd": result.cost_usd,
            "duration_seconds": result.duration_seconds,
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
