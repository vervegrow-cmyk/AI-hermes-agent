from __future__ import annotations

from src.shared.contracts import DobaProductInput


def load_mock_doba_products() -> list[DobaProductInput]:
    return [
        DobaProductInput(
            supplier_id="sup-home-001",
            product_id="prod-home-1001",
            sku="HOME-BIN-001",
            title="Foldable Closet Organizer Bins",
            brand="",
            category_path="Home > Storage > Closet Organization",
            supplier_status="active",
            cost=18.0,
            msrp=54.0,
            inventory=30,
            ship_from_country="US",
            ships_to_countries=["US", "CA"],
            shipping_cost=6.0,
            delivery_days=5,
            description="Lightweight storage bins for closet organization and home tidying.",
            image_urls=[
                "https://example.com/images/home-bin-1.jpg",
                "https://example.com/images/home-bin-2.jpg",
            ],
            variant_attributes={"color": "gray", "size": "medium"},
            attributes={"material": "fabric", "use": "storage", "feature": "foldable"},
        ),
        DobaProductInput(
            supplier_id="sup-beauty-009",
            product_id="prod-beauty-2201",
            sku="COS-BAG-2201",
            title="Branded Travel Cosmetic Bag",
            brand="LunaCase",
            category_path="Beauty > Cosmetics Storage",
            supplier_status="active",
            cost=16.0,
            msrp=38.0,
            inventory=22,
            ship_from_country="US",
            ships_to_countries=["US"],
            shipping_cost=7.0,
            delivery_days=8,
            description="Travel cosmetic organizer with compartments for brushes and bottles.",
            image_urls=["https://example.com/images/cos-bag-1.jpg"],
            variant_attributes={"color": "pink"},
            attributes={"material": "polyester", "compartments": "multiple"},
        ),
    ]

