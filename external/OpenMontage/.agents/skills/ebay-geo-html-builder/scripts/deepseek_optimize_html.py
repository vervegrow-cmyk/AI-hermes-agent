#!/usr/bin/env python3
"""Polish an existing eBay HTML file with DeepSeek while preserving structure."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from openai import OpenAI


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        key, value = s.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="Optimize eBay HTML copy with DeepSeek.")
    parser.add_argument("input", help="Path to source HTML file")
    parser.add_argument("-o", "--output", help="Output path")
    parser.add_argument("--env-file", help="Optional .env path to load before calling DeepSeek")
    parser.add_argument("--model", help="Optional DeepSeek model override")
    args = parser.parse_args()

    if args.env_file:
        load_env(Path(args.env_file))

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise SystemExit("DEEPSEEK_API_KEY is not configured.")

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path.with_name(input_path.stem + "-deepseek.html")
    html = input_path.read_text(encoding="utf-8")

    client = OpenAI(
        api_key=api_key,
        base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    )

    prompt = f"""
You are optimizing an eBay product description HTML for GEO, Google search understanding, and eBay conversion.

Requirements:
- Keep the HTML structure, inline styles, table layout, and image URLs intact.
- Improve only the English copywriting inside text nodes and alt text.
- Do not add scripts, CSS blocks, classes, markdown, or explanations.
- Keep it compliant: avoid absolute safety claims, medical claims, rehab language, guarantee wording, and exaggerated promises.
- Make the copy more natural, commercial, and search-friendly.
- Preserve the existing sections and order.
- Return HTML only.

HTML to optimize:
{html}
""".strip()

    response = client.chat.completions.create(
        model=args.model or os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
        temperature=0.6,
        messages=[
            {"role": "system", "content": "You are a senior eCommerce copywriter specializing in eBay GEO optimization."},
            {"role": "user", "content": prompt},
        ],
    )

    content = response.choices[0].message.content.strip()
    output_path.write_text(content + "\n", encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
