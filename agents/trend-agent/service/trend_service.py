def discover_trends(niche: str, sources: list[str], market: str) -> dict:
    topics = [
        f"{niche} buying guides",
        f"{niche} comparison content",
        f"{niche} workflow automation",
    ]
    pain_points = [
        "Users struggle to compare options quickly.",
        "Information is scattered across marketplaces and communities.",
        "Content angles are often repetitive and fail to convert.",
    ]
    return {
        "keyword": f"{niche} trends {market.lower()}",
        "pain_points": pain_points,
        "topics": topics,
        "opportunity_score": 82,
        "sources": sources,
        "market": market,
    }

