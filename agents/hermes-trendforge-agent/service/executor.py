from schemas import ExecuteRequest

from service.openhands_service import openhands_conversation
from service.openhands_status_service import get_openhands_status
from service.intelligence_service import discover_insights, discover_insights_from_urls, scrape_urls


def execute_task(request: ExecuteRequest) -> dict:
    payload = request.payload
    capability = (request.capability or "").strip().lower()

    if capability == "openhands-conversation":
        return openhands_conversation(
            prompt=payload.get("prompt", request.task),
            conversation_id=payload.get("conversation_id"),
            title=payload.get("title"),
            run=payload.get("run", True),
            wait_for_ready=payload.get("wait_for_ready", True),
            ready_timeout_seconds=payload.get("ready_timeout_seconds", 180.0),
            poll_interval_seconds=payload.get("poll_interval_seconds", 2.0),
            llm_model=payload.get("llm_model"),
            agent_type=payload.get("agent_type"),
        )

    if capability == "openhands-status":
        return get_openhands_status()

    if capability == "firecrawl-scrape":
        return scrape_urls(
            urls=payload.get("urls", []),
            formats=payload.get("formats", ["markdown"]),
            only_main_content=payload.get("only_main_content", True),
        )

    if capability in {"firecrawl-discover", "discover-insights-web"}:
        return discover_insights_from_urls(
            urls=payload.get("urls", []),
            market=payload.get("market", "US"),
            audience=payload.get("audience", "general"),
            formats=payload.get("formats", ["markdown"]),
        )

    return discover_insights(
        search_queries=payload.get("search_queries", []),
        comments=payload.get("comments", []),
        market=payload.get("market", "US"),
        audience=payload.get("audience", "general"),
    )
