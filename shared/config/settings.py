from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE_CANDIDATES = (
    ".env",
    REPO_ROOT / ".env",
    REPO_ROOT.parent / f"{REPO_ROOT.name}.env",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_CANDIDATES,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="ai-hermes-agent")
    hermes_env: str = Field(default="development", alias="HERMES_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    prometheus_enabled: bool = Field(default=True, alias="PROMETHEUS_ENABLED")

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    deepseek_api_key: str = Field(default="", alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(default="https://api.deepseek.com", alias="DEEPSEEK_BASE_URL")
    deepseek_model: str = Field(default="deepseek-chat", alias="DEEPSEEK_MODEL")
    default_llm_provider: str = Field(default="openai", alias="DEFAULT_LLM_PROVIDER")
    default_llm_model: str = Field(default="gpt-4.1-mini", alias="DEFAULT_LLM_MODEL")
    openhands_base_url: str = Field(default="http://127.0.0.1:3002", alias="OPENHANDS_BASE_URL")
    firecrawl_base_url: str = Field(default="http://127.0.0.1:3003", alias="FIRECRAWL_BASE_URL")
    firecrawl_api_key: str = Field(default="", alias="FIRECRAWL_LOCAL_API_KEY")
    firecrawl_timeout_seconds: float = Field(default=60.0, alias="FIRECRAWL_TIMEOUT_SECONDS")
    agent_reach_root: str = Field(
        default=str(REPO_ROOT / "external" / "Agent-Reach"),
        alias="AGENT_REACH_ROOT",
    )
    agent_reach_python: str = Field(
        default=str(REPO_ROOT / "external" / "Agent-Reach" / ".venv-agent-reach" / "Scripts" / "python.exe"),
        alias="AGENT_REACH_PYTHON",
    )
    agent_reach_cli: str = Field(
        default=str(REPO_ROOT / "external" / "Agent-Reach" / ".venv-agent-reach" / "Scripts" / "agent-reach.exe"),
        alias="AGENT_REACH_CLI",
    )
    opencli_root: str = Field(default=str(REPO_ROOT / "external" / "OpenCLI"), alias="OPENCLI_ROOT")
    opencli_cli: str = Field(
        default=str(REPO_ROOT / "scripts" / "opencli.ps1"),
        alias="OPENCLI_CLI",
    )
    browser_harness_root: str = Field(
        default=str(REPO_ROOT / "external" / "browser-harness"),
        alias="BROWSER_HARNESS_ROOT",
    )
    browser_harness_cli: str = Field(
        default=str(REPO_ROOT / "scripts" / "browser-harness.ps1"),
        alias="BROWSER_HARNESS_CLI",
    )
    browser_harness_exe: str = Field(
        default=str(Path.home() / ".local" / "bin" / "browser-harness.exe"),
        alias="BROWSER_HARNESS_EXE",
    )
    yt_dlp_root: str = Field(default=str(REPO_ROOT / "external" / "yt-dlp"), alias="YT_DLP_ROOT")
    yt_dlp_downloads_dir: str = Field(
        default=str(REPO_ROOT / "external" / "yt-dlp" / "downloads"),
        alias="YT_DLP_DOWNLOADS_DIR",
    )
    yt_dlp_python: str = Field(default="python", alias="YT_DLP_PYTHON")

    postgres_url: str = Field(
        default="postgresql+psycopg://hermes:hermes@postgres:5432/hermes",
        alias="POSTGRES_URL",
    )
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    qdrant_url: str = Field(default="http://qdrant:6333", alias="QDRANT_URL")

    # Shopify Admin API runtime config
    shopify_token: str = Field(default="", alias="SHOPIFY_TOKEN")
    shopify_admin_access_token: str = Field(default="", alias="SHOPIFY_ADMIN_ACCESS_TOKEN")
    shopify_store: str = Field(default="", alias="SHOPIFY_STORE")
    shopify_shop: str = Field(default="", alias="SHOPIFY_SHOP")
    shopify_shop_domain: str = Field(default="", alias="SHOPIFY_SHOP_DOMAIN")
    shopify_client_id: str = Field(default="", alias="SHOPIFY_CLIENT_ID")
    shopify_client_secret: str = Field(default="", alias="SHOPIFY_CLIENT_SECRET")
    shopify_auth_mode: str = Field(default="client_credentials", alias="SHOPIFY_AUTH_MODE")
    shopify_api_version: str = Field(default="2026-01", alias="SHOPIFY_API_VERSION")
    shopify_pilot_create_approved: bool = Field(default=False, alias="SHOPIFY_PILOT_CREATE_APPROVED")
    shopify_inventory_location_id: str = Field(default="", alias="SHOPIFY_INVENTORY_LOCATION_ID")
    shopify_inventory_sync_query: str = Field(default="", alias="SHOPIFY_INVENTORY_SYNC_QUERY")
    inventory_sync_dry_run: bool = Field(default=True, alias="INVENTORY_SYNC_DRY_RUN")
    inventory_sync_max_items: int = Field(default=0, alias="INVENTORY_SYNC_MAX_ITEMS")
    inventory_sync_request_timeout_seconds: float = Field(default=30.0, alias="INVENTORY_SYNC_REQUEST_TIMEOUT_SECONDS")
    inventory_sync_retry_attempts: int = Field(default=3, alias="INVENTORY_SYNC_RETRY_ATTEMPTS")
    # Shopify CLI / CI-CD automation config
    shopify_app_automation_token: str = Field(default="", alias="SHOPIFY_APP_AUTOMATION_TOKEN")
    doba_api_base_url: str = Field(default="https://openapi.doba.com", alias="DOBA_API_BASE_URL")
    doba_retailer_id: str = Field(default="", alias="DOBA_RETAILER_ID")
    doba_app_key: str = Field(default="", alias="DOBA_APP_KEY")
    doba_sign_type: str = Field(default="RSA2", alias="DOBA_SIGN_TYPE")
    doba_public_key: str = Field(default="", alias="DOBA_PUBLIC_KEY")
    doba_private_key: str = Field(default="", alias="DOBA_PRIVATE_KEY")
    doba_api_key: str = Field(default="", alias="DOBA_API_KEY")
    doba_api_secret: str = Field(default="", alias="DOBA_API_SECRET")
    doba_client_id: str = Field(default="", alias="DOBA_CLIENT_ID")
    doba_app_secret: str = Field(default="", alias="DOBA_APP_SECRET")
    doba_access_token: str = Field(default="", alias="DOBA_ACCESS_TOKEN")
    doba_refresh_token: str = Field(default="", alias="DOBA_REFRESH_TOKEN")
    doba_auth_mode: str = Field(default="signature", alias="DOBA_AUTH_MODE")
    doba_api_version: str = Field(default="", alias="DOBA_API_VERSION")
    doba_price_endpoint: str = Field(default="/inventory-api/v1/product/price", alias="DOBA_PRICE_ENDPOINT")
    doba_price_sync_platform_name: str = Field(default="Shopify", alias="DOBA_PRICE_SYNC_PLATFORM_NAME")
    doba_price_sync_platform_id: str = Field(default="", alias="DOBA_PRICE_SYNC_PLATFORM_ID")
    doba_price_sync_ship_to_country: str = Field(default="US", alias="DOBA_PRICE_SYNC_SHIP_TO_COUNTRY")
    doba_price_sync_full_page_size: int = Field(default=20, alias="DOBA_PRICE_SYNC_FULL_PAGE_SIZE")
    doba_price_sync_full_max_pages: int = Field(default=0, alias="DOBA_PRICE_SYNC_FULL_MAX_PAGES")
    doba_allow_full_scan: bool = Field(default=False, alias="DOBA_ALLOW_FULL_SCAN")
    doba_default_market: str = Field(default="US", alias="DOBA_DEFAULT_MARKET")
    doba_allowed_ship_from_countries: str = Field(
        default="US,CN,CA",
        alias="DOBA_ALLOWED_SHIP_FROM_COUNTRIES",
    )
    doba_min_inventory: int = Field(default=5, alias="DOBA_MIN_INVENTORY")
    doba_min_margin_dollars: float = Field(default=15, alias="DOBA_MIN_MARGIN_DOLLARS")
    doba_min_margin_rate: float = Field(default=0.25, alias="DOBA_MIN_MARGIN_RATE")
    doba_max_shipping_ratio: float = Field(default=0.35, alias="DOBA_MAX_SHIPPING_RATIO")
    doba_max_delivery_days: int = Field(default=10, alias="DOBA_MAX_DELIVERY_DAYS")
    doba_restricted_categories: str = Field(
        default="weapons,adult,tobacco,supplements,medical,hazardous",
        alias="DOBA_RESTRICTED_CATEGORIES",
    )
    doba_manual_review_categories: str = Field(
        default="battery,cosmetics,children",
        alias="DOBA_MANUAL_REVIEW_CATEGORIES",
    )
    doba_ad_buffer: float = Field(default=6, alias="DOBA_AD_BUFFER")
    doba_shopify_fee_buffer: float = Field(default=4, alias="DOBA_SHOPIFY_FEE_BUFFER")
    doba_publish_duplicates: bool = Field(default=False, alias="DOBA_PUBLISH_DUPLICATES")
    giga_api_base_url: str = Field(default="", alias="GIGA_API_BASE_URL")
    giga_api_key: str = Field(default="", alias="GIGA_API_KEY")
    giga_api_secret: str = Field(default="", alias="GIGA_API_SECRET")
    giga_sandbox_client_id: str = Field(default="", alias="GIGA_SANDBOX_CLIENT_ID")
    giga_sandbox_app_secret: str = Field(default="", alias="GIGA_SANDBOX_APP_SECRET")
    giga_sandbox_client_secret: str = Field(default="", alias="GIGA_SANDBOX_CLIENT_SECRET")
    giga_production_client_id: str = Field(default="", alias="GIGA_PRODUCTION_CLIENT_ID")
    giga_production_app_secret: str = Field(default="", alias="GIGA_PRODUCTION_APP_SECRET")
    giga_sandbox_base_url: str = Field(default="https://openapi-sandbox.gigab2b.com", alias="GIGA_SANDBOX_BASE_URL")
    giga_production_base_url: str = Field(default="https://openapi.gigab2b.com", alias="GIGA_PRODUCTION_BASE_URL")
    giga_timeout_seconds: float = Field(default=30.0, alias="GIGA_TIMEOUT_SECONDS")
    giga_sign_type: str = Field(default="HMAC-SHA256", alias="GIGA_SIGN_TYPE")
    giga_page_size: int = Field(default=100, alias="GIGA_PAGE_SIZE")
    giga_inventory_endpoint: str = Field(
        default="/b2b-overseas-api/v1/buyer/inventory/quantity/v2",
        alias="GIGA_INVENTORY_ENDPOINT",
    )
    giga_validation_endpoint: str = Field(default="", alias="GIGA_VALIDATION_ENDPOINT")
    giga_price_endpoint: str = Field(
        default="/b2b-overseas-api/v1/buyer/product/price/v1",
        alias="GIGA_PRICE_ENDPOINT",
    )
    giga_product_list_endpoint: str = Field(
        default="/b2b-overseas-api/v1/buyer/product/skus/v1",
        alias="GIGA_PRODUCT_LIST_ENDPOINT",
    )
    giga_buyer_session_cookie: str = Field(default="", alias="GIGA_BUYER_SESSION_COOKIE")
    giga_buyer_csrf_token: str = Field(default="", alias="GIGA_BUYER_CSRF_TOKEN")
    giga_buyer_user_agent: str = Field(default="", alias="GIGA_BUYER_USER_AGENT")
    giga_buyer_site_base_url: str = Field(default="", alias="GIGA_BUYER_SITE_BASE_URL")
    giga_frontend_product_list_route: str = Field(default="", alias="GIGA_FRONTEND_PRODUCT_LIST_ROUTE")
    giga_frontend_chrome_debug_port: int = Field(default=9222, alias="GIGA_FRONTEND_CHROME_DEBUG_PORT")
    giga_frontend_use_existing_chrome: bool = Field(default=True, alias="GIGA_FRONTEND_USE_EXISTING_CHROME")
    price_sync_product_markup_rate: float = Field(default=0.15, alias="PRICE_SYNC_PRODUCT_MARKUP_RATE")
    price_sync_min_margin_rate: float = Field(default=0.2, alias="PRICE_SYNC_MIN_MARGIN_RATE")
    price_sync_min_margin_amount: float = Field(default=5.0, alias="PRICE_SYNC_MIN_MARGIN_AMOUNT")
    price_sync_max_up_delta_rate: float = Field(default=0.2, alias="PRICE_SYNC_MAX_UP_DELTA_RATE")
    price_sync_max_down_delta_rate: float = Field(default=0.2, alias="PRICE_SYNC_MAX_DOWN_DELTA_RATE")
    price_sync_rounding_mode: str = Field(default="ending_99", alias="PRICE_SYNC_ROUNDING_MODE")
    price_sync_max_increase_percent_without_review: float = Field(
        default=30.0,
        alias="PRICE_SYNC_MAX_INCREASE_PERCENT_WITHOUT_REVIEW",
    )
    price_sync_max_decrease_percent_without_review: float = Field(
        default=30.0,
        alias="PRICE_SYNC_MAX_DECREASE_PERCENT_WITHOUT_REVIEW",
    )
    price_sync_min_delta_amount: float = Field(default=0.01, alias="PRICE_SYNC_MIN_DELTA_AMOUNT")
    price_sync_dry_run: bool = Field(default=True, alias="PRICE_SYNC_DRY_RUN")
    price_sync_log_level: str = Field(default="INFO", alias="PRICE_SYNC_LOG_LEVEL")
    price_sync_print_detail: bool = Field(default=True, alias="PRICE_SYNC_PRINT_DETAIL")
    price_sync_print_table: bool = Field(default=True, alias="PRICE_SYNC_PRINT_TABLE")
    tiktok_token: str = Field(default="", alias="TIKTOK_TOKEN")
    youtube_api_key: str = Field(default="", alias="YOUTUBE_API_KEY")
    reddit_client_id: str = Field(default="", alias="REDDIT_CLIENT_ID")
    reddit_secret: str = Field(default="", alias="REDDIT_SECRET")
    amazon_affiliate_tag: str = Field(default="", alias="AMAZON_AFFILIATE_TAG")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
