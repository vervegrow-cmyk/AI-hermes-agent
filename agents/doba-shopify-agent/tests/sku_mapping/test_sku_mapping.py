from src.modules.sku_mapping import resolve_sku_mapping
from src.shared.contracts.mapping import ResolveSkuCommand, SkuMappingRecord
from src.shared.repositories import InMemorySkuMappingRepository


def test_sku_mapping_returns_existing_record():
    repository = InMemorySkuMappingRepository()
    repository.save(
        SkuMappingRecord(
            supplier_product_id="prod-1",
            sku="sku-1",
            shopify_product_id="shop-prod-1",
            shopify_variant_id="shop-var-1",
        )
    )
    result = resolve_sku_mapping(ResolveSkuCommand(supplier_product_id="prod-1", sku="sku-1"), repository)
    assert result.shopify_product_id == "shop-prod-1"


def test_sku_mapping_returns_empty_record_when_missing():
    repository = InMemorySkuMappingRepository()
    result = resolve_sku_mapping(ResolveSkuCommand(supplier_product_id="prod-2", sku="sku-2"), repository)
    assert result.shopify_product_id == ""

