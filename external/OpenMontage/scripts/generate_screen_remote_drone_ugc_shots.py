from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.video.video_selector import VideoSelector


OUTPUT_DIR = ROOT_DIR / "outputs" / "tiktok_screen_remote_drone_v3"
CLIPS_DIR = OUTPUT_DIR / "generated_shots"
REPORT_PATH = OUTPUT_DIR / "generated_shots_report.json"
MARKDOWN_LOG_PATH = OUTPUT_DIR / "generated_shots_log.md"

PROVIDER_ORDER = [
    "seedance",
    "kling",
    "veo",
    "vidu",
    "ark",
    "pixverse",
    "minimax",
    "heygen",
]


@dataclass
class ShotSpec:
    shot_id: str
    title: str
    reference_image: str
    duration: str
    prompt: str


SHOT_SPECS = [
    ShotSpec(
        shot_id="shot_01_hand_place_drone",
        title="Hand places drone on table",
        reference_image="assets/products/screen_remote_drone/01_package.jpg",
        duration="5",
        prompt=(
            "Single continuous shot, vertical TikTok UGC product demo, a stylish young woman beauty-tech "
            "creator in a casual home setup places a compact black foldable beginner drone onto a clean "
            "light-wood desk, then sets the screen remote beside it, her hands and upper body briefly "
            "visible, attractive but realistic lifestyle creator look, natural indoor daylight, friendly "
            "review vibe, soft handheld camera micro-movement, product remains visually consistent with "
            "the reference, no logos added, no fake UI, no extra accessories beyond the product kit, "
            "photorealistic."
        ),
    ),
    ShotSpec(
        shot_id="shot_02_hold_remote_screen",
        title="Hands holding screen remote",
        reference_image="assets/products/screen_remote_drone/02_screen_remote.jpg",
        duration="5",
        prompt=(
            "Single continuous shot, realistic vertical TikTok UGC clip, a young woman creator holds a "
            "black screen remote controller for a beginner drone close to camera, her face softly visible "
            "in the background with a pleased expression, the built-in screen glows and is clearly visible, "
            "thumbs naturally resting on the sticks, modern gadget review desk setup, clean background, "
            "subtle handheld motion, photoreal skin and textures, product design must stay consistent "
            "with the reference image."
        ),
    ),
    ShotSpec(
        shot_id="shot_03_press_takeoff_button",
        title="Finger presses takeoff button",
        reference_image="assets/products/screen_remote_drone/04_one_click.jpg",
        duration="5",
        prompt=(
            "Macro close-up, vertical TikTok UGC product test, a young woman's manicured index finger "
            "presses the one-click takeoff button on a black beginner drone remote controller, satisfying "
            "tactile motion, part of her face and smile softly blurred in the background, the remote "
            "matches the reference product, realistic hand, natural lighting, shallow depth of field, "
            "no sci-fi interface, no text rendered in video, photorealistic."
        ),
    ),
    ShotSpec(
        shot_id="shot_04_drone_hover",
        title="Drone takeoff and hover",
        reference_image="assets/products/screen_remote_drone/04_one_click.jpg",
        duration="5",
        prompt=(
            "Single continuous shot, realistic vertical TikTok UGC test clip, a compact black foldable "
            "beginner drone lifts off safely from a clean indoor table and hovers steadily at chest height, "
            "a young woman user stands behind it holding the remote, impressed and slightly smiling, calm "
            "beginner-friendly demo, stable hovering, natural room lighting, the drone remains visually "
            "consistent with the reference, no dangerous environment, no crowds, no windows, photorealistic."
        ),
    ),
    ShotSpec(
        shot_id="shot_05_pack_into_case",
        title="Fold and pack into case",
        reference_image="assets/products/screen_remote_drone/01_package.jpg",
        duration="5",
        prompt=(
            "Single continuous shot, realistic vertical TikTok UGC lifestyle clip, a stylish young woman "
            "folds up a compact black beginner drone and places it with the screen remote into a small "
            "black carrying case on a desk, hands clearly visible, quick practical pack-up moment, casual "
            "tech gadget vibe, natural light, product and case stay consistent with the reference image, "
            "no extra props, photorealistic."
        ),
    ),
]


def load_shared_env() -> None:
    for env_file in [ROOT_DIR.parent.parent / ".env", ROOT_DIR / ".env"]:
        if env_file.exists():
            load_dotenv(env_file, override=False)


def ensure_dirs() -> None:
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)


def generate_one_shot(selector: VideoSelector, shot: ShotSpec) -> dict[str, Any]:
    shot_result: dict[str, Any] = {
        "shot_id": shot.shot_id,
        "title": shot.title,
        "reference_image": shot.reference_image,
        "prompt": shot.prompt,
        "attempts": [],
        "success": False,
        "output_path": None,
        "total_cost_usd": 0.0,
    }

    reference_path = ROOT_DIR / shot.reference_image
    if not reference_path.exists():
        shot_result["error"] = f"Missing reference image: {reference_path}"
        return shot_result

    for provider in PROVIDER_ORDER:
        output_path = CLIPS_DIR / f"{shot.shot_id}_{provider}.mp4"
        inputs = {
            "prompt": shot.prompt,
            "preferred_provider": provider,
            "operation": "image_to_video",
            "aspect_ratio": "9:16",
            "duration": shot.duration,
            "resolution": "720p",
            "reference_image_path": str(reference_path),
            "output_path": str(output_path),
        }
        result = selector.execute(inputs)
        attempt = {
            "provider": provider,
            "success": result.success,
            "error": result.error,
            "cost_usd": result.cost_usd,
            "selected_provider": result.data.get("selected_provider"),
            "selected_tool": result.data.get("selected_tool"),
            "artifacts": result.artifacts,
        }
        shot_result["attempts"].append(attempt)
        shot_result["total_cost_usd"] += result.cost_usd

        if result.success:
            mp4_artifact = next(
                (artifact for artifact in result.artifacts if artifact.lower().endswith(".mp4")),
                str(output_path),
            )
            shot_result["success"] = True
            shot_result["output_path"] = mp4_artifact
            shot_result["final_provider"] = result.data.get("selected_provider", provider)
            shot_result["final_tool"] = result.data.get("selected_tool")
            return shot_result

    shot_result["error"] = "All providers failed."
    return shot_result


def write_reports(results: list[dict[str, Any]]) -> None:
    REPORT_PATH.write_text(
        json.dumps(
            {
                "output_dir": str(CLIPS_DIR),
                "provider_order": PROVIDER_ORDER,
                "shots": results,
                "total_cost_usd": round(sum(item["total_cost_usd"] for item in results), 4),
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    lines = [
        "# Screen Remote Drone UGC Main Shots",
        "",
        f"- Output directory: `{CLIPS_DIR}`",
        f"- Total cost (reported): `${sum(item['total_cost_usd'] for item in results):.2f}`",
        "",
    ]
    for item in results:
        lines.append(f"## {item['shot_id']}")
        lines.append(f"- Title: {item['title']}")
        lines.append(f"- Success: {item['success']}")
        if item.get("output_path"):
            lines.append(f"- Output: `{item['output_path']}`")
        if item.get("final_provider"):
            lines.append(f"- Final provider: `{item['final_provider']}`")
        if item.get("final_tool"):
            lines.append(f"- Final tool: `{item['final_tool']}`")
        lines.append(f"- Cost: `${item['total_cost_usd']:.2f}`")
        if item.get("error"):
            lines.append(f"- Error: {item['error']}")
        lines.append("- Attempts:")
        for attempt in item["attempts"]:
            lines.append(
                f"  - `{attempt['provider']}` -> success={attempt['success']}, "
                f"tool={attempt['selected_tool']}, cost=${attempt['cost_usd']:.2f}, "
                f"error={attempt['error']}"
            )
        lines.append("")
    MARKDOWN_LOG_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    load_shared_env()
    ensure_dirs()
    selector = VideoSelector()
    results = [generate_one_shot(selector, shot) for shot in SHOT_SPECS]
    write_reports(results)

    print("DONE")
    print(f"Shots dir: {CLIPS_DIR}")
    print(f"Report: {REPORT_PATH}")
    print(f"Log: {MARKDOWN_LOG_PATH}")
    print(f"Successful shots: {sum(1 for item in results if item['success'])}/{len(results)}")
    print(f"Total cost: ${sum(item['total_cost_usd'] for item in results):.2f}")
    for item in results:
        status = "OK" if item["success"] else "FAIL"
        print(f"{status} {item['shot_id']}: {item.get('output_path') or item.get('error')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
