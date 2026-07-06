#!/usr/bin/env python3
"""Finalize an eBay HTML file by uploading local images to ImgBB and exporting body HTML."""

from __future__ import annotations

import argparse
from pathlib import Path

from extract_html_body import extract_body
from upload_html_images_to_imgbb import load_env, rewrite_html


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Upload local HTML images to ImgBB, rewrite the full HTML, and export a body-only HTML file."
    )
    parser.add_argument("input", help="Path to the full HTML file")
    parser.add_argument("--env-file", help="Optional .env file to load before upload")
    parser.add_argument("--output-full", help="Output path for rewritten full HTML")
    parser.add_argument("--output-body", help="Output path for rewritten body HTML")
    parser.add_argument("--manifest", help="Optional JSON manifest output path")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()

    if args.env_file:
        load_env(Path(args.env_file))

    import os

    api_key = os.environ.get("IMGBB_API_KEY")
    if not api_key:
        raise SystemExit("IMGBB_API_KEY is not configured.")

    html = input_path.read_text(encoding="utf-8")
    rewritten_html, manifest = rewrite_html(html, input_path, api_key)

    output_full = (
        Path(args.output_full)
        if args.output_full
        else input_path.with_name(input_path.stem + "-final" + input_path.suffix)
    )
    output_full.write_text(rewritten_html, encoding="utf-8")

    body_html = extract_body(rewritten_html)
    output_body = (
        Path(args.output_body)
        if args.output_body
        else output_full.with_name(output_full.stem + "-body.html")
    )
    output_body.write_text(body_html, encoding="utf-8")

    manifest_path = (
        Path(args.manifest)
        if args.manifest
        else output_full.with_name(output_full.stem + "-manifest.json")
    )
    import json

    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(output_full)
    print(output_body)
    print(manifest_path)


if __name__ == "__main__":
    main()
