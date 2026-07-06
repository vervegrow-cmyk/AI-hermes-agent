#!/usr/bin/env python3
"""Upload one image or all images in a folder to ImgBB and print public URLs."""

from __future__ import annotations

import argparse
import base64
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        key, value = s.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def list_images(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    if not path.is_dir():
        raise FileNotFoundError(f"Path not found: {path}")
    return sorted(
        p for p in path.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )


def upload_image(path: Path, api_key: str) -> dict:
    payload = urllib.parse.urlencode(
        {
            "key": api_key,
            "name": path.stem,
            "image": base64.b64encode(path.read_bytes()).decode("ascii"),
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.imgbb.com/1/upload",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        data = json.loads(response.read().decode("utf-8"))
    if not data.get("success"):
        raise RuntimeError(f"ImgBB upload failed for {path}")
    body = data["data"]
    return {
        "source_path": str(path),
        "url": body.get("url"),
        "display_url": body.get("display_url"),
        "delete_url": body.get("delete_url"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload one image or a folder of images to ImgBB.")
    parser.add_argument("input", help="Path to an image file or folder")
    parser.add_argument("-o", "--output", help="Optional JSON output manifest path")
    parser.add_argument("--env-file", help="Optional .env file to load before upload")
    args = parser.parse_args()

    if args.env_file:
        load_env(Path(args.env_file))

    api_key = os.environ.get("IMGBB_API_KEY")
    if not api_key:
        raise SystemExit("IMGBB_API_KEY is not configured.")

    input_path = Path(args.input)
    images = list_images(input_path)
    if not images:
        raise SystemExit("No supported image files found.")

    results = [upload_image(image, api_key) for image in images]

    if args.output:
        output_path = Path(args.output)
    elif input_path.is_dir():
        output_path = input_path / "imgbb-upload-manifest.json"
    else:
        output_path = input_path.with_name(input_path.stem + "-imgbb.json")

    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(output_path)
    for item in results:
        print(f"{item['source_path']} -> {item['display_url'] or item['url']}")


if __name__ == "__main__":
    main()
