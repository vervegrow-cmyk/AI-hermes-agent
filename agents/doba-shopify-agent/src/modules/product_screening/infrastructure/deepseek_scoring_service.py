from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Protocol

import bootstrap
from shared.config import get_settings
from shared.llm import get_llm

from src.shared.contracts.screening import DeepSeekScoreRequest, DeepSeekScoreResponse


def _clamp_score(value: Any) -> int:
    try:
        number = int(round(float(value)))
    except (TypeError, ValueError):
        return 0
    return max(0, min(100, number))


def build_deepseek_prompt(product) -> str:
    return (
        "You are scoring a dropshipping product for future AI screening.\n"
        "Return JSON only.\n"
        "Use integer scores from 0 to 100 for every score field.\n"
        "reasoning must be a short explanation.\n"
        "risk_notes must be an array of short strings.\n"
        "Expected JSON keys: trend_score, season_score, profit_score, price_score, inventory_score, "
        "seller_score, fulfillment_score, review_score, shipping_score, return_risk_score, "
        "compliance_risk_score, reasoning, risk_notes.\n\n"
        f"supplier: {product.supplier}\n"
        f"sku: {product.supplier_sku}\n"
        f"title: {product.title}\n"
        f"category: {product.category}\n"
        f"price: {product.price}\n"
        f"shipping_cost: {product.shipping_cost}\n"
        f"inventory: {product.inventory}\n"
        f"warehouse: {product.warehouse}\n"
        f"seller_rating: {product.seller_rating}\n"
        f"review_count: {product.review_count}\n"
        f"fulfillment_speed_days: {product.fulfillment_speed_days}\n"
        f"images_count: {product.images_count}\n"
        f"snapshot_history: {json.dumps(product.snapshot_history.model_dump(), ensure_ascii=False)}\n"
    )


def normalize_score_response(payload: dict[str, Any], *, fallback_reason: str = "") -> DeepSeekScoreResponse:
    return DeepSeekScoreResponse(
        trend_score=_clamp_score(payload.get("trend_score")),
        season_score=_clamp_score(payload.get("season_score")),
        profit_score=_clamp_score(payload.get("profit_score")),
        price_score=_clamp_score(payload.get("price_score")),
        inventory_score=_clamp_score(payload.get("inventory_score")),
        seller_score=_clamp_score(payload.get("seller_score")),
        fulfillment_score=_clamp_score(payload.get("fulfillment_score")),
        review_score=_clamp_score(payload.get("review_score")),
        shipping_score=_clamp_score(payload.get("shipping_score")),
        return_risk_score=_clamp_score(payload.get("return_risk_score")),
        compliance_risk_score=_clamp_score(payload.get("compliance_risk_score")),
        reasoning=str(payload.get("reasoning", "") or "").strip(),
        risk_notes=[str(item).strip() for item in payload.get("risk_notes", []) if str(item).strip()],
        fallback_reason=fallback_reason,
    )


def build_mock_score_response(request: DeepSeekScoreRequest, *, fallback_reason: str = "") -> DeepSeekScoreResponse:
    key = f"{request.product.supplier_sku}|{request.product.title}|{request.product.category}|{request.product.price}"
    digest = sha256(key.encode("utf-8")).digest()

    def pick(index: int, floor: int, ceil: int) -> int:
        span = ceil - floor + 1
        return floor + (digest[index] % span)

    payload = {
        "trend_score": pick(0, 45, 82),
        "season_score": pick(1, 40, 78),
        "profit_score": pick(2, 50, 88),
        "price_score": pick(3, 48, 85),
        "inventory_score": pick(4, 55, 90),
        "seller_score": pick(5, 50, 92),
        "fulfillment_score": pick(6, 45, 88),
        "review_score": pick(7, 42, 90),
        "shipping_score": pick(8, 40, 84),
        "return_risk_score": pick(9, 8, 35),
        "compliance_risk_score": pick(10, 5, 28),
        "reasoning": f"Mock DeepSeek scoring for {request.product.supplier_sku} based on pricing, inventory, seller, and fulfillment signals.",
        "risk_notes": [
            f"Inventory stability: {request.product.snapshot_history.inventory_stability}",
            f"Warehouse: {request.product.warehouse or 'missing'}",
        ],
    }
    return normalize_score_response(payload, fallback_reason=fallback_reason)


class ProductScoringService(Protocol):
    mode: str
    model_name: str

    def score(self, request: DeepSeekScoreRequest) -> DeepSeekScoreResponse: ...


@dataclass
class MockDeepSeekScoringService:
    mode: str = "mock"
    model_name: str = "deepseek-mock"

    def score(self, request: DeepSeekScoreRequest) -> DeepSeekScoreResponse:
        return build_mock_score_response(request)


@dataclass
class DeepSeekScoringService:
    llm_client: Any
    mode: str = "real"
    model_name: str = "deepseek-chat"

    def score(self, request: DeepSeekScoreRequest) -> DeepSeekScoreResponse:
        response = self.llm_client.generate(
            request.prompt,
            temperature=0,
            text={"format": {"type": "json_object"}},
        )
        response_text = str(response.get("text", "") or "").strip()
        if not response_text:
            return build_mock_score_response(request, fallback_reason="empty_response")
        try:
            payload = json.loads(response_text)
        except json.JSONDecodeError:
            return build_mock_score_response(request, fallback_reason="invalid_json")
        return normalize_score_response(payload)


def get_product_scoring_service() -> ProductScoringService:
    settings = get_settings()
    if not settings.deepseek_api_key:
        return MockDeepSeekScoringService()
    return DeepSeekScoringService(
        llm_client=get_llm(provider="deepseek"),
        model_name=settings.deepseek_model,
    )
