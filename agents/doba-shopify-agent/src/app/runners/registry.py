from __future__ import annotations

from src.app.runners.tasks import (
    doba_pipeline_task,
    evaluate_batch_task,
    evaluate_product_task,
    publish_approved_task,
    sync_candidates_task,
    sync_inventory_task,
    sync_prices_task,
)


RUNNERS = {
    "doba-pipeline": doba_pipeline_task,
    "evaluate-product": evaluate_product_task,
    "evaluate-batch": evaluate_batch_task,
    "publish-approved": publish_approved_task,
    "sync-candidates": sync_candidates_task,
    "inventory-sync": sync_inventory_task,
    "price-sync": sync_prices_task,
}
