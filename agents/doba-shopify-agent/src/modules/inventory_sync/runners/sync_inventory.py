from __future__ import annotations

from src.modules.inventory_sync.application.service import build_inventory_sync_plan, run_inventory_sync_runtime
from src.shared.contracts.inventory import InventorySyncCommand, InventorySyncResult


def run_inventory_sync(command: InventorySyncCommand) -> InventorySyncResult:
    return run_inventory_sync_runtime(command)


def apply_inventory_sync(command: InventorySyncCommand) -> InventorySyncResult:
    return run_inventory_sync_runtime(command)


__all__ = ["apply_inventory_sync", "build_inventory_sync_plan", "run_inventory_sync"]
