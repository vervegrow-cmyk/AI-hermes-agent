from models.category_sync import CategorySyncRequest
from shared.config import get_settings
from shared.schemas import ExecuteRequest
from service.category_optimization_service import get_category_optimization_service


def execute_task(request: ExecuteRequest) -> dict:
    settings = get_settings()
    payload = dict(request.payload or {})
    command = CategorySyncRequest.model_validate(
        {
            "store_name": payload.get("store_name") or payload.get("store") or settings.shopify_shop,
            "mode": payload.get("mode", "dry-run"),
            "source": payload.get("source", "manual"),
            "product_query": payload.get("product_query", ""),
            "candidate_category": payload.get("candidate_category", ""),
            "max_items": payload.get("max_items", 0),
            "product_ids": payload.get("product_ids", []),
            "exclude_product_ids": payload.get("exclude_product_ids", []),
            "shopify_suggestions": payload.get("shopify_suggestions", {}),
            "apply_metafields": payload.get("apply_metafields", True),
        }
    )
    service = get_category_optimization_service()
    result = service.run(command, task=request.task)
    result["data"]["environment"] = settings.hermes_env
    result["data"]["shopify_api_version"] = settings.shopify_api_version
    result["data"]["source"] = command.source
    result["data"]["candidate_category"] = command.candidate_category
    result["data"]["max_items"] = command.max_items
    return result
