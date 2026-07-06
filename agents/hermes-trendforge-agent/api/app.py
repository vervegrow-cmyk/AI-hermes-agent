import bootstrap

from fastapi import APIRouter
from pydantic import BaseModel, Field

from service.executor import execute_task
from service.intelligence_service import (
    discover_insights as discover_insights_service,
    discover_insights_from_urls as discover_insights_from_urls_service,
    scrape_urls as scrape_urls_service,
)
from service.openhands_service import openhands_conversation as openhands_conversation_service
from service.openhands_status_service import get_openhands_status as get_openhands_status_service
from shared.agent_runtime import create_agent_app

app = create_agent_app(
    agent_name="hermes-trendforge-agent",
    description="Intelligence collection agent for topic discovery and customer demand mapping.",
    executor=execute_task,
    capabilities=[
        "topic-discovery",
        "firecrawl-scrape",
        "discover-insights-web",
        "openhands-conversation",
        "openhands-status",
    ],
)

router = APIRouter()


class DiscoverInsightsRequest(BaseModel):
    search_queries: list[str] = Field(default_factory=list)
    comments: list[str] = Field(default_factory=list)
    market: str = "US"
    audience: str = "general"


class FirecrawlScrapeRequest(BaseModel):
    urls: list[str] = Field(default_factory=list)
    formats: list[str] = Field(default_factory=lambda: ["markdown"])
    only_main_content: bool = True


class FirecrawlDiscoverRequest(BaseModel):
    urls: list[str] = Field(default_factory=list)
    market: str = "US"
    audience: str = "general"
    formats: list[str] = Field(default_factory=lambda: ["markdown"])


class OpenHandsConversationRequest(BaseModel):
    prompt: str
    conversation_id: str | None = None
    title: str | None = None
    run: bool = True
    wait_for_ready: bool = True
    ready_timeout_seconds: float = 180.0
    poll_interval_seconds: float = 2.0
    llm_model: str | None = None
    agent_type: str | None = None


class OpenHandsStatusResponse(BaseModel):
    agent: str
    tool: str
    base_url: str
    service_reachable: bool
    service_status_code: int | None = None
    mcp_registered: bool
    registered_server_names: list[str] = Field(default_factory=list)
    registered_server: str
    connected: bool
    summary: str


@router.post("/discover-insights")
def discover_insights_route(request: DiscoverInsightsRequest) -> dict:
    return discover_insights_service(
        search_queries=request.search_queries,
        comments=request.comments,
        market=request.market,
        audience=request.audience,
    )


@router.post("/tools/firecrawl/scrape")
def firecrawl_scrape_route(request: FirecrawlScrapeRequest) -> dict:
    return scrape_urls_service(
        urls=request.urls,
        formats=request.formats,
        only_main_content=request.only_main_content,
    )


@router.post("/discover-insights-web")
def discover_insights_web_route(request: FirecrawlDiscoverRequest) -> dict:
    return discover_insights_from_urls_service(
        urls=request.urls,
        market=request.market,
        audience=request.audience,
        formats=request.formats,
    )


@router.post("/tools/openhands/conversation")
def openhands_conversation_route(request: OpenHandsConversationRequest) -> dict:
    return openhands_conversation_service(
        prompt=request.prompt,
        conversation_id=request.conversation_id,
        title=request.title,
        run=request.run,
        wait_for_ready=request.wait_for_ready,
        ready_timeout_seconds=request.ready_timeout_seconds,
        poll_interval_seconds=request.poll_interval_seconds,
        llm_model=request.llm_model,
        agent_type=request.agent_type,
    )


@router.get("/tools/openhands/status", response_model=OpenHandsStatusResponse)
def openhands_status_route() -> OpenHandsStatusResponse:
    return OpenHandsStatusResponse(**get_openhands_status_service())


app.include_router(router)
