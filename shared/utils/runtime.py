from shared.config import get_settings


def build_runtime_metadata(
    agent_name: str,
    version: str = "0.1.0",
    capabilities: list[str] | None = None,
) -> dict[str, object]:
    settings = get_settings()
    return {
        "status": "ok",
        "agent": agent_name,
        "version": version,
        "environment": settings.hermes_env,
        "capabilities": capabilities or [],
    }
