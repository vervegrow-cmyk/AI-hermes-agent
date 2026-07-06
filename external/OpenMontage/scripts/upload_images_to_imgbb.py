#!/usr/bin/env python
"""
Upload one or more local images to ImgBB and print public HTTPS URLs.

Usage:
  python scripts/upload_images_to_imgbb.py image1.png image2.webp
  python scripts/upload_images_to_imgbb.py preview-assets/safety-alarm/*

Environment:
  IMGBB_API_KEY=your_real_key
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


API_ENDPOINT = "https://api.imgbb.com/1/upload"


def upload_image(path: Path, api_key: str) -> dict:
    image_bytes = path.read_bytes()
    encoded_image = base64.b64encode(image_bytes).decode("ascii")

    payload = urllib.parse.urlencode(
        {
            "key": api_key,
            "name": path.stem,
            "image": encoded_image,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        API_ENDPOINT,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Upload local images to ImgBB and print public HTTPS URLs."
    )
    parser.add_argument("paths", nargs="+", help="Image files to upload")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    api_key = os.getenv("IMGBB_API_KEY", "").strip()
    if not api_key:
        print("Missing IMGBB_API_KEY environment variable.", file=sys.stderr)
        print("Set it in your local .env or shell before running this script.", file=sys.stderr)
        return 1

    exit_code = 0

    for raw_path in args.paths:
        path = Path(raw_path).expanduser().resolve()
        if not path.exists() or not path.is_file():
            print(f"[skip] Not a file: {raw_path}", file=sys.stderr)
            exit_code = 1
            continue

        mime_type, _ = mimetypes.guess_type(path.name)
        if mime_type and not mime_type.startswith("image/"):
            print(f"[skip] Not an image: {raw_path}", file=sys.stderr)
            exit_code = 1
            continue

        try:
            result = upload_image(path, api_key)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            print(f"[error] Upload failed for {path.name}: HTTP {exc.code}", file=sys.stderr)
            print(body, file=sys.stderr)
            exit_code = 1
            continue
        except urllib.error.URLError as exc:
            print(f"[error] Upload failed for {path.name}: {exc}", file=sys.stderr)
            exit_code = 1
            continue

        if not result.get("success"):
            print(f"[error] Upload failed for {path.name}: {result}", file=sys.stderr)
            exit_code = 1
            continue

        data = result.get("data", {})
        print(f"{path.name}")
        print(f"  url: {data.get('url')}")
        print(f"  viewer: {data.get('url_viewer')}")
        print(f"  delete: {data.get('delete_url')}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
