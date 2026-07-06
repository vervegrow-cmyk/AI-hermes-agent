from __future__ import annotations

from pathlib import Path
import json
import sqlite3
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
from src.shared.repositories.local_json import LISTING_RUNTIME_DIR, SUPPLIER_ARCHIVE_DIR, _JsonListStore
from src.shared.repositories.protocols import SupplierArchiveRepository


SQLITE_RUNTIME_PATH = Path("data/runtime/runtime_state.sqlite3")


def _json_default(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


class _SqliteStore:
    def __init__(self, path: str | Path = SQLITE_RUNTIME_PATH) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 30000")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = NORMAL")
        return connection

    def _initialize(self) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS supplier_products (
                    record_key TEXT PRIMARY KEY,
                    supplier_name TEXT NOT NULL,
                    supplier_id TEXT NOT NULL,
                    product_id TEXT NOT NULL,
                    sku TEXT NOT NULL,
                    supplier_spu_no TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    source_hash TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS supplier_product_changes (
                    supplier_spu_no TEXT PRIMARY KEY,
                    updated_at TEXT NOT NULL
                )
                """
            )
            for table_name in ("product_snapshots", "inventory_snapshots", "price_snapshots", "seller_snapshots", "screening_inputs"):
                connection.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        supplier_id TEXT NOT NULL,
                        product_id TEXT NOT NULL,
                        sku TEXT NOT NULL,
                        snapshot_at TEXT NOT NULL,
                        payload_json TEXT NOT NULL
                    )
                    """
                )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS publish_mappings (
                    record_key TEXT PRIMARY KEY,
                    supplier_product_id TEXT NOT NULL,
                    supplier_spu_no TEXT NOT NULL,
                    supplier_sku TEXT NOT NULL,
                    status TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS candidate_pool_entries (
                    supplier_spu_no TEXT PRIMARY KEY,
                    supplier_product_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    seller_name TEXT NOT NULL,
                    category_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    skip_reason TEXT NOT NULL,
                    source_hash TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS runtime_state (
                    namespace TEXT NOT NULL,
                    state_key TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    PRIMARY KEY(namespace, state_key)
                )
                """
            )


class SQLiteSupplierArchiveRepository(SupplierArchiveRepository):
    def __init__(
        self,
        db_path: str | Path = SQLITE_RUNTIME_PATH,
        legacy_base_dir: str | Path = SUPPLIER_ARCHIVE_DIR,
    ) -> None:
        self.store = _SqliteStore(db_path)
        self.legacy_base_dir = Path(legacy_base_dir)
        self._maybe_migrate_legacy_json()

    def _maybe_migrate_legacy_json(self) -> None:
        with self.store.connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM supplier_products").fetchone()
            if int((row or {})["count"]) > 0:
                return
        legacy_products_path = self.legacy_base_dir / "supplier_products.json"
        if not legacy_products_path.exists():
            return
        for row in _JsonListStore(legacy_products_path).load():
            self.save_supplier_product(SupplierProduct.model_validate(row))
        for row in _JsonListStore(self.legacy_base_dir / "product_snapshots.json").load():
            self.save_product_snapshot(ProductSnapshot.model_validate(row))
        for row in _JsonListStore(self.legacy_base_dir / "inventory_snapshots.json").load():
            self.save_inventory_snapshot(InventorySnapshot.model_validate(row))
        for row in _JsonListStore(self.legacy_base_dir / "price_snapshots.json").load():
            self.save_price_snapshot(PriceSnapshot.model_validate(row))
        for row in _JsonListStore(self.legacy_base_dir / "seller_snapshots.json").load():
            self.save_seller_snapshot(SellerSnapshot.model_validate(row))
        for row in _JsonListStore(self.legacy_base_dir / "screening_inputs.json").load():
            self.save_screening_input(ScreeningInput.model_validate(row))

    def _record_key(self, supplier_name: str, supplier_id: str, product_id: str, sku: str) -> str:
        return "::".join([supplier_name, supplier_id, product_id, sku])

    def _touch_change(self, supplier_spu_no: str, updated_at: str) -> None:
        if not supplier_spu_no:
            return
        with self.store.connect() as connection:
            connection.execute(
                """
                INSERT INTO supplier_product_changes (supplier_spu_no, updated_at)
                VALUES (?, ?)
                ON CONFLICT(supplier_spu_no) DO UPDATE SET updated_at=excluded.updated_at
                """,
                (supplier_spu_no, updated_at),
            )

    def save_supplier_product(self, product: SupplierProduct) -> SupplierProduct:
        payload = product.model_dump()
        record_key = self._record_key(product.supplier_name, product.supplier_id, product.product_id, product.sku)
        source_hash = _json_default(payload)
        updated_at = str(payload.get("seller_info", {}).get("updated_at") or payload.get("warehouse_info", {}).get("updated_at") or "")
        with self.store.connect() as connection:
            previous = connection.execute(
                "SELECT source_hash FROM supplier_products WHERE record_key = ?",
                (record_key,),
            ).fetchone()
            connection.execute(
                """
                INSERT INTO supplier_products (
                    record_key, supplier_name, supplier_id, product_id, sku, supplier_spu_no, payload_json, source_hash, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(record_key) DO UPDATE SET
                    supplier_spu_no=excluded.supplier_spu_no,
                    payload_json=excluded.payload_json,
                    source_hash=excluded.source_hash,
                    updated_at=excluded.updated_at
                """,
                (
                    record_key,
                    product.supplier_name,
                    product.supplier_id,
                    product.product_id,
                    product.sku,
                    product.supplier_spu_no,
                    _json_default(payload),
                    source_hash,
                    updated_at,
                ),
            )
        if previous is None or str(previous["source_hash"]) != source_hash:
            self._touch_change(str(product.supplier_spu_no or product.product_id or ""), updated_at or "changed")
        return product

    def list_supplier_products(self) -> list[SupplierProduct]:
        with self.store.connect() as connection:
            rows = connection.execute("SELECT payload_json FROM supplier_products ORDER BY supplier_spu_no, sku").fetchall()
        return [SupplierProduct.model_validate(json.loads(str(row["payload_json"]))) for row in rows]

    def list_supplier_products_by_spu_nos(self, supplier_spu_nos: list[str]) -> list[SupplierProduct]:
        normalized = [str(value or "").strip() for value in supplier_spu_nos if str(value or "").strip()]
        if not normalized:
            return []
        unique_normalized: list[str] = []
        seen: set[str] = set()
        for value in normalized:
            if value in seen:
                continue
            seen.add(value)
            unique_normalized.append(value)
        batch_size = 500
        rows: list[sqlite3.Row] = []
        with self.store.connect() as connection:
            for start in range(0, len(unique_normalized), batch_size):
                batch = unique_normalized[start : start + batch_size]
                placeholders = ",".join("?" for _ in batch)
                rows.extend(
                    connection.execute(
                        f"SELECT payload_json FROM supplier_products WHERE supplier_spu_no IN ({placeholders}) ORDER BY supplier_spu_no, sku",
                        batch,
                    ).fetchall()
                )
        return [SupplierProduct.model_validate(json.loads(str(row["payload_json"]))) for row in rows]

    def count_supplier_product_groups(self) -> int:
        with self.store.connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(DISTINCT CASE
                    WHEN TRIM(COALESCE(supplier_spu_no, '')) != '' THEN TRIM(supplier_spu_no)
                    ELSE TRIM(COALESCE(product_id, ''))
                END) AS count
                FROM supplier_products
                """
            ).fetchone()
        return int((row or {})["count"] or 0)

    def consume_changed_supplier_spu_nos(self) -> list[str]:
        with self.store.connect() as connection:
            rows = connection.execute(
                "SELECT supplier_spu_no FROM supplier_product_changes ORDER BY updated_at, supplier_spu_no"
            ).fetchall()
            connection.execute("DELETE FROM supplier_product_changes")
        return [str(row["supplier_spu_no"]) for row in rows if str(row["supplier_spu_no"] or "").strip()]

    def _append_snapshot(self, table_name: str, supplier_id: str, product_id: str, sku: str, snapshot_at: str, payload: dict[str, Any]) -> None:
        with self.store.connect() as connection:
            connection.execute(
                f"""
                INSERT INTO {table_name} (supplier_id, product_id, sku, snapshot_at, payload_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (supplier_id, product_id, sku, snapshot_at, _json_default(payload)),
            )

    def _list_snapshots(self, table_name: str, model_cls: Any) -> list[Any]:
        with self.store.connect() as connection:
            rows = connection.execute(f"SELECT payload_json FROM {table_name} ORDER BY id").fetchall()
        return [model_cls.model_validate(json.loads(str(row["payload_json"]))) for row in rows]

    def save_product_snapshot(self, snapshot: ProductSnapshot) -> ProductSnapshot:
        self._append_snapshot("product_snapshots", snapshot.supplier_id, snapshot.product_id, snapshot.sku, snapshot.snapshot_at, snapshot.model_dump())
        return snapshot

    def list_product_snapshots(self) -> list[ProductSnapshot]:
        return self._list_snapshots("product_snapshots", ProductSnapshot)

    def save_inventory_snapshot(self, snapshot: InventorySnapshot) -> InventorySnapshot:
        self._append_snapshot("inventory_snapshots", snapshot.supplier_id, snapshot.product_id, snapshot.sku, snapshot.snapshot_at, snapshot.model_dump())
        return snapshot

    def list_inventory_snapshots(self) -> list[InventorySnapshot]:
        return self._list_snapshots("inventory_snapshots", InventorySnapshot)

    def save_price_snapshot(self, snapshot: PriceSnapshot) -> PriceSnapshot:
        self._append_snapshot("price_snapshots", snapshot.supplier_id, snapshot.product_id, snapshot.sku, snapshot.snapshot_at, snapshot.model_dump())
        return snapshot

    def list_price_snapshots(self) -> list[PriceSnapshot]:
        return self._list_snapshots("price_snapshots", PriceSnapshot)

    def save_seller_snapshot(self, snapshot: SellerSnapshot) -> SellerSnapshot:
        self._append_snapshot("seller_snapshots", snapshot.supplier_id, "", "", snapshot.snapshot_at, snapshot.model_dump())
        return snapshot

    def list_seller_snapshots(self) -> list[SellerSnapshot]:
        return self._list_snapshots("seller_snapshots", SellerSnapshot)

    def save_screening_input(self, screening_input: ScreeningInput) -> ScreeningInput:
        with self.store.connect() as connection:
            connection.execute(
                """
                INSERT INTO screening_inputs (supplier_id, product_id, sku, snapshot_at, payload_json)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT DO NOTHING
                """,
                (
                    screening_input.supplier_id,
                    screening_input.product_id,
                    screening_input.supplier_sku,
                    "",
                    _json_default(screening_input.model_dump()),
                ),
            )
        return screening_input

    def list_screening_inputs(self) -> list[ScreeningInput]:
        return self._list_snapshots("screening_inputs", ScreeningInput)


class SQLitePublishMappingRepository:
    def __init__(
        self,
        db_path: str | Path = SQLITE_RUNTIME_PATH,
        legacy_path: str | Path = LISTING_RUNTIME_DIR / "publish_mappings.json",
    ) -> None:
        self.store = _SqliteStore(db_path)
        self.legacy_path = Path(legacy_path)
        self._maybe_migrate_legacy_json()

    def _maybe_migrate_legacy_json(self) -> None:
        with self.store.connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM publish_mappings").fetchone()
            if int((row or {})["count"]) > 0:
                return
        if not self.legacy_path.exists():
            return
        for row in _JsonListStore(self.legacy_path).load():
            self.save_publish_mapping(ShopifyPublishMappingRecord.model_validate(row))

    def _record_key(self, record: ShopifyPublishMappingRecord) -> str:
        return "::".join([record.supplier_product_id, record.supplier_sku])

    def save_publish_mapping(self, record: ShopifyPublishMappingRecord) -> ShopifyPublishMappingRecord:
        payload = record.model_dump()
        with self.store.connect() as connection:
            connection.execute(
                """
                INSERT INTO publish_mappings (
                    record_key, supplier_product_id, supplier_spu_no, supplier_sku, status, updated_at, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(record_key) DO UPDATE SET
                    supplier_spu_no=excluded.supplier_spu_no,
                    status=excluded.status,
                    updated_at=excluded.updated_at,
                    payload_json=excluded.payload_json
                """,
                (
                    self._record_key(record),
                    record.supplier_product_id,
                    record.supplier_spu_no,
                    record.supplier_sku,
                    record.status,
                    record.updated_at,
                    _json_default(payload),
                ),
            )
        return record

    def list_publish_mappings(self) -> list[ShopifyPublishMappingRecord]:
        with self.store.connect() as connection:
            rows = connection.execute("SELECT payload_json FROM publish_mappings ORDER BY supplier_spu_no, supplier_sku").fetchall()
        return [ShopifyPublishMappingRecord.model_validate(json.loads(str(row["payload_json"]))) for row in rows]

    def list_sku_mappings(self) -> list[SkuMappingRecord]:
        return [
            SkuMappingRecord(
                supplier_product_id=record.supplier_product_id,
                supplier_sku=record.supplier_sku,
                sku=record.supplier_sku,
                shopify_product_id=record.shopify_product_id,
                shopify_variant_id=record.shopify_variant_id,
                handle=record.shopify_handle,
                created_at=record.published_at or record.updated_at,
            )
            for record in self.list_publish_mappings()
        ]


class SQLiteCandidatePoolRepository:
    def __init__(self, db_path: str | Path = SQLITE_RUNTIME_PATH) -> None:
        self.store = _SqliteStore(db_path)

    def has_entries(self) -> bool:
        with self.store.connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM candidate_pool_entries").fetchone()
        return int((row or {})["count"]) > 0

    def upsert_entry(
        self,
        *,
        supplier_spu_no: str,
        supplier_product_id: str,
        title: str,
        seller_name: str,
        category_name: str,
        status: str,
        skip_reason: str,
        source_hash: str,
        payload: dict[str, Any],
        updated_at: str,
    ) -> None:
        with self.store.connect() as connection:
            connection.execute(
                """
                INSERT INTO candidate_pool_entries (
                    supplier_spu_no, supplier_product_id, title, seller_name, category_name, status, skip_reason, source_hash, updated_at, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(supplier_spu_no) DO UPDATE SET
                    supplier_product_id=excluded.supplier_product_id,
                    title=excluded.title,
                    seller_name=excluded.seller_name,
                    category_name=excluded.category_name,
                    status=excluded.status,
                    skip_reason=excluded.skip_reason,
                    source_hash=excluded.source_hash,
                    updated_at=excluded.updated_at,
                    payload_json=excluded.payload_json
                """,
                (
                    supplier_spu_no,
                    supplier_product_id,
                    title,
                    seller_name,
                    category_name,
                    status,
                    skip_reason,
                    source_hash,
                    updated_at,
                    _json_default(payload),
                ),
            )

    def clear_all(self) -> None:
        with self.store.connect() as connection:
            connection.execute("DELETE FROM candidate_pool_entries")

    def delete_entries_by_spu_nos(self, supplier_spu_nos: list[str]) -> None:
        normalized = [str(value or "").strip() for value in supplier_spu_nos if str(value or "").strip()]
        if not normalized:
            return
        placeholders = ",".join("?" for _ in normalized)
        with self.store.connect() as connection:
            connection.execute(
                f"DELETE FROM candidate_pool_entries WHERE supplier_spu_no IN ({placeholders})",
                normalized,
            )

    def list_qualified_candidates(self) -> list[dict[str, Any]]:
        with self.store.connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM candidate_pool_entries WHERE status = 'qualified' ORDER BY supplier_spu_no"
            ).fetchall()
        return [json.loads(str(row["payload_json"])) for row in rows]

    def list_candidates_by_spu_nos(
        self,
        supplier_spu_nos: list[str],
        *,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        normalized = [str(value or "").strip() for value in supplier_spu_nos if str(value or "").strip()]
        if not normalized:
            return []
        placeholders = ",".join("?" for _ in normalized)
        params: list[str] = list(normalized)
        query = f"SELECT payload_json FROM candidate_pool_entries WHERE supplier_spu_no IN ({placeholders})"
        if status is not None:
            query += " AND status = ?"
            params.append(str(status))
        query += " ORDER BY supplier_spu_no"
        with self.store.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [json.loads(str(row["payload_json"])) for row in rows]

    def build_summary(self) -> dict[str, Any]:
        skipped_by_reason: dict[str, int] = {}
        missing_category_examples: list[dict[str, Any]] = []
        ship_from_summary = {"us": 0, "non_us": 0, "unknown": 0}
        with self.store.connect() as connection:
            qualified_count = int(connection.execute(
                "SELECT COUNT(*) AS count FROM candidate_pool_entries WHERE status = 'qualified'"
            ).fetchone()["count"])
            payload_rows = connection.execute(
                "SELECT payload_json FROM candidate_pool_entries ORDER BY supplier_spu_no"
            ).fetchall()
            rows = connection.execute(
                "SELECT skip_reason, COUNT(*) AS count FROM candidate_pool_entries WHERE status != 'qualified' GROUP BY skip_reason"
            ).fetchall()
            for row in rows:
                reason = str(row["skip_reason"] or "unknown")
                skipped_by_reason[reason] = int(row["count"] or 0)
            missing_rows = connection.execute(
                """
                SELECT payload_json FROM candidate_pool_entries
                WHERE status != 'qualified' AND skip_reason = 'missing_shopify_category'
                ORDER BY updated_at DESC LIMIT 20
                """
            ).fetchall()
        for row in payload_rows:
            payload = json.loads(str(row["payload_json"]))
            ship_from_country = str(payload.get("ship_from_country") or "").strip()
            if ship_from_country == "United States":
                ship_from_summary["us"] += 1
            elif not ship_from_country or ship_from_country == "UNKNOWN":
                ship_from_summary["unknown"] += 1
            else:
                ship_from_summary["non_us"] += 1
        for row in missing_rows:
            payload = json.loads(str(row["payload_json"]))
            missing_category_examples.append(
                {
                    "spu_id": str(payload.get("spu_id") or ""),
                    "spu_no": str(payload.get("spu_no") or ""),
                    "title": str(payload.get("title") or ""),
                    "category_name": str(payload.get("category_name") or ""),
                    "sku_list": list(payload.get("sku_list") or []),
                }
            )
        return {
            "qualified_count": qualified_count,
            "skipped_by_reason": skipped_by_reason,
            "missing_category_examples": missing_category_examples,
            "ship_from_summary": ship_from_summary,
        }


class SQLiteRuntimeStateRepository:
    def __init__(self, db_path: str | Path = SQLITE_RUNTIME_PATH) -> None:
        self.store = _SqliteStore(db_path)

    def load(self, namespace: str, state_key: str) -> dict[str, Any]:
        with self.store.connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM runtime_state WHERE namespace = ? AND state_key = ?",
                (namespace, state_key),
            ).fetchone()
        if row is None:
            return {}
        payload = json.loads(str(row["payload_json"]))
        return payload if isinstance(payload, dict) else {}

    def save(self, namespace: str, state_key: str, payload: dict[str, Any], updated_at: str) -> None:
        with self.store.connect() as connection:
            connection.execute(
                """
                INSERT INTO runtime_state (namespace, state_key, updated_at, payload_json)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(namespace, state_key) DO UPDATE SET
                    updated_at=excluded.updated_at,
                    payload_json=excluded.payload_json
                """,
                (namespace, state_key, updated_at, _json_default(payload)),
            )
