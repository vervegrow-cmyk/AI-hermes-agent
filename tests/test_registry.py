from shared.registry import registry


def test_registry_contains_seed_agents():
    agents = registry.list_agents()
    assert len(agents) >= 6
    assert any(agent["name"] == "trend-agent" for agent in agents)
    assert any(agent["name"] == "hermes-trendforge-agent" for agent in agents)
    assert any(agent["name"] == "yt-dlp-service" for agent in agents)
    assert any(agent["name"] == "agent-reach" for agent in agents)
    assert any(agent["name"] == "browser-harness" for agent in agents)
