from __future__ import annotations

import json
from typing import Any

import bootstrap
from shared.llm import get_llm
from src.shared.contracts.product import NormalizedProduct


def _heuristic_score(product: NormalizedProduct) -> tuple[float, str]:
    text = f"{product.title} {product.description} {product.brand}".lower()
    score = 0.1
    if product.brand:
        score += 0.25
    if "medical" in text or "vape" in text:
        score += 0.55
    elif "battery" in text or "cosmetic" in text:
        score += 0.2
    summary = f"deepseek-fallback-score={round(score, 2)}"
    return round(min(score, 1.0), 2), summary


def _build_prompt(product: NormalizedProduct) -> str:
    return (
        "You are a compliance and resale risk scorer for dropshipping products. "
        "Return JSON only with keys score and summary. "
        "score must be a number between 0 and 1 where higher means riskier. "
        "summary must be a short English sentence.\n\n"
        f"title: {product.title}\n"
        f"brand: {product.brand}\n"
        f"category_path: {product.category_path}\n"
        f"description: {product.description}\n"
        f"ship_from_country: {product.ship_from_country}\n"
        f"attributes: {json.dumps(product.attributes, ensure_ascii=False)}\n"
        f"variant_attributes: {json.dumps(product.variant_attributes, ensure_ascii=False)}\n"
    )


def _get_client() -> Any | None:
    try:
        return get_llm(provider="deepseek")
    except Exception:
        return None


def _parse_response_text(text: str) -> tuple[float, str]:
    payload = json.loads(text)
    score = float(payload.get("score", 0))
    summary = str(payload.get("summary", "")).strip() or "deepseek-empty-summary"
    return max(0.0, min(1.0, round(score, 2))), summary


def score_product_risk(product: NormalizedProduct) -> tuple[float, str]:
    client = _get_client()
    if client is None:
        return _heuristic_score(product)

    try:
        response = client.generate(
            _build_prompt(product),
            temperature=0,
            text={"format": {"type": "json_object"}},
        )
        text = response.get("text", "{}")
        return _parse_response_text(text)
    except Exception as exc:
        fallback_score, fallback_summary = _heuristic_score(product)
        return fallback_score, f"{fallback_summary}; error={type(exc).__name__}"
