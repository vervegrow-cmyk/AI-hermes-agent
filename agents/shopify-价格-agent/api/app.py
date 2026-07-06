from bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from fastapi import APIRouter, HTTPException

from models.price_sync import PriceSyncRequest
from shared.agent_runtime import create_agent_app
from shared.clients import ShopifyAuthClient
from shared.config import get_settings
from service.giga_client import GigaClient
from service.mapping_repository import MappingRepository
from service.executor import run_price_sync
from service.executor import execute_task

app = create_agent_app(
    agent_name="shopify-price-agent",
    description="Shopify price operations agent wired to the shared Hermes settings.",
    executor=execute_task,
    capabilities=["price-analysis", "price-sync"],
)

router = APIRouter(prefix="/price-sync", tags=["price-sync"])


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
                "mode": request.mode,
                "sync_scope": "single_sku",
                "force_recalculate": True,
                "skip_incremental_cache": True,
            }
        )
    )
    return batch.model_dump(mode="json")


@router.get("/batches/{batch_id}")
def get_batch(batch_id: str) -> dict:
    from service.sync_repository import SyncRepository

    batch = SyncRepository().get_batch(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found.")
    return batch


@router.get("/debug/giga")
def debug_giga(
    store_name: str = "",
    sync_scope: str = "full",
    updated_since: str = "",
    endpoint: str = "",
    skus: str = "",
) -> dict:
    return GigaClient().debug_price_snapshots(
        store_name=store_name,
        sync_scope=sync_scope,
        updated_since=updated_since,
        endpoint_override=endpoint,
        skus=[item.strip() for item in skus.split(",") if item.strip()],
    )


@router.get("/debug/giga-probe")
def debug_giga_probe(store_name: str = "", sync_scope: str = "full") -> dict:
    return GigaClient().probe_endpoints(store_name=store_name, sync_scope=sync_scope)


@router.get("/debug/frontend")
def debug_frontend() -> dict:
    return GigaClient().debug_frontend_access()


@router.get("/debug/shopify-auth")
def debug_shopify_auth() -> dict:
    return ShopifyAuthClient.from_settings(get_settings()).debug_admin_session()


@router.post("/mapping-template")
def create_mapping_template() -> dict:
    path = MappingRepository().write_template()
    return {"ok": True, "path": path}


app.include_router(router)
