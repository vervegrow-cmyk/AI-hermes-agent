from fastapi import APIRouter
from pydantic import BaseModel

from service.executor import execute_task
from service.trend_service import discover_trends
from shared.agent_runtime import create_agent_app
from shared.registry import registry

_definition = registry.get_agent("trend-agent") or {}

app = create_agent_app(
    agent_name="trend-agent",
    description="Trend discovery agent for multi-source market research.",
    executor=execute_task,
    capabilities=_definition.get("capabilities", []),
)

router = APIRouter()


class TrendDiscoverRequest(BaseModel):
    niche: str
    sources: list[str] = ["google-trends", "youtube", "reddit", "amazon"]
    market: str = "US"


@router.post("/discover")
def discover(request: TrendDiscoverRequest) -> dict:
    return discover_trends(niche=request.niche, sources=request.sources, market=request.market)


app.include_router(router)
