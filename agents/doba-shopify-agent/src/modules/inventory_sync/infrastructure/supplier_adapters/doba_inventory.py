from __future__ import annotations

from src.shared.contracts.inventory import InventorySnapshot


def load_inventory_snapshots(payload: dict) -> list[InventorySnapshot]:
    return [InventorySnapshot.model_validate(item) for item in payload.get("snapshots", [])]

