from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Mapping
from urllib.parse import urlencode, urlparse
import hashlib
import hmac
import httpx
import secrets
import time
import uuid

from shared.clients.http import get_http_client
from shared.config.settings import Settings, get_settings


class ShopifyOAuthError(RuntimeError):
    """Raised when Shopify OAuth configuration or token acquisition fails."""


class ShopifyGraphQLError(RuntimeError):
    """Raised when a Shopify GraphQL request returns errors or userErrors."""


RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_BACKOFF_SECONDS = 1.5


def normalize_shop_domain(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        raise ShopifyOAuthError("Missing Shopify store domain.")

    if "://" in raw:
        raw = urlparse(raw).netloc

    domain = raw.strip().strip("/").lower()
    if not domain:
        raise ShopifyOAuthError("Invalid Shopify store domain.")

    return domain


def build_shopify_hmac_message(params: Mapping[str, str]) -> str:
    filtered = {
        key: value
        for key, value in params.items()
        if key not in {"hmac", "signature"} and value is not None
    }
    return "&".join(f"{key}={filtered[key]}" for key in sorted(filtered))


def verify_shopify_oauth_hmac(params: Mapping[str, str], client_secret: str) -> bool:
    provided_hmac = params.get("hmac", "")
    if not provided_hmac:
        return False

    message = build_shopify_hmac_message(params)
    expected_hmac = hmac.new(
        client_secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(provided_hmac, expected_hmac)


@dataclass(slots=True)
class ShopifyAccessToken:
    access_token: str
    source: str
    scope: str = ""
    expires_at: datetime | None = None
    refresh_token: str | None = None

    def is_expired(self, skew_seconds: int = 60) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(UTC) >= self.expires_at - timedelta(seconds=skew_seconds)


class ShopifyAuthClient:
    def __init__(
        self,
        *,
        store_domain: str,
        auth_mode: str,
        client_id: str = "",
        client_secret: str = "",
        admin_access_token: str = "",
        legacy_token: str = "",
        api_version: str = "2026-01",
        http_client: httpx.Client | None = None,
    ) -> None:
        self.store_domain = normalize_shop_domain(store_domain)
        self.auth_mode = (auth_mode or "custom_admin_token").strip().lower()
        self.client_id = (client_id or "").strip()
        self.client_secret = (client_secret or "").strip()
        self.admin_access_token = (admin_access_token or "").strip()
        self.legacy_token = (legacy_token or "").strip()
        self.api_version = (api_version or "2026-01").strip()
        self.http_client = http_client or get_http_client()
        self._cached_token: ShopifyAccessToken | None = None

    @classmethod
    def from_settings(
        cls,
        settings: Settings | None = None,
        *,
        http_client: httpx.Client | None = None,
    ) -> "ShopifyAuthClient":
        active_settings = settings or get_settings()
        store_domain = (
            active_settings.shopify_store
            or active_settings.shopify_shop
            or active_settings.shopify_shop_domain
        )
        return cls(
            store_domain=store_domain,
            auth_mode=active_settings.shopify_auth_mode,
            client_id=active_settings.shopify_client_id,
            client_secret=active_settings.shopify_client_secret,
            admin_access_token=active_settings.shopify_admin_access_token,
            legacy_token=active_settings.shopify_token,
            api_version=active_settings.shopify_api_version,
            http_client=http_client,
        )

    def describe_admin_session(self) -> dict[str, Any]:
        if self.admin_access_token:
            source = "admin_access_token"
            ready = True
        elif self.legacy_token:
            source = "legacy_token"
            ready = True
        elif self.auth_mode == "client_credentials" and self.client_id and self.client_secret:
            source = "oauth_client_credentials"
            ready = True
        elif self.auth_mode == "authorization_code" and self.client_id and self.client_secret:
            source = "oauth_authorization_code"
            ready = False
        else:
            source = "unconfigured"
            ready = False

        return {
            "store_domain": self.store_domain,
            "auth_mode": self.auth_mode,
            "auth_source": source,
            "auth_ready": ready,
            "graphql_endpoint": self.build_graphql_endpoint(),
        }

    def debug_admin_session(self) -> dict[str, Any]:
        session = self.describe_admin_session()
        try:
            token = self.get_admin_access_token()
            return {
                **session,
                "token_ready": True,
                "token_source": token.source,
                "token_scope": token.scope,
                "token_expires_at": token.expires_at.isoformat() if token.expires_at else None,
            }
        except Exception as exc:
            return {
                **session,
                "token_ready": False,
                "error": str(exc),
            }

    def build_graphql_endpoint(self) -> str:
        return f"https://{self.store_domain}/admin/api/{self.api_version}/graphql.json"

    def build_authorize_url(
        self,
        *,
        scopes: list[str] | tuple[str, ...],
        redirect_uri: str,
        state: str | None = None,
        online_access: bool = False,
    ) -> tuple[str, str]:
        if not self.client_id or not self.client_secret:
            raise ShopifyOAuthError("SHOPIFY_CLIENT_ID and SHOPIFY_CLIENT_SECRET are required.")

        oauth_state = state or secrets.token_urlsafe(24)
        params: dict[str, str] = {
            "client_id": self.client_id,
            "scope": ",".join(scopes),
            "redirect_uri": redirect_uri,
            "state": oauth_state,
        }
        if online_access:
            params["grant_options[]"] = "per-user"

        query = urlencode(params)
        return f"https://{self.store_domain}/admin/oauth/authorize?{query}", oauth_state

    def exchange_authorization_code(
        self,
        *,
        code: str,
        redirect_uri: str,
        expiring: bool = False,
    ) -> ShopifyAccessToken:
        if not self.client_id or not self.client_secret:
            raise ShopifyOAuthError("SHOPIFY_CLIENT_ID and SHOPIFY_CLIENT_SECRET are required.")

        response = self.http_client.post(
            self._build_access_token_endpoint(),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
                "expiring": "1" if expiring else "0",
            },
        )
        return self._parse_access_token_response(response, source="oauth_authorization_code")

    def get_admin_access_token(self, *, force_refresh: bool = False) -> ShopifyAccessToken:
        if self.admin_access_token:
            return ShopifyAccessToken(
                access_token=self.admin_access_token,
                scope="",
                source="admin_access_token",
            )

        if self.legacy_token:
            return ShopifyAccessToken(
                access_token=self.legacy_token,
                scope="",
                source="legacy_token",
            )

        if self.auth_mode == "client_credentials":
            if not force_refresh and self._cached_token and not self._cached_token.is_expired():
                return self._cached_token

            self._cached_token = self._request_client_credentials_token()
            return self._cached_token

        if self.auth_mode == "authorization_code":
            raise ShopifyOAuthError(
                "Authorization code flow requires an installation callback exchange or a stored "
                "SHOPIFY_ADMIN_ACCESS_TOKEN."
            )

        raise ShopifyOAuthError(
            "Shopify Admin authentication is not configured. Provide SHOPIFY_CLIENT_ID and "
            "SHOPIFY_CLIENT_SECRET for SHOPIFY_AUTH_MODE=client_credentials, or provide "
            "SHOPIFY_ADMIN_ACCESS_TOKEN for legacy fixed-token mode."
        )

    def build_admin_headers(self) -> dict[str, str]:
        token = self.get_admin_access_token()
        return {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": token.access_token,
        }

    def graphql(self, query: str, variables: Mapping[str, Any] | None = None) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(1, DEFAULT_RETRY_ATTEMPTS + 1):
            try:
                response = self.http_client.post(
                    self.build_graphql_endpoint(),
                    headers=self.build_admin_headers(),
                    json={"query": query, "variables": dict(variables or {})},
                )
                response.raise_for_status()
                payload = response.json()
                if payload.get("errors"):
                    raise ShopifyGraphQLError(str(payload["errors"]))
                return payload.get("data", {})
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if exc.response.status_code not in RETRYABLE_STATUS_CODES or attempt == DEFAULT_RETRY_ATTEMPTS:
                    detail = exc.response.text.strip()
                    raise ShopifyGraphQLError(
                        f"Shopify GraphQL request failed with {exc.response.status_code}: {detail}"
                    ) from exc
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt == DEFAULT_RETRY_ATTEMPTS:
                    raise ShopifyGraphQLError(
                        f"Shopify GraphQL transport failed after {attempt} attempts: {exc}"
                    ) from exc
            time.sleep(DEFAULT_RETRY_BACKOFF_SECONDS * attempt)

        raise ShopifyGraphQLError(f"Shopify GraphQL request failed: {last_error}")

    def query_shop_info(self) -> dict[str, Any]:
        data = self.graphql(
            """
            query ShopInfo {
              shop {
                id
                name
                myshopifyDomain
                currencyCode
              }
            }
            """
        )
        return data.get("shop") or {}

    def find_variant_by_sku(self, sku: str) -> dict[str, Any] | None:
        clean_sku = sku.strip()
        if not clean_sku:
            return None

        data = self.graphql(
            """
            query VariantBySku($query: String!) {
              productVariants(first: 1, query: $query) {
                edges {
                  node {
                    id
                    sku
                    price
                    inventoryQuantity
                    inventoryItem {
                      id
                    }
                    product {
                      id
                      status
                      title
                    }
                  }
                }
              }
            }
            """,
            {"query": f"sku:{clean_sku}"},
        )
        edges = data.get("productVariants", {}).get("edges", [])
        if not edges:
            return None
        return edges[0].get("node")

    def list_product_variants(
        self,
        *,
        query: str = "",
        page_size: int = 100,
        progress_callback: Any | None = None,
    ) -> list[dict[str, Any]]:
        cursor: str | None = None
        variants: list[dict[str, Any]] = []
        page = 0

        while True:
            page += 1
            data = self.graphql(
                """
                query ProductVariantsPage($first: Int!, $after: String, $query: String!) {
                  productVariants(first: $first, after: $after, query: $query) {
                    edges {
                      cursor
                      node {
                        id
                        sku
                        price
                        inventoryQuantity
                        product {
                          id
                          status
                          title
                        }
                      }
                    }
                    pageInfo {
                      hasNextPage
                      endCursor
                    }
                  }
                }
                """,
                {
                    "first": page_size,
                    "after": cursor,
                    "query": query,
                },
            )
            connection = data.get("productVariants", {}) or {}
            edges = connection.get("edges", []) or []
            for edge in edges:
                node = edge.get("node")
                if node:
                    variants.append(node)
            if progress_callback is not None:
                progress_callback(
                    {
                        "page": page,
                        "page_size": page_size,
                        "fetched_in_page": len(edges),
                        "fetched_total": len(variants),
                        "query": query,
                    }
                )
            page_info = connection.get("pageInfo", {}) or {}
            if not page_info.get("hasNextPage"):
                break
            cursor = page_info.get("endCursor")
            if not cursor:
                break

        return variants

    def get_primary_location(self) -> dict[str, Any] | None:
        data = self.graphql(
            """
            query PrimaryLocation {
              locations(first: 1) {
                edges {
                  node {
                    id
                    name
                    isActive
                  }
                }
              }
            }
            """
        )
        edges = data.get("locations", {}).get("edges", [])
        if not edges:
            return None
        return edges[0].get("node")

    def create_draft_product(self, product_input: Mapping[str, Any]) -> dict[str, Any]:
        data = self.graphql(
            """
            mutation CreateDraftProduct($input: ProductCreateInput!) {
              productCreate(product: $input) {
                product {
                  id
                  title
                  status
                  variants(first: 1) {
                    edges {
                      node {
                        id
                        sku
                        inventoryItem {
                          id
                        }
                      }
                    }
                  }
                }
                userErrors {
                  field
                  message
                }
              }
            }
            """,
            {"input": dict(product_input)},
        )
        result = data.get("productCreate") or {}
        user_errors = result.get("userErrors") or []
        if user_errors:
            raise ShopifyGraphQLError(str(user_errors))
        return result.get("product") or {}

    def update_variant_fields(
        self,
        *,
        product_id: str,
        variant_id: str,
        price: float | None = None,
        sku: str | None = None,
    ) -> dict[str, Any]:
        variant_payload: dict[str, Any] = {"id": variant_id}
        if price is not None:
            variant_payload["price"] = round(price, 2)
        if sku is not None:
            variant_payload["sku"] = sku

        data = self.graphql(
            """
            mutation UpdateVariantFields($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
              productVariantsBulkUpdate(productId: $productId, variants: $variants) {
                productVariants {
                  id
                  sku
                  price
                  compareAtPrice
                }
                userErrors {
                  field
                  message
                }
              }
            }
            """,
            {
                "productId": product_id,
                "variants": [variant_payload],
            },
        )
        result = data.get("productVariantsBulkUpdate") or {}
        user_errors = result.get("userErrors") or []
        if user_errors:
            raise ShopifyGraphQLError(str(user_errors))
        variants = result.get("productVariants") or []
        return variants[0] if variants else {}

    def update_variant_price(self, *, product_id: str, variant_id: str, price: float) -> dict[str, Any]:
        return self.update_variant_fields(product_id=product_id, variant_id=variant_id, price=price)

    def update_product_status(self, *, product_id: str, status: str) -> dict[str, Any]:
        data = self.graphql(
            """
            mutation UpdateProductStatus($product: ProductUpdateInput!) {
              productUpdate(product: $product) {
                product {
                  id
                  title
                  status
                }
                userErrors {
                  field
                  message
                }
              }
            }
            """,
            {
                "product": {
                    "id": product_id,
                    "status": status,
                }
            },
        )
        result = data.get("productUpdate") or {}
        user_errors = result.get("userErrors") or []
        if user_errors:
            raise ShopifyGraphQLError(str(user_errors))
        return result.get("product") or {}

    def set_inventory_quantity(
        self,
        *,
        inventory_item_id: str,
        location_id: str,
        quantity: int,
        change_from_quantity: int | None = 0,
        reference_document_uri: str | None = None,
    ) -> dict[str, Any]:
        quantity_payload: dict[str, Any] = {
            "inventoryItemId": inventory_item_id,
            "locationId": location_id,
            "quantity": int(quantity),
        }
        if change_from_quantity is not None:
            quantity_payload["changeFromQuantity"] = int(change_from_quantity)
        data = self.graphql(
            """
            mutation SetInventory($input: InventorySetQuantitiesInput!, $idempotencyKey: String!) {
              inventorySetQuantities(input: $input) @idempotent(key: $idempotencyKey) {
                inventoryAdjustmentGroup {
                  reason
                  changes {
                    name
                    delta
                    quantityAfterChange
                  }
                }
                userErrors {
                  code
                  field
                  message
                }
              }
            }
            """,
            {
                "input": {
                    "name": "available",
                    "reason": "correction",
                    "ignoreCompareQuantity": change_from_quantity is None,
                    "referenceDocumentUri": reference_document_uri
                    or f"hermes://inventory-sync/{inventory_item_id}",
                    "quantities": [quantity_payload],
                },
                "idempotencyKey": str(uuid.uuid4()),
            },
        )
        result = data.get("inventorySetQuantities") or {}
        user_errors = result.get("userErrors") or []
        if user_errors:
            raise ShopifyGraphQLError(str(user_errors))
        return result.get("inventoryAdjustmentGroup") or {}

    def _request_client_credentials_token(self) -> ShopifyAccessToken:
        if not self.client_id or not self.client_secret:
            raise ShopifyOAuthError("SHOPIFY_CLIENT_ID and SHOPIFY_CLIENT_SECRET are required.")
        last_error: Exception | None = None
        for attempt in range(1, DEFAULT_RETRY_ATTEMPTS + 1):
            try:
                response = self.http_client.post(
                    self._build_access_token_endpoint(),
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "grant_type": "client_credentials",
                    },
                )
                return self._parse_access_token_response(response, source="oauth_client_credentials")
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if exc.response.status_code not in RETRYABLE_STATUS_CODES or attempt == DEFAULT_RETRY_ATTEMPTS:
                    detail = exc.response.text.strip()
                    raise ShopifyOAuthError(
                        f"Shopify OAuth token request failed with {exc.response.status_code}: {detail}"
                    ) from exc
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt == DEFAULT_RETRY_ATTEMPTS:
                    raise ShopifyOAuthError(
                        f"Shopify OAuth token request transport failed after {attempt} attempts: {exc}"
                    ) from exc
            time.sleep(DEFAULT_RETRY_BACKOFF_SECONDS * attempt)
        raise ShopifyOAuthError(f"Shopify OAuth token request failed: {last_error}")

    def _build_access_token_endpoint(self) -> str:
        return f"https://{self.store_domain}/admin/oauth/access_token"

    def _parse_access_token_response(self, response: httpx.Response, *, source: str) -> ShopifyAccessToken:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text.strip()
            raise ShopifyOAuthError(
                f"Shopify OAuth token request failed with {exc.response.status_code}: {detail}"
            ) from exc

        payload = response.json()
        access_token = str(payload.get("access_token", "")).strip()
        if not access_token:
            raise ShopifyOAuthError("Shopify OAuth response did not include access_token.")

        expires_in = payload.get("expires_in")
        expires_at = None
        if expires_in not in (None, ""):
            expires_at = datetime.now(UTC) + timedelta(seconds=int(expires_in))

        return ShopifyAccessToken(
            access_token=access_token,
            scope=str(payload.get("scope", "")),
            expires_at=expires_at,
            refresh_token=payload.get("refresh_token"),
            source=source,
        )
