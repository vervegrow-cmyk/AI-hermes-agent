from __future__ import annotations

from dataclasses import dataclass

import bootstrap
from shared.config import get_settings


RESTRICTED_KEYWORDS = {
    "weapon",
    "weapons",
    "adult",
    "tobacco",
    "vape",
    "vaping",
    "supplement",
    "supplements",
    "medical",
    "medicine",
    "hazardous",
    "chemical",
    "chemicals",
}

MANUAL_REVIEW_KEYWORDS = {
    "battery",
    "batteries",
    "cosmetic",
    "cosmetics",
    "children",
    "child",
    "baby",
}


@dataclass
class RiskConfig:
    restricted_categories: set[str]
    manual_review_categories: set[str]


def _split_csv(raw_value: str, default: list[str]) -> set[str]:
    if not raw_value.strip():
        return {item.upper() for item in default}
    return {item.strip().upper() for item in raw_value.split(",") if item.strip()}


def get_risk_config() -> RiskConfig:
    settings = get_settings()
    return RiskConfig(
        restricted_categories=_split_csv(
            settings.doba_restricted_categories,
            ["weapons", "adult", "tobacco", "supplements", "medical", "hazardous"],
        ),
        manual_review_categories=_split_csv(
            settings.doba_manual_review_categories,
            ["battery", "cosmetics", "children"],
        ),
    )
