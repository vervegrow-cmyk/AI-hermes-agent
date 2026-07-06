from unittest.mock import patch


def test_publish_vendor_catalog_runner_passes_arguments():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import publish_vendor_catalog

    with patch("src.modules.shopify_listing.runners.publish_vendor_catalog._ensure_collection") as ensure_collection:
        with patch("src.modules.shopify_listing.runners.publish_vendor_catalog._get_publication_map") as get_publication_map:
            with patch("src.modules.shopify_listing.runners.publish_vendor_catalog._get_vendor_products") as get_vendor_products:
                with patch("src.modules.shopify_listing.runners.publish_vendor_catalog._get_product_by_id") as get_product_by_id:
                    with patch("src.modules.shopify_listing.runners.publish_vendor_catalog.ShopifyAuthClient.from_settings") as from_settings:
                        ensure_collection.return_value = {"id": "col-1", "title": "NEW ARRIVALS", "handle": "new-arrivals"}
                        get_publication_map.return_value = {
                            "Online Store": {"id": "pub-online"},
                            "Shop": {"id": "pub-shop"},
                        }
                        get_vendor_products.return_value = [
                            {
                                "id": "gid://shopify/Product/1",
                                "title": "Big  Flower Duvet Cover Queen",
                                "vendor": "Doba",
                                "status": "ACTIVE",
                                "productType": "",
                                "tags": [],
                                "descriptionHtml": "",
                                "category": None,
                                "resourcePublicationsV2": {"edges": []},
                            }
                        ]
                        get_product_by_id.return_value = {
                            "id": "gid://shopify/Product/1",
                            "title": "Big  Flower Duvet Cover Queen",
                            "vendor": "Doba",
                            "status": "ACTIVE",
                            "productType": "Duvet Covers",
                            "tags": ["doba-import", "category:duvet-covers"],
                            "descriptionHtml": "",
                            "category": {"id": "gid://shopify/TaxonomyCategory/hg-15-1-5", "fullName": "Duvet Covers"},
                            "resourcePublicationsV2": {
                                "edges": [
                                    {"node": {"publication": {"name": "Online Store"}}},
                                    {"node": {"publication": {"name": "Shop"}}},
                                ]
                            },
                        }

                        graphql_calls = []

                        def graphql_side_effect(query, variables=None):
                            graphql_calls.append((query, variables))
                            if "SearchTaxonomyCategories" in query:
                                return {
                                    "taxonomy": {
                                        "categories": {
                                            "nodes": [
                                                {
                                                    "id": "gid://shopify/TaxonomyCategory/hg-15-1-5",
                                                    "fullName": "Home & Garden > Bedding > Duvet Covers",
                                                    "isLeaf": True,
                                                    "isArchived": False,
                                                    "name": "Duvet Covers",
                                                }
                                            ]
                                        }
                                    }
                                }
                            if "UpdateProductFields" in query:
                                return {
                                    "productUpdate": {
                                        "product": {
                                            "id": "gid://shopify/Product/1",
                                            "productType": "Duvet Covers",
                                            "tags": ["doba-import", "category:duvet-covers"],
                                            "category": {
                                                "id": "gid://shopify/TaxonomyCategory/hg-15-1-5",
                                                "fullName": "Duvet Covers",
                                            },
                                        },
                                        "userErrors": [],
                                    }
                                }
                            if "AddProductsToCollection" in query:
                                return {"collectionAddProducts": {"collection": {"id": "col-1", "title": "NEW ARRIVALS"}, "userErrors": []}}
                            if "metafieldsSet" in query:
                                return {"metafieldsSet": {"metafields": [], "userErrors": []}}
                            return {"publishablePublish": {"userErrors": []}}

                        from_settings.return_value.graphql.side_effect = graphql_side_effect

                        result = publish_vendor_catalog(
                            vendor="Doba",
                            publication_names=["Online Store", "Shop"],
                            report_path="docs/audits/test-vendor-report.json",
                        )

    assert result["vendor"] == "Doba"
    assert result["summary"]["total_products"] == 1
    assert result["summary"]["publish_requested_ok"] == 1
    assert result["summary"]["source_fields_updated_ok"] == 1
    assert result["summary"]["added_to_new_arrivals_count"] == 1
    assert any("metafieldsSet" in query for query, _ in graphql_calls)


def test_publish_vendor_catalog_limits_to_one_product_and_reports_progress(tmp_path):
    from src.modules.shopify_listing.runners.publish_vendor_catalog import publish_vendor_catalog

    report_path = tmp_path / "vendor-report.json"
    with patch("src.modules.shopify_listing.runners.publish_vendor_catalog._ensure_collection") as ensure_collection:
        with patch("src.modules.shopify_listing.runners.publish_vendor_catalog._get_publication_map") as get_publication_map:
            with patch("src.modules.shopify_listing.runners.publish_vendor_catalog._get_vendor_products") as get_vendor_products:
                with patch("src.modules.shopify_listing.runners.publish_vendor_catalog._get_product_by_id") as get_product_by_id:
                    with patch("src.modules.shopify_listing.runners.publish_vendor_catalog.ShopifyAuthClient.from_settings") as from_settings:
                        ensure_collection.return_value = {"id": "col-1", "title": "NEW ARRIVALS", "handle": "new-arrivals"}
                        get_publication_map.return_value = {"Online Store": {"id": "pub-online"}}
                        get_vendor_products.return_value = [
                            {
                                "id": "gid://shopify/Product/1",
                                "title": "Big  Flower Duvet Cover Queen",
                                "vendor": "Doba",
                                "status": "ACTIVE",
                                "productType": "",
                                "tags": [],
                                "descriptionHtml": "",
                                "category": None,
                                "resourcePublicationsV2": {"edges": []},
                            },
                            {
                                "id": "gid://shopify/Product/2",
                                "title": "Garden Dining Set Black PE Rattan Large Foldable",
                                "vendor": "Doba",
                                "status": "ACTIVE",
                                "productType": "",
                                "tags": [],
                                "descriptionHtml": "",
                                "category": None,
                                "resourcePublicationsV2": {"edges": []},
                            },
                        ]
                        get_product_by_id.return_value = {
                            "id": "gid://shopify/Product/1",
                            "title": "Big  Flower Duvet Cover Queen",
                            "vendor": "Doba",
                            "status": "ACTIVE",
                            "productType": "Duvet Covers",
                            "tags": ["doba-import", "category:duvet-covers"],
                            "descriptionHtml": "",
                            "category": {"id": "gid://shopify/TaxonomyCategory/hg-15-1-5", "fullName": "Duvet Covers"},
                            "resourcePublicationsV2": {
                                "edges": [
                                    {"node": {"publication": {"name": "Online Store"}}},
                                ]
                            },
                        }

                        def graphql_side_effect(query, variables=None):
                            if "SearchTaxonomyCategories" in query:
                                return {
                                    "taxonomy": {
                                        "categories": {
                                            "nodes": [
                                                {
                                                    "id": "gid://shopify/TaxonomyCategory/hg-15-1-5",
                                                    "fullName": "Home & Garden > Bedding > Duvet Covers",
                                                    "isLeaf": True,
                                                    "isArchived": False,
                                                    "name": "Duvet Covers",
                                                }
                                            ]
                                        }
                                    }
                                }
                            if "UpdateProductFields" in query:
                                return {
                                    "productUpdate": {
                                        "product": {
                                            "id": "gid://shopify/Product/1",
                                            "productType": "Duvet Covers",
                                            "tags": ["doba-import", "category:duvet-covers"],
                                            "category": {
                                                "id": "gid://shopify/TaxonomyCategory/hg-15-1-5",
                                                "fullName": "Duvet Covers",
                                            },
                                        },
                                        "userErrors": [],
                                    }
                                }
                            if "AddProductsToCollection" in query:
                                return {"collectionAddProducts": {"collection": {"id": "col-1", "title": "NEW ARRIVALS"}, "userErrors": []}}
                            if "metafieldsSet" in query:
                                return {"metafieldsSet": {"metafields": [], "userErrors": []}}
                            return {"publishablePublish": {"userErrors": []}}

                        from_settings.return_value.graphql.side_effect = graphql_side_effect

                        result = publish_vendor_catalog(
                            vendor="Doba",
                            publication_names=["Online Store"],
                            report_path=str(report_path),
                            max_products=1,
                        )

    assert len(result["results"]) == 1
    assert result["progress"]["selected_for_run"] == 1
    assert result["progress"]["processed_this_run"] == 1
    assert result["progress"]["remaining_after_run"] == 1
    assert result["results"][0]["progress"]["current_in_run"] == 1
    assert result["results"][0]["progress"]["remaining_in_run"] == 0


def test_publish_vendor_catalog_resumes_from_existing_report(tmp_path):
    from src.modules.shopify_listing.runners.publish_vendor_catalog import publish_vendor_catalog

    report_path = tmp_path / "resume-report.json"
    report_path.write_text(
        """
{
  "vendor": "Doba",
  "results": [
    {
      "id": "gid://shopify/Product/1",
      "title": "already processed"
    }
  ]
}
        """.strip(),
        encoding="utf-8",
    )

    with patch("src.modules.shopify_listing.runners.publish_vendor_catalog._ensure_collection") as ensure_collection:
        with patch("src.modules.shopify_listing.runners.publish_vendor_catalog._get_publication_map") as get_publication_map:
            with patch("src.modules.shopify_listing.runners.publish_vendor_catalog._get_vendor_products") as get_vendor_products:
                with patch("src.modules.shopify_listing.runners.publish_vendor_catalog._get_product_by_id") as get_product_by_id:
                    with patch("src.modules.shopify_listing.runners.publish_vendor_catalog.ShopifyAuthClient.from_settings") as from_settings:
                        ensure_collection.return_value = {"id": "col-1", "title": "NEW ARRIVALS", "handle": "new-arrivals"}
                        get_publication_map.return_value = {"Online Store": {"id": "pub-online"}}
                        get_vendor_products.return_value = [
                            {
                                "id": "gid://shopify/Product/1",
                                "title": "Big  Flower Duvet Cover Queen",
                                "vendor": "Doba",
                                "status": "ACTIVE",
                                "productType": "",
                                "tags": [],
                                "descriptionHtml": "",
                                "category": None,
                                "resourcePublicationsV2": {"edges": []},
                            },
                            {
                                "id": "gid://shopify/Product/2",
                                "title": "Garden Dining Set Black PE Rattan Large Foldable",
                                "vendor": "Doba",
                                "status": "ACTIVE",
                                "productType": "",
                                "tags": [],
                                "descriptionHtml": "",
                                "category": None,
                                "resourcePublicationsV2": {"edges": []},
                            },
                        ]
                        get_product_by_id.return_value = {
                            "id": "gid://shopify/Product/2",
                            "title": "Garden Dining Set Black PE Rattan Large Foldable",
                            "vendor": "Doba",
                            "status": "ACTIVE",
                            "productType": "Outdoor Dining Sets",
                            "tags": ["doba-import", "category:outdoor-dining-sets"],
                            "descriptionHtml": "",
                            "category": {"id": "gid://shopify/TaxonomyCategory/fr-15-2", "fullName": "Outdoor Dining Sets"},
                            "resourcePublicationsV2": {
                                "edges": [
                                    {"node": {"publication": {"name": "Online Store"}}},
                                ]
                            },
                        }

                        def graphql_side_effect(query, variables=None):
                            if "UpdateProductFields" in query:
                                return {
                                    "productUpdate": {
                                        "product": {
                                            "id": "gid://shopify/Product/2",
                                            "productType": "Outdoor Dining Sets",
                                            "tags": ["doba-import", "category:outdoor-dining-sets"],
                                            "category": {
                                                "id": "gid://shopify/TaxonomyCategory/fr-15-2",
                                                "fullName": "Outdoor Dining Sets",
                                            },
                                        },
                                        "userErrors": [],
                                    }
                                }
                            if "AddProductsToCollection" in query:
                                return {"collectionAddProducts": {"collection": {"id": "col-1", "title": "NEW ARRIVALS"}, "userErrors": []}}
                            if "metafieldsSet" in query:
                                return {"metafieldsSet": {"metafields": [], "userErrors": []}}
                            return {"publishablePublish": {"userErrors": []}}

                        from_settings.return_value.graphql.side_effect = graphql_side_effect

                        result = publish_vendor_catalog(
                            vendor="Doba",
                            publication_names=["Online Store"],
                            report_path=str(report_path),
                            max_products=1,
                            resume_from_report=True,
                        )

    assert [item["id"] for item in result["results"]] == [
        "gid://shopify/Product/1",
        "gid://shopify/Product/2",
    ]
    assert result["progress"]["processed_before_run"] == 1
    assert result["progress"]["processed_this_run"] == 1
    assert result["progress"]["remaining_after_run"] == 0


def test_resolve_category_uses_keyword_rules():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import _resolve_category

    assert _resolve_category("Insulated Lunch Bag for Men & Women - Olive Green Thermal Meal Tote")
    assert _resolve_category({"title": "3pcs Boho Tribal Duvet Cover Set, Colorful Red & Turquoise Ethnic Print Bedding"})
    assert _resolve_category({"title": 'Double Layer Clear Makeup Bag with Colorful Chenille "STUFF" Letters'})


def test_publish_vendor_catalog_stops_on_first_failure():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import publish_vendor_catalog

    with patch("src.modules.shopify_listing.runners.publish_vendor_catalog._ensure_collection") as ensure_collection:
        with patch("src.modules.shopify_listing.runners.publish_vendor_catalog._add_product_to_collection") as add_product_to_collection:
            with patch("src.modules.shopify_listing.runners.publish_vendor_catalog._get_publication_map") as get_publication_map:
                with patch("src.modules.shopify_listing.runners.publish_vendor_catalog._get_vendor_products") as get_vendor_products:
                    with patch("src.modules.shopify_listing.runners.publish_vendor_catalog._get_product_by_id") as get_product_by_id:
                        with patch("src.modules.shopify_listing.runners.publish_vendor_catalog.ShopifyAuthClient.from_settings") as from_settings:
                            ensure_collection.return_value = {"id": "col-1", "title": "NEW ARRIVALS", "handle": "new-arrivals"}
                            add_product_to_collection.return_value = None
                            get_publication_map.return_value = {
                                "Online Store": {"id": "pub-online"},
                            }
                            get_vendor_products.return_value = [
                                {
                                    "id": "gid://shopify/Product/1",
                                    "title": "Big  Flower Duvet Cover Queen",
                                    "vendor": "Doba",
                                    "status": "ACTIVE",
                                    "productType": "",
                                    "tags": [],
                                    "descriptionHtml": "",
                                    "category": None,
                                    "resourcePublicationsV2": {"edges": []},
                                },
                                {
                                    "id": "gid://shopify/Product/2",
                                    "title": "Unknown Product B",
                                    "vendor": "Doba",
                                    "status": "ACTIVE",
                                    "productType": "",
                                    "tags": [],
                                    "descriptionHtml": "",
                                    "category": None,
                                    "resourcePublicationsV2": {"edges": []},
                                },
                            ]
                            get_product_by_id.return_value = {
                                "id": "gid://shopify/Product/1",
                                "title": "Big  Flower Duvet Cover Queen",
                                "vendor": "Doba",
                                "status": "ACTIVE",
                                "productType": "",
                                "tags": [],
                                "descriptionHtml": "",
                                "category": None,
                                "resourcePublicationsV2": {"edges": []},
                            }

                            def graphql_side_effect(query, variables=None):
                                if "SearchTaxonomyCategories" in query:
                                    return {
                                        "taxonomy": {
                                            "categories": {
                                                "nodes": [
                                                    {
                                                        "id": "gid://shopify/TaxonomyCategory/hg-15-1-5",
                                                        "fullName": "Home & Garden > Bedding > Duvet Covers",
                                                        "isLeaf": True,
                                                        "isArchived": False,
                                                        "name": "Duvet Covers",
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                if "UpdateProductFields" in query:
                                    return {
                                        "productUpdate": {
                                            "product": {
                                                "id": "gid://shopify/Product/1",
                                                "productType": "Duvet Covers",
                                                "tags": ["doba-import"],
                                                "category": {
                                                    "id": "gid://shopify/TaxonomyCategory/hg-15-1-5",
                                                    "fullName": "Duvet Covers",
                                                },
                                            },
                                            "userErrors": [],
                                        }
                                    }
                                if "metafieldsSet" in query:
                                    return {"metafieldsSet": {"metafields": [], "userErrors": []}}
                                return {
                                    "publishablePublish": {
                                        "userErrors": [{"field": ["id"], "message": "publish failed"}]
                                    }
                                }

                            from_settings.return_value.graphql.side_effect = graphql_side_effect

                            result = publish_vendor_catalog(
                                vendor="Doba",
                                publication_names=["Online Store"],
                                report_path="docs/audits/test-vendor-stop-report.json",
                                stop_on_failure=True,
                            )

    assert result["stopped_early"] is True
    assert result["summary"]["total_products"] == 1
    assert result["summary"]["publish_failed"] == 1


def test_resolve_category_uses_product_context():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import _resolve_category

    resolution = _resolve_category(
        {
            "title": "Indoor Digital Signal Receiver",
            "productType": "TV Accessories",
            "tags": ["living-room", "antenna"],
            "descriptionHtml": "<p>4K HDTV antenna for indoor use</p>",
        }
    )

    assert resolution is not None
    assert resolution.category_label == "tv-antennas"
    assert resolution.product_type == "TV Antennas"


def test_get_product_by_id_returns_empty_when_shopify_returns_no_match():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import _get_product_by_id

    class _Client:
        def __init__(self):
            self.calls = 0

        def graphql(self, query, variables=None):
            self.calls += 1
            if self.calls == 1:
                return {"product": None}
            return {"products": {"edges": []}}

    result = _get_product_by_id(_Client(), "gid://shopify/Product/999")

    assert result == {}


def test_garden_dining_set_no_longer_maps_to_porch_swing_cover():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import _resolve_category

    resolution = _resolve_category({"title": "Garden Dining Set Black PE Rattan Large Foldable"})

    assert resolution is not None
    assert resolution.category_label == "outdoor-dining-sets"
    assert resolution.product_type == "Outdoor Dining Sets"


def test_extract_attribute_suggestions_includes_color_material_and_propulsion():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import _extract_attribute_suggestions

    suggestions = _extract_attribute_suggestions(
        {
            "title": "Black Push Lawn Sweeper with Steel Frame",
            "descriptionHtml": "<p>Steel and rubber build with AC power option</p>",
            "productType": "",
            "tags": [],
        },
        None,
    )

    assert "Black" in suggestions["color"]
    assert "Steel" in suggestions["material"]
    assert "Push" in suggestions["propulsion_type"]


def test_extract_attribute_suggestions_does_not_false_positive_red_from_outdoor():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import _extract_attribute_suggestions

    suggestions = _extract_attribute_suggestions(
        {
            "title": "Outdoor Bar Table Natural Bamboo",
            "descriptionHtml": "<p>Natural bamboo patio table</p>",
            "productType": "",
            "tags": [],
        },
        None,
    )

    assert "Red" not in suggestions.get("color", [])


def test_category_search_blob_ignores_existing_wrong_category_tags():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import _resolve_category

    resolution = _resolve_category(
        {
            "title": "Garden Dining Set Black and Cream White",
            "descriptionHtml": "",
            "productType": "Porch Swing Covers",
            "tags": ["category:porch-swing-covers", "patio", "cover"],
        }
    )

    assert resolution is not None
    assert resolution.category_label == "outdoor-dining-sets"


def test_hydrate_resolution_keeps_explicit_category_id():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import CategoryResolution, _hydrate_resolution

    class _Client:
        def graphql(self, query, variables=None):
            raise AssertionError("taxonomy search should not run when category_id is already explicit")

    resolution = CategoryResolution(
        category_id="gid://shopify/TaxonomyCategory/hg-12-2-9-2",
        product_type="Porch Swing Covers",
        category_label="porch-swing-covers",
        tags=("outdoor-living",),
        matched_rule="exact:test",
        taxonomy_search="porch swing covers",
        taxonomy_path_tokens=("porch swing covers",),
        allow_category_update=True,
    )

    hydrated = _hydrate_resolution(_Client(), resolution, {})

    assert hydrated.category_id == "gid://shopify/TaxonomyCategory/hg-12-2-9-2"


def test_is_missing_resource_error_detects_shopify_missing_product_shapes():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import _is_missing_resource_error

    assert _is_missing_resource_error("Shopify GraphQL request failed with 500: Resource does not exist")
    assert _is_missing_resource_error([{"message": "Owner does not exist."}])
    assert _is_missing_resource_error({"field": ["id"], "message": "Product does not exist"})


def test_resolve_category_uses_normalized_override_title():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import _resolve_category

    resolution = _resolve_category(
        {"title": "Compact Under-Desk Elliptical - Quiet Mini Pedal Exerciser with Adjustable Speed and LED Display"}
    )

    assert resolution is not None
    assert resolution.category_label == "exercise-ellipticals"
    assert resolution.product_type == "Under-Desk Ellipticals"


def test_resolve_category_matches_new_fill_in_rules():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import _resolve_category

    resolution = _resolve_category(
        {"title": "10ft Offset Hanging Outdoor Patio Umbrella with Base Stand Rotate and Tilt"}
    )

    assert resolution is not None
    assert resolution.category_label == "patio-umbrellas"


def test_resolve_category_matches_garden_stool_rule():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import _resolve_category

    resolution = _resolve_category({"title": "Garden Stool Set of 4 Black"})

    assert resolution is not None
    assert resolution.category_label == "garden-stools"
    assert resolution.product_type == "Garden Stools"


def test_resolve_category_prefers_hand_sanitizers_over_crossbody_bags():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import _resolve_category

    resolution = _resolve_category(
        {"title": "Portable Pocket Hand Sanitizer Spray 38ML, Moisturizing Travel Hand Sanitizer"}
    )

    assert resolution is not None
    assert resolution.category_label == "hand-sanitizers"
    assert resolution.product_type == "Hand Sanitizers"


def test_resolve_category_prefers_duffel_bags_over_generic_bags():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import _resolve_category

    resolution = _resolve_category(
        {"title": "Women's Lightweight Nylon Weekender Duffel Bag with Side Pocket"}
    )

    assert resolution is not None
    assert resolution.category_label == "duffel-bags"
    assert resolution.product_type == "Duffel Bags"


def test_resolve_category_prefers_pet_bathing_supplies_over_dog_supplies():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import _resolve_category

    resolution = _resolve_category({"title": "Portable Dog Bathtub"})

    assert resolution is not None
    assert resolution.category_label == "pet-bathing-supplies"
    assert resolution.product_type == "Pet Grooming Supplies"


def test_resolve_category_prefers_teapots_over_generic_drinkware():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import _resolve_category

    resolution = _resolve_category({"title": "Heat-resistant glass teapot, magnetic switch, Gunmetal Black 800mL"})

    assert resolution is not None
    assert resolution.category_label == "teapots"
    assert resolution.product_type == "Teapots"


def test_resolve_category_matches_pergola_rule():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import _resolve_category

    resolution = _resolve_category({"title": "3*9m 5-Sided Iron PE Cloth Spiral Pipe Pergola"})

    assert resolution is not None
    assert resolution.category_label == "pergolas"
    assert resolution.product_type == "Pergola"


def test_resolve_category_matches_zero_gravity_lounge_chairs_rule():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import _resolve_category

    resolution = _resolve_category(
        {"title": "Set of 2 Zero Gravity Lounge Chairs,Outdoor Patio Folding Recliners for Pool Beach"}
    )

    assert resolution is not None
    assert resolution.category_label == "outdoor-lounge-chairs"
    assert resolution.product_type == "Outdoor Lounge Chairs"


def test_resolve_category_keeps_party_tents_product_type():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import _resolve_category

    resolution = _resolve_category(
        {"title": "10'x20' Outdoor Party Tent with 6 Removable Sidewalls, Waterproof Canopy Patio Wedding Gazebo"}
    )

    assert resolution is not None
    assert resolution.category_label == "outdoor-party-tents"
    assert resolution.product_type == "Tents"


def test_resolve_category_keeps_grass_trimmer_product_type():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import _resolve_category

    resolution = _resolve_category(
        {"title": "3 in 1 Electric Cordless Grass Wacker Battery Powered Grass Trimmer With Wheels"}
    )

    assert resolution is not None
    assert resolution.category_label == "lawn-mowers-trimmers"
    assert resolution.product_type == "Grass Trimmers"


def test_parse_deepseek_fallback_response_normalizes_payload():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import _parse_deepseek_fallback_response

    suggestion = _parse_deepseek_fallback_response(
        '{"product_type":"Patio Umbrellas","category_label":"Patio Umbrellas","taxonomy_search":"patio umbrellas","path_tokens":["umbrellas","patio"],"tags":["Outdoor Living","Umbrella"],"attributes":{"color":["Beige"]},"confidence":0.91,"reason":"Title clearly describes a patio umbrella."}'
    )

    assert suggestion.category_label == "patio-umbrellas"
    assert suggestion.tags == ("outdoor-living", "umbrella")
    assert suggestion.confidence == 0.91


def test_publish_vendor_catalog_uses_llm_fallback_for_no_match():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import publish_vendor_catalog

    class FakeLLMClient:
        @staticmethod
        def generate(prompt, **kwargs):
            return {
                "text": '{"product_type":"Patio Umbrellas","category_label":"patio-umbrellas","taxonomy_search":"patio umbrellas","path_tokens":["umbrellas","patio"],"tags":["outdoor-living","umbrella"],"attributes":{"color":["Beige"]},"confidence":0.88,"reason":"Title identifies a patio umbrella."}',
                "raw": {},
            }

    with patch("src.modules.shopify_listing.runners.publish_vendor_catalog._ensure_collection") as ensure_collection:
        with patch("src.modules.shopify_listing.runners.publish_vendor_catalog._add_product_to_collection") as add_product_to_collection:
            with patch("src.modules.shopify_listing.runners.publish_vendor_catalog._get_deepseek_client", lambda: (FakeLLMClient(), "enabled:test")):
                with patch("src.modules.shopify_listing.runners.publish_vendor_catalog._get_publication_map") as get_publication_map:
                    with patch("src.modules.shopify_listing.runners.publish_vendor_catalog._get_vendor_products") as get_vendor_products:
                        with patch("src.modules.shopify_listing.runners.publish_vendor_catalog._get_product_by_id") as get_product_by_id:
                            with patch("src.modules.shopify_listing.runners.publish_vendor_catalog.ShopifyAuthClient.from_settings") as from_settings:
                                ensure_collection.return_value = {"id": "col-1", "title": "NEW ARRIVALS", "handle": "new-arrivals"}
                                add_product_to_collection.return_value = None
                                get_publication_map.return_value = {"Online Store": {"id": "pub-online"}}
                                get_vendor_products.return_value = [
                                    {
                                        "id": "gid://shopify/Product/1",
                                        "title": "Mystery Shade Pro Max with Rotating Stand",
                                        "vendor": "Doba",
                                        "status": "ACTIVE",
                                        "productType": "",
                                        "tags": [],
                                        "descriptionHtml": "",
                                        "category": None,
                                        "resourcePublicationsV2": {"edges": []},
                                    }
                                ]
                                get_product_by_id.return_value = {
                                    "id": "gid://shopify/Product/1",
                                    "title": "Mystery Shade Pro Max with Rotating Stand",
                                    "vendor": "Doba",
                                    "status": "ACTIVE",
                                    "productType": "Patio Umbrellas",
                                    "tags": ["category:patio-umbrellas"],
                                    "descriptionHtml": "",
                                    "category": {"id": "gid://shopify/TaxonomyCategory/hg-test", "fullName": "Patio Umbrellas"},
                                    "resourcePublicationsV2": {"edges": [{"node": {"publication": {"name": "Online Store"}}}]},
                                }

                                def graphql_side_effect(query, variables=None):
                                    if "SearchTaxonomyCategories" in query:
                                        return {
                                            "taxonomy": {
                                                "categories": {
                                                    "nodes": [
                                                        {
                                                            "id": "gid://shopify/TaxonomyCategory/hg-test",
                                                            "fullName": "Home & Garden > Lawn & Garden > Outdoor Living > Patio Umbrellas",
                                                            "isLeaf": True,
                                                            "isArchived": False,
                                                            "name": "Patio Umbrellas",
                                                        }
                                                    ]
                                                }
                                            }
                                        }
                                    if "UpdateProductFields" in query:
                                        return {
                                            "productUpdate": {
                                                "product": {
                                                    "id": "gid://shopify/Product/1",
                                                    "productType": "Patio Umbrellas",
                                                    "tags": ["category:patio-umbrellas"],
                                                    "category": {"id": "gid://shopify/TaxonomyCategory/hg-test", "fullName": "Patio Umbrellas"},
                                                },
                                                "userErrors": [],
                                            }
                                        }
                                    if "metafieldsSet" in query:
                                        return {"metafieldsSet": {"metafields": [], "userErrors": []}}
                                    return {"publishablePublish": {"userErrors": []}}

                                from_settings.return_value.graphql.side_effect = graphql_side_effect

                                result = publish_vendor_catalog(
                                    vendor="Doba",
                                    publication_names=["Online Store"],
                                    report_path="docs/audits/test-vendor-llm-report.json",
                                )

    assert result["summary"]["llm_suggestions_generated"] == 1
    assert result["results"][0]["category_rule"] == "llm:patio-umbrellas"
    assert result["results"][0]["category_action"] == "category_applied"


def test_hydrate_resolution_keeps_category_update_enabled_when_taxonomy_is_found():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import CategoryResolution, _hydrate_resolution

    class _Client:
        def graphql(self, query, variables=None):
            return {
                "taxonomy": {
                    "categories": {
                        "nodes": [
                            {
                                "id": "gid://shopify/TaxonomyCategory/bad-match",
                                "fullName": "Vehicles & Parts > Vehicle Parts & Accessories > Motor Vehicle Parts > Motor Vehicle Frame & Body Parts > Side Panels",
                                "isLeaf": True,
                                "isArchived": False,
                                "name": "Side Panels",
                            }
                        ]
                    }
                }
            }

    resolution = CategoryResolution(
        category_id=None,
        product_type="Side Awnings",
        category_label="side-awnings",
        tags=("outdoor-living", "awning"),
        matched_rule="keyword:side-awnings",
        taxonomy_search="side awnings",
        taxonomy_path_tokens=("awnings",),
        allow_category_update=True,
    )

    hydrated = _hydrate_resolution(_Client(), resolution, {})

    assert hydrated.category_id == "gid://shopify/TaxonomyCategory/bad-match"
    assert hydrated.allow_category_update is True


def test_should_apply_llm_suggestion_uses_llm_when_rule_cannot_write():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import (
        CategoryResolution,
        LLMFallbackSuggestion,
        _should_apply_llm_suggestion,
    )

    resolution = CategoryResolution(
        category_id="gid://shopify/TaxonomyCategory/bad-match",
        product_type="Side Awnings",
        category_label="side-awnings",
        tags=("outdoor-living", "awning"),
        matched_rule="keyword:side-awnings",
        taxonomy_search="side awnings",
        taxonomy_path_tokens=("awnings",),
        allow_category_update=False,
    )
    llm_suggestion = LLMFallbackSuggestion(
        product_type="Patio Privacy Screens",
        category_label="patio-privacy-screens",
        taxonomy_search="patio privacy screens",
        tags=("outdoor-living", "privacy-screen"),
        path_tokens=("privacy", "screen"),
        attributes={},
        confidence=0.9,
        reason="Context describes an outdoor screen.",
        category_id="gid://shopify/TaxonomyCategory/good-match",
    )

    assert _should_apply_llm_suggestion(resolution, llm_suggestion) is True


def test_should_apply_llm_suggestion_for_generic_rule_override():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import (
        CategoryResolution,
        LLMFallbackSuggestion,
        _should_apply_llm_suggestion,
    )

    resolution = CategoryResolution(
        category_id="gid://shopify/TaxonomyCategory/lb-6",
        product_type="Bags",
        category_label="bags",
        tags=("fashion", "bag"),
        matched_rule="keyword:bags",
        taxonomy_search="bags",
        taxonomy_path_tokens=("bags",),
        allow_category_update=True,
    )
    llm_suggestion = LLMFallbackSuggestion(
        product_type="Duffel Bags",
        category_label="duffel-bags",
        taxonomy_search="duffel bags",
        tags=("travel", "bag", "duffel"),
        path_tokens=("duffel", "bags"),
        attributes={},
        confidence=0.95,
        reason="Title clearly indicates a duffel bag.",
        category_id="gid://shopify/TaxonomyCategory/lb-6",
    )

    assert _should_apply_llm_suggestion(resolution, llm_suggestion) is True


def test_should_apply_llm_suggestion_when_rule_cannot_write_but_llm_has_category_id():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import (
        CategoryResolution,
        LLMFallbackSuggestion,
        _should_apply_llm_suggestion,
    )

    resolution = CategoryResolution(
        category_id="gid://shopify/TaxonomyCategory/rule-match",
        product_type="Doors",
        category_label="doors",
        tags=("home-improvement", "door"),
        matched_rule="keyword:doors",
        taxonomy_search="doors",
        taxonomy_path_tokens=("doors",),
        allow_category_update=False,
    )
    llm_suggestion = LLMFallbackSuggestion(
        product_type="Door Fly Screen",
        category_label="door-fly-screens",
        taxonomy_search="door fly screen",
        tags=("door", "fly-screen"),
        path_tokens=("doors", "fly", "screens"),
        attributes={},
        confidence=0.95,
        reason="Specific fly screen product with matching taxonomy.",
        category_id="gid://shopify/TaxonomyCategory/vp-1-4-9-2",
    )

    assert _should_apply_llm_suggestion(resolution, llm_suggestion) is True


def test_should_clear_existing_category_is_disabled_without_safety_gate():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import (
        CategoryResolution,
        _should_clear_existing_category,
    )

    resolution = CategoryResolution(
        category_id="gid://shopify/TaxonomyCategory/bad-match",
        product_type="Garden Chair Sets",
        category_label="garden-chair-sets",
        tags=("outdoor-living", "patio", "chairs"),
        matched_rule="keyword:garden-chair-sets",
        taxonomy_search="patio chairs",
        taxonomy_path_tokens=("chairs",),
        allow_category_update=False,
    )

    should_clear = _should_clear_existing_category(
        existing_category={
            "id": "gid://shopify/TaxonomyCategory/hg-9-1-11",
            "fullName": "Home & Garden > Household Appliances > Climate Control Appliances > Patio Heaters",
        },
        resolution=resolution,
    )

    assert should_clear is False


def test_should_not_clear_existing_category_for_tv_antenna_conflict_without_gate():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import (
        CategoryResolution,
        _should_clear_existing_category,
    )

    resolution = CategoryResolution(
        category_id=None,
        product_type="TV Antennas",
        category_label="tv-antennas",
        tags=("electronics", "tv", "antenna"),
        matched_rule="exact:tv-antenna",
        taxonomy_search="tv antennas",
        taxonomy_path_tokens=("tv", "antenna"),
        allow_category_update=False,
    )

    should_clear = _should_clear_existing_category(
        existing_category={
            "id": "gid://shopify/TaxonomyCategory/el-7-6-1",
            "fullName": "Electronics > Electronics Accessories > Cable Management > Cable Clips",
        },
        resolution=resolution,
    )

    assert should_clear is False


def test_publish_vendor_catalog_uses_llm_for_source_fields_when_taxonomy_missing():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import publish_vendor_catalog

    class FakeLLMClient:
        @staticmethod
        def generate(prompt, **kwargs):
            return {
                "text": '{"product_type":"Waste Baskets","category_label":"waste-baskets","taxonomy_search":"waste baskets","path_tokens":["trash","waste"],"tags":["bathroom","trash-can"],"attributes":{"color":["White"]},"confidence":0.58,"reason":"Title clearly indicates a small waste basket."}',
                "raw": {},
            }

    with patch("src.modules.shopify_listing.runners.publish_vendor_catalog._ensure_collection") as ensure_collection:
        with patch("src.modules.shopify_listing.runners.publish_vendor_catalog._add_product_to_collection") as add_product_to_collection:
            with patch("src.modules.shopify_listing.runners.publish_vendor_catalog._get_deepseek_client", lambda: (FakeLLMClient(), "enabled:test")):
                with patch("src.modules.shopify_listing.runners.publish_vendor_catalog._get_publication_map") as get_publication_map:
                    with patch("src.modules.shopify_listing.runners.publish_vendor_catalog._get_vendor_products") as get_vendor_products:
                        with patch("src.modules.shopify_listing.runners.publish_vendor_catalog._get_product_by_id") as get_product_by_id:
                            with patch("src.modules.shopify_listing.runners.publish_vendor_catalog.ShopifyAuthClient.from_settings") as from_settings:
                                ensure_collection.return_value = {"id": "col-1", "title": "NEW ARRIVALS", "handle": "new-arrivals"}
                                add_product_to_collection.return_value = None
                                get_publication_map.return_value = {"Online Store": {"id": "pub-online"}}
                                get_vendor_products.return_value = [
                                    {
                                        "id": "gid://shopify/Product/1",
                                        "title": "2.5gal Waste Basket White Compact Plastic Trash Can for Bathroom or Kitchen",
                                        "vendor": "Doba",
                                        "status": "ACTIVE",
                                        "productType": "",
                                        "tags": [],
                                        "descriptionHtml": "",
                                        "category": None,
                                        "resourcePublicationsV2": {"edges": []},
                                    }
                                ]
                                get_product_by_id.return_value = {
                                    "id": "gid://shopify/Product/1",
                                    "title": "2.5gal Waste Basket White Compact Plastic Trash Can for Bathroom or Kitchen",
                                    "vendor": "Doba",
                                    "status": "ACTIVE",
                                    "productType": "Waste Baskets",
                                    "tags": ["category:waste-baskets", "bathroom", "trash-can"],
                                    "descriptionHtml": "",
                                    "category": None,
                                    "resourcePublicationsV2": {"edges": [{"node": {"publication": {"name": "Online Store"}}}]},
                                }

                                def graphql_side_effect(query, variables=None):
                                    if "SearchTaxonomyCategories" in query:
                                        return {"taxonomy": {"categories": {"nodes": []}}}
                                    if "UpdateProductFields" in query:
                                        return {
                                            "productUpdate": {
                                                "product": {
                                                    "id": "gid://shopify/Product/1",
                                                    "productType": "Waste Baskets",
                                                    "tags": ["category:waste-baskets", "bathroom", "trash-can"],
                                                    "category": None,
                                                },
                                                "userErrors": [],
                                            }
                                        }
                                    if "metafieldsSet" in query:
                                        return {"metafieldsSet": {"metafields": [], "userErrors": []}}
                                    return {"publishablePublish": {"userErrors": []}}

                                from_settings.return_value.graphql.side_effect = graphql_side_effect

                                result = publish_vendor_catalog(
                                    vendor="Doba",
                                    publication_names=["Online Store"],
                                    report_path="docs/audits/test-vendor-llm-source-fields-report.json",
                                )

    assert result["results"][0]["source_fields_after"]["productType"] == "Waste Baskets"
    assert result["results"][0]["category_action"] == "llm_suggested_review"
    assert result["summary"]["llm_suggestions_generated"] == 1


def test_search_taxonomy_category_id_rejects_irrelevant_results():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import _search_taxonomy_category_id

    class _Client:
        def graphql(self, query, variables=None):
            return {
                "taxonomy": {
                    "categories": {
                        "nodes": [
                            {
                                "id": "gid://shopify/TaxonomyCategory/el-7-6-1",
                                "fullName": "Electronics > Electronics Accessories > Cable Management > Cable Clips",
                                "isLeaf": True,
                                "isArchived": False,
                                "name": "Cable Clips",
                            }
                        ]
                    }
                }
            }

    result = _search_taxonomy_category_id(
        client=_Client(),
        category_label="tv-antennas",
        search="tv antennas",
        path_tokens=("tv", "antenna"),
    )

    assert result is None


def test_is_category_consistent_with_resolution_rejects_disallowed_taxonomy():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import (
        CategoryResolution,
        _is_category_consistent_with_resolution,
    )

    resolution = CategoryResolution(
        category_id="gid://shopify/TaxonomyCategory/bad-match",
        product_type="Raised Garden Beds",
        category_label="raised-garden-beds",
        tags=("garden", "raised-bed"),
        matched_rule="llm:raised-garden-beds",
        taxonomy_search="raised garden beds",
        taxonomy_path_tokens=("raised", "garden", "beds"),
        allow_category_update=True,
    )

    assert _is_category_consistent_with_resolution(
        category={
            "id": "gid://shopify/TaxonomyCategory/el-bad",
            "fullName": "Home & Garden > Kitchen & Dining > Kitchen Appliances > Outdoor Grills",
        },
        resolution=resolution,
    ) is False


def test_is_category_consistent_with_resolution_accepts_tv_antenna_taxonomy():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import (
        CategoryResolution,
        _is_category_consistent_with_resolution,
    )

    resolution = CategoryResolution(
        category_id="gid://shopify/TaxonomyCategory/el-good",
        product_type="TV Antennas",
        category_label="tv-antennas",
        tags=("electronics", "tv", "antenna"),
        matched_rule="exact:tv-antenna",
        taxonomy_search="tv antennas",
        taxonomy_path_tokens=("tv", "antenna"),
        allow_category_update=True,
    )

    assert _is_category_consistent_with_resolution(
        category={
            "id": "gid://shopify/TaxonomyCategory/el-good",
            "fullName": "Electronics > Electronics Accessories > Antennas > TV Antennas",
        },
        resolution=resolution,
    ) is True


def test_search_taxonomy_category_id_rejects_disallowed_raised_bed_match():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import _search_taxonomy_category_id

    class _Client:
        def graphql(self, query, variables=None):
            return {
                "taxonomy": {
                    "categories": {
                        "nodes": [
                            {
                                "id": "gid://shopify/TaxonomyCategory/bad-grill",
                                "fullName": "Home & Garden > Kitchen & Dining > Kitchen Appliances > Outdoor Grills",
                                "isLeaf": True,
                                "isArchived": False,
                                "name": "Outdoor Grills",
                            }
                        ]
                    }
                }
            }

    result = _search_taxonomy_category_id(
        client=_Client(),
        category_label="raised-garden-beds",
        search="raised garden beds",
        path_tokens=("raised", "garden", "beds"),
    )

    assert result is None


def test_classify_with_deepseek_reports_parse_error():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import _classify_with_deepseek

    class FakeLLMClient:
        @staticmethod
        def generate(prompt, **kwargs):
            return {"text": "not-json", "raw": {}}

    class _Client:
        def graphql(self, query, variables=None):
            return {}

    result = _classify_with_deepseek(
        llm_client=FakeLLMClient(),
        product={"title": "Bad response example", "vendor": "Doba", "tags": [], "descriptionHtml": "", "productType": ""},
        client=_Client(),
        taxonomy_cache={},
    )

    assert result.status == "parse_error"
    assert result.suggestion is None


def test_classify_with_deepseek_reports_empty_response():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import _classify_with_deepseek

    class FakeLLMClient:
        @staticmethod
        def generate(prompt, **kwargs):
            return {"text": "", "raw": {}}

    class _Client:
        def graphql(self, query, variables=None):
            return {}

    result = _classify_with_deepseek(
        llm_client=FakeLLMClient(),
        product={"title": "Empty response example", "vendor": "Doba", "tags": [], "descriptionHtml": "", "productType": ""},
        client=_Client(),
        taxonomy_cache={},
    )

    assert result.status == "empty_response"
    assert result.suggestion is None


def test_classify_with_deepseek_reports_request_error():
    from src.modules.shopify_listing.runners.publish_vendor_catalog import _classify_with_deepseek

    class FakeLLMClient:
        @staticmethod
        def generate(prompt, **kwargs):
            raise RuntimeError("boom")

    class _Client:
        def graphql(self, query, variables=None):
            return {}

    result = _classify_with_deepseek(
        llm_client=FakeLLMClient(),
        product={"title": "Request error example", "vendor": "Doba", "tags": [], "descriptionHtml": "", "productType": ""},
        client=_Client(),
        taxonomy_cache={},
    )

    assert result.status == "request_error"
    assert result.suggestion is None
