from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.graphics.comfyui_image import ComfyUIImage


DEFAULT_WORKFLOW = ROOT_DIR / "assets" / "workflows" / "comfyui" / "keyframe_lock_workflow_api.json"


def load_prompts(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        if isinstance(payload.get("prompts"), list):
            return list(payload["prompts"])
        if isinstance(payload.get("keyframe_prompts"), list):
            return list(payload["keyframe_prompts"])
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate normalized keyframes via ComfyUI for frame-lock planning.")
    parser.add_argument("--plan", required=True, help="Path to keyframe prompt plan JSON.")
    parser.add_argument("--product-dir", required=True, help="Directory containing referenced source images.")
    parser.add_argument(
        "--workflow",
        default=str(DEFAULT_WORKFLOW),
        help="Path to the ComfyUI keyframe lock workflow JSON.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(ROOT_DIR / "outputs" / "keyframe_lock_test"),
        help="Directory for generated keyframes.",
    )
    args = parser.parse_args()

    tool = ComfyUIImage()
    prompts = load_prompts(Path(args.plan))
    product_dir = Path(args.product_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, object]] = []
    for index, prompt_def in enumerate(prompts, start=1):
        source_raw = (
            prompt_def.get("source_image")
            or prompt_def.get("source_path")
            or prompt_def.get("reference_image")
            or prompt_def.get("reference_image_path")
        )
        if not source_raw:
            results.append(
                {
                    "success": False,
                    "id": prompt_def.get("id", f"keyframe_{index:02d}"),
                    "error": "source_image missing in plan entry",
                }
            )
            continue

        source_path = Path(str(source_raw))
        if not source_path.is_absolute():
            source_path = (product_dir / source_path).resolve()

        output_path = output_dir / f"{prompt_def.get('id', f'keyframe_{index:02d}')}.png"
        result = tool.execute(
            {
                "prompt": str(prompt_def.get("prompt") or prompt_def.get("target_frame_description") or ""),
                "generation_mode": "edit",
                "image_path": str(source_path),
                "workflow_path": str(Path(args.workflow).resolve()),
                "output_node": "13",
                "width": 1080,
                "height": 1920,
                "upscale_method": "lanczos",
                "output_path": str(output_path),
                "workflow_name": "keyframe_lock_workflow_api",
                "workflow_model": "keyframe_lock_reference_prep",
            }
        )
        results.append(
            {
                "success": result.success,
                "id": prompt_def.get("id", f"keyframe_{index:02d}"),
                "source_path": str(source_path),
                "output_path": str(result.data.get("output")) if result.success else None,
                "error": result.error,
            }
        )

    print(json.dumps({"success": all(item["success"] for item in results), "results": results}, ensure_ascii=False, indent=2))
    return 0 if all(item["success"] for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
