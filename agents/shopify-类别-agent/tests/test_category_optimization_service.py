from pathlib import Path
import sys

AGENT_ROOT = Path(__file__).resolve().parents[1]
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from service.category_optimization_service import CategoryOptimizationService
from models.category_sync import CategorySyncRequest


class FakeLLM:
    def __init__(self, payload: str):
        self.payload = payload
        self.prompts = []

    def generate(self, prompt: str, **kwargs):
        self.prompts.append({"prompt": prompt, "kwargs": kwargs})
        return {"text": self.payload, "raw": {"id": "fake"}}


class FakeShopifyClient:
    def __init__(self):
        self.store_domain = "demo-shop.myshopify.com"
        self.updated_categories = []
        self.metafields_set_payloads = []
        self.deleted_metafields_payloads = []

    def graphql(self, query: str, variables=None):
        variables = variables or {}
        if "query ProductsPage" in query:
            return {
                "products": {
                    "edges": [
                        {
                            "node": {
                                "id": "gid://shopify/Product/1",
                                "title": "Portable Bluetooth Speaker",
                                "vendor": "Dekuch",
                                "productType": "Speaker",
                                "tags": ["audio", "portable"],
                                "description": "Waterproof outdoor speaker in blue color.",
                                "featuredImage": {"url": "https://example.com/speaker.jpg", "altText": "speaker"},
                                "category": {
                                    "id": "gid://shopify/TaxonomyCategory/el-2-2-10",
                                    "name": "Speakers",
                                    "fullName": "Electronics > Audio > Audio Components > Speakers",
                                    "isLeaf": True,
                                    "attributes": {
                                        "nodes": [
                                            {
                                                "__typename": "TaxonomyChoiceListAttribute",
                                                "id": "1",
                                                "name": "Color",
                                                "values": {"nodes": [{"id": "2", "name": "Blue"}]},
                                            },
                                            {
                                                "__typename": "TaxonomyChoiceListAttribute",
                                                "id": "3",
                                                "name": "Material",
                                                "values": {"nodes": [{"id": "4", "name": "Plastic"}]},
                                            },
                                        ]
                                    },
                                },
                                "metafields": {
                                    "edges": [
                                        {
                                            "node": {
                                                "namespace": "shopify",
                                                "key": "color-pattern",
                                                "type": "list.metaobject_reference",
                                                "value": '["gid://shopify/Metaobject/1"]',
                                            }
                                        }
                                    ]
                                },
                            }
                        }
                    ],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        if "query ProductById" in query:
            return {
                "product": {
                    "id": "gid://shopify/Product/1",
                    "title": "Portable Bluetooth Speaker",
                    "vendor": "Dekuch",
                    "productType": "Speaker",
                    "tags": ["audio", "portable"],
                    "description": "Waterproof outdoor speaker in blue color.",
                    "featuredImage": {"url": "https://example.com/speaker.jpg", "altText": "speaker"},
                    "category": {
                        "id": "gid://shopify/TaxonomyCategory/el-2-2-10",
                        "name": "Speakers",
                        "fullName": "Electronics > Audio > Audio Components > Speakers",
                        "isLeaf": True,
                        "attributes": {
                            "nodes": [
                                {
                                    "__typename": "TaxonomyChoiceListAttribute",
                                    "id": "1",
                                    "name": "Color",
                                    "values": {"nodes": [{"id": "2", "name": "Blue"}]},
                                },
                                {
                                    "__typename": "TaxonomyChoiceListAttribute",
                                    "id": "3",
                                    "name": "Material",
                                    "values": {"nodes": [{"id": "4", "name": "Plastic"}]},
                                },
                            ]
                        },
                    },
                    "metafields": {
                        "edges": [
                            {
                                "node": {
                                    "namespace": "shopify",
                                    "key": "color-pattern",
                                    "type": "list.metaobject_reference",
                                    "value": '["gid://shopify/Metaobject/1"]',
                                }
                            }
                        ]
                    },
                }
            }
        if "query ProductMetafieldDefinitions" in query:
            return {
                "metafieldDefinitions": {
                    "edges": [
                        {
                            "node": {
                                "namespace": "shopify",
                                "key": "color-pattern",
                                "name": "Color",
                                "type": {"name": "list.metaobject_reference", "category": "REFERENCE"},
                            }
                        },
                        {
                            "node": {
                                "namespace": "shopify",
                                "key": "material",
                                "name": "Material",
                                "type": {"name": "list.metaobject_reference", "category": "REFERENCE"},
                            }
                        },
                    ]
                }
            }
        if "query TaxonomySearch" in query:
            return {
                "taxonomy": {
                    "categories": {
                        "nodes": [
                            {
                                "id": "gid://shopify/TaxonomyCategory/el-2-2-10",
                                "name": "Speakers",
                                "fullName": "Electronics > Audio > Audio Components > Speakers",
                                "isLeaf": True,
                                "attributes": {
                                    "nodes": [
                                        {
                                            "__typename": "TaxonomyChoiceListAttribute",
                                            "id": "1",
                                            "name": "Color",
                                            "values": {"nodes": [{"id": "2", "name": "Blue"}]},
                                        },
                                        {
                                            "__typename": "TaxonomyChoiceListAttribute",
                                            "id": "3",
                                            "name": "Material",
                                            "values": {"nodes": [{"id": "4", "name": "Plastic"}]},
                                        },
                                    ]
                                },
                            }
                        ]
                    }
                }
            }
        if "query MetaobjectsByDisplayName" in query:
            display_query = variables.get("query", "")
            if "Blue" in display_query:
                return {"metaobjects": {"edges": [{"node": {"id": "gid://shopify/Metaobject/blue", "displayName": "Blue"}}]}}
            if "Plastic" in display_query:
                return {"metaobjects": {"edges": [{"node": {"id": "gid://shopify/Metaobject/plastic", "displayName": "Plastic"}}]}}
            return {"metaobjects": {"edges": []}}
        if "mutation UpdateProductCategory" in query:
            self.updated_categories.append(variables)
            return {"productUpdate": {"product": {"id": "gid://shopify/Product/1", "category": {"id": variables["product"]["category"], "fullName": "Electronics > Audio > Audio Components > Speakers"}}, "userErrors": []}}
        if "mutation SetProductMetafields" in query:
            self.metafields_set_payloads.append(variables)
            return {"metafieldsSet": {"metafields": [{"id": "1", "key": "color-pattern", "namespace": "shopify"}], "userErrors": []}}
        if "mutation RestoreProductCategory" in query:
            self.updated_categories.append(variables)
            return {"productUpdate": {"product": {"id": "gid://shopify/Product/1"}, "userErrors": []}}
        if "mutation RestoreMetafields" in query:
            self.metafields_set_payloads.append(variables)
            return {"metafieldsSet": {"metafields": [{"id": "restore-1"}], "userErrors": []}}
        if "mutation DeleteMetafields" in query:
            self.deleted_metafields_payloads.append(variables)
            return {"metafieldsDelete": {"deletedMetafields": [{"key": variables["metafields"][0]["key"], "namespace": variables["metafields"][0]["namespace"]}], "userErrors": []}}
        raise AssertionError(f"Unexpected query: {query}")


class FakeShopifyClientWithMetafieldError(FakeShopifyClient):
    def graphql(self, query: str, variables=None):
        if "mutation SetProductMetafields" in query:
            self.metafields_set_payloads.append(variables or {})
            return {
                "metafieldsSet": {
                    "metafields": [],
                    "userErrors": [
                        {
                            "field": ["metafields", "0"],
                            "message": "Owner subtype does not match the metafield definition's constraints.",
                            "code": "INVALID_VALUE",
                        }
                    ],
                }
            }
        return super().graphql(query, variables)


class FakeShopifyClientForCategorySuggestion(FakeShopifyClient):
    def graphql(self, query: str, variables=None):
        variables = variables or {}
        if "query ProductsPage" in query:
            return {
                "products": {
                    "edges": [
                        {
                            "node": {
                                "id": "gid://shopify/Product/2",
                                "title": "Modern Style Dining Chairs Set of 6 in Light Gray",
                                "vendor": "Dekuch",
                                "productType": "Dining Chair",
                                "tags": ["chair", "dining-room"],
                                "description": "PU material dining chairs with silver metal legs.",
                                "featuredImage": {"url": "https://example.com/chair.jpg", "altText": "chair"},
                                "category": {
                                    "id": "gid://shopify/TaxonomyCategory/furniture-generic-chair",
                                    "name": "Chairs",
                                    "fullName": "Furniture > Chairs",
                                    "isLeaf": False,
                                    "attributes": {"nodes": []},
                                },
                                "metafields": {"edges": []},
                            }
                        }
                    ],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        if "query TaxonomyNodeById" in query:
            return {
                "node": {
                    "__typename": "ProductTaxonomyNode",
                    "id": variables["id"],
                    "name": "Kitchen & Dining Room Chairs",
                    "fullName": "Furniture > Chairs > Kitchen & Dining Room Chairs",
                    "isLeaf": False,
                    "attributes": {"nodes": []},
                }
            }
        if "query TaxonomySearch" in query:
            return {
                "taxonomy": {
                    "categories": {
                        "nodes": [
                            {
                                "id": "gid://shopify/TaxonomyCategory/furniture-dining-chairs",
                                "name": "Dining Chairs",
                                "fullName": "Furniture > Chairs > Dining Chairs",
                                "isLeaf": True,
                                "attributes": {"nodes": []},
                            }
                        ]
                    }
                }
            }
        if "mutation UpdateProductCategory" in query:
            self.updated_categories.append(variables)
            return {
                "productUpdate": {
                    "product": {
                        "id": "gid://shopify/Product/2",
                        "category": {
                            "id": variables["product"]["category"],
                            "fullName": "Furniture > Chairs > Dining Chairs",
                        },
                    },
                    "userErrors": [],
                }
            }
        return super().graphql(query, variables)


class FakeShopifyClientForMismatchedSuggestion(FakeShopifyClient):
    def graphql(self, query: str, variables=None):
        variables = variables or {}
        if "query ProductsPage" in query:
            return {
                "products": {
                    "edges": [
                        {
                            "node": {
                                "id": "gid://shopify/Product/3",
                                "title": "Patio Table Bronze 35.4x35.4x28.7 Cast Aluminum",
                                "vendor": "DOBA",
                                "productType": "Other Patio Tables",
                                "tags": ["table", "patio"],
                                "description": "Outdoor patio table made of cast aluminum in bronze finish.",
                                "featuredImage": {"url": "https://example.com/table.jpg", "altText": "table"},
                                "category": {
                                    "id": "gid://shopify/TaxonomyCategory/outdoor-generic",
                                    "name": "Other Patio Tables",
                                    "fullName": "Furniture > Outdoor Furniture > Outdoor Tables > Other Outdoor Tables",
                                    "isLeaf": True,
                                    "attributes": {"nodes": []},
                                },
                                "metafields": {"edges": []},
                            }
                        }
                    ],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        return super().graphql(query, variables)


def test_service_uses_deepseek_path_for_dry_run():
    llm = FakeLLM(
        '{"category_id":"gid://shopify/TaxonomyCategory/el-2-2-10","confidence":88,"risk_level":"low","needs_review":false,"reasoning":"Best fit for a portable speaker.","suggested_metafields":[{"key":"color-pattern","name":"Color","values":["Blue"]},{"key":"material","name":"Material","values":["Plastic"]}]}'
    )
    service = CategoryOptimizationService(shopify_client=FakeShopifyClient(), llm_client=llm, settings=type("S", (), {"deepseek_api_key": "x"})())
    result = service.run(CategorySyncRequest(mode="dry-run", product_query="vendor:Dekuch", max_items=1), task="categorize-products")

    item = result["data"]["items"][0]
    assert item["source"] == "deepseek"
    assert item["suggested_category"]["full_name"] == "Electronics > Audio > Audio Components > Speakers"
    assert item["suggested_metafields"][0]["key"] == "color-pattern"
    assert item["apply_result"]["status"] == "dry_run"


def test_service_uses_shopify_suggestion_when_provided():
    service = CategoryOptimizationService(shopify_client=FakeShopifyClient(), llm_client=None, settings=type("S", (), {"deepseek_api_key": ""})())
    request = CategorySyncRequest(
        mode="dry-run",
        max_items=1,
        shopify_suggestions={
            "gid://shopify/Product/1": {
                "category_full_name": "Electronics > Audio > Audio Components > Speakers",
                "metafields": [{"key": "color-pattern", "values": ["Blue"]}],
            }
        },
    )
    result = service.run(request, task="categorize-products")

    item = result["data"]["items"][0]
    assert item["source"] == "shopify_suggestion"
    assert item["suggested_metafields"][0]["key"] == "color-pattern"


def test_service_maps_shopify_metafield_suggestion_from_label_and_key_candidates():
    service = CategoryOptimizationService(shopify_client=FakeShopifyClient(), llm_client=None, settings=type("S", (), {"deepseek_api_key": ""})())
    request = CategorySyncRequest(
        mode="dry-run",
        max_items=1,
        shopify_suggestions={
            "gid://shopify/Product/1": {
                "category_full_name": "Electronics > Audio > Audio Components > Speakers",
                "metafields": [
                    {
                        "key": "",
                        "label": "Material",
                        "name": "Material",
                        "key_candidates": ["material", "metaobject-material"],
                        "values": ["Plastic"],
                    }
                ],
            }
        },
    )

    result = service.run(request, task="categorize-products")

    item = result["data"]["items"][0]
    assert item["source"] == "shopify_suggestion"
    assert item["suggested_metafields"][0]["key"] == "material"
    assert item["suggested_metafields"][0]["values"] == ["Plastic"]


def test_service_uses_shopify_category_suggestion_text_when_full_name_missing():
    service = CategoryOptimizationService(
        shopify_client=FakeShopifyClientForCategorySuggestion(),
        llm_client=None,
        settings=type("S", (), {"deepseek_api_key": ""})(),
    )
    request = CategorySyncRequest(
        mode="dry-run",
        max_items=1,
        shopify_suggestions={
            "gid://shopify/Product/2": {
                "category_suggestion_text": "厨房/餐厅坐椅（在 椅子 中）",
                "category_suggestion_candidates": ["厨房/餐厅坐椅（在 椅子 中）"],
            }
        },
    )

    result = service.run(request, task="categorize-products")

    item = result["data"]["items"][0]
    assert item["source"] == "shopify_suggestion"
    assert item["suggested_category"]["id"] == "gid://shopify/TaxonomyCategory/furniture-dining-chairs"
    assert item["needs_review"] is False


def test_service_uses_shopify_category_suggestion_node_id_when_available():
    service = CategoryOptimizationService(
        shopify_client=FakeShopifyClientForCategorySuggestion(),
        llm_client=None,
        settings=type("S", (), {"deepseek_api_key": ""})(),
    )
    request = CategorySyncRequest(
        mode="dry-run",
        max_items=1,
        shopify_suggestions={
            "gid://shopify/Product/2": {
                "category_suggestion_node_ids": ["gid://shopify/ProductTaxonomyNode/2104"],
            }
        },
    )

    result = service.run(request, task="categorize-products")

    item = result["data"]["items"][0]
    assert item["source"] == "shopify_suggestion"
    assert item["suggested_category"]["id"] == "gid://shopify/TaxonomyCategory/furniture-dining-chairs"
    assert item["suggested_category"]["full_name"] == "Furniture > Chairs > Dining Chairs"
    assert item["needs_review"] is False


def test_service_does_not_force_review_when_shopify_suggestion_changes_category():
    service = CategoryOptimizationService(
        shopify_client=FakeShopifyClientForCategorySuggestion(),
        llm_client=None,
        settings=type("S", (), {"deepseek_api_key": ""})(),
    )
    request = CategorySyncRequest(
        mode="dry-run",
        max_items=1,
        shopify_suggestions={
            "gid://shopify/Product/2": {
                "category_full_name": "Furniture > Chairs > Dining Chairs",
            }
        },
    )

    result = service.run(request, task="categorize-products")

    item = result["data"]["items"][0]
    assert item["source"] == "shopify_suggestion"
    assert item["suggested_category"]["full_name"] == "Furniture > Chairs > Dining Chairs"
    assert item["risk_level"] == "medium"
    assert item["needs_review"] is False


def test_service_rejects_mismatched_shopify_suggestion_and_falls_back_to_deepseek():
    llm = FakeLLM(
        '{"category_id":"gid://shopify/TaxonomyCategory/outdoor-table","confidence":88,"risk_level":"medium","needs_review":false,"reasoning":"商品是户外桌子，Shopify 建议的取暖器类目不匹配。","suggested_metafields":[]}'
    )
    service = CategoryOptimizationService(
        shopify_client=FakeShopifyClientForMismatchedSuggestion(),
        llm_client=llm,
        settings=type("S", (), {"deepseek_api_key": "x"})(),
    )
    request = CategorySyncRequest(
        mode="dry-run",
        max_items=1,
        shopify_suggestions={
            "gid://shopify/Product/3": {
                "category_full_name": "Home & Garden > Climate Control Appliances > Outdoor Heaters",
                "category_suggestion_candidates": [
                    "Outdoor Heaters (in Climate Control Appliances)",
                    "Outdoor Heaters 建议 确定税率并添加元字段",
                ],
            }
        },
    )

    result = service.run(request, task="categorize-products")

    item = result["data"]["items"][0]
    assert item["source"] == "deepseek"
    assert item["needs_review"] is True
    assert "Shopify 建议未通过自动校验" in item["decision_reason"]


def test_validate_shopify_suggestion_accepts_clear_overlap():
    service = CategoryOptimizationService(
        shopify_client=FakeShopifyClientForCategorySuggestion(),
        llm_client=None,
        settings=type("S", (), {"deepseek_api_key": ""})(),
    )
    product = {
        "title": "Modern Style Dining Chairs Set of 6 in Light Gray",
        "vendor": "Dekuch",
        "productType": "Dining Chair",
        "tags": ["chair", "dining-room"],
        "description": "PU material dining chairs with silver metal legs.",
        "category": {
            "id": "gid://shopify/TaxonomyCategory/furniture-generic-chair",
            "name": "Chairs",
            "fullName": "Furniture > Chairs",
        },
    }
    suggestion = {
        "category": {
            "id": "gid://shopify/TaxonomyCategory/furniture-dining-chairs",
            "name": "Dining Chairs",
            "fullName": "Furniture > Chairs > Dining Chairs",
        },
        "raw_category_full_name": "Furniture > Chairs > Dining Chairs",
        "raw_category_candidates": ["Furniture > Chairs > Dining Chairs"],
        "metafields": [],
    }

    validation = service._validate_shopify_suggestion(product, suggestion)

    assert validation["accepted"] is True
    assert validation["needs_review"] is False


def test_service_apply_updates_category_and_metafields():
    client = FakeShopifyClient()
    llm = FakeLLM(
        '{"category_id":"gid://shopify/TaxonomyCategory/el-2-2-10","confidence":90,"risk_level":"low","needs_review":false,"reasoning":"Best fit.","suggested_metafields":[{"key":"color-pattern","name":"Color","values":["Blue"]},{"key":"material","name":"Material","values":["Plastic"]}]}'
    )
    service = CategoryOptimizationService(shopify_client=client, llm_client=llm, settings=type("S", (), {"deepseek_api_key": "x"})())
    result = service.run(CategorySyncRequest(mode="apply", max_items=1), task="apply-category-optimizations")

    item = result["data"]["items"][0]
    assert item["apply_result"]["status"] == "applied"
    assert item["apply_result"]["metafields_updated"] == 2
    assert client.metafields_set_payloads


def test_service_emits_progress_events():
    llm = FakeLLM(
        '{"category_id":"gid://shopify/TaxonomyCategory/el-2-2-10","confidence":88,"risk_level":"low","needs_review":false,"reasoning":"Best fit for a portable speaker.","suggested_metafields":[]}'
    )
    events = []
    service = CategoryOptimizationService(shopify_client=FakeShopifyClient(), llm_client=llm, settings=type("S", (), {"deepseek_api_key": "x"})())
    service.run(
        CategorySyncRequest(mode="dry-run", max_items=1),
        task="diagnose-category-quality",
        progress_callback=events.append,
    )

    assert events[0]["stage"] == "start"
    assert events[1]["stage"] == "scan_progress"
    assert events[2]["stage"] == "products_loaded"
    assert events[3]["event"] == "item"
    assert events[4]["stage"] == "finished"


def test_service_can_run_single_product():
    llm = FakeLLM(
        '{"category_id":"gid://shopify/TaxonomyCategory/el-2-2-10","confidence":88,"risk_level":"low","needs_review":false,"reasoning":"Best fit for a portable speaker.","suggested_metafields":[]}'
    )
    service = CategoryOptimizationService(
        shopify_client=FakeShopifyClient(),
        llm_client=llm,
        settings=type("S", (), {"deepseek_api_key": "x"})(),
    )
    request = CategorySyncRequest(mode="dry-run", product_ids=["gid://shopify/Product/1"])

    item = service.run_single_product(request, product_id="gid://shopify/Product/1")

    assert item is not None
    assert item["product_id"] == "gid://shopify/Product/1"
    assert item["source"] == "deepseek"


def test_service_apply_continues_when_metafield_write_is_rejected():
    client = FakeShopifyClientWithMetafieldError()
    llm = FakeLLM(
        '{"category_id":"gid://shopify/TaxonomyCategory/el-2-2-10","confidence":90,"risk_level":"low","needs_review":false,"reasoning":"Best fit.","suggested_metafields":[{"key":"color-pattern","name":"Color","values":["Blue"]}]}'
    )
    service = CategoryOptimizationService(shopify_client=client, llm_client=llm, settings=type("S", (), {"deepseek_api_key": "x"})())

    result = service.run(CategorySyncRequest(mode="apply", max_items=1), task="apply-category-optimizations")

    item = result["data"]["items"][0]
    assert item["apply_result"]["status"] == "unchanged"
    assert item["apply_result"]["metafields_updated"] == 0
    assert item["apply_result"]["skipped_metafields"][0]["reason"] == "shopify_validation_error"


def test_service_can_rollback_applied_items():
    client = FakeShopifyClient()
    service = CategoryOptimizationService(shopify_client=client, llm_client=None, settings=type("S", (), {"deepseek_api_key": ""})())
    items = [
        {
            "product_id": "gid://shopify/Product/1",
            "title": "Portable Bluetooth Speaker",
            "rollback_snapshot": {
                "category": {
                    "id": "gid://shopify/TaxonomyCategory/el-2-2-10",
                    "name": "Speakers",
                    "full_name": "Electronics > Audio > Audio Components > Speakers",
                },
                "metafields": [
                    {
                        "namespace": "shopify",
                        "key": "color-pattern",
                        "type": "list.metaobject_reference",
                        "value": '["gid://shopify/Metaobject/1"]',
                    }
                ],
            },
            "apply_result": {
                "rollback_ready": True,
                "category_updated": True,
                "written_metafields": [
                    {
                        "namespace": "shopify",
                        "key": "color-pattern",
                        "type": "list.metaobject_reference",
                        "values": ["Blue"],
                    },
                    {
                        "namespace": "shopify",
                        "key": "material",
                        "type": "list.metaobject_reference",
                        "values": ["Plastic"],
                    },
                ],
            },
        }
    ]

    result = service.rollback_items(items)

    assert result["data"]["rolled_back_count"] == 1
    assert client.deleted_metafields_payloads
