from __future__ import annotations

import os
from typing import Any

import bootstrap
from shared.clients.shopify import ShopifyAuthClient, ShopifyOAuthError
from shared.config import get_settings
from shared.llm import get_llm
from shared.schemas import ExecuteRequest

bootstrap.load_shared_environment()

STORE_TARGETS = [
    "Shopify Catalog",
    "ChatGPT",
    "Google AI Mode/Gemini",
    "Microsoft Copilot",
    "Shop AI Search",
]


def execute_task(request: ExecuteRequest) -> dict[str, Any]:
    payload = request.payload or {}
    product = _normalize_product(payload)
    audit = _build_geo_audit(product)
    storefront = _build_storefront_readiness(product)
    environment = _build_environment_summary()

    response: dict[str, Any] = {
        "summary": _build_summary(product, audit, storefront),
        "data": {
            "product": product,
            "geo_audit": audit,
            "agentic_storefront_readiness": storefront,
            "environment": environment,
        },
    }

    if payload.get("use_llm", True):
        response["data"]["llm_rewrite"] = _build_llm_rewrite(product, audit, storefront)

    return response


def _normalize_product(payload: dict[str, Any]) -> dict[str, Any]:
    product = dict(payload.get("product") or {})
    if not product:
        product = {
            "title": payload.get("title", ""),
            "description": payload.get("description", ""),
            "benefits": payload.get("benefits", []),
            "specifications": payload.get("specifications", {}),
            "faq": payload.get("faq", []),
            "brand": payload.get("brand", ""),
            "category": payload.get("category", ""),
            "materials": payload.get("materials", []),
            "use_cases": payload.get("use_cases", []),
            "audience": payload.get("audience", ""),
        }

    product.setdefault("title", "")
    product.setdefault("description", "")
    product.setdefault("benefits", [])
    product.setdefault("specifications", {})
    product.setdefault("faq", [])
    product.setdefault("brand", "")
    product.setdefault("category", "")
    product.setdefault("materials", [])
    product.setdefault("use_cases", [])
    product.setdefault("audience", "")
    return product


def _build_geo_audit(product: dict[str, Any]) -> dict[str, Any]:
    title = str(product.get("title", "")).strip()
    description = str(product.get("description", "")).strip()
    benefits = _as_list(product.get("benefits"))
    specifications = _as_dict(product.get("specifications"))
    faq = _as_list(product.get("faq"))
    materials = _as_list(product.get("materials"))
    use_cases = _as_list(product.get("use_cases"))

    score = 0
    recommendations: list[str] = []
    strengths: list[str] = []

    if len(title) >= 45:
        score += 20
        strengths.append("Title is long enough to expose product type and buying intent.")
    else:
        recommendations.append("Expand the title with product type, audience, and core differentiator.")

    if len(description) >= 280:
        score += 20
        strengths.append("Description has enough room for AI summary and citation extraction.")
    else:
        recommendations.append("Add a richer description with problem, solution, and key proof points.")

    if len(benefits) >= 3:
        score += 15
        strengths.append("Benefits list gives models scannable claims to summarize.")
    else:
        recommendations.append("Add at least 3 concrete benefits in short, factual bullets.")

    if len(specifications) >= 4:
        score += 15
        strengths.append("Specifications provide structured facts for retrieval and comparison.")
    else:
        recommendations.append("Add 4 or more normalized specs such as size, material, compatibility, and care.")

    if len(faq) >= 3:
        score += 15
        strengths.append("FAQ coverage improves answerability for conversational search.")
    else:
        recommendations.append("Add 3 to 5 FAQ items answering fit, usage, shipping, and maintenance questions.")

    if materials or use_cases:
        score += 15
        strengths.append("Materials or use cases improve semantic relevance across AI storefronts.")
    else:
        recommendations.append("Include materials and use cases to strengthen recommendation context.")

    missing_entities = [
        label
        for label, value in {
            "brand": product.get("brand"),
            "category": product.get("category"),
            "audience": product.get("audience"),
        }.items()
        if not str(value or "").strip()
    ]
    if missing_entities:
        recommendations.append(
            "Fill entity fields for "
            + ", ".join(missing_entities)
            + " so models can classify the item consistently."
        )

    return {
        "score": min(score, 100),
        "strengths": strengths,
        "recommendations": recommendations,
        "citation_ready_facts": _build_citation_ready_facts(product),
        "suggested_sections": [
            "AI-readable summary",
            "What problem it solves",
            "Top benefits",
            "Specifications",
            "Compatibility and use cases",
            "FAQ",
            "Shipping, returns, and trust signals",
        ],
    }


def _build_storefront_readiness(product: dict[str, Any]) -> dict[str, Any]:
    title = str(product.get("title", "")).strip()
    description = str(product.get("description", "")).strip()
    specifications = _as_dict(product.get("specifications"))
    faq = _as_list(product.get("faq"))

    base_pass = {
        "has_title": bool(title),
        "has_description": bool(description),
        "has_specs": bool(specifications),
        "has_faq": bool(faq),
        "has_brand": bool(str(product.get("brand", "")).strip()),
        "has_category": bool(str(product.get("category", "")).strip()),
    }
    passed = sum(1 for value in base_pass.values() if value)
    status = "ready" if passed >= 5 else "partial" if passed >= 3 else "not_ready"

    common_actions = [
        "Use concise, factual claims instead of vague marketing language.",
        "Keep specs normalized so comparison agents can parse them reliably.",
        "Add FAQ and compatibility data for conversational answer engines.",
    ]

    targets = {
        "shopify_catalog": {
            "status": status,
            "focus": "Structured product facts, brand/category clarity, and consistent attributes.",
        },
        "chatgpt": {
            "status": status,
            "focus": "Summary-friendly description, explicit use cases, and quotable facts.",
        },
        "google_ai_mode_gemini": {
            "status": status,
            "focus": "Entity clarity, answerable headings, and detailed supporting context.",
        },
        "microsoft_copilot": {
            "status": status,
            "focus": "Comparison-ready bullets, specs, and confidence-building details.",
        },
        "shop_ai_search": {
            "status": status,
            "focus": "Catalog cleanliness, commercial intent, and shopping-specific attributes.",
        },
    }

    return {
        "overall_status": status,
        "passed_checks": base_pass,
        "targets": targets,
        "priority_actions": common_actions,
    }


def _build_environment_summary() -> dict[str, Any]:
    settings = get_settings()
    provider = os.getenv("SHOPIFY_GEO_LLM_PROVIDER", "deepseek")
    model = os.getenv("SHOPIFY_GEO_LLM_MODEL", "") or (
        settings.deepseek_model if provider == "deepseek" else settings.default_llm_model
    )
    shopify_session = _build_shopify_session_summary()

    return {
        "repo_root": os.getenv("REPO_ROOT", ""),
        "agent_root": os.getenv("AGENT_ROOT", ""),
        "root_env_loaded": bool(settings.hermes_env),
        "llm_provider": provider,
        "llm_model": model,
        "deepseek_configured": bool(settings.deepseek_api_key),
        "openai_configured": bool(settings.openai_api_key),
        "anthropic_configured": bool(settings.anthropic_api_key),
        "google_configured": bool(settings.google_api_key),
        "shopify_admin_session": shopify_session,
        "target_channels": STORE_TARGETS,
    }


def _build_shopify_session_summary() -> dict[str, Any]:
    try:
        client = ShopifyAuthClient.from_settings()
        return client.describe_admin_session()
    except ShopifyOAuthError as exc:
        return {
            "auth_ready": False,
            "error": str(exc),
        }


def _build_llm_rewrite(
    product: dict[str, Any],
    audit: dict[str, Any],
    storefront: dict[str, Any],
) -> dict[str, Any]:
    provider = os.getenv("SHOPIFY_GEO_LLM_PROVIDER", "deepseek")
    settings = get_settings()
    model = os.getenv("SHOPIFY_GEO_LLM_MODEL", "") or (
        settings.deepseek_model if provider == "deepseek" else settings.default_llm_model
    )

    configured = {
        "deepseek": bool(settings.deepseek_api_key),
        "openai": bool(settings.openai_api_key),
        "anthropic": bool(settings.anthropic_api_key),
        "claude": bool(settings.anthropic_api_key),
        "gemini": bool(settings.google_api_key),
        "google": bool(settings.google_api_key),
    }
    if not configured.get(provider, False):
        return {
            "enabled": False,
            "provider": provider,
            "model": model,
            "reason": f"Missing API key for provider '{provider}'.",
        }

    prompt = (
        "You are a Shopify Product GEO strategist. Improve the product page so it is easier for "
        "AI systems to understand, summarize, cite, compare, recommend, and surface in shopping "
        "assistants.\n\n"
        f"Product:\n{product}\n\n"
        f"Current GEO audit:\n{audit}\n\n"
        f"Storefront readiness:\n{storefront}\n\n"
        "Return:\n"
        "1. A 2-3 sentence AI-readable product summary.\n"
        "2. A rewritten title.\n"
        "3. 5 benefit bullets.\n"
        "4. 5 FAQ suggestions.\n"
        "5. A short section called 'Why AI shopping engines can trust this listing'."
    )

    try:
        llm = get_llm(provider=provider, model=model)
        result = llm.generate(prompt)
        return {
            "enabled": True,
            "provider": provider,
            "model": model,
            "output": result.get("text", ""),
        }
    except Exception as exc:  # pragma: no cover - network/provider errors
        return {
            "enabled": False,
            "provider": provider,
            "model": model,
            "reason": str(exc),
        }


def _build_citation_ready_facts(product: dict[str, Any]) -> list[str]:
    facts: list[str] = []
    title = str(product.get("title", "")).strip()
    brand = str(product.get("brand", "")).strip()
    category = str(product.get("category", "")).strip()
    audience = str(product.get("audience", "")).strip()

    if title:
        facts.append(f"Product title: {title}")
    if brand:
        facts.append(f"Brand: {brand}")
    if category:
        facts.append(f"Category: {category}")
    if audience:
        facts.append(f"Audience: {audience}")

    for key, value in list(_as_dict(product.get("specifications")).items())[:5]:
        facts.append(f"{key}: {value}")

    return facts


def _build_summary(product: dict[str, Any], audit: dict[str, Any], storefront: dict[str, Any]) -> str:
    title = str(product.get("title", "")).strip() or "Product"
    return (
        f"{title} GEO audit scored {audit['score']}/100 and storefront readiness is "
        f"{storefront['overall_status']}. Focus next on structured specs, FAQ coverage, "
        "and clearer AI-citable product facts."
    )


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}
