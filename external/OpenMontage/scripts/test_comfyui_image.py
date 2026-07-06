from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools._comfyui.client import ComfyUIClient, ComfyUIError


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Test a ComfyUI image workflow with optional prompt and image upload support."
    )
    parser.add_argument("--workflow", required=True, help="Path to the workflow_api.json file.")
    parser.add_argument(
        "--prompt",
        help="Prompt text to inject into a workflow node if a text field is present.",
    )
    parser.add_argument(
        "--input-image",
        help="Optional local image to upload for workflows that use a LoadImage node.",
    )
    parser.add_argument(
        "--input-glob",
        help="Optional glob pattern for batch processing, e.g. D:\\\\桌面文件下载\\\\ebay-product-*.jpg",
    )
    parser.add_argument("--output-node", default="13", help="Output node id for the workflow.")
    parser.add_argument("--width", type=int, default=1080, help="Optional output width patch.")
    parser.add_argument("--height", type=int, default=1920, help="Optional output height patch.")
    parser.add_argument(
        "--upscale-method",
        default="lanczos",
        help="Optional ImageScale upscale_method patch.",
    )
    parser.add_argument(
        "--output-path",
        default=str(ROOT_DIR / "outputs" / "comfyui_test_image.png"),
        help="Where to save the generated image.",
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory for batch runs. Defaults to outputs/comfyui_product_assets.",
    )
    args = parser.parse_args()

    client = ComfyUIClient()
    health = client.health_check()
    if not health.get("ok"):
        print(json.dumps(health, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    workflow = ComfyUIClient.load_workflow(Path(args.workflow))

    def build_replacements(output_prefix: str, input_image: Path | None) -> dict[str, dict[str, object]]:
        replacements: dict[str, dict[str, object]] = {
            "13": {"filename_prefix": output_prefix},
        }

        if args.prompt:
            for node_id, node in workflow.items():
                inputs = node.get("inputs", {})
                if "text" in inputs:
                    replacements.setdefault(node_id, {})["text"] = args.prompt

        if input_image is not None:
            uploaded_name = client.upload_image(input_image, input_image.name)
            for node_id, node in workflow.items():
                if node.get("class_type") == "LoadImage":
                    replacements.setdefault(node_id, {})["image"] = uploaded_name

        for node_id, node in workflow.items():
            inputs = node.get("inputs", {})
            if "width" in inputs:
                replacements.setdefault(node_id, {})["width"] = args.width
            if "height" in inputs:
                replacements.setdefault(node_id, {})["height"] = args.height
            if "upscale_method" in inputs:
                replacements.setdefault(node_id, {})["upscale_method"] = args.upscale_method
        return replacements

    batch_pattern = args.input_glob
    if batch_pattern:
        input_files = [Path(path) for path in sorted(glob.glob(batch_pattern))]
        if not input_files:
            print(
                json.dumps(
                    {"success": False, "error": f"No files matched input glob: {batch_pattern}"},
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 1

        output_dir = Path(args.output_dir or (ROOT_DIR / "outputs" / "comfyui_product_assets"))
        output_dir.mkdir(parents=True, exist_ok=True)
        results: list[dict[str, object]] = []
        for image_path in input_files:
            replacements = build_replacements(image_path.stem, image_path)
            try:
                response = client.run_workflow(
                    args.workflow,
                    replacements=replacements,
                    output_dir=output_dir,
                    output_node=args.output_node,
                )
            except ComfyUIError as exc:
                print(
                    json.dumps(
                        {
                            "success": False,
                            "error": str(exc),
                            "failed_input": str(image_path),
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return 1

            results.append(
                {
                    "input_file": str(image_path),
                    "prompt_id": response["prompt_id"],
                    "output_files": response["output_files"],
                }
            )

        print(
            json.dumps(
                {
                    "success": True,
                    "mode": "batch",
                    "count": len(results),
                    "output_dir": str(output_dir),
                    "results": results,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    input_image: Path | None = None
    if args.input_image:
        input_image = Path(args.input_image)
        if not input_image.exists():
            print(
                json.dumps(
                    {
                        "success": False,
                        "error": f"Input image not found: {input_image}",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 1

    output_path = Path(args.output_path)
    replacements = build_replacements(output_path.stem, input_image)

    try:
        response = client.run_workflow(
            args.workflow,
            replacements=replacements,
            output_dir=output_path.parent,
            output_node=args.output_node,
        )
    except ComfyUIError as exc:
        print(json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    print(
        json.dumps(
            {
                "success": True,
                "mode": "single",
                "prompt_id": response["prompt_id"],
                "output_files": response["output_files"],
                "output_node": response.get("output_node"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
