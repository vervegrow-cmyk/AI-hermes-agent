from dataclasses import asdict, dataclass, field


@dataclass
class AgentDefinition:
    name: str
    description: str
    capabilities: list[str]
    url: str
    version: str = "0.1.0"
    tags: list[str] = field(default_factory=list)


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, AgentDefinition] = {}

    def register(self, definition: AgentDefinition) -> AgentDefinition:
        self._agents[definition.name] = definition
        return definition

    def list_agents(self) -> list[dict]:
        return [asdict(agent) for agent in self._agents.values()]

    def get_agent(self, name: str) -> dict | None:
        agent = self._agents.get(name)
        return asdict(agent) if agent else None


registry = AgentRegistry()
registry.register(
    AgentDefinition(
        name="trend-agent",
        description="Discovers trends, pain points, and product/content opportunities.",
        capabilities=["trend-discovery", "keyword-analysis", "sentiment-extraction"],
        url="http://trend-agent:8081",
        tags=["trends", "research"],
    )
)
registry.register(
    AgentDefinition(
        name="content-agent",
        description="Generates multi-channel marketing and content assets.",
        capabilities=["content-generation", "copywriting", "script-writing"],
        url="http://content-agent:8082",
        tags=["content", "marketing"],
    )
)
registry.register(
    AgentDefinition(
        name="shopify-agent",
        description="Coordinates Shopify operations and content publishing workflows.",
        capabilities=["shopify-ops", "catalog-sync", "product-publish"],
        url="http://shopify-agent:8083",
        tags=["shopify", "commerce"],
    )
)
registry.register(
    AgentDefinition(
        name="analytics-agent",
        description="Produces analytics summaries, alerts, and KPI interpretation.",
        capabilities=["analytics-reporting", "kpi-summary", "forecasting"],
        url="http://analytics-agent:8084",
        tags=["analytics", "bi"],
    )
)
registry.register(
    AgentDefinition(
        name="hermes-trendforge-agent",
        description="Collects search and comment intelligence to uncover topic opportunities and customer needs.",
        capabilities=["execute", "discover-insights", "demand-intelligence", "pain-point-analysis"],
        url="http://hermes-trendforge-agent:8085",
        tags=["intelligence", "research", "topics"],
    )
)
registry.register(
    AgentDefinition(
        name="doba-shopify-agent",
        description="Evaluates Doba supplier products and creates controlled Shopify draft listings.",
        capabilities=["execute", "evaluate-product", "evaluate-batch", "publish-approved"],
        url="http://doba-shopify-agent:8086",
        tags=["doba", "shopify", "catalog"],
    )
)
registry.register(
    AgentDefinition(
        name="shopify-inventory-agent",
        description="Validates Shopify and Giga connections, then syncs Shopify inventory by SKU.",
        capabilities=["execute", "inventory-sync", "sku-sync", "shopify-inventory"],
        url="http://shopify-inventory-agent:8087",
        tags=["shopify", "inventory", "giga"],
    )
)
registry.register(
    AgentDefinition(
        name="shopify-category-agent",
        description="Prepares Shopify category classification and taxonomy mapping workflows.",
        capabilities=["execute", "category-sync", "taxonomy-mapping", "shopify-category"],
        url="http://shopify-category-agent:8088",
        tags=["shopify", "category", "taxonomy"],
    )
)
registry.register(
    AgentDefinition(
        name="yt-dlp-service",
        description="Wraps the local external/yt-dlp project for media metadata extraction and downloads.",
        capabilities=[
            "media-download",
            "video-metadata-extraction",
            "playlist-inspection",
            "audio-extraction",
        ],
        url="http://127.0.0.1:8092/mcp",
        tags=["media", "yt-dlp", "downloads", "mcp"],
    )
)
registry.register(
    AgentDefinition(
        name="agent-reach",
        description="Provides internet channel diagnostics, update checks, and transcription through the local Agent Reach integration.",
        capabilities=[
            "internet-diagnostics",
            "channel-registry",
            "update-check",
            "transcription",
            "web-research-routing",
        ],
        url="local://external/Agent-Reach",
        tags=["research", "internet", "mcp", "tooling"],
    )
)
registry.register(
    AgentDefinition(
        name="opencli",
        description="Wraps the local external/OpenCLI install so Hermes and Codex can drive browser-backed adapters and local CLI bridges.",
        capabilities=[
            "browser-automation",
            "site-adapters",
            "desktop-app-automation",
            "local-cli-bridge",
        ],
        url="http://127.0.0.1:8093/mcp",
        tags=["opencli", "browser", "mcp", "automation"],
    )
)
registry.register(
    AgentDefinition(
        name="browser-harness",
        description="Wraps the local browser-harness install so Hermes and Codex can drive Chrome via the shared Browser Use harness.",
        capabilities=[
            "browser-automation",
            "cdp-browser-control",
            "visual-browser-testing",
            "local-mcp-bridge",
        ],
        url="http://127.0.0.1:8094/mcp",
        tags=["browser-harness", "browser", "mcp", "automation"],
    )
)
