from __future__ import annotations

from pathlib import Path
import json
from typing import Any

from src.shared.contracts.mapping import SkuMappingRecord
from src.shared.contracts.publish_mapping import ShopifyPublishMappingRecord
from src.shared.contracts.supplier_archive import (
    InventorySnapshot,
    PriceSnapshot,
    ProductSnapshot,
    ScreeningInput,
    SellerSnapshot,
    SupplierProduct,
)
from src.shared.repositories.protocols import SupplierArchiveRepository


RUNTIME_DATA_DIR = Path("data/runtime")
SUPPLIER_ARCHIVE_DIR = RUNTIME_DATA_DIR / "supplier_archive"
LISTING_RUNTIME_DIR = RUNTIME_DATA_DIR / "shopify_listing"


class _JsonListStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        return []

    def save(self, rows: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


class LocalJsonSupplierArchiveRepository(SupplierArchiveRepository):
    def __init__(self, base_dir: str | Path = SUPPLIER_ARCHIVE_DIR) -> None:
        root = Path(base_dir)
        self.supplier_products_store = _JsonListStore(root / "supplier_products.json")
        self.product_snapshots_store = _JsonListStore(root / "product_snapshots.json")
        self.inventory_snapshots_store = _JsonListStore(root / "inventory_snapshots.json")
        self.price_snapshots_store = _JsonListStore(root / "price_snapshots.json")
        self.seller_snapshots_store = _JsonListStore(root / "seller_snapshots.json")
        self.screening_inputs_store = _JsonListStore(root / "screening_inputs.json")

    def _upsert(self, store: _JsonListStore, key_fields: tuple[str, ...], payload: dict[str, Any]) -> None:
        rows = store.load()
        for index, row in enumerate(rows):
            if all(str(row.get(field) or "") == str(payload.get(field) or "") for field in key_fields):
                rows[index] = payload
                store.save(rows)
                return
        rows.append(payload)
        store.save(rows)

    def _append(self, store: _JsonListStore, payload: dict[str, Any]) -> None:
        rows = store.load()
        rows.append(payload)
        store.save(rows)

    def save_supplier_product(self, product: SupplierProduct) -> SupplierProduct:
        self._upsert(
            self.supplier_products_store,
            ("supplier_name", "supplier_id", "product_id", "sku"),
            product.model_dump(),
        )
        return product

    def list_supplier_products(self) -> list[SupplierProduct]:
        return [SupplierProduct.model_validate(row) for row in self.supplier_products_store.load()]

    def save_product_snapshot(self, snapshot: ProductSnapshot) -> ProductSnapshot:
        self._append(self.product_snapshots_store, snapshot.model_dump())
        return snapshot

    def list_product_snapshots(self) -> list[ProductSnapshot]:
        return [ProductSnapshot.model_validate(row) for row in self.product_snapshots_store.load()]

    def save_inventory_snapshot(self, snapshot: InventorySnapshot) -> InventorySnapshot:
        self._append(self.inventory_snapshots_store, snapshot.model_dump())
        return snapshot

    def list_inventory_snapshots(self) -> list[InventorySnapshot]:
        return [InventorySnapshot.model_validate(row) for row in self.inventory_snapshots_store.load()]

    def save_price_snapshot(self, snapshot: PriceSnapshot) -> PriceSnapshot:
        self._append(self.price_snapshots_store, snapshot.model_dump())
        return snapshot

    def list_price_snapshots(self) -> list[PriceSnapshot]:
        return [PriceSnapshot.model_validate(row) for row in self.price_snapshots_store.load()]

    def save_seller_snapshot(self, snapshot: SellerSnapshot) -> SellerSnapshot:
        self._append(self.seller_snapshots_store, snapshot.model_dump())
        return snapshot

    def list_seller_snapshots(self) -> list[SellerSnapshot]:
        return [SellerSnapshot.model_validate(row) for row in self.seller_snapshots_store.load()]

    def save_screening_input(self, screening_input: ScreeningInput) -> ScreeningInput:
        self._upsert(
            self.screening_inputs_store,
            ("supplier", "supplier_id", "product_id", "supplier_sku"),
            screening_input.model_dump(),
        )
        return screening_input

    def list_screening_inputs(self) -> list[ScreeningInput]:
        return [ScreeningInput.model_validate(row) for row in self.screening_inputs_store.load()]


class LocalJsonPublishMappingRepository:
    def __init__(self, path: str | Path = LISTING_RUNTIME_DIR / "publish_mappings.json") -> None:
        self.store = _JsonListStore(path)

    def save_publish_mapping(self, record: ShopifyPublishMappingRecord) -> ShopifyPublishMappingRecord:
        rows = self.store.load()
        payload = record.model_dump()
        for index, row in enumerate(rows):
            if (
                str(row.get("supplier_product_id") or "") == record.supplier_product_id
                and str(row.get("supplier_sku") or "") == record.supplier_sku
            ):
                rows[index] = payload
                self.store.save(rows)
                return record
        rows.append(payload)
        self.store.save(rows)
        return record

    def list_publish_mappings(self) -> list[ShopifyPublishMappingRecord]:
        return [ShopifyPublishMappingRecord.model_validate(row) for row in self.store.load()]

    def list_sku_mappings(self) -> list[SkuMappingRecord]:
        records: list[SkuMappingRecord] = []
        for row in self.store.load():
            records.append(
                SkuMappingRecord(
                    supplier_product_id=str(row.get("supplier_product_id") or ""),
                    supplier_sku=str(row.get("supplier_sku") or ""),
                    sku=str(row.get("supplier_sku") or ""),
                    shopify_product_id=str(row.get("shopify_product_id") or ""),
                    shopify_variant_id=str(row.get("shopify_variant_id") or ""),
                    handle=str(row.get("shopify_handle") or ""),
                    created_at=str(row.get("published_at") or row.get("updated_at") or ""),
                )
            )
        return records
