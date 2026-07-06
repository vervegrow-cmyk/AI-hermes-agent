from __future__ import annotations

from pathlib import Path

from src.modules.supplier_archive.application.service import archive_supplier_products
from src.modules.supplier_archive.infrastructure.supplier_adapters.mock_doba import load_mock_doba_products
from src.shared.contracts import ArchiveResult
from src.shared.repositories import InMemorySupplierArchiveRepository


REPORT_PATH = Path("docs/audits/supplier-archive-report.md")


def _build_report(result: ArchiveResult) -> str:
    stats = result.archive_statistics
    warnings = result.warnings or []
    lines = [
        "# Supplier Archive Report",
        "",
        "## Summary",
        f"- Supplier: `{result.supplier_name}`",
        f"- Products archived: `{result.archived_products}`",
        f"- Product snapshots created: `{result.product_snapshots}`",
        f"- Inventory snapshots created: `{result.inventory_snapshots}`",
        f"- Price snapshots created: `{result.price_snapshots}`",
        f"- Seller snapshots created: `{result.seller_snapshots}`",
        f"- Screening inputs generated: `{result.screening_inputs}`",
        f"- Skipped products: `{result.skipped_products}`",
        "",
        "## Archive Statistics",
        f"- Products received: `{stats.get('products_received', 0)}`",
        f"- Products archived: `{stats.get('products_archived', 0)}`",
        f"- Products skipped: `{stats.get('products_skipped', 0)}`",
        f"- Product snapshots created: `{stats.get('product_snapshots_created', 0)}`",
        f"- Inventory snapshots created: `{stats.get('inventory_snapshots_created', 0)}`",
        f"- Price snapshots created: `{stats.get('price_snapshots_created', 0)}`",
        f"- Seller snapshots created: `{stats.get('seller_snapshots_created', 0)}`",
        f"- Screening inputs generated: `{stats.get('screening_inputs_generated', 0)}`",
        "",
        "## Warnings",
    ]
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def _write_report(result: ArchiveResult) -> str:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(_build_report(result), encoding="utf-8")
    return str(REPORT_PATH.resolve())


def run_supplier_archive() -> ArchiveResult:
    repository = InMemorySupplierArchiveRepository()
    products = load_mock_doba_products()
    result = archive_supplier_products(products, repository)
    result.report_path = _write_report(result)
    return result
