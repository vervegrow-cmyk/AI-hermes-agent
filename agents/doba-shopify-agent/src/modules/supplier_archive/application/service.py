from __future__ import annotations

from datetime import datetime, timezone

from src.shared.contracts import DobaProductInput
from src.shared.contracts.supplier_archive import (
    ArchiveResult,
    InventorySnapshot,
    PriceSnapshot,
    ProductSnapshot,
    ScreeningInput,
    SellerSnapshot,
    SnapshotHistorySummary,
    SupplierProduct,
)
from src.shared.repositories.protocols import SupplierArchiveRepository


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _to_supplier_product(product: DobaProductInput) -> SupplierProduct:
    return SupplierProduct(
        supplier_name="doba",
        supplier_id=product.supplier_id,
        supplier_spu_no=product.supplier_spu_no,
        product_id=product.product_id,
        sku=product.sku,
        sku_code=product.sku_code,
        sku_id=product.sku_id,
        item_no=product.item_no,
        title=product.title,
        brand=product.brand,
        category_id=product.category_id,
        category_name=product.category_name,
        category_path=product.category_path,
        supplier_status=product.supplier_status,
        source_vendor=product.source_vendor,
        source_channels=list(product.source_channels),
        cost=product.cost,
        msrp=product.msrp,
        inventory=product.inventory,
        ship_from_country=product.ship_from_country,
        ship_from_raw=product.ship_from_raw,
        ship_from_source=product.ship_from_source,
        ship_from_confidence=product.ship_from_confidence,
        warehouse_name=product.warehouse_name,
        ships_to_countries=list(product.ships_to_countries),
        shipping_cost=product.shipping_cost,
        delivery_days=product.delivery_days,
        description=product.description,
        image_urls=list(product.image_urls),
        attributes=dict(product.attributes),
        variant_attributes=dict(product.variant_attributes),
        category_metafields=dict(product.category_metafields),
        seller_name=product.seller_name,
        seller_info=dict(product.seller_info),
        warehouse_info=dict(product.warehouse_info),
    )


def _build_product_snapshot(product: SupplierProduct, snapshot_at: str) -> ProductSnapshot:
    return ProductSnapshot(
        supplier_name=product.supplier_name,
        supplier_id=product.supplier_id,
        product_id=product.product_id,
        sku=product.sku,
        snapshot_at=snapshot_at,
        title=product.title,
        brand=product.brand,
        category_id=product.category_id,
        category_name=product.category_name,
        supplier_status=product.supplier_status,
        category_path=product.category_path,
        description=product.description,
        image_count=len(product.image_urls),
        warehouse=product.ship_from_country,
        source_vendor=product.source_vendor,
        source_channels=list(product.source_channels),
        delivery_days=float(product.delivery_days),
        ships_to_countries=list(product.ships_to_countries),
        category_metafields=dict(product.category_metafields),
    )


def _build_inventory_snapshot(product: SupplierProduct, snapshot_at: str) -> InventorySnapshot:
    return InventorySnapshot(
        supplier_name=product.supplier_name,
        supplier_id=product.supplier_id,
        product_id=product.product_id,
        sku=product.sku,
        snapshot_at=snapshot_at,
        warehouse=product.ship_from_country,
        warehouse_name=product.warehouse_name,
        ship_from_country=product.ship_from_country,
        supplier_inventory=product.inventory,
    )


def _build_price_snapshot(product: SupplierProduct, snapshot_at: str) -> PriceSnapshot:
    return PriceSnapshot(
        supplier_name=product.supplier_name,
        supplier_id=product.supplier_id,
        product_id=product.product_id,
        sku=product.sku,
        snapshot_at=snapshot_at,
        supplier_cost=product.cost,
        shipping_cost=product.shipping_cost,
        true_cost=round(product.cost + product.shipping_cost, 2),
        target_price=product.msrp,
        msrp=product.msrp,
    )


def _build_seller_snapshot(product: SupplierProduct, snapshot_at: str) -> SellerSnapshot:
    return SellerSnapshot(
        supplier_name=product.supplier_name,
        supplier_id=product.supplier_id,
        snapshot_at=snapshot_at,
        seller_name=product.seller_name or product.supplier_id or product.supplier_name,
        seller_status=product.supplier_status,
        ship_from_country=product.ship_from_country,
        fulfillment_speed_days=float(product.delivery_days),
        metadata={
            "source": "doba",
            "seller_name": product.seller_name,
            "seller_info": dict(product.seller_info),
            "warehouse_name": product.warehouse_name,
            "warehouse_info": dict(product.warehouse_info),
            "source_vendor": product.source_vendor,
        },
    )


def _compute_inventory_stability(inventory_snapshots: list[InventorySnapshot]) -> str:
    values = {snapshot.supplier_inventory for snapshot in inventory_snapshots}
    if len(values) <= 1:
        return "stable"
    return "volatile"


def _compute_price_change(price_snapshots: list[PriceSnapshot]) -> float:
    if len(price_snapshots) <= 1:
        return 0
    return round(price_snapshots[-1].supplier_cost - price_snapshots[0].supplier_cost, 2)


def _compute_seller_rating_change(seller_snapshots: list[SellerSnapshot]) -> float:
    if len(seller_snapshots) <= 1:
        return 0
    return round(seller_snapshots[-1].rating - seller_snapshots[0].rating, 2)


def build_screening_input(
    *,
    supplier_product: SupplierProduct,
    product_snapshots: list[ProductSnapshot],
    inventory_snapshots: list[InventorySnapshot],
    price_snapshots: list[PriceSnapshot],
    seller_snapshots: list[SellerSnapshot],
) -> ScreeningInput:
    latest_product = product_snapshots[-1]
    latest_inventory = inventory_snapshots[-1]
    latest_price = price_snapshots[-1]
    latest_seller = seller_snapshots[-1]
    snapshot_history = SnapshotHistorySummary(
        inventory_stability=_compute_inventory_stability(inventory_snapshots),
        price_change_7d=_compute_price_change(price_snapshots),
        seller_rating_change_30d=_compute_seller_rating_change(seller_snapshots),
        inventory_snapshots=len(inventory_snapshots),
        price_snapshots=len(price_snapshots),
        seller_snapshots=len(seller_snapshots),
    )
    return ScreeningInput(
        supplier=supplier_product.supplier_name,
        supplier_id=supplier_product.supplier_id,
        product_id=supplier_product.product_id,
        supplier_sku=supplier_product.sku,
        title=supplier_product.title,
        category=supplier_product.category_path,
        price=latest_price.supplier_cost,
        shipping_cost=latest_price.shipping_cost,
        inventory=latest_inventory.supplier_inventory,
        warehouse=latest_inventory.warehouse or latest_product.warehouse,
        ship_from_country=latest_inventory.ship_from_country or supplier_product.ship_from_country,
        seller_rating=latest_seller.rating,
        review_count=latest_seller.review_count,
        fulfillment_speed_days=latest_seller.fulfillment_speed_days or latest_product.delivery_days,
        images_count=latest_product.image_count,
        snapshot_history=snapshot_history,
    )


def archive_supplier_products(
    products: list[DobaProductInput],
    repository: SupplierArchiveRepository,
) -> ArchiveResult:
    warnings: list[str] = []
    archived_products = 0
    product_snapshots_count = 0
    inventory_snapshots_count = 0
    price_snapshots_count = 0
    seller_snapshots_count = 0
    screening_inputs_count = 0
    skipped_products = 0

    for product in products:
        if not product.product_id or not product.sku:
            skipped_products += 1
            warnings.append("Skipped product missing product_id or sku.")
            continue

        snapshot_at = _now_iso()
        supplier_product = repository.save_supplier_product(_to_supplier_product(product))
        archived_products += 1

        product_snapshot = repository.save_product_snapshot(_build_product_snapshot(supplier_product, snapshot_at))
        product_snapshots_count += 1

        inventory_snapshot = repository.save_inventory_snapshot(_build_inventory_snapshot(supplier_product, snapshot_at))
        inventory_snapshots_count += 1

        price_snapshot = repository.save_price_snapshot(_build_price_snapshot(supplier_product, snapshot_at))
        price_snapshots_count += 1

        seller_snapshot = repository.save_seller_snapshot(_build_seller_snapshot(supplier_product, snapshot_at))
        seller_snapshots_count += 1

        screening_input = build_screening_input(
            supplier_product=supplier_product,
            product_snapshots=[product_snapshot],
            inventory_snapshots=[inventory_snapshot],
            price_snapshots=[price_snapshot],
            seller_snapshots=[seller_snapshot],
        )
        repository.save_screening_input(screening_input)
        screening_inputs_count += 1

    archive_statistics = {
        "products_received": len(products),
        "products_archived": archived_products,
        "products_skipped": skipped_products,
        "product_snapshots_created": product_snapshots_count,
        "inventory_snapshots_created": inventory_snapshots_count,
        "price_snapshots_created": price_snapshots_count,
        "seller_snapshots_created": seller_snapshots_count,
        "screening_inputs_generated": screening_inputs_count,
    }
    return ArchiveResult(
        supplier_name="doba",
        archived_products=archived_products,
        product_snapshots=product_snapshots_count,
        inventory_snapshots=inventory_snapshots_count,
        price_snapshots=price_snapshots_count,
        seller_snapshots=seller_snapshots_count,
        screening_inputs=screening_inputs_count,
        skipped_products=skipped_products,
        archive_statistics=archive_statistics,
        warnings=warnings,
    )
