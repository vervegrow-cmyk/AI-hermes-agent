from bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from fastapi import APIRouter, HTTPException

from models.price_sync import PriceSyncRequest
from models.variant_mapping import VariantMappingBuildRequest, VariantMappingImportRequest, VariantMappingValidateRequest
from service.doba_client import DobaPriceSyncClient
from service.executor import execute_task, run_price_sync
from service.mapping_exporter import MappingExporter
from service.mapping_importer import MappingImporter
from service.mapping_repository import MappingRepository
from service.mapping_validator import MappingValidator
from service.sync_repository import SyncRepository
from service.terminal_reporter import build_mapping_build_lines, build_mapping_validate_lines, emit_lines
from service.variant_mapping_builder import VariantMappingBuilder
from shared.agent_runtime import create_agent_app

app = create_agent_app(
    agent_name="doba-price-sync-agent",
    description="Doba to Shopify variant price synchronization agent using shared Hermes settings.",
    executor=execute_task,
    capabilities=["price-sync", "doba-price-sync"],
)

router = APIRouter(prefix="/price-sync", tags=["price-sync"])
mapping_router = APIRouter(prefix="/variant-mapping", tags=["variant-mapping"])


@router.post("/dry-run")
def dry_run_price_sync(request: PriceSyncRequest) -> dict:
    batch = run_price_sync(request.model_copy(update={"mode": "dry-run"}))
    return batch.model_dump(mode="json")


@router.post("/apply")
def apply_price_sync(request: PriceSyncRequest) -> dict:
    batch = run_price_sync(request.model_copy(update={"mode": "apply"}))
    return batch.model_dump(mode="json")


@router.post("/single")
def sync_single_price(request: PriceSyncRequest) -> dict:
    batch = run_price_sync(
        request.model_copy(
            update={
                "sync_scope": "single_sku",
                "force_recalculate": True,
                "skip_incremental_cache": True,
            }
        )
    )
    return batch.model_dump(mode="json")


@router.get("/batches/{batch_id}")
def get_batch(batch_id: str) -> dict:
    batch = SyncRepository().get_batch(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found.")
    return batch


@router.post("/mapping-template")
def create_mapping_template() -> dict:
    path = MappingRepository().write_template()
    return {"ok": True, "path": path}


@router.get("/debug/doba")
def debug_doba(
    store_name: str = "",
    sync_scope: str = "full",
    updated_since: str = "",
    endpoint: str = "",
    skus: str = "",
) -> dict:
    return DobaPriceSyncClient().debug_price_snapshots(
        store_name=store_name,
        sync_scope=sync_scope,
        updated_since=updated_since,
        endpoint_override=endpoint,
        skus=[item.strip() for item in skus.split(",") if item.strip()],
    )


@mapping_router.post("/build")
def build_variant_mapping(request: VariantMappingBuildRequest) -> dict:
    report = VariantMappingBuilder().build(request)
    if request.print_detail:
        emit_lines(build_mapping_build_lines(report=report))
    return report


@mapping_router.post("/validate")
def validate_variant_mapping(request: VariantMappingValidateRequest) -> dict:
    repository = MappingRepository()
    validation = MappingValidator().validate(
        store_name=request.store_name,
        records=repository.load_variant_records(),
    )
    emit_lines(build_mapping_validate_lines(validation=validation))
    return validation


@mapping_router.get("/stats")
def get_variant_mapping_stats(store_name: str) -> dict:
    repository = MappingRepository()
    records = repository.load_variant_records()
    return repository.build_mapping_stats(store_name=store_name, records=records)


@mapping_router.get("/export-review")
def export_variant_mapping_review(store_name: str) -> dict:
    return MappingExporter().export_review(store_name=store_name)


@mapping_router.post("/import-reviewed")
def import_reviewed_variant_mapping(request: VariantMappingImportRequest) -> dict:
    result = MappingImporter().import_reviewed(store_name=request.store_name, file_path=request.file_path)
    validation = MappingValidator().validate(
        store_name=request.store_name,
        records=MappingRepository().load_variant_records(),
    )
    return {"ok": True, "import_result": result, "validation": validation}


@mapping_router.get("/debug")
def debug_variant_mapping(store_name: str) -> dict:
    repository = MappingRepository()
    records = repository.load_variant_records()
    stats = repository.build_mapping_stats(store_name=store_name, records=records)
    return {
        "ok": True,
        "store_name": store_name,
        "paths": {
            "mappings": str(repository.path.resolve()),
            "candidates": str(repository.candidates_path.resolve()),
            "review_csv": str(repository.review_csv_path.resolve()),
            "unmatched_doba": str(repository.unmatched_doba_path.resolve()),
            "unmatched_shopify": str(repository.unmatched_shopify_path.resolve()),
            "duplicates": str(repository.duplicates_path.resolve()),
        },
        "stats": stats,
        "preview": [item.model_dump(mode="json") for item in records if item.store_name == store_name][:5],
        "shopify_query": "vendor:Doba",
    }


app.include_router(router)
app.include_router(mapping_router)
