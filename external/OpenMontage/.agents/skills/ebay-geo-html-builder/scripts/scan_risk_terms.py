#!/usr/bin/env python3
"""Scan HTML for risky compliance phrases and print safer suggestions."""

from __future__ import annotations

import argparse
from pathlib import Path


RISK_MAP = {
    "zero injury risk": "designed for more comfortable landings",
    "injury-preventing": "soft foam construction",
    "no slips": "helps provide better grip",
    "non-slip surface": "textured grip surface",
    "shin-safe": "soft foam build",
    "rehab": "low-impact exercise routines",
    "guaranteed safe": "built for confident everyday use",
    "100% safe": "designed with a stable training surface",
    "pain-free": "more comfortable workout feel",
    "medical recovery": "everyday fitness use",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan HTML for risky compliance phrases.")
    parser.add_argument("input", help="Path to HTML file")
    args = parser.parse_args()

    html = Path(args.input).read_text(encoding="utf-8", errors="ignore")
    lower_html = html.lower()

    found = []
    for bad, replacement in RISK_MAP.items():
        if bad in lower_html:
            found.append((bad, replacement))

    if not found:
        print("No configured risk terms found.")
        return

    for bad, replacement in found:
        print(f"{bad} -> {replacement}")


if __name__ == "__main__":
    main()
