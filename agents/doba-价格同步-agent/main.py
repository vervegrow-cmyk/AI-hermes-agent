from bootstrap import ensure_repo_root_on_path

PROJECT_ROOT = ensure_repo_root_on_path()

import uvicorn

from api.app import app
from service.terminal_reporter import build_boot_lines, emit_lines
from shared.config import get_settings
from shared.config.settings import ENV_FILE_CANDIDATES


def print_boot_info() -> None:
    settings = get_settings()
    registered_routes = sorted(
        {
            route.path
            for route in app.routes
            if getattr(route, "path", "")
        }
    )
    env_loaded = any((candidate if isinstance(candidate, str) else candidate).exists() for candidate in ENV_FILE_CANDIDATES if not isinstance(candidate, str))
    emit_lines(
        build_boot_lines(
            agent_name="doba-price-sync-agent",
            current_dir=PROJECT_ROOT / "agents" / "doba-价格同步-agent",
            project_root=PROJECT_ROOT,
            env_loaded=env_loaded,
            doba_base_url=settings.doba_api_base_url,
            doba_token_loaded=bool(settings.doba_access_token),
            shopify_store=settings.shopify_shop or settings.shopify_store or settings.shopify_shop_domain,
            shopify_token_loaded=bool(
                settings.shopify_admin_access_token
                or settings.shopify_token
                or (settings.shopify_client_id and settings.shopify_client_secret)
            ),
            runtime_dir=PROJECT_ROOT / "agents" / "doba-价格同步-agent" / "runtime",
            registered_routes=registered_routes,
        )
    )


if __name__ == "__main__":
    print_boot_info()
    uvicorn.run(app, host="0.0.0.0", port=8086)
