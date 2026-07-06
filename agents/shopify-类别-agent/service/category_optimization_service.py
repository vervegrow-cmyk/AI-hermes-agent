from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any

from models.category_sync import CategorySyncRequest
from shared.clients import ShopifyAuthClient
from shared.clients.shopify import ShopifyGraphQLError
from shared.config import get_settings
from shared.llm import get_llm


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower()).strip("-")


def _truncate(value: str, limit: int = 600) -> str:
    text = _normalize_text(value)
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _safe_json_loads(value: str) -> Any:
    try:
        return json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None


def _risk_rank(level: str) -> int:
    return {"low": 0, "medium": 1, "high": 2}.get((level or "").strip().lower(), 1)


_CATEGORY_TERM_STOPWORDS = {
    "and",
    "for",
    "with",
    "the",
    "into",
    "from",
    "other",
    "misc",
    "general",
    "home",
    "garden",
    "furniture",
    "decor",
    "accessories",
    "accessory",
    "supplies",
    "supply",
    "equipment",
    "fixture",
    "fixtures",
    "product",
    "products",
    "indoor",
    "outdoor",
    "room",
    "other",
}


@dataclass
class CategoryOptimizationService:
    shopify_client: ShopifyAuthClient | Any | None = None
    llm_client: Any | None = None
    settings: Any | None = None

    def __post_init__(self) -> None:
        self.settings = self.settings or get_settings()
        self.shopify_client = self.shopify_client or ShopifyAuthClient.from_settings(self.settings)
        self.llm_client = self.llm_client or self._build_default_llm_client()
        self._definition_cache: dict[str, dict[str, str]] | None = None

    def _build_default_llm_client(self) -> Any | None:
        if not self.settings.deepseek_api_key:
            return None
        return get_llm(provider="deepseek")

    def run(
        self,
        request: CategorySyncRequest,
        *,
        task: str = "",
        progress_callback: Any | None = None,
    ) -> dict[str, Any]:
        self._emit(
            progress_callback,
            {
                "event": "stage",
                "stage": "start",
                "task": task,
                "mode": request.mode,
                "store": self.shopify_client.store_domain,
                "product_query": request.product_query,
                "max_items": request.max_items,
            },
        )
        products = self._fetch_products(request, progress_callback=progress_callback)
        self._emit(
            progress_callback,
            {
                "event": "stage",
                "stage": "products_loaded",
                "count": len(products),
            },
        )

        items = []
        for index, product in enumerate(products, start=1):
            item = self._process_product(product, request)
            items.append(item)
            self._emit(
                progress_callback,
                {
                    "event": "item",
                    "index": index,
                    "total": len(products),
                    "item": item,
                },
            )

        applied_count = sum(1 for item in items if item["apply_result"]["category_updated"] or item["apply_result"]["metafields_updated"])
        review_count = sum(1 for item in items if item["risk_level"] == "high" or item["needs_review"])
        summary = (
            f"本次以 {request.mode} 模式处理了 {len(items)} 个 Shopify 商品，"
            f"其中 {applied_count} 个已修改，{review_count} 个需要人工复核。"
        )
        self._emit(
            progress_callback,
            {
                "event": "stage",
                "stage": "finished",
                "processed_count": len(items),
                "applied_count": applied_count,
                "review_count": review_count,
                "mode": request.mode,
            },
        )
        return {
            "summary": summary,
            "data": {
                "task": task,
                "store": self.shopify_client.store_domain,
                "mode": request.mode,
                "product_query": request.product_query,
                "processed_count": len(items),
                "applied_count": applied_count,
                "review_count": review_count,
                "items": items,
            },
        }

    def run_single_product(
        self,
        request: CategorySyncRequest,
        *,
        product_id: str,
    ) -> dict[str, Any] | None:
        product = self._get_product_by_id(product_id)
        if not product:
            return None
        return self._process_product(product, request)

    def _fetch_products(
        self,
        request: CategorySyncRequest,
        *,
        progress_callback: Any | None = None,
    ) -> list[dict[str, Any]]:
        limit = request.max_items if request.max_items and request.max_items > 0 else None
        products: list[dict[str, Any]] = []
        excluded_ids = {item for item in request.exclude_product_ids if item}

        if request.product_ids:
            explicit_ids = request.product_ids[:limit] if limit else request.product_ids
            for product_id in explicit_ids:
                if product_id in excluded_ids:
                    continue
                product = self._get_product_by_id(product_id)
                if product:
                    products.append(product)
            return products

        cursor: str | None = None
        page = 0
        while True:
            page += 1
            data = self.shopify_client.graphql(
                """
                query ProductsPage($first: Int!, $after: String, $query: String!) {
                  products(first: $first, after: $after, query: $query) {
                    edges {
                      cursor
                      node {
                        id
                        title
                        vendor
                        productType
                        tags
                        description
                        featuredImage {
                          url
                          altText
                        }
                        category {
                          id
                          name
                          fullName
                          isLeaf
                          attributes(first: 20) {
                            nodes {
                              __typename
                              ... on TaxonomyChoiceListAttribute {
                                id
                                name
                                values(first: 20) {
                                  nodes {
                                    id
                                    name
                                  }
                                }
                              }
                              ... on TaxonomyMeasurementAttribute {
                                id
                                name
                              }
                              ... on TaxonomyAttribute {
                                id
                              }
                            }
                          }
                        }
                        metafields(first: 80) {
                          edges {
                            node {
                              namespace
                              key
                              type
                              value
                            }
                          }
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
                    "first": min(20, max(1, (limit - len(products)) if limit else 20)),
                    "after": cursor,
                    "query": request.product_query,
                },
            )
            connection = data.get("products", {}) or {}
            for edge in connection.get("edges", []) or []:
                node = edge.get("node")
                if node:
                    if node.get("id", "") in excluded_ids:
                        continue
                    products.append(node)
                    if limit and len(products) >= limit:
                        break
            self._emit(
                progress_callback,
                {
                    "event": "stage",
                    "stage": "scan_progress",
                    "page": page,
                    "loaded_count": len(products),
                    "page_count": len(connection.get("edges", []) or []),
                    "mode": "all_products" if not request.product_query else "query",
                    "product_query": request.product_query,
                },
            )
            page_info = connection.get("pageInfo", {}) or {}
            if (limit and len(products) >= limit) or not page_info.get("hasNextPage"):
                break
            cursor = page_info.get("endCursor")
            if not cursor:
                break

        return products

    def _get_product_by_id(self, product_id: str) -> dict[str, Any] | None:
        data = self.shopify_client.graphql(
            """
            query ProductById($id: ID!) {
              product(id: $id) {
                id
                title
                vendor
                productType
                tags
                description
                featuredImage {
                  url
                  altText
                }
                category {
                  id
                  name
                  fullName
                  isLeaf
                  attributes(first: 20) {
                    nodes {
                      __typename
                      ... on TaxonomyChoiceListAttribute {
                        id
                        name
                        values(first: 20) {
                          nodes {
                            id
                            name
                          }
                        }
                      }
                      ... on TaxonomyMeasurementAttribute {
                        id
                        name
                      }
                      ... on TaxonomyAttribute {
                        id
                      }
                    }
                  }
                }
                metafields(first: 80) {
                  edges {
                    node {
                      namespace
                      key
                      type
                      value
                    }
                  }
                }
              }
            }
            """,
            {"id": product_id},
        )
        return data.get("product")

    def _process_product(self, product: dict[str, Any], request: CategorySyncRequest) -> dict[str, Any]:
        current_category = product.get("category") or {}
        current_metafields = self._serialize_metafields(product)
        current_metafields_raw = self._shopify_namespace_metafields(product)
        decision = dict(self._build_decision(product, request))
        original_needs_review = bool(decision.get("needs_review"))
        review_bypassed = bool(request.mode == "apply" and request.force_apply_review_items and original_needs_review)
        if review_bypassed:
            decision["needs_review"] = False
        apply_result = self._apply_decision(product, decision, request) if request.mode == "apply" else self._build_dry_run_apply_result(decision)
        if review_bypassed:
            apply_result["review_bypassed"] = True
        return {
            "product_id": product.get("id", ""),
            "title": product.get("title", ""),
            "vendor": product.get("vendor", ""),
            "product_type": product.get("productType", ""),
            "current_category": {
                "id": current_category.get("id", ""),
                "name": current_category.get("name", ""),
                "full_name": current_category.get("fullName", ""),
            },
            "current_metafields": current_metafields,
            "rollback_snapshot": {
                "category": {
                    "id": current_category.get("id", ""),
                    "name": current_category.get("name", ""),
                    "full_name": current_category.get("fullName", ""),
                },
                "metafields": current_metafields_raw,
            },
            "suggested_category": decision["suggested_category"],
            "suggested_metafields": decision["suggested_metafields"],
            "source": decision["source"],
            "risk_level": decision["risk_level"],
            "needs_review": decision["needs_review"],
            "original_needs_review": original_needs_review,
            "review_bypassed": review_bypassed,
            "decision_reason": decision["decision_reason"],
            "candidate_categories": decision["candidate_categories"],
            "apply_result": apply_result,
        }

    def _build_decision(self, product: dict[str, Any], request: CategorySyncRequest) -> dict[str, Any]:
        shopify_suggestion = self._resolve_shopify_suggestion(product, request)
        if shopify_suggestion:
            validation = self._validate_shopify_suggestion(product, shopify_suggestion)
            if validation.get("accepted"):
                return self._build_shopify_suggestion_decision(product, shopify_suggestion, validation=validation)

            candidates = self._search_candidate_categories_from_terms(
                product,
                candidate_category=request.candidate_category,
                suggestion_texts=shopify_suggestion.get("raw_category_candidates", []),
            )
            decision = self._build_deepseek_decision(product, candidates)
            decision["decision_reason"] = (
                f"Shopify 建议未通过自动校验，已回退 DeepSeek 复判。原因：{validation.get('reason', 'suggestion_not_reliable')}；"
                f"{decision.get('decision_reason', '')}"
            )
            decision["risk_level"] = "high" if _risk_rank(str(decision.get("risk_level", "medium"))) < 2 else decision.get("risk_level", "high")
            decision["needs_review"] = bool(decision.get("needs_review", False)) or bool(validation.get("needs_review", True))
            return decision

        candidates = self._search_candidate_categories(product, request)
        return self._build_deepseek_decision(product, candidates)

    def _resolve_shopify_suggestion(self, product: dict[str, Any], request: CategorySyncRequest) -> dict[str, Any] | None:
        raw = request.shopify_suggestions.get(product.get("id", "")) or {}
        metafields = raw.get("metafields", []) if isinstance(raw.get("metafields", []), list) else []
        suggestion_texts = self._collect_shopify_suggestion_texts(raw)
        suggestion_node_ids = self._collect_shopify_suggestion_node_ids(raw)
        if not suggestion_texts and not suggestion_node_ids and not metafields:
            return None
        category = self._resolve_shopify_suggestion_category(product, suggestion_texts, suggestion_node_ids)
        if not category and metafields and (product.get("category") or {}).get("id"):
            category = product.get("category") or {}
        return {
            "category": category,
            "metafields": metafields,
            "raw_category_full_name": suggestion_texts[0] if suggestion_texts else "",
            "raw_category_candidates": suggestion_texts,
            "raw_category_node_ids": suggestion_node_ids,
        }

    def _build_shopify_suggestion_decision(
        self,
        product: dict[str, Any],
        suggestion: dict[str, Any],
        *,
        validation: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        metafields = self._normalize_metafield_suggestions(suggestion.get("metafields", []))
        category = suggestion.get("category") or {}
        current_full_name = ((product.get("category") or {}).get("fullName") or "").strip()
        suggested_full_name = (category.get("fullName") or suggestion.get("raw_category_full_name") or "").strip()
        category_changed = bool(current_full_name and suggested_full_name and current_full_name != suggested_full_name)
        needs_review = not category
        if not category:
            risk_level = "high"
            decision_reason = "Shopify 后台存在建议条，但当前未能稳定解析到 taxonomy category，已转人工复核。"
        elif not current_full_name:
            risk_level = "low"
            decision_reason = "Shopify 后台已提供类别建议，当前商品未设置类别，已直接采用该建议。"
        elif metafields and not suggestion.get("raw_category_candidates") and not suggestion.get("raw_category_node_ids"):
            risk_level = "low"
            decision_reason = "Shopify 后台已提供类别元字段建议，当前类别已明确，已沿用当前类别并优先采用 Shopify 建议值。"
        elif category_changed:
            risk_level = "medium"
            decision_reason = "Shopify 后台已提供类别建议，当前类别与建议不同，按 Shopify 建议优先采用。"
        else:
            risk_level = "low"
            decision_reason = "Shopify 后台已提供类别建议，且与当前类别一致，已直接采用。"
        if validation and validation.get("reason"):
            decision_reason = f"{decision_reason} 自动校验：{validation['reason']}"
        return {
            "source": "shopify_suggestion",
            "risk_level": risk_level,
            "needs_review": needs_review,
            "decision_reason": decision_reason,
            "candidate_categories": [self._serialize_candidate_category(category)] if category else [],
            "suggested_category": {
                "id": category.get("id", ""),
                "name": category.get("name", ""),
                "full_name": suggested_full_name,
            },
            "suggested_metafields": metafields,
        }

    def _validate_shopify_suggestion(self, product: dict[str, Any], suggestion: dict[str, Any]) -> dict[str, Any]:
        category = suggestion.get("category") or {}
        current_full_name = _normalize_text(((product.get("category") or {}).get("fullName") or ""))
        suggested_full_name = _normalize_text(category.get("fullName") or suggestion.get("raw_category_full_name") or "")
        raw_candidates = [item for item in (suggestion.get("raw_category_candidates") or []) if _normalize_text(str(item or ""))]

        if not category and not suggestion.get("metafields"):
            return {"accepted": False, "needs_review": True, "reason": "未能稳定解析到 Shopify taxonomy 类目。"}

        if suggested_full_name and current_full_name and suggested_full_name == current_full_name:
            return {"accepted": True, "needs_review": False, "reason": "Shopify 建议与当前类目一致。"}

        overlap_terms = self._match_product_terms_with_category(product, suggested_full_name)
        if overlap_terms:
            return {
                "accepted": True,
                "needs_review": False,
                "reason": f"商品语义与建议类目存在交集：{', '.join(overlap_terms[:4])}",
            }

        malformed = any(self._looks_like_malformed_shopify_suggestion_text(text) for text in raw_candidates[:6])
        if malformed:
            return {"accepted": False, "needs_review": True, "reason": "前端建议文本混入了无关内容，疑似抓取到脏建议。"}

        llm_validation = self._validate_shopify_suggestion_with_llm(product, suggested_full_name)
        if llm_validation:
            return llm_validation

        if suggestion.get("metafields") and current_full_name and not suggested_full_name:
            return {"accepted": True, "needs_review": False, "reason": "仅存在 Shopify 元字段建议，沿用当前类目。"}

        return {"accepted": False, "needs_review": True, "reason": "建议类目与商品标题/描述缺少有效语义交集。"}

    def _looks_like_malformed_shopify_suggestion_text(self, value: str) -> bool:
        text = _normalize_text(value)
        if not text:
            return False
        noise_markers = ["确定税率", "全部接受", "Google:", "false", "搜索类别"]
        if any(marker.lower() in text.lower() for marker in noise_markers):
            return True
        return len(text) > 140 or text.count(">") > 6

    def _match_product_terms_with_category(self, product: dict[str, Any], suggested_full_name: str) -> list[str]:
        product_tokens = self._keyword_tokens(
            " ".join(
                [
                    str(product.get("title", "")),
                    str(product.get("vendor", "")),
                    str(product.get("productType", "")),
                    " ".join(product.get("tags", [])[:12]) if isinstance(product.get("tags", []), list) else "",
                    _truncate(str(product.get("description", "")), 400),
                ]
            )
        )
        category_tokens = self._keyword_tokens(suggested_full_name)
        return sorted(product_tokens.intersection(category_tokens))[:8]

    def _keyword_tokens(self, value: str) -> set[str]:
        return {
            token.lower()
            for token in re.findall(r"[A-Za-z]{3,}", _normalize_text(value))
            if token and token.lower() not in _CATEGORY_TERM_STOPWORDS
        }

    def _validate_shopify_suggestion_with_llm(self, product: dict[str, Any], suggested_full_name: str) -> dict[str, Any] | None:
        if not self.llm_client or not suggested_full_name:
            return None

        prompt = (
            "You are validating whether a Shopify admin category suggestion matches the product.\n"
            "Return JSON only.\n"
            "All reasoning text must be in Simplified Chinese.\n"
            "Schema:\n"
            "{"
            "\"accepted\":true|false,"
            "\"confidence\":0-100,"
            "\"needs_review\":true|false,"
            "\"reason\":\"简体中文说明\""
            "}\n\n"
            f"title: {_truncate(str(product.get('title', '')), 220)}\n"
            f"vendor: {_truncate(str(product.get('vendor', '')), 80)}\n"
            f"product_type: {_truncate(str(product.get('productType', '')), 80)}\n"
            f"description: {_truncate(str(product.get('description', '')), 360)}\n"
            f"current_category: {_truncate(str((product.get('category') or {}).get('fullName', '')), 180)}\n"
            f"shopify_suggested_category: {_truncate(suggested_full_name, 180)}\n"
        )
        response = self.llm_client.generate(
            prompt,
            temperature=0,
            text={"format": {"type": "json_object"}},
        )
        parsed = _safe_json_loads(response.get("text", ""))
        if not isinstance(parsed, dict):
            return None
        confidence = int(parsed.get("confidence", 0) or 0)
        accepted = bool(parsed.get("accepted", False)) and confidence >= 70
        return {
            "accepted": accepted,
            "needs_review": bool(parsed.get("needs_review", not accepted)) or not accepted,
            "reason": _normalize_text(str(parsed.get("reason", "") or "LLM 已完成 Shopify 建议有效性校验。")),
        }

    def _search_candidate_categories(self, product: dict[str, Any], request: CategorySyncRequest) -> list[dict[str, Any]]:
        return self._search_candidate_categories_from_terms(
            product,
            candidate_category=request.candidate_category,
            suggestion_texts=[],
        )

    def _search_candidate_categories_from_terms(
        self,
        product: dict[str, Any],
        *,
        candidate_category: str,
        suggestion_texts: list[str],
    ) -> list[dict[str, Any]]:
        search_terms = [
            candidate_category,
            *suggestion_texts[:6],
            (product.get("category") or {}).get("fullName", ""),
            product.get("productType", ""),
            " ".join(str(product.get("title", "")).split()[:8]),
        ]
        candidates_by_id: dict[str, dict[str, Any]] = {}
        for term in search_terms:
            cleaned = _normalize_text(term)
            if not cleaned:
                continue
            for category in self._taxonomy_search(cleaned, first=6):
                category_id = category.get("id", "")
                if category_id and category_id not in candidates_by_id:
                    candidates_by_id[category_id] = category
            if len(candidates_by_id) >= 8:
                break
        return list(candidates_by_id.values())[:8]

    def _taxonomy_search(self, search: str, *, first: int = 6) -> list[dict[str, Any]]:
        data = self.shopify_client.graphql(
            """
            query TaxonomySearch($search: String!, $first: Int!) {
              taxonomy {
                categories(search: $search, first: $first) {
                  nodes {
                    id
                    name
                    fullName
                    isLeaf
                    attributes(first: 20) {
                      nodes {
                        __typename
                        ... on TaxonomyChoiceListAttribute {
                          id
                          name
                          values(first: 12) {
                            nodes {
                              id
                              name
                            }
                          }
                        }
                        ... on TaxonomyMeasurementAttribute {
                          id
                          name
                        }
                        ... on TaxonomyAttribute {
                          id
                        }
                      }
                    }
                  }
                }
              }
            }
            """,
            {"search": search, "first": first},
        )
        categories = ((data.get("taxonomy") or {}).get("categories") or {}).get("nodes", []) or []
        return [category for category in categories if category]

    def _find_taxonomy_category_by_full_name(self, full_name: str) -> dict[str, Any] | None:
        cleaned = _normalize_text(full_name)
        if not cleaned:
            return None
        matches = self._taxonomy_search(cleaned, first=10)
        for match in matches:
            if _normalize_text(match.get("fullName", "")) == cleaned:
                return match
        return matches[0] if matches else None

    def _collect_shopify_suggestion_texts(self, raw: dict[str, Any]) -> list[str]:
        values: list[str] = []

        def add(value: Any) -> None:
            cleaned = _normalize_text(str(value or ""))
            if cleaned and cleaned not in values:
                values.append(cleaned)

        add(raw.get("category_full_name", ""))
        add(raw.get("full_name", ""))
        add(raw.get("category_suggestion_text", ""))

        for item in raw.get("category_suggestion_candidates", []) or []:
            add(item)
        for item in raw.get("category_attribute_candidates", []) or []:
            add(item)
        for item in raw.get("category_suggestion_rows", []) or []:
            if isinstance(item, dict):
                add(item.get("text", ""))
                add(item.get("raw_text", ""))

        expanded: list[str] = []
        for value in values:
            if value not in expanded:
                expanded.append(value)
            zh_match = re.match(r"(.+?)（在\s*(.+?)\s*中）", value)
            en_match = re.match(r"(.+?)\s*\(in\s+(.+?)\)", value, flags=re.IGNORECASE)
            match = zh_match or en_match
            if match:
                for part in match.groups():
                    cleaned = _normalize_text(part)
                    if cleaned and cleaned not in expanded:
                        expanded.append(cleaned)
            if " > " in value:
                for part in value.split(">"):
                    cleaned = _normalize_text(part)
                    if cleaned and cleaned not in expanded:
                        expanded.append(cleaned)
        return expanded

    def _collect_shopify_suggestion_node_ids(self, raw: dict[str, Any]) -> list[str]:
        values: list[str] = []
        for item in raw.get("category_suggestion_node_ids", []) or []:
            cleaned = _normalize_text(str(item or ""))
            if cleaned and cleaned not in values:
                values.append(cleaned)
        return values

    def _resolve_shopify_suggestion_category(
        self,
        product: dict[str, Any],
        suggestion_texts: list[str],
        suggestion_node_ids: list[str],
    ) -> dict[str, Any] | None:
        for node_id in suggestion_node_ids:
            resolved = self._get_taxonomy_node_by_id(node_id)
            if resolved:
                return resolved

        for text in suggestion_texts:
            exact = self._find_taxonomy_category_by_full_name(text)
            if not exact:
                continue
            normalized = _normalize_text(text)
            if normalized in {
                _normalize_text(exact.get("fullName", "")),
                _normalize_text(exact.get("name", "")),
            }:
                return exact

        for text in suggestion_texts:
            matches = self._taxonomy_search(text, first=8)
            normalized = _normalize_text(text)
            for match in matches:
                if normalized in {
                    _normalize_text(match.get("fullName", "")),
                    _normalize_text(match.get("name", "")),
                }:
                    return match
            if len(matches) == 1:
                return matches[0]

        candidates = self._search_candidate_categories_from_terms(
            product,
            candidate_category="",
            suggestion_texts=suggestion_texts,
        )
        if len(candidates) == 1:
            return candidates[0]

        return self._resolve_shopify_suggestion_with_llm(product, suggestion_texts, candidates)

    def _get_taxonomy_node_by_id(self, node_id: str) -> dict[str, Any] | None:
        cleaned = _normalize_text(node_id)
        if not cleaned:
            return None
        data = self.shopify_client.graphql(
            """
            query TaxonomyNodeById($id: ID!) {
              node(id: $id) {
                __typename
                ... on ProductTaxonomyNode {
                  id
                  name
                  fullName
                  isLeaf
                }
              }
            }
            """,
            {"id": cleaned},
        )
        node = data.get("node") or {}
        if node.get("__typename") != "ProductTaxonomyNode":
            return None
        mapped = self._find_taxonomy_category_by_full_name(node.get("fullName", ""))
        if mapped:
            return mapped
        return {
            "id": node.get("id", ""),
            "name": node.get("name", ""),
            "fullName": node.get("fullName", ""),
            "isLeaf": node.get("isLeaf", False),
        }

    def _resolve_shopify_suggestion_with_llm(
        self,
        product: dict[str, Any],
        suggestion_texts: list[str],
        candidates: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        if not self.llm_client or not suggestion_texts or not candidates:
            return None

        candidate_lines = []
        for item in candidates[:8]:
            candidate_lines.append(
                {
                    "id": item.get("id", ""),
                    "name": item.get("name", ""),
                    "full_name": item.get("fullName", ""),
                }
            )

        prompt = (
            "You are resolving a Shopify admin category suggestion to a Shopify taxonomy category.\n"
            "Return JSON only.\n"
            "All reasoning text must be written in Simplified Chinese.\n"
            "Choose exactly one category_id from the candidate list when the Shopify suggestion clearly matches.\n"
            "If no candidate is reliable, return an empty category_id.\n"
            "JSON schema:\n"
            "{"
            "\"category_id\":\"...\"," 
            "\"reasoning\":\"简体中文短说明\""
            "}\n\n"
            f"title: {_truncate(str(product.get('title', '')), 240)}\n"
            f"vendor: {_truncate(str(product.get('vendor', '')), 80)}\n"
            f"product_type: {_truncate(str(product.get('productType', '')), 80)}\n"
            f"shopify_admin_suggestion_texts: {json.dumps(suggestion_texts[:12], ensure_ascii=False)}\n"
            f"candidate_categories: {json.dumps(candidate_lines, ensure_ascii=False)}\n"
        )
        response = self.llm_client.generate(
            prompt,
            temperature=0,
            text={"format": {"type": "json_object"}},
        )
        parsed = _safe_json_loads(response.get("text", ""))
        if not isinstance(parsed, dict):
            return None

        category_id = _normalize_text(str(parsed.get("category_id", "") or ""))
        if not category_id:
            return None
        for item in candidates:
            if item.get("id", "") == category_id:
                return item
        return None

    def _build_deepseek_decision(self, product: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any]:
        current_category = product.get("category") or {}
        if not candidates and current_category:
            candidates = [current_category]

        if not self.llm_client:
            chosen = candidates[0] if candidates else current_category
            return {
                "source": "heuristic_fallback",
                "risk_level": "medium",
                "needs_review": True,
                "decision_reason": "DeepSeek unavailable; used fallback candidate selection.",
                "candidate_categories": [self._serialize_candidate_category(item) for item in candidates],
                "suggested_category": self._serialize_candidate_category(chosen),
                "suggested_metafields": [],
            }

        prompt = self._build_deepseek_prompt(product, candidates)
        response = self.llm_client.generate(
            prompt,
            temperature=0,
            text={"format": {"type": "json_object"}},
        )
        parsed = _safe_json_loads(response.get("text", ""))
        if not isinstance(parsed, dict):
            chosen = candidates[0] if candidates else current_category
            return {
                "source": "deepseek_fallback",
                "risk_level": "high",
                "needs_review": True,
                "decision_reason": "DeepSeek returned invalid JSON; falling back to first candidate.",
                "candidate_categories": [self._serialize_candidate_category(item) for item in candidates],
                "suggested_category": self._serialize_candidate_category(chosen),
                "suggested_metafields": [],
            }

        category_id = str(parsed.get("category_id", "")).strip()
        candidate_map = {item.get("id", ""): item for item in candidates if item.get("id")}
        chosen = candidate_map.get(category_id) or (candidates[0] if candidates else current_category)
        suggested_metafields = self._normalize_metafield_suggestions(parsed.get("suggested_metafields", []))
        risk_level = str(parsed.get("risk_level", "medium") or "medium").lower()
        confidence = int(parsed.get("confidence", 0) or 0)
        if confidence < 65:
            risk_level = "high"
        if _risk_rank(risk_level) < 0:
            risk_level = "medium"
        needs_review = bool(parsed.get("needs_review", False)) or risk_level == "high"
        return {
            "source": "deepseek",
            "risk_level": risk_level,
            "needs_review": needs_review,
            "decision_reason": _normalize_text(str(parsed.get("reasoning", "") or "DeepSeek generated category decision.")),
            "candidate_categories": [self._serialize_candidate_category(item) for item in candidates],
            "suggested_category": self._serialize_candidate_category(chosen),
            "suggested_metafields": suggested_metafields,
        }

    def _build_deepseek_prompt(self, product: dict[str, Any], candidates: list[dict[str, Any]]) -> str:
        current_category = product.get("category") or {}
        current_shopify_metafields = [
            {
                "key": node["key"],
                "type": node["type"],
                "value": self._summarize_metafield_value(node["value"]),
            }
            for node in self._shopify_namespace_metafields(product)
        ]
        candidate_lines = []
        for item in candidates[:8]:
            attrs = self._serialize_category_attributes(item.get("attributes", {}).get("nodes", []) or [])
            candidate_lines.append(
                {
                    "id": item.get("id", ""),
                    "full_name": item.get("fullName", ""),
                    "attributes": attrs,
                }
            )
        return (
            "You are optimizing Shopify product category data.\n"
            "Return JSON only.\n"
            "All reasoning text must be written in Simplified Chinese.\n"
            "Choose exactly one category_id from the candidate list.\n"
            "If the current category is already the best match, you may keep it.\n"
            "Suggested metafields must only use keys that appear in the candidate attributes with a mapped_key.\n"
            "Each suggested metafield must be an object with keys: key, name, values.\n"
            "values must be an array of human-readable labels.\n"
            "Return JSON schema:\n"
            "{"
            "\"category_id\":\"...\","
            "\"confidence\":0-100,"
            "\"risk_level\":\"low|medium|high\","
            "\"needs_review\":true|false,"
            "\"reasoning\":\"简体中文短说明\","
            "\"suggested_metafields\":[{\"key\":\"...\",\"name\":\"...\",\"values\":[\"...\"]}]"
            "}\n\n"
            f"title: {_truncate(str(product.get('title', '')), 240)}\n"
            f"vendor: {_truncate(str(product.get('vendor', '')), 80)}\n"
            f"product_type: {_truncate(str(product.get('productType', '')), 80)}\n"
            f"tags: {json.dumps(product.get('tags', [])[:15], ensure_ascii=False)}\n"
            f"description: {_truncate(str(product.get('description', '')), 600)}\n"
            f"current_category: {current_category.get('fullName', '')}\n"
            f"current_shopify_metafields: {json.dumps(current_shopify_metafields[:15], ensure_ascii=False)}\n"
            f"candidate_categories: {json.dumps(candidate_lines, ensure_ascii=False)}\n"
        )

    def _serialize_candidate_category(self, category: dict[str, Any] | None) -> dict[str, Any]:
        category = category or {}
        return {
            "id": category.get("id", ""),
            "name": category.get("name", ""),
            "full_name": category.get("fullName", ""),
        }

    def _serialize_category_attributes(self, nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        output = []
        for node in nodes:
            typename = node.get("__typename", "")
            name = node.get("name", "")
            definition = self._get_definition_for_attribute(name)
            mapped_key = definition.get("key", "") if definition else ""
            values = []
            if typename == "TaxonomyChoiceListAttribute":
                values = [value.get("name", "") for value in (node.get("values", {}) or {}).get("nodes", []) or []]
            output.append(
                {
                    "name": name,
                    "mapped_key": mapped_key,
                    "type": typename,
                    "values": values[:12],
                }
            )
        return output

    def _get_definition_for_attribute(self, attribute_name: str) -> dict[str, str] | None:
        definitions = self._load_shopify_metafield_definitions()
        normalized = _slugify(attribute_name)
        if normalized in definitions:
            return definitions[normalized]
        for key, definition in definitions.items():
            if normalized == _slugify(definition["name"]):
                return definition
        return None

    def _load_shopify_metafield_definitions(self) -> dict[str, dict[str, str]]:
        if self._definition_cache is not None:
            return self._definition_cache

        data = self.shopify_client.graphql(
            """
            query ProductMetafieldDefinitions {
              metafieldDefinitions(first: 250, ownerType: PRODUCT, namespace: "shopify") {
                edges {
                  node {
                    namespace
                    key
                    name
                    type {
                      name
                      category
                    }
                  }
                }
              }
            }
            """
        )
        cache: dict[str, dict[str, str]] = {}
        for edge in (data.get("metafieldDefinitions", {}) or {}).get("edges", []) or []:
            node = edge.get("node") or {}
            cache[_slugify(node.get("key", ""))] = {
                "namespace": node.get("namespace", "shopify"),
                "key": node.get("key", ""),
                "name": node.get("name", ""),
                "type": ((node.get("type") or {}).get("name") or ""),
            }
        self._definition_cache = cache
        return cache

    def _normalize_metafield_suggestions(self, payload: Any) -> list[dict[str, Any]]:
        if not isinstance(payload, list):
            return []
        definitions = self._load_shopify_metafield_definitions()
        output: list[dict[str, Any]] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            values = item.get("values", [])
            if not isinstance(values, list):
                continue
            definition = self._resolve_definition_from_metafield_suggestion(item, definitions)
            if not definition:
                continue
            cleaned_values = [_normalize_text(str(value)) for value in values if _normalize_text(str(value))]
            if not cleaned_values:
                continue
            output.append(
                {
                    "namespace": definition["namespace"],
                    "key": definition["key"],
                    "name": definition["name"],
                    "type": definition["type"],
                    "values": cleaned_values[:8],
                }
            )
        return output

    def _resolve_definition_from_metafield_suggestion(
        self,
        item: dict[str, Any],
        definitions: dict[str, dict[str, str]],
    ) -> dict[str, str] | None:
        candidates: list[str] = []
        for value in [
            item.get("key", ""),
            item.get("label", ""),
            item.get("name", ""),
        ]:
            cleaned = _normalize_text(str(value or ""))
            if cleaned and cleaned not in candidates:
                candidates.append(cleaned)
        for value in item.get("key_candidates", []) or []:
            cleaned = _normalize_text(str(value or ""))
            if cleaned and cleaned not in candidates:
                candidates.append(cleaned)

        for candidate in candidates:
            slug = _slugify(candidate)
            if slug in definitions:
                return definitions[slug]

        for candidate in candidates:
            slug = _slugify(candidate)
            for definition in definitions.values():
                if slug in {_slugify(definition["key"]), _slugify(definition["name"])}:
                    return definition
        return None

    def _apply_decision(self, product: dict[str, Any], decision: dict[str, Any], request: CategorySyncRequest) -> dict[str, Any]:
        suggested_category = decision["suggested_category"]
        current_category = product.get("category") or {}
        category_updated = False
        metafields_updated = 0
        skipped_metafields: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        written_metafields: list[dict[str, Any]] = []

        if decision["needs_review"]:
            return {
                "mode": request.mode,
                "category_updated": False,
                "metafields_updated": 0,
                "skipped_metafields": [],
                "errors": [],
                "written_metafields": [],
                "rollback_ready": False,
                "status": "review_required",
            }

        if suggested_category.get("id") and suggested_category.get("id") != current_category.get("id"):
            try:
                data = self.shopify_client.graphql(
                    """
                    mutation UpdateProductCategory($product: ProductUpdateInput!) {
                      productUpdate(product: $product) {
                        product {
                          id
                          category {
                            id
                            fullName
                          }
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
                            "id": product.get("id", ""),
                            "category": suggested_category["id"],
                        }
                    },
                )
                user_errors = ((data.get("productUpdate") or {}).get("userErrors") or [])
                if user_errors:
                    errors.append(
                        {
                            "scope": "category",
                            "reason": "shopify_category_update_error",
                            "detail": self._format_shopify_errors(user_errors),
                        }
                    )
                else:
                    category_updated = True
            except ShopifyGraphQLError as exc:
                errors.append(
                    {
                        "scope": "category",
                        "reason": "shopify_category_update_exception",
                        "detail": self._format_exception_message(exc),
                    }
                )

        if request.apply_metafields and decision["suggested_metafields"]:
            metafield_inputs = []
            metafield_specs: list[dict[str, Any]] = []
            for metafield in decision["suggested_metafields"]:
                resolved = self._resolve_metaobject_ids(metafield["key"], metafield["values"])
                if not resolved:
                    skipped_metafields.append(
                        {
                            "key": metafield["key"],
                            "reason": "unresolved_metaobject_values",
                            "values": metafield["values"],
                        }
                    )
                    continue
                metafield_input = {
                    "ownerId": product.get("id", ""),
                    "namespace": metafield["namespace"],
                    "key": metafield["key"],
                    "type": metafield["type"],
                    "value": json.dumps(resolved, ensure_ascii=False)
                    if metafield["type"].startswith("list.")
                    else resolved[0],
                }
                metafield_inputs.append(metafield_input)
                metafield_specs.append(metafield)
            for metafield_input, metafield_spec in zip(metafield_inputs, metafield_specs):
                try:
                    data = self.shopify_client.graphql(
                        """
                        mutation SetProductMetafields($metafields: [MetafieldsSetInput!]!) {
                          metafieldsSet(metafields: $metafields) {
                            metafields {
                              id
                              key
                              namespace
                            }
                            userErrors {
                              field
                              message
                              code
                            }
                          }
                        }
                        """,
                        {"metafields": [metafield_input]},
                    )
                    result = data.get("metafieldsSet") or {}
                    user_errors = result.get("userErrors") or []
                    if user_errors:
                        skipped_metafields.append(
                            {
                                "key": metafield_spec["key"],
                                "reason": "shopify_validation_error",
                                "detail": self._format_shopify_errors(user_errors),
                                "values": metafield_spec["values"],
                            }
                        )
                        continue
                    metafields_updated += len(result.get("metafields") or [])
                    if result.get("metafields"):
                        written_metafields.append(
                            {
                                "namespace": metafield_spec["namespace"],
                                "key": metafield_spec["key"],
                                "type": metafield_spec["type"],
                                "values": metafield_spec["values"],
                            }
                        )
                except ShopifyGraphQLError as exc:
                    skipped_metafields.append(
                        {
                            "key": metafield_spec["key"],
                            "reason": "shopify_metafield_exception",
                            "detail": self._format_exception_message(exc),
                            "values": metafield_spec["values"],
                        }
                    )

        if category_updated or metafields_updated:
            status = "applied"
        elif errors:
            status = "apply_failed"
        else:
            status = "unchanged"
        return {
            "mode": request.mode,
            "category_updated": category_updated,
            "metafields_updated": metafields_updated,
            "skipped_metafields": skipped_metafields,
            "errors": errors,
            "written_metafields": written_metafields,
            "rollback_ready": bool(category_updated or metafields_updated),
            "status": status,
        }

    def _build_dry_run_apply_result(self, decision: dict[str, Any]) -> dict[str, Any]:
        return {
            "mode": "dry-run",
            "category_updated": False,
            "metafields_updated": 0,
            "skipped_metafields": [],
            "errors": [],
            "written_metafields": [],
            "rollback_ready": False,
            "status": "review_required" if decision["needs_review"] else "dry_run",
        }

    def _format_shopify_errors(self, errors: list[dict[str, Any]]) -> str:
        parts = []
        for error in errors:
            field = ".".join(str(item) for item in (error.get("field") or []))
            code = error.get("code", "")
            message = error.get("message", "")
            parts.append(" / ".join(part for part in [field, code, message] if part))
        return "; ".join(parts)

    def _format_exception_message(self, exc: Exception) -> str:
        text = str(exc).strip()
        if not text:
            return exc.__class__.__name__
        return text

    def _resolve_metaobject_ids(self, key: str, values: list[str]) -> list[str]:
        resolved: list[str] = []
        metaobject_type = f"shopify--{key}"
        for value in values:
            cleaned = _normalize_text(value)
            if not cleaned:
                continue
            escaped = cleaned.replace('"', '\\"')
            data = self.shopify_client.graphql(
                """
                query MetaobjectsByDisplayName($type: String!, $query: String!) {
                  metaobjects(first: 5, type: $type, query: $query) {
                    edges {
                      node {
                        id
                        displayName
                      }
                    }
                  }
                }
                """,
                {
                    "type": metaobject_type,
                    "query": f'display_name:"{escaped}"',
                },
            )
            edges = ((data.get("metaobjects") or {}).get("edges") or [])
            match = next(
                (
                    edge.get("node")
                    for edge in edges
                    if _normalize_text((edge.get("node") or {}).get("displayName", "")) == cleaned
                ),
                None,
            )
            if not match:
                return []
            resolved.append(match.get("id", ""))
        return [item for item in resolved if item]

    def _serialize_metafields(self, product: dict[str, Any]) -> list[dict[str, Any]]:
        output = []
        for node in self._shopify_namespace_metafields(product):
            output.append(
                {
                    "namespace": node["namespace"],
                    "key": node["key"],
                    "type": node["type"],
                    "value": self._summarize_metafield_value(node["value"]),
                }
            )
        return output

    def _shopify_namespace_metafields(self, product: dict[str, Any]) -> list[dict[str, str]]:
        edges = ((product.get("metafields") or {}).get("edges") or [])
        nodes = []
        for edge in edges:
            node = edge.get("node") or {}
            if node.get("namespace") == "shopify":
                nodes.append(
                    {
                        "namespace": node.get("namespace", ""),
                        "key": node.get("key", ""),
                        "type": node.get("type", ""),
                        "value": node.get("value", ""),
                    }
                )
        return nodes

    def _summarize_metafield_value(self, value: str) -> Any:
        parsed = _safe_json_loads(value)
        return parsed if parsed is not None else _truncate(str(value), 120)

    def _emit(self, progress_callback: Any | None, event: dict[str, Any]) -> None:
        if progress_callback is not None:
            progress_callback(event)

    def rollback_items(
        self,
        items: list[dict[str, Any]],
        *,
        progress_callback: Any | None = None,
    ) -> dict[str, Any]:
        rolled_back = 0
        failed = 0
        skipped = 0
        results: list[dict[str, Any]] = []
        total = len(items)
        for index, item in enumerate(items, start=1):
            result = self._rollback_item(item)
            results.append(result)
            if result["status"] == "rolled_back":
                rolled_back += 1
            elif result["status"] == "rollback_failed":
                failed += 1
            else:
                skipped += 1
            self._emit(
                progress_callback,
                {
                    "event": "rollback_item",
                    "index": index,
                    "total": total,
                    "item": result,
                },
            )
        return {
            "summary": f"本次回滚共处理 {total} 个商品，成功回滚 {rolled_back} 个，失败 {failed} 个，跳过 {skipped} 个。",
            "data": {
                "processed_count": total,
                "rolled_back_count": rolled_back,
                "failed_count": failed,
                "skipped_count": skipped,
                "items": results,
            },
        }

    def _rollback_item(self, item: dict[str, Any]) -> dict[str, Any]:
        apply_result = item.get("apply_result") or {}
        if not apply_result.get("rollback_ready"):
            return {
                "product_id": item.get("product_id", ""),
                "title": item.get("title", ""),
                "status": "skipped",
                "reason": "not_modified_in_original_batch",
                "detail": "该商品在原批次中没有成功写回，无需回滚。",
            }

        snapshot = item.get("rollback_snapshot") or {}
        original_category = snapshot.get("category") or {}
        original_metafields = snapshot.get("metafields") or []
        written_metafields = apply_result.get("written_metafields") or []

        errors: list[str] = []
        category_restored = False
        metafields_restored = 0
        metafields_deleted = 0

        if apply_result.get("category_updated"):
            try:
                data = self.shopify_client.graphql(
                    """
                    mutation RestoreProductCategory($product: ProductUpdateInput!) {
                      productUpdate(product: $product) {
                        product {
                          id
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
                            "id": item.get("product_id", ""),
                            "category": original_category.get("id") or None,
                        }
                    },
                )
                user_errors = ((data.get("productUpdate") or {}).get("userErrors") or [])
                if user_errors:
                    errors.append(self._format_shopify_errors(user_errors))
                else:
                    category_restored = True
            except ShopifyGraphQLError as exc:
                errors.append(self._format_exception_message(exc))

        original_by_key = {
            (mf.get("namespace", ""), mf.get("key", "")): mf
            for mf in original_metafields
            if mf.get("namespace") and mf.get("key")
        }
        to_restore = []
        to_delete = []
        for written in written_metafields:
            key = (written.get("namespace", ""), written.get("key", ""))
            if key in original_by_key:
                original = original_by_key[key]
                to_restore.append(
                    {
                        "ownerId": item.get("product_id", ""),
                        "namespace": original.get("namespace", ""),
                        "key": original.get("key", ""),
                        "type": original.get("type", ""),
                        "value": original.get("value", ""),
                    }
                )
            else:
                to_delete.append(
                    {
                        "ownerId": item.get("product_id", ""),
                        "namespace": written.get("namespace", ""),
                        "key": written.get("key", ""),
                    }
                )

        for metafield_input in to_restore:
            try:
                data = self.shopify_client.graphql(
                    """
                    mutation RestoreMetafields($metafields: [MetafieldsSetInput!]!) {
                      metafieldsSet(metafields: $metafields) {
                        metafields {
                          id
                        }
                        userErrors {
                          field
                          message
                          code
                        }
                      }
                    }
                    """,
                    {"metafields": [metafield_input]},
                )
                user_errors = ((data.get("metafieldsSet") or {}).get("userErrors") or [])
                if user_errors:
                    errors.append(self._format_shopify_errors(user_errors))
                else:
                    metafields_restored += 1
            except ShopifyGraphQLError as exc:
                errors.append(self._format_exception_message(exc))

        for metafield_identifier in to_delete:
            try:
                data = self.shopify_client.graphql(
                    """
                    mutation DeleteMetafields($metafields: [MetafieldIdentifierInput!]!) {
                      metafieldsDelete(metafields: $metafields) {
                        deletedMetafields {
                          key
                          namespace
                        }
                        userErrors {
                          field
                          message
                          code
                        }
                      }
                    }
                    """,
                    {"metafields": [metafield_identifier]},
                )
                user_errors = ((data.get("metafieldsDelete") or {}).get("userErrors") or [])
                if user_errors:
                    errors.append(self._format_shopify_errors(user_errors))
                else:
                    metafields_deleted += len(((data.get("metafieldsDelete") or {}).get("deletedMetafields") or []))
            except ShopifyGraphQLError as exc:
                errors.append(self._format_exception_message(exc))

        status = "rolled_back" if not errors else "rollback_failed"
        return {
            "product_id": item.get("product_id", ""),
            "title": item.get("title", ""),
            "status": status,
            "category_restored": category_restored,
            "metafields_restored": metafields_restored,
            "metafields_deleted": metafields_deleted,
            "detail": "；".join(errors) if errors else "回滚成功",
        }


def get_category_optimization_service() -> CategoryOptimizationService:
    return CategoryOptimizationService()
