from __future__ import annotations

from collections import Counter
import re
from typing import Any

from shared.clients import FirecrawlClient


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "be",
    "best",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "with",
}

PAIN_POINT_MARKERS = {
    "can't",
    "confusing",
    "difficult",
    "expensive",
    "hard",
    "hate",
    "issue",
    "missing",
    "problem",
    "slow",
    "stuck",
    "waste",
    "wish",
}

INTENT_MARKERS = {
    "comparison": ["vs", "compare", "comparison", "better"],
    "purchase": ["buy", "price", "worth", "cheap", "affordable"],
    "education": ["how", "guide", "learn", "tutorial", "tips"],
    "troubleshooting": ["fix", "problem", "issue", "not working", "stuck"],
}


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9\-']+", text.lower())


def _rank_keywords(search_queries: list[str], comments: list[str]) -> list[str]:
    tokens: list[str] = []
    for text in [*search_queries, *comments]:
        tokens.extend(token for token in _tokenize(text) if token not in STOPWORDS and len(token) > 2)
    return [keyword for keyword, _ in Counter(tokens).most_common(8)]


def _extract_pain_points(comments: list[str]) -> list[str]:
    findings: list[str] = []
    for comment in comments:
        lowered = comment.lower()
        if any(marker in lowered for marker in PAIN_POINT_MARKERS):
            findings.append(comment.strip())
    if findings:
        return findings[:5]
    return ["No explicit pain points detected yet. Collect more user comments for stronger signals."]


def _build_topic_clusters(search_queries: list[str], comments: list[str]) -> list[dict]:
    combined = [*search_queries, *comments]
    clusters = []
    for keyword in _rank_keywords(search_queries, comments)[:4]:
        related = [entry for entry in combined if keyword in entry.lower()]
        clusters.append(
            {
                "topic": keyword,
                "signal_count": len(related),
                "sample_signals": related[:3],
            }
        )
    return clusters


def _detect_intents(search_queries: list[str], comments: list[str]) -> dict[str, int]:
    scores = {intent: 0 for intent in INTENT_MARKERS}
    for text in [*search_queries, *comments]:
        lowered = text.lower()
        for intent, markers in INTENT_MARKERS.items():
            if any(marker in lowered for marker in markers):
                scores[intent] += 1
    return scores


def _generate_opportunities(keywords: list[str], intents: dict[str, int], audience: str) -> list[dict]:
    top_intents = sorted(intents.items(), key=lambda item: item[1], reverse=True)
    dominant_intent = top_intents[0][0] if top_intents else "education"
    opportunities = []
    for keyword in keywords[:3]:
        opportunities.append(
            {
                "title": f"{keyword.title()} demand brief for {audience}",
                "angle": f"Create a {dominant_intent}-focused asset around {keyword}.",
                "priority_score": min(95, 55 + len(keyword) + intents.get(dominant_intent, 0) * 8),
            }
        )
    return opportunities


def discover_insights(
    search_queries: list[str],
    comments: list[str],
    market: str,
    audience: str,
) -> dict:
    keywords = _rank_keywords(search_queries, comments)
    pain_points = _extract_pain_points(comments)
    intents = _detect_intents(search_queries, comments)
    topic_clusters = _build_topic_clusters(search_queries, comments)
    opportunities = _generate_opportunities(keywords, intents, audience)

    demand_summary = (
        "High research intent detected"
        if intents.get("education", 0) + intents.get("comparison", 0) >= 3
        else "Emerging demand signals detected"
    )

    return {
        "agent": "hermes-trendforge-agent",
        "market": market,
        "audience": audience,
        "search_signal_count": len(search_queries),
        "comment_signal_count": len(comments),
        "keywords": keywords,
        "pain_points": pain_points,
        "customer_needs": [
            "Faster evaluation of options",
            "Clearer implementation guidance",
            "More trustworthy comparisons before purchase",
        ],
        "topic_clusters": topic_clusters,
        "intent_scores": intents,
        "opportunities": opportunities,
        "demand_summary": demand_summary,
    }


def scrape_urls(
    urls: list[str],
    *,
    formats: list[str | dict[str, Any]] | None = None,
    only_main_content: bool = True,
) -> dict[str, Any]:
    client = FirecrawlClient()
    results: list[dict[str, Any]] = []

    for url in urls:
        response = client.scrape(
            url,
            formats=formats or ["markdown"],
            only_main_content=only_main_content,
        )
        payload = response.json()
        results.append(
            {
                "url": url,
                "status_code": response.status_code,
                "success": bool(payload.get("success", response.is_success)),
                "data": payload.get("data", {}),
                "raw": payload,
            }
        )

    success_count = sum(1 for item in results if item["success"])
    return {
        "agent": "hermes-trendforge-agent",
        "tool": "firecrawl",
        "url_count": len(urls),
        "success_count": success_count,
        "results": results,
        "summary": f"Scraped {success_count}/{len(urls)} urls with Firecrawl.",
    }


def discover_insights_from_urls(
    urls: list[str],
    *,
    market: str,
    audience: str,
    formats: list[str | dict[str, Any]] | None = None,
) -> dict[str, Any]:
    scrape_result = scrape_urls(urls, formats=formats or ["markdown"], only_main_content=True)

    search_queries = list(urls)
    comments: list[str] = []
    sources: list[dict[str, Any]] = []
    for result in scrape_result["results"]:
        data = result.get("data", {})
        markdown = str(data.get("markdown", "") or "")
        metadata = data.get("metadata", {}) if isinstance(data.get("metadata"), dict) else {}
        if markdown:
            comments.append(markdown[:2000])
        sources.append(
            {
                "url": result["url"],
                "status_code": result["status_code"],
                "title": metadata.get("title", ""),
                "source_url": metadata.get("sourceURL", result["url"]),
            }
        )

    insight = discover_insights(
        search_queries=search_queries,
        comments=comments,
        market=market,
        audience=audience,
    )
    insight["tool"] = "firecrawl"
    insight["sources"] = sources
    insight["scrape_summary"] = scrape_result["summary"]
    return insight
