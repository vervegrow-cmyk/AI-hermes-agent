from shared.schemas import ExecuteRequest


def execute_task(request: ExecuteRequest) -> dict:
    metric = request.payload.get("metric", "revenue")
    return {
        "metric": metric,
        "summary": f"{metric} is stable but needs source-specific drill-down.",
        "alerts": ["CTR dipped on short-form content", "Organic conversions improved week-over-week"],
        "recommended_actions": [
            "Compare top 10 landing pages.",
            "Correlate trend keywords with content output volume.",
            "Review paid vs organic attribution consistency.",
        ],
    }

