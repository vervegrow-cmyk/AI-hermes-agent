from shared.schemas import ExecuteRequest

from service.trend_service import discover_trends


def execute_task(request: ExecuteRequest) -> dict:
    niche = request.payload.get("niche", request.task)
    sources = request.payload.get("sources", ["google-trends", "youtube", "reddit", "amazon"])
    market = request.payload.get("market", "US")
    return discover_trends(niche=niche, sources=sources, market=market)
