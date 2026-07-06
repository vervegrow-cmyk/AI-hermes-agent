from __future__ import annotations

from src.shared.contracts.pricing import PriceSnapshot


def load_price_snapshots(payload: dict) -> list[PriceSnapshot]:
    return [PriceSnapshot.model_validate(item) for item in payload.get("snapshots", [])]

