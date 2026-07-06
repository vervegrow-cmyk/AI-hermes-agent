from __future__ import annotations

from src.shared.contracts.inventory import (
    InventorySyncBatchResult,
    InventorySyncRecord,
    ShopifyInventoryState,
    SupplierInventory,
)
from src.shared.contracts.listing import ListingBatchResult, ShopifyDraftProduct
from src.shared.contracts.mapping import SkuMappingRecord
from src.shared.contracts.pricing import (
    PlatformCost,
    PricingDecision,
    PriceSyncBatchResult,
    PriceSyncRecord,
    ShippingCost,
    ShopifyPriceState,
    SupplierCost,
    WarehouseCost,
)
from src.shared.contracts.risk import (
    ApprovalQueueItem,
    BlockedProduct,
    RiskAlert,
    RiskBatchResult,
    RiskEvent,
    RiskReport,
    RiskScore,
    SupplierRiskScore,
)
from src.shared.contracts.screening import (
    CandidatePoolBatchResult,
    ListingCandidate,
    ProductScore,
    ProductScoreBatchResult,
    RuleEngineResult,
    ScreeningDecision,
)
from src.shared.contracts.supplier_archive import (
    InventorySnapshot,
    PriceSnapshot,
    ProductSnapshot,
    ScreeningInput,
    SellerSnapshot,
    SupplierProduct,
)
from src.shared.repositories.protocols import (
    DecisionLogRepository,
    InventorySyncBatchRepository,
    InventorySyncLogRepository,
    ListingRepository,
    PlatformCostRepository,
    PriceSyncBatchRepository,
    PriceSyncLogRepository,
    PricingDecisionRepository,
    ProductScreeningRepository,
    ProductStateRepository,
    ShippingCostRepository,
    ShopifyInventoryRepository,
    ShopifyPriceRepository,
    SupplierCostRepository,
    SupplierInventoryRepository,
    SupplierArchiveRepository,
    SkuMappingRepository,
    WarehouseCostRepository,
    ApprovalQueueRepository,
    BlockedProductRepository,
    RiskAlertRepository,
    RiskBatchRepository,
    RiskEventRepository,
    RiskReportRepository,
    RiskScoreRepository,
    SupplierRiskRepository,
)


class InMemoryDecisionLogRepository(DecisionLogRepository):
    def __init__(self) -> None:
        self.records: list[dict] = []

    def save(self, decision: ScreeningDecision) -> dict:
        record = {
            "product_id": decision.product_id,
            "sku": decision.sku,
            "status": decision.status,
            "reasons": list(decision.reasons),
            "target_market": decision.target_market,
            "score": decision.score,
        }
        self.records.append(record)
        return record


class InMemorySkuMappingRepository(SkuMappingRepository):
    def __init__(self) -> None:
        self.by_sku: dict[str, SkuMappingRecord] = {}
        self.by_supplier_product_id: dict[str, SkuMappingRecord] = {}

    def get_by_sku(self, sku: str) -> SkuMappingRecord | None:
        return self.by_sku.get(sku.strip().lower())

    def get_by_supplier_product_id(self, supplier_product_id: str) -> SkuMappingRecord | None:
        return self.by_supplier_product_id.get(supplier_product_id.strip().lower())

    def save(self, record: SkuMappingRecord) -> SkuMappingRecord:
        sku_key = (record.supplier_sku or record.sku).strip().lower()
        if sku_key:
            self.by_sku[sku_key] = record
        if record.supplier_product_id:
            self.by_supplier_product_id[record.supplier_product_id.strip().lower()] = record
        return record

    def list_all(self) -> list[SkuMappingRecord]:
        return list(self.by_sku.values())


class InMemoryProductStateRepository(ProductStateRepository):
    def __init__(self) -> None:
        self.keys: set[str] = set()

    def is_duplicate(self, duplicate_key: str) -> bool:
        return duplicate_key in self.keys

    def remember(self, duplicate_key: str) -> None:
        if duplicate_key:
            self.keys.add(duplicate_key)


class InMemoryListingRepository(ListingRepository):
    def __init__(self) -> None:
        self.drafts: dict[str, str] = {}
        self.shopify_products: list[ShopifyDraftProduct] = []
        self.batch_results: list[ListingBatchResult] = []

    def mark_created(self, duplicate_key: str, draft_id: str) -> None:
        if duplicate_key and draft_id:
            self.drafts[duplicate_key] = draft_id

    def get_draft_id(self, duplicate_key: str) -> str | None:
        return self.drafts.get(duplicate_key)

    def save_shopify_product(self, product: ShopifyDraftProduct) -> ShopifyDraftProduct:
        self.shopify_products.append(product)
        return product

    def list_shopify_products(self) -> list[ShopifyDraftProduct]:
        return list(self.shopify_products)

    def get_shopify_product_by_supplier_sku(self, supplier_sku: str) -> ShopifyDraftProduct | None:
        key = supplier_sku.strip().lower()
        for product in reversed(self.shopify_products):
            if product.supplier_sku.strip().lower() == key:
                return product
        return None

    def handle_exists(self, handle: str) -> bool:
        key = handle.strip().lower()
        return any(product.handle.strip().lower() == key for product in self.shopify_products)

    def product_hash_exists(self, product_hash: str) -> bool:
        key = product_hash.strip().lower()
        return any(product.product_hash.strip().lower() == key for product in self.shopify_products)

    def save_listing_batch_result(self, result: ListingBatchResult) -> ListingBatchResult:
        self.batch_results.append(result)
        return result

    def list_listing_batch_results(self) -> list[ListingBatchResult]:
        return list(self.batch_results)


class InMemoryProductScreeningRepository(ProductScreeningRepository):
    def __init__(self) -> None:
        self.rule_engine_results: list[RuleEngineResult] = []
        self.pre_filtered_products: list[ScreeningInput] = []
        self.ai_product_scores: list[ProductScore] = []
        self.product_score_batch_results: list[ProductScoreBatchResult] = []
        self.listing_candidates: list[ListingCandidate] = []
        self.candidate_pool_batch_results: list[CandidatePoolBatchResult] = []

    def save_rule_engine_result(self, result: RuleEngineResult) -> RuleEngineResult:
        self.rule_engine_results.append(result)
        return result

    def list_rule_engine_results(self) -> list[RuleEngineResult]:
        return list(self.rule_engine_results)

    def save_pre_filtered_product(self, product: ScreeningInput) -> ScreeningInput:
        self.pre_filtered_products.append(product)
        return product

    def list_pre_filtered_products(self) -> list[ScreeningInput]:
        return list(self.pre_filtered_products)

    def save_ai_product_score(self, score: ProductScore) -> ProductScore:
        self.ai_product_scores.append(score)
        return score

    def list_ai_product_scores(self) -> list[ProductScore]:
        return list(self.ai_product_scores)

    def get_latest_ai_product_score(self, supplier_sku: str) -> ProductScore | None:
        key = supplier_sku.strip().lower()
        for score in reversed(self.ai_product_scores):
            if score.supplier_sku.strip().lower() == key:
                return score
        return None

    def save_product_score_batch_result(self, result: ProductScoreBatchResult) -> ProductScoreBatchResult:
        self.product_score_batch_results.append(result)
        return result

    def save_listing_candidate(self, candidate: ListingCandidate) -> ListingCandidate:
        self.listing_candidates.append(candidate)
        return candidate

    def list_listing_candidates(self) -> list[ListingCandidate]:
        return list(self.listing_candidates)

    def get_listing_candidate_by_sku(self, supplier_sku: str) -> ListingCandidate | None:
        key = supplier_sku.strip().lower()
        for candidate in reversed(self.listing_candidates):
            if candidate.supplier_sku.strip().lower() == key:
                return candidate
        return None

    def save_candidate_pool_batch_result(self, result: CandidatePoolBatchResult) -> CandidatePoolBatchResult:
        self.candidate_pool_batch_results.append(result)
        return result

    def list_candidate_pool_batch_results(self) -> list[CandidatePoolBatchResult]:
        return list(self.candidate_pool_batch_results)


class InMemorySupplierArchiveRepository(SupplierArchiveRepository):
    def __init__(self) -> None:
        self.supplier_products: list[SupplierProduct] = []
        self.product_snapshots: list[ProductSnapshot] = []
        self.inventory_snapshots: list[InventorySnapshot] = []
        self.price_snapshots: list[PriceSnapshot] = []
        self.seller_snapshots: list[SellerSnapshot] = []
        self.screening_inputs: list[ScreeningInput] = []

    def save_supplier_product(self, product: SupplierProduct) -> SupplierProduct:
        self.supplier_products.append(product)
        return product

    def list_supplier_products(self) -> list[SupplierProduct]:
        return list(self.supplier_products)

    def save_product_snapshot(self, snapshot: ProductSnapshot) -> ProductSnapshot:
        self.product_snapshots.append(snapshot)
        return snapshot

    def list_product_snapshots(self) -> list[ProductSnapshot]:
        return list(self.product_snapshots)

    def save_inventory_snapshot(self, snapshot: InventorySnapshot) -> InventorySnapshot:
        self.inventory_snapshots.append(snapshot)
        return snapshot

    def list_inventory_snapshots(self) -> list[InventorySnapshot]:
        return list(self.inventory_snapshots)

    def save_price_snapshot(self, snapshot: PriceSnapshot) -> PriceSnapshot:
        self.price_snapshots.append(snapshot)
        return snapshot

    def list_price_snapshots(self) -> list[PriceSnapshot]:
        return list(self.price_snapshots)

    def save_seller_snapshot(self, snapshot: SellerSnapshot) -> SellerSnapshot:
        self.seller_snapshots.append(snapshot)
        return snapshot

    def list_seller_snapshots(self) -> list[SellerSnapshot]:
        return list(self.seller_snapshots)

    def save_screening_input(self, screening_input: ScreeningInput) -> ScreeningInput:
        self.screening_inputs.append(screening_input)
        return screening_input

    def list_screening_inputs(self) -> list[ScreeningInput]:
        return list(self.screening_inputs)


class InMemorySupplierInventoryRepository(SupplierInventoryRepository):
    def __init__(self) -> None:
        self.records: dict[str, SupplierInventory] = {}

    def save_supplier_inventory(self, inventory: SupplierInventory) -> SupplierInventory:
        self.records[inventory.supplier_sku.strip().lower()] = inventory
        return inventory

    def list_supplier_inventories(self) -> list[SupplierInventory]:
        return list(self.records.values())

    def get_supplier_inventory_by_sku(self, supplier_sku: str) -> SupplierInventory | None:
        return self.records.get(supplier_sku.strip().lower())


class InMemoryShopifyInventoryRepository(ShopifyInventoryRepository):
    def __init__(self) -> None:
        self.records: dict[str, ShopifyInventoryState] = {}

    def save_shopify_inventory_state(self, state: ShopifyInventoryState) -> ShopifyInventoryState:
        self.records[state.supplier_sku.strip().lower()] = state
        return state

    def list_shopify_inventory_states(self) -> list[ShopifyInventoryState]:
        return list(self.records.values())

    def get_shopify_inventory_state_by_sku(self, supplier_sku: str) -> ShopifyInventoryState | None:
        return self.records.get(supplier_sku.strip().lower())


class InMemoryInventorySyncLogRepository(InventorySyncLogRepository):
    def __init__(self) -> None:
        self.records: list[InventorySyncRecord] = []

    def save_inventory_sync_record(self, record: InventorySyncRecord) -> InventorySyncRecord:
        self.records.append(record)
        return record

    def list_inventory_sync_records(self) -> list[InventorySyncRecord]:
        return list(self.records)


class InMemoryInventorySyncBatchRepository(InventorySyncBatchRepository):
    def __init__(self) -> None:
        self.results: list[InventorySyncBatchResult] = []

    def save_inventory_sync_batch_result(self, result: InventorySyncBatchResult) -> InventorySyncBatchResult:
        self.results.append(result)
        return result

    def list_inventory_sync_batch_results(self) -> list[InventorySyncBatchResult]:
        return list(self.results)


class InMemorySupplierCostRepository(SupplierCostRepository):
    def __init__(self) -> None:
        self.records: dict[str, SupplierCost] = {}

    def save_supplier_cost(self, cost: SupplierCost) -> SupplierCost:
        self.records[cost.supplier_sku.strip().lower()] = cost
        return cost

    def list_supplier_costs(self) -> list[SupplierCost]:
        return list(self.records.values())

    def get_supplier_cost_by_sku(self, supplier_sku: str) -> SupplierCost | None:
        return self.records.get(supplier_sku.strip().lower())


class InMemoryShippingCostRepository(ShippingCostRepository):
    def __init__(self) -> None:
        self.records: dict[str, ShippingCost] = {}

    def save_shipping_cost(self, cost: ShippingCost) -> ShippingCost:
        self.records[cost.supplier_sku.strip().lower()] = cost
        return cost

    def list_shipping_costs(self) -> list[ShippingCost]:
        return list(self.records.values())

    def get_shipping_cost_by_sku(self, supplier_sku: str) -> ShippingCost | None:
        return self.records.get(supplier_sku.strip().lower())


class InMemoryWarehouseCostRepository(WarehouseCostRepository):
    def __init__(self) -> None:
        self.records: dict[str, WarehouseCost] = {}

    def save_warehouse_cost(self, cost: WarehouseCost) -> WarehouseCost:
        self.records[cost.supplier_sku.strip().lower()] = cost
        return cost

    def list_warehouse_costs(self) -> list[WarehouseCost]:
        return list(self.records.values())

    def get_warehouse_cost_by_sku(self, supplier_sku: str) -> WarehouseCost | None:
        return self.records.get(supplier_sku.strip().lower())


class InMemoryPlatformCostRepository(PlatformCostRepository):
    def __init__(self) -> None:
        self.records: dict[str, PlatformCost] = {}

    def save_platform_cost(self, cost: PlatformCost) -> PlatformCost:
        self.records[cost.supplier_sku.strip().lower()] = cost
        return cost

    def list_platform_costs(self) -> list[PlatformCost]:
        return list(self.records.values())

    def get_platform_cost_by_sku(self, supplier_sku: str) -> PlatformCost | None:
        return self.records.get(supplier_sku.strip().lower())


class InMemoryShopifyPriceRepository(ShopifyPriceRepository):
    def __init__(self) -> None:
        self.records: dict[str, ShopifyPriceState] = {}

    def save_shopify_price_state(self, state: ShopifyPriceState) -> ShopifyPriceState:
        self.records[state.supplier_sku.strip().lower()] = state
        return state

    def list_shopify_price_states(self) -> list[ShopifyPriceState]:
        return list(self.records.values())

    def get_shopify_price_state_by_sku(self, supplier_sku: str) -> ShopifyPriceState | None:
        return self.records.get(supplier_sku.strip().lower())


class InMemoryPricingDecisionRepository(PricingDecisionRepository):
    def __init__(self) -> None:
        self.records: list[PricingDecision] = []

    def save_pricing_decision(self, decision: PricingDecision) -> PricingDecision:
        self.records.append(decision)
        return decision

    def list_pricing_decisions(self) -> list[PricingDecision]:
        return list(self.records)


class InMemoryPriceSyncLogRepository(PriceSyncLogRepository):
    def __init__(self) -> None:
        self.records: list[PriceSyncRecord] = []

    def save_price_sync_record(self, record: PriceSyncRecord) -> PriceSyncRecord:
        self.records.append(record)
        return record

    def list_price_sync_records(self) -> list[PriceSyncRecord]:
        return list(self.records)


class InMemoryPriceSyncBatchRepository(PriceSyncBatchRepository):
    def __init__(self) -> None:
        self.results: list[PriceSyncBatchResult] = []

    def save_price_sync_batch_result(self, result: PriceSyncBatchResult) -> PriceSyncBatchResult:
        self.results.append(result)
        return result

    def list_price_sync_batch_results(self) -> list[PriceSyncBatchResult]:
        return list(self.results)


class InMemoryRiskEventRepository(RiskEventRepository):
    def __init__(self) -> None:
        self.records: list[RiskEvent] = []

    def save_risk_event(self, event: RiskEvent) -> RiskEvent:
        self.records.append(event)
        return event

    def list_risk_events(self) -> list[RiskEvent]:
        return list(self.records)


class InMemoryRiskAlertRepository(RiskAlertRepository):
    def __init__(self) -> None:
        self.records: list[RiskAlert] = []

    def save_risk_alert(self, alert: RiskAlert) -> RiskAlert:
        self.records.append(alert)
        return alert

    def list_risk_alerts(self) -> list[RiskAlert]:
        return list(self.records)


class InMemoryRiskReportRepository(RiskReportRepository):
    def __init__(self) -> None:
        self.records: list[RiskReport] = []

    def save_risk_report(self, report: RiskReport) -> RiskReport:
        self.records.append(report)
        return report

    def list_risk_reports(self) -> list[RiskReport]:
        return list(self.records)


class InMemoryApprovalQueueRepository(ApprovalQueueRepository):
    def __init__(self) -> None:
        self.records: list[ApprovalQueueItem] = []

    def save_approval_queue_item(self, item: ApprovalQueueItem) -> ApprovalQueueItem:
        self.records.append(item)
        return item

    def list_approval_queue_items(self) -> list[ApprovalQueueItem]:
        return list(self.records)


class InMemoryBlockedProductRepository(BlockedProductRepository):
    def __init__(self) -> None:
        self.records: list[BlockedProduct] = []

    def save_blocked_product(self, product: BlockedProduct) -> BlockedProduct:
        self.records.append(product)
        return product

    def list_blocked_products(self) -> list[BlockedProduct]:
        return list(self.records)


class InMemorySupplierRiskRepository(SupplierRiskRepository):
    def __init__(self) -> None:
        self.records: list[SupplierRiskScore] = []

    def save_supplier_risk_score(self, score: SupplierRiskScore) -> SupplierRiskScore:
        self.records.append(score)
        return score

    def list_supplier_risk_scores(self) -> list[SupplierRiskScore]:
        return list(self.records)


class InMemoryRiskScoreRepository(RiskScoreRepository):
    def __init__(self) -> None:
        self.records: list[RiskScore] = []

    def save_risk_score(self, score: RiskScore) -> RiskScore:
        self.records.append(score)
        return score

    def list_risk_scores(self) -> list[RiskScore]:
        return list(self.records)


class InMemoryRiskBatchRepository(RiskBatchRepository):
    def __init__(self) -> None:
        self.records: list[RiskBatchResult] = []

    def save_risk_batch_result(self, result: RiskBatchResult) -> RiskBatchResult:
        self.records.append(result)
        return result

    def list_risk_batch_results(self) -> list[RiskBatchResult]:
        return list(self.records)
