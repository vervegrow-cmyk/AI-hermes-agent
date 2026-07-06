#!/usr/bin/env python3
"""Upload local image sources found in HTML to ImgBB and rewrite the HTML."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path


SRC_PATTERN = re.compile(r'(<img\b[^>]*\bsrc=")([^"]+)(")', re.IGNORECASE)


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        key, value = s.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def is_remote(src: str) -> bool:
    lower = src.lower()
    return (
        lower.startswith("http://")
        or lower.startswith("https://")
        or lower.startswith("//")
        or lower.startswith("data:")
    )


def resolve_local_src(src: str, html_path: Path) -> Path | None:
    candidate = Path(src)
    if candidate.is_absolute() and candidate.exists():
        return candidate
    candidate = (html_path.parent / src).resolve()
    if candidate.exists():
        return candidate
    return None


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
    original_url = body.get("image", {}).get("url") or body.get("url")
    display_url = body.get("display_url") or body.get("medium", {}).get("url") or original_url
    return {
        "source_path": str(path),
        "url": original_url,
        "display_url": display_url,
        "delete_url": body.get("delete_url"),
    }


def rewrite_html(html: str, html_path: Path, api_key: str) -> tuple[str, list[dict]]:
    uploads: dict[str, dict] = {}
    manifest: list[dict] = []

    def replacer(match: re.Match[str]) -> str:
        prefix, src, suffix = match.groups()
        if is_remote(src):
            return match.group(0)
        local_path = resolve_local_src(src, html_path)
        if not local_path:
            return match.group(0)
        key = str(local_path)
        if key not in uploads:
            uploads[key] = upload_image(local_path, api_key)
            manifest.append(
                {
                    "original_src": src,
                    "local_path": str(local_path),
                    "public_url": uploads[key]["url"],
                    "display_url": uploads[key]["display_url"],
                    "delete_url": uploads[key]["delete_url"],
                }
            )
        return f"{prefix}{uploads[key]['url']}{suffix}"

    return SRC_PATTERN.sub(replacer, html), manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload local HTML images to ImgBB and rewrite src URLs.")
    parser.add_argument("input", help="Path to HTML file")
    parser.add_argument("-o", "--output", help="Rewritten HTML output path")
    parser.add_argument("--manifest", help="Optional JSON manifest output path")
    parser.add_argument("--env-file", help="Optional .env file to load before upload")
    args = parser.parse_args()

    if args.env_file:
        load_env(Path(args.env_file))

    api_key = os.environ.get("IMGBB_API_KEY")
    if not api_key:
        raise SystemExit("IMGBB_API_KEY is not configured.")

    input_path = Path(args.input).resolve()
    html = input_path.read_text(encoding="utf-8")
    rewritten_html, manifest = rewrite_html(html, input_path, api_key)

    output_path = Path(args.output) if args.output else input_path.with_name(input_path.stem + "-imgbb" + input_path.suffix)
    output_path.write_text(rewritten_html, encoding="utf-8")

    manifest_path = Path(args.manifest) if args.manifest else output_path.with_name(output_path.stem + "-manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(output_path)
    print(manifest_path)


if __name__ == "__main__":
    main()
