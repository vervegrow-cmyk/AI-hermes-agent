from __future__ import annotations

from src.modules.price_sync.application.service import build_price_sync_plan, run_price_sync_runtime
from src.shared.contracts.pricing import PriceSyncCommand, PriceSyncResult


def run_price_sync(command: PriceSyncCommand) -> PriceSyncResult:
    return run_price_sync_runtime(command)


def apply_price_sync(command: PriceSyncCommand) -> PriceSyncResult:
    return run_price_sync_runtime(command)


__all__ = ["apply_price_sync", "build_price_sync_plan", "run_price_sync"]
