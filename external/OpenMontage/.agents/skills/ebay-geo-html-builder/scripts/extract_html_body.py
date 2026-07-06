#!/usr/bin/env python3
"""Extract the inner <body> HTML from a full document."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def extract_body(html: str) -> str:
    match = re.search(r"<body[^>]*>(.*)</body>", html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        raise ValueError("No <body>...</body> block found.")
    body = match.group(1).strip()
    return body + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract inner body HTML from a full document.")
    parser.add_argument("input", help="Path to full HTML file")
    parser.add_argument("-o", "--output", help="Output path for body-only HTML")
    args = parser.parse_args()

    input_path = Path(args.input)
    html = input_path.read_text(encoding="utf-8")
    body = extract_body(html)

    output_path = Path(args.output) if args.output else input_path.with_name(input_path.stem + "-body.html")
    output_path.write_text(body, encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
