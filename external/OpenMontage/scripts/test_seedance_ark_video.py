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
    parser = argparse.ArgumentParser(description="Test the official Ark Seedance 2.0 provider.")
    parser.add_argument("--prompt", required=True, help="Prompt for Seedance 2.0.")
    parser.add_argument(
        "--operation",
        default="text_to_video",
        choices=["text_to_video", "image_to_video", "reference_to_video"],
        help="Seedance generation mode.",
    )
    parser.add_argument(
        "--duration",
        default="4",
        help="Duration in seconds, or auto.",
    )
    parser.add_argument(
        "--aspect-ratio",
        default="9:16",
        help="Aspect ratio, e.g. 9:16, 16:9, 1:1.",
    )
    parser.add_argument(
        "--resolution",
        default="720p",
        help="Resolution hint, e.g. 480p, 720p, 1080p.",
    )
    parser.add_argument(
        "--model-variant",
        default="mini",
        choices=["mini", "standard", "fast"],
        help="Official Ark Seedance model variant.",
    )
    parser.add_argument(
        "--reference-image",
        action="append",
        dest="reference_images",
        default=[],
        help="Optional local reference image path. Repeat for multiple images.",
    )
    parser.add_argument(
        "--reference-image-url",
        action="append",
        dest="reference_image_urls",
        default=[],
        help="Optional remote reference image URL. Repeat for multiple URLs.",
    )
    parser.add_argument(
        "--reference-video-url",
        action="append",
        dest="reference_video_urls",
        default=[],
        help="Optional reference video URL. Repeat for multiple URLs.",
    )
    parser.add_argument(
        "--reference-audio-url",
        action="append",
        dest="reference_audio_urls",
        default=[],
        help="Optional reference audio URL. Repeat for multiple URLs.",
    )
    parser.add_argument(
        "--negative-prompt",
        help="Optional negative prompt.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Optional random seed.",
    )
    parser.add_argument(
        "--generate-audio",
        action="store_true",
        help="Request native synchronized audio generation.",
    )
    parser.add_argument(
        "--output-path",
        default=str(ROOT_DIR / "outputs" / "seedance_ark_test.mp4"),
        help="Where to save the generated video.",
    )
    args = parser.parse_args()

    registry.ensure_discovered()
    tool = registry.get("seedance_ark_video")
    if tool is None:
        print("seedance_ark_video tool was not discovered.", file=sys.stderr)
        return 1

    payload = {
        "prompt": args.prompt,
        "operation": args.operation,
        "duration": args.duration,
        "aspect_ratio": args.aspect_ratio,
        "resolution": args.resolution,
        "model_variant": args.model_variant,
        "reference_image_paths": args.reference_images,
        "reference_image_urls": args.reference_image_urls,
        "reference_video_urls": args.reference_video_urls,
        "reference_audio_urls": args.reference_audio_urls,
        "generate_audio": args.generate_audio,
        "output_path": args.output_path,
    }
    if args.negative_prompt:
        payload["negative_prompt"] = args.negative_prompt
    if args.seed is not None:
        payload["seed"] = args.seed

    result = tool.execute(payload)
    print(
        json.dumps(
            {
                "success": result.success,
                "error": result.error,
                "data": result.data,
                "artifacts": result.artifacts,
                "cost_usd": result.cost_usd,
                "duration_seconds": result.duration_seconds,
                "request": payload,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
