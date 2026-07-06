from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import bootstrap
from shared.clients import ShopifyAuthClient, ShopifyGraphQLError
from shared.config import get_settings
from shared.llm import get_llm

TARGET_PUBLICATION_NAMES = [
    "Online Store",
    "Shop",
    "Pinterest",
    "Facebook & Instagram",
]

COMMON_COLORS = (
    "black",
    "white",
    "brown",
    "gray",
    "grey",
    "green",
    "red",
    "blue",
    "beige",
    "orange",
    "pink",
    "purple",
    "yellow",
    "silver",
    "gold",
    "cream",
    "natural",
    "anthracite",
)

COMMON_MATERIALS = (
    "steel",
    "metal",
    "aluminium",
    "aluminum",
    "iron",
    "wood",
    "solid wood",
    "mahogany",
    "pine",
    "bamboo",
    "glass",
    "tempered glass",
    "plastic",
    "polyester",
    "rattan",
    "pe rattan",
    "poly rattan",
    "cotton",
    "faux leather",
    "rubber",
)

EXCLUDED_CATEGORY_TAG_PREFIXES = (
    "category:",
    "needs-shopify-category-suggestion",
    "hermes-category-optimized",
)
MISSING_RESOURCE_MESSAGES = (
    "product does not exist",
    "resource does not exist",
    "owner does not exist",
)
LLM_SOURCE_FIELD_MIN_CONFIDENCE = 0.0
LLM_FALLBACK_MIN_CONFIDENCE = 0.0
HIGH_RISK_CATEGORY_LABELS: set[str] = set()
LLM_OVERRIDEABLE_RULE_LABELS = {
    "bags",
    "crossbody-bags",
    "dog-supplies",
    "drinkware",
    "muscle-stimulators",
}
GENERIC_CATEGORY_TOKENS = {
    "outdoor",
    "garden",
    "patio",
    "set",
    "sets",
    "living",
}
TAXONOMY_SEARCH_STOPWORDS = {
    "and",
    "for",
    "the",
    "with",
    "set",
    "sets",
}
TAXONOMY_DISALLOWED_TOKENS: dict[str, tuple[str, ...]] = {
    "raised-garden-beds": ("grill", "grills", "spa", "spas", "hot tub", "hot tubs"),
    "tv-cabinets": ("speaker", "speakers", "audio"),
    "garden-chair-sets": ("heater", "heaters", "grill", "grills"),
}
NEW_ARRIVALS_COLLECTION_TITLE = "NEW ARRIVALS"


@dataclass(frozen=True, slots=True)
class CategoryRule:
    category_id: str | None
    product_type: str
    category_label: str
    tags: tuple[str, ...]
    all_keywords: tuple[str, ...] = ()
    any_keywords: tuple[str, ...] = ()
    blocked_keywords: tuple[str, ...] = ()
    taxonomy_search: str = ""
    taxonomy_path_tokens: tuple[str, ...] = ()
    allow_category_update: bool = True


@dataclass(frozen=True, slots=True)
class CategoryResolution:
    category_id: str | None
    product_type: str
    category_label: str
    tags: tuple[str, ...]
    matched_rule: str
    taxonomy_search: str = ""
    taxonomy_path_tokens: tuple[str, ...] = ()
    allow_category_update: bool = True


@dataclass(frozen=True, slots=True)
class LLMFallbackSuggestion:
    product_type: str
    category_label: str
    taxonomy_search: str
    tags: tuple[str, ...]
    path_tokens: tuple[str, ...]
    attributes: dict[str, list[str]]
    confidence: float
    reason: str
    category_id: str | None = None


@dataclass(frozen=True, slots=True)
class LLMClassificationResult:
    status: str
    suggestion: LLMFallbackSuggestion | None = None
    response_text: str = ""
    error: str = ""


CATEGORY_OVERRIDES: dict[str, CategoryRule] = {
    'Compact Under-Desk Elliptical 濮?Quiet Mini Pedal Exerciser with Adjustable Speed and LED Display': CategoryRule(
        category_id="gid://shopify/TaxonomyCategory/sg-2-4-2-1",
        taxonomy_search="under desk ellipticals",
        taxonomy_path_tokens=("elliptical",),
        product_type="Under-Desk Ellipticals",
        category_label="exercise-ellipticals",
        tags=("fitness", "home-office", "cardio"),
    ),
    '3-Seater Patio Swing Cover, Outdoor Garden Furniture Protection Hammock Cover Waterproof 85" X 61" X 59", Dark Green': CategoryRule(
        category_id="gid://shopify/TaxonomyCategory/hg-12-2-9-2",
        taxonomy_search="porch swing covers",
        taxonomy_path_tokens=("porch swing covers",),
        product_type="Porch Swing Covers",
        category_label="porch-swing-covers",
        tags=("outdoor-living", "patio", "cover"),
    ),
    'USA Mouse Trap Rat Trap Rodent Trap Live Catch Cage, Easy to Set Up and Reuse': CategoryRule(
        category_id="gid://shopify/TaxonomyCategory/hg-10-11-2",
        taxonomy_search="pest control traps",
        taxonomy_path_tokens=("pest control", "traps"),
        product_type="Pest Control Traps",
        category_label="pest-control-traps",
        tags=("pest-control", "household"),
    ),
    '4X Magnetic Car Side Front Rear Window Sun Shade Cover Mesh Shield UV Protection': CategoryRule(
        category_id="gid://shopify/TaxonomyCategory/vp-1-4-11-7",
        taxonomy_search="vehicle sun shades",
        taxonomy_path_tokens=("sun shades",),
        product_type="Vehicle Sun Shades",
        category_label="vehicle-sun-shades",
        tags=("automotive", "interior", "sun-shade"),
    ),
    '10 PCS LR1130 AG10 389 Alkaline Battery 1.5V Button Cell for Watch Calculator US': CategoryRule(
        category_id="gid://shopify/TaxonomyCategory/el-7-15-1-15",
        taxonomy_search="watch batteries",
        taxonomy_path_tokens=("watch batteries",),
        product_type="Watch Batteries",
        category_label="watch-batteries",
        tags=("electronics", "battery", "watch"),
    ),
    '[Same Code: 52463595]HT-200 x 100 Household Application Door & Window Rain Cover Eaves Canopy Silver & Gray Bracket': CategoryRule(
        category_id="gid://shopify/TaxonomyCategory/hg-12-2-2",
        taxonomy_search="awnings",
        taxonomy_path_tokens=("awnings",),
        product_type="Awnings",
        category_label="awnings",
        tags=("home-improvement", "outdoor", "canopy"),
    ),
    'Trucker Bluetooth 5.2 Wireless Headset With Noise Cancelling Mic For Phones PC': CategoryRule(
        category_id="gid://shopify/TaxonomyCategory/el-2-2-7-2-4",
        taxonomy_search="office headsets",
        taxonomy_path_tokens=("headsets",),
        product_type="Office Headsets",
        category_label="office-headsets",
        tags=("electronics", "audio", "headset"),
    ),
    "Big  Flower Duvet Cover Queen": CategoryRule(
        category_id="gid://shopify/TaxonomyCategory/hg-15-1-5",
        taxonomy_search="duvet covers",
        taxonomy_path_tokens=("duvet covers",),
        product_type="Duvet Covers",
        category_label="duvet-covers",
        tags=("bedding", "home-textile"),
    ),
    '5/6-layer practical storage rack, shoe rack, space-saving design, multi-layer independent storage rack, wood grain finish, easy to assemble, self-supporting cubic shoe storage rack, storage rack, suit': CategoryRule(
        category_id="gid://shopify/TaxonomyCategory/hg-10-16-1-6-2",
        taxonomy_search="shoe racks",
        taxonomy_path_tokens=("shoe racks",),
        product_type="Shoe Racks",
        category_label="shoe-racks",
        tags=("storage", "organization", "shoe-rack"),
    ),
    '2Pack 11.81x5.63x4.45In 2-Door Humane Rat Trap Automatic Continuous Mouse Trap Reusable Galvanized Iron Live Animal Cage': CategoryRule(
        category_id="gid://shopify/TaxonomyCategory/hg-10-11-2",
        taxonomy_search="pest control traps",
        taxonomy_path_tokens=("pest control", "traps"),
        product_type="Pest Control Traps",
        category_label="pest-control-traps",
        tags=("pest-control", "household"),
    ),
    "5600Miles Upgraded TV Antenna HDTV Amplified Digital 4K 1080P Long Range Indoor": CategoryRule(
        category_id=None,
        taxonomy_search="tv antennas",
        taxonomy_path_tokens=("tv", "antenna"),
        product_type="TV Antennas",
        category_label="tv-antennas",
        tags=("electronics", "tv", "antenna"),
        allow_category_update=True,
    ),
    '3 Color Lighting Mirror with LED Lights, 64"x21" Lighted Floor Standing Mirror with Stand, Wall Mounted Hanging': CategoryRule(
        category_id="gid://shopify/TaxonomyCategory/hg-3-47-1",
        taxonomy_search="floor mirrors",
        taxonomy_path_tokens=("mirrors",),
        product_type="Floor Mirrors",
        category_label="floor-mirrors",
        tags=("home-decor", "mirror", "led"),
    ),
    "75-inch heavy-duty  folding bed, 10-leg design for stable support, portable camping bed with side pockets and mattress, winter camping equipment": CategoryRule(
        category_id="gid://shopify/TaxonomyCategory/fr-2-2",
        taxonomy_search="folding beds",
        taxonomy_path_tokens=("beds",),
        product_type="Folding Beds",
        category_label="folding-beds",
        tags=("furniture", "bed", "portable"),
    ),
    "Fenben Fenbendazole 444mg 90 Count 99% Purity Lab Tested Supplement For Dietary Fitness": CategoryRule(
        category_id="gid://shopify/TaxonomyCategory/hb-1-9-6-5",
        taxonomy_search="herbal supplements",
        taxonomy_path_tokens=("supplements",),
        product_type="Herbal Supplements",
        category_label="herbal-supplements",
        tags=("health", "supplement"),
    ),
    "Boxed Disposable Garbage Bag 70 Pieces Puncture Tear Resistant Trash Bags, 39 Gallon Capacity, Multipurpose Cleaning Supplies For Industrial, Garden, Home, And Commercial Use - Durable, Leak-Proof": CategoryRule(
        category_id="gid://shopify/TaxonomyCategory/hg-10-5",
        taxonomy_search="garbage bags",
        taxonomy_path_tokens=("garbage bags",),
        product_type="Garbage Bags",
        category_label="garbage-bags",
        tags=("household", "cleaning"),
    ),
    "4-Piece Set, Women's Eau De Parfuma Spray Gift Box, Long Lasting Fragrance, 4 Different Flavor, Perfect For Holiday Gifts, Dating, Daily Life, Parties": CategoryRule(
        category_id="gid://shopify/TaxonomyCategory/hb-3-2-8-3",
        taxonomy_search="eau de parfum",
        taxonomy_path_tokens=("perfumes",),
        product_type="Eaux de Parfum",
        category_label="eau-de-parfum",
        tags=("beauty", "fragrance", "gift"),
    ),
    "XXL 304 Stainless Steel Cutting Board  Anti-Slip & Mildew-Proof! No More Moldy Wooden Boards | Heavy-Duty & Food-Safe, Easy to Clean 濮?Chop Meat, Knead Dough, Bake Prep All-in-One | Must-Have for Home": CategoryRule(
        category_id="gid://shopify/TaxonomyCategory/hg-11-8-21",
        taxonomy_search="cutting boards",
        taxonomy_path_tokens=("cutting boards",),
        product_type="Cutting Boards",
        category_label="cutting-boards",
        tags=("kitchen", "cooking", "cutting-board"),
    ),
    "Stainless Steel Cutting Board with Lip for Kitchen Chopping Boards for Countertop Large Metal Cutting Board over Sink Suitable for Meat Fruits Vegetables Bread Noodle and Pizza Bamboo Knives": CategoryRule(
        category_id="gid://shopify/TaxonomyCategory/hg-11-8-21",
        taxonomy_search="cutting boards",
        taxonomy_path_tokens=("cutting boards",),
        product_type="Cutting Boards",
        category_label="cutting-boards",
        tags=("kitchen", "cooking", "cutting-board"),
    ),
    "Heavy duty folding bed, camping bed with flip-up mattress (mattress included), portable guest bed, suitable for teenagers, adults, travel, garden, balcony, camping supplies": CategoryRule(
        category_id="gid://shopify/TaxonomyCategory/fr-2-2",
        taxonomy_search="folding beds",
        taxonomy_path_tokens=("beds",),
        product_type="Folding Beds",
        category_label="folding-beds",
        tags=("furniture", "bed", "portable"),
    ),
    "24 Modes TENS Unit Muscle Stimulator, Red Color, Rechargeable Electronic Pulse Massager with 8 Pads for Back and Shoulder Pain Relief and Muscle Strength": CategoryRule(
        category_id=None,
        taxonomy_search="muscle stimulators",
        taxonomy_path_tokens=("stimulation", "massager"),
        product_type="Muscle Stimulators",
        category_label="muscle-stimulators",
        tags=("health", "massager", "recovery"),
        allow_category_update=True,
    ),
    "Stainless Steel Cutting Board for Kitchen - Large 304 Chopping Boards, Suitable for Meat Vegetables Bread and Baking,Kitchen Accessories,": CategoryRule(
        category_id="gid://shopify/TaxonomyCategory/hg-11-8-21",
        taxonomy_search="cutting boards",
        taxonomy_path_tokens=("cutting boards",),
        product_type="Cutting Boards",
        category_label="cutting-boards",
        tags=("kitchen", "cooking", "cutting-board"),
    ),
}
NORMALIZED_CATEGORY_OVERRIDES: dict[str, CategoryRule] = {}

CATEGORY_KEYWORD_RULES: list[CategoryRule] = [
    CategoryRule(
        "gid://shopify/TaxonomyCategory/hb-3-2-1-6",
        "Hand Sanitizers",
        "hand-sanitizers",
        ("health", "sanitizer", "travel"),
        any_keywords=("hand sanitizer", "sanitizer spray", "sanitizer mist"),
        taxonomy_search="hand sanitizers",
        taxonomy_path_tokens=("hand", "sanitizers"),
    ),
    CategoryRule(
        "gid://shopify/TaxonomyCategory/lb-6",
        "Duffel Bags",
        "duffel-bags",
        ("travel", "bag", "duffel"),
        any_keywords=("duffel bag", "weekender duffel", "weekender bag", "gym bag"),
        taxonomy_search="duffel bags",
        taxonomy_path_tokens=("duffel", "bags"),
    ),
    CategoryRule(
        "gid://shopify/TaxonomyCategory/ap-2-26",
        "Pet Grooming Supplies",
        "pet-bathing-supplies",
        ("pets", "grooming", "bath"),
        any_keywords=("dog bathtub", "pet bathtub", "dog bathing", "pet bathing"),
        taxonomy_search="pet grooming supplies",
        taxonomy_path_tokens=("pet", "grooming"),
        allow_category_update=True,
    ),
    CategoryRule(
        "gid://shopify/TaxonomyCategory/hg-11-10-2-2",
        "Teapots",
        "teapots",
        ("kitchen", "teapot", "drinkware"),
        any_keywords=("teapot", "tea pot"),
        taxonomy_search="teapots",
        taxonomy_path_tokens=("teapots",),
    ),
    CategoryRule(
        "gid://shopify/TaxonomyCategory/el-8",
        "GPS Tracker Accessories",
        "gps-tracker-accessories",
        ("electronics", "gps", "tracker"),
        any_keywords=("gps tracker", "gps cards sim", "tracker sim", "gps sim"),
        taxonomy_search="gps tracker accessories",
        taxonomy_path_tokens=("gps", "accessories"),
        allow_category_update=True,
    ),
    CategoryRule(
        "gid://shopify/TaxonomyCategory/hg-12-3-15",
        "Grass Trimmers",
        "lawn-mowers-trimmers",
        ("garden", "trimmer", "power-equipment"),
        any_keywords=("grass trimmer", "grass wacker", "weed trimmer", "string trimmer"),
        taxonomy_search="weed trimmers",
        taxonomy_path_tokens=("weed", "trimmers"),
        allow_category_update=True,
    ),
    CategoryRule(
        "gid://shopify/TaxonomyCategory/fr-15-4-2",
        "Outdoor Lounge Chairs",
        "outdoor-lounge-chairs",
        ("outdoor", "lounge", "chairs"),
        any_keywords=("zero gravity lounge chairs", "zero gravity chairs", "folding recliners for pool", "outdoor patio folding recliners"),
        taxonomy_search="outdoor lounge chairs",
        taxonomy_path_tokens=("outdoor", "chairs"),
        allow_category_update=True,
    ),
    CategoryRule(
        "gid://shopify/TaxonomyCategory/hg-12-2-6-3-4",
        "Garden Trellis",
        "garden-trellises",
        ("garden", "trellis", "outdoor"),
        any_keywords=("garden trellis", "obelisk trellis", "arbor trellis", "climbing plants support"),
        taxonomy_search="trellises",
        taxonomy_path_tokens=("trellises",),
        allow_category_update=True,
    ),
    CategoryRule(
        "gid://shopify/TaxonomyCategory/hg-12-2-6-3-3",
        "Pergola",
        "pergolas",
        ("garden", "pergola", "outdoor"),
        any_keywords=("pergola",),
        taxonomy_search="pergolas",
        taxonomy_path_tokens=("pergolas",),
        allow_category_update=True,
    ),
    CategoryRule(
        "gid://shopify/TaxonomyCategory/hg-12-2-6-1-2",
        "Tents",
        "outdoor-party-tents",
        ("outdoor", "party", "gazebo"),
        any_keywords=("party tent", "wedding gazebo", "patio wedding gazebo"),
        taxonomy_search="gazebos",
        taxonomy_path_tokens=("gazebos",),
        allow_category_update=True,
    ),
    CategoryRule(
        "gid://shopify/TaxonomyCategory/ae-2-7-9-5",
        "Amplifier Stands",
        "amp-stands",
        ("music", "amplifier", "stand"),
        any_keywords=("amp stand", "amplifier stand", "guitar amplifier"),
        taxonomy_search="amplifier stands",
        taxonomy_path_tokens=("amplifier", "stands"),
        allow_category_update=True,
    ),
    CategoryRule(
        "gid://shopify/TaxonomyCategory/fr-15-2",
        "Outdoor Furniture Sets",
        "outdoor-dining-sets",
        ("outdoor-living", "patio", "dining"),
        any_keywords=("garden dining set", "outdoor dining set", "patio dining set"),
        blocked_keywords=("swing cover", "porch swing cover"),
        taxonomy_search="outdoor dining furniture",
        taxonomy_path_tokens=("outdoor", "furniture", "sets"),
        allow_category_update=True,
    ),
    CategoryRule(
        "gid://shopify/TaxonomyCategory/hg-15-1-5",
        "Duvet Covers",
        "duvet-covers",
        ("bedding", "home-textile"),
        any_keywords=("duvet cover", "bedding", "comforter set"),
        taxonomy_search="duvet covers",
        taxonomy_path_tokens=("duvet covers",),
    ),
    CategoryRule(
        None,
        "Fitted Sheets",
        "fitted-sheets",
        ("bedding", "sheet"),
        any_keywords=("fitted sheet",),
        taxonomy_search="fitted sheets",
        taxonomy_path_tokens=("sheets",),
    ),
    CategoryRule(
        None,
        "Area Rugs",
        "area-rugs",
        ("home-decor", "rug"),
        any_keywords=("kitchen rug", "hallway rug", "bathroom rug"),
        taxonomy_search="area rugs",
        taxonomy_path_tokens=("rugs",),
    ),
    CategoryRule(
        None,
        "Cosmetic Bags",
        "cosmetic-bags",
        ("beauty", "travel", "organizer"),
        any_keywords=("makeup bag", "cosmetic bag", "toiletry bag", "travel wash bag", "organizer pouch"),
        taxonomy_search="cosmetic bags",
        taxonomy_path_tokens=("bags",),
    ),
    CategoryRule(
        None,
        "Crossbody Bags",
        "crossbody-bags",
        ("fashion", "bag", "halloween"),
        any_keywords=("crossbody bag", "pumpkin purse", "funny purses", "handbags"),
        blocked_keywords=("hand sanitizer", "sanitizer spray", "sanitizer mist"),
        taxonomy_search="crossbody bags",
        taxonomy_path_tokens=("bags",),
    ),
    CategoryRule(
        None,
        "Gift Buckets",
        "gift-buckets",
        ("halloween", "bucket", "gift"),
        any_keywords=("jack-o-lantern pail", "gift basket pumpkin", "plastic buckets"),
        taxonomy_search="gift buckets",
        taxonomy_path_tokens=("buckets",),
        allow_category_update=False,
    ),
    CategoryRule(
        None,
        "Lunch Bags",
        "lunch-bags",
        ("lunch", "insulated", "bag"),
        any_keywords=("lunch bag", "meal tote", "lunch box bag"),
        taxonomy_search="lunch bags",
        taxonomy_path_tokens=("bags",),
        allow_category_update=False,
    ),
    CategoryRule(
        None,
        "Drinkware",
        "drinkware",
        ("kitchen", "drinkware"),
        any_keywords=("tumbler", "thermos", "tea tumbler", "cup with straw", "insulated cup"),
        taxonomy_search="drinkware",
        taxonomy_path_tokens=("drinkware",),
        allow_category_update=False,
    ),
    CategoryRule(
        None,
        "Decorative Lighting",
        "decorative-lighting",
        ("decor", "lighting", "halloween"),
        any_keywords=("halloween string lights", "ghost witch hat", "light up halloween witch", "glowing ghost"),
        taxonomy_search="decorative lighting",
        taxonomy_path_tokens=("lighting",),
        allow_category_update=False,
    ),
    CategoryRule(
        None,
        "Halloween Decorations",
        "halloween-decorations",
        ("decor", "halloween"),
        any_keywords=("skeleton halloween decorations", "haunted house decor", "creepy halloween"),
        taxonomy_search="halloween decorations",
        taxonomy_path_tokens=("decor",),
        allow_category_update=False,
    ),
    CategoryRule(
        None,
        "Landscape Lighting",
        "landscape-lighting",
        ("garden", "outdoor-lighting"),
        any_keywords=("solar garden lights", "landscape lighting", "bird bath fountain", "water fountain pump"),
        taxonomy_search="landscape lighting",
        taxonomy_path_tokens=("lighting",),
        allow_category_update=False,
    ),
    CategoryRule(
        None,
        "Dog Supplies",
        "dog-supplies",
        ("pets", "dog"),
        any_keywords=("dog washing", "dog bathtub", "dog clippers", "pet stairs"),
        blocked_keywords=("pet bathtub", "dog bathtub", "pet bathing"),
        taxonomy_search="dog supplies",
        taxonomy_path_tokens=("dogs",),
        allow_category_update=False,
    ),
    CategoryRule(
        "gid://shopify/TaxonomyCategory/hb-3-11-8-1",
        "Electric Massagers",
        "massage-mats",
        ("health", "massage", "relaxation"),
        any_keywords=("massage mat", "massager pad"),
        taxonomy_search="electric massagers",
        taxonomy_path_tokens=("electric", "massagers"),
        allow_category_update=True,
    ),
    CategoryRule(
        "gid://shopify/TaxonomyCategory/hb-3-11-8-1",
        "Electric Massagers",
        "neck-massagers",
        ("health", "massage", "neck"),
        any_keywords=("neck massager", "shiatsu neck massager"),
        taxonomy_search="electric massagers",
        taxonomy_path_tokens=("electric", "massagers"),
        allow_category_update=True,
    ),
    CategoryRule(
        None,
        "Cat Doors",
        "cat-doors",
        ("pets", "cat"),
        any_keywords=("cat door",),
        taxonomy_search="cat doors",
        taxonomy_path_tokens=("cats", "doors"),
        allow_category_update=False,
    ),
    CategoryRule(
        None,
        "Dash Cams",
        "dash-cams",
        ("automotive", "camera"),
        any_keywords=("dash cam", "car dash cam"),
        taxonomy_search="dash cams",
        taxonomy_path_tokens=("camera",),
        allow_category_update=False,
    ),
    CategoryRule(
        None,
        "Muscle Stimulators",
        "muscle-stimulators",
        ("health", "massager", "recovery"),
        any_keywords=("muscle stimulator", "pulse massager", "tens unit"),
        taxonomy_search="muscle stimulators",
        taxonomy_path_tokens=("stimulation",),
        allow_category_update=True,
    ),
    CategoryRule(
        None,
        "Poultry Feeders",
        "poultry-feeders",
        ("farm", "poultry"),
        any_keywords=("chicken feeder", "chicken waterer", "poultry waterer"),
        taxonomy_search="poultry feeders",
        taxonomy_path_tokens=("poultry",),
        allow_category_update=False,
    ),
    CategoryRule(
        None,
        "Chicken Coops",
        "chicken-coops",
        ("farm", "poultry", "coop"),
        any_keywords=("chicken coop", "hen house", "poultry cage", "rabbit hutch"),
        taxonomy_search="chicken coops",
        taxonomy_path_tokens=("poultry", "coops"),
        allow_category_update=False,
    ),
    CategoryRule(
        None,
        "Outdoor Dining Chairs",
        "garden-chair-sets",
        ("outdoor-living", "patio", "chairs"),
        any_keywords=("garden chair set", "dining chairs", "chair set of 4"),
        taxonomy_search="outdoor dining chairs",
        taxonomy_path_tokens=("outdoor", "dining", "chairs"),
        allow_category_update=True,
    ),
    CategoryRule(
        None,
        "Garden Stools",
        "garden-stools",
        ("outdoor-living", "patio", "stool"),
        any_keywords=("garden stool", "stool set of 4", "outdoor stool", "patio stool"),
        taxonomy_search="patio stools",
        taxonomy_path_tokens=("stools", "patio"),
        allow_category_update=False,
    ),
    CategoryRule(
        None,
        "Outdoor Sofa Sets",
        "outdoor-sofa-sets",
        ("outdoor-living", "patio", "sofa"),
        any_keywords=("garden sofa set", "glider bench", "hammock chair", "rocking chair loveseat"),
        taxonomy_search="outdoor sofa sets",
        taxonomy_path_tokens=("outdoor", "sofa", "sets"),
        allow_category_update=True,
    ),
    CategoryRule(
        None,
        "Door Fly Screens",
        "door-fly-screens",
        ("home-improvement", "door", "fly-screen"),
        any_keywords=("door fly screen", "chain door fly screen", "insect screen"),
        taxonomy_search="door fly screen",
        taxonomy_path_tokens=("doors", "fly", "screens"),
        allow_category_update=True,
    ),
    CategoryRule(
        "gid://shopify/TaxonomyCategory/hg-12-2-9-2",
        "Porch Swing Covers",
        "porch-swing-covers",
        ("outdoor-living", "patio", "cover"),
        any_keywords=("patio swing cover", "porch swing cover"),
        taxonomy_search="porch swing covers",
        taxonomy_path_tokens=("porch swing covers",),
    ),
    CategoryRule(
        "gid://shopify/TaxonomyCategory/hg-11-6-19",
        "Outdoor Cooking Accessories",
        "outdoor-cooking-accessories",
        ("kitchen", "outdoor-cooking"),
        any_keywords=("bbq griddle", "paper towel holder", "camping picnic", "griddle caddy", "bbq organizer"),
        taxonomy_search="outdoor cooking accessories",
        taxonomy_path_tokens=("outdoor cooking",),
        allow_category_update=True,
    ),
    CategoryRule(
        "gid://shopify/TaxonomyCategory/lb-6",
        "Bags",
        "bags",
        ("fashion", "bag"),
        any_keywords=("credit card holder", "tote bag"),
        taxonomy_search="bags",
        taxonomy_path_tokens=("bags",),
        allow_category_update=True,
    ),
    CategoryRule(
        "gid://shopify/TaxonomyCategory/hg-11-8-21",
        "Cutting Boards",
        "cutting-boards",
        ("kitchen", "cooking", "cutting-board"),
        any_keywords=("cutting board", "chopping board"),
        taxonomy_search="cutting boards",
        taxonomy_path_tokens=("cutting boards",),
    ),
    CategoryRule(
        "gid://shopify/TaxonomyCategory/hg-3-47-1",
        "Floor Mirrors",
        "floor-mirrors",
        ("home-decor", "mirror", "led"),
        any_keywords=("lighted mirror", "floor mirror", "led mirror", "standing mirror"),
        taxonomy_search="floor mirrors",
        taxonomy_path_tokens=("mirrors",),
    ),
    CategoryRule(
        None,
        "Wall Mirrors",
        "wall-mirrors",
        ("home-decor", "mirror"),
        any_keywords=("wall mirror", "rectangular mirror"),
        taxonomy_search="wall mirrors",
        taxonomy_path_tokens=("mirrors",),
        allow_category_update=True,
    ),
    CategoryRule(
        None,
        "TV Antennas",
        "tv-antennas",
        ("electronics", "tv", "antenna"),
        any_keywords=("tv antenna", "hdtv antenna", "digital antenna"),
        taxonomy_search="tv antennas",
        taxonomy_path_tokens=("tv", "antenna"),
        allow_category_update=True,
    ),
    CategoryRule(
        "gid://shopify/TaxonomyCategory/hg-10-16-1-6-2",
        "Shoe Racks",
        "shoe-racks",
        ("storage", "organization", "shoe-rack"),
        any_keywords=("shoe rack", "shoe storage"),
        taxonomy_search="shoe racks",
        taxonomy_path_tokens=("shoe racks",),
    ),
    CategoryRule(
        None,
        "Raised Garden Beds",
        "raised-garden-beds",
        ("garden", "raised-bed", "planter"),
        any_keywords=("raised bed", "garden raised bed", "planter boxes"),
        taxonomy_search="raised garden beds",
        taxonomy_path_tokens=("raised", "garden"),
        allow_category_update=True,
    ),
    CategoryRule(
        None,
        "Side Awnings",
        "side-awnings",
        ("outdoor-living", "awning"),
        any_keywords=("side awning", "retractable side awning"),
        taxonomy_search="side awnings",
        taxonomy_path_tokens=("awnings",),
        allow_category_update=False,
    ),
    CategoryRule(
        None,
        "Outdoor Bar Tables",
        "outdoor-bar-tables",
        ("outdoor-living", "bar-table", "patio"),
        any_keywords=("outdoor bar table",),
        taxonomy_search="outdoor bar tables",
        taxonomy_path_tokens=("tables", "outdoor"),
        allow_category_update=True,
    ),
    CategoryRule(
        None,
        "TV Cabinets",
        "tv-cabinets",
        ("furniture", "tv-cabinet"),
        any_keywords=("tv cabinet",),
        taxonomy_search="tv cabinets",
        taxonomy_path_tokens=("tv", "cabinets"),
        allow_category_update=True,
    ),
    CategoryRule(
        None,
        "Doors",
        "doors",
        ("home-improvement", "door"),
        any_keywords=("door narvik", "solid pine wood", "fly screen"),
        taxonomy_search="doors",
        taxonomy_path_tokens=("doors",),
        allow_category_update=False,
    ),
    CategoryRule(
        None,
        "Greenhouses",
        "greenhouses",
        ("garden", "greenhouse"),
        any_keywords=("garden greenhouse",),
        taxonomy_search="greenhouses",
        taxonomy_path_tokens=("greenhouses",),
        allow_category_update=False,
    ),
    CategoryRule(
        None,
        "Bed Frames",
        "bed-frames",
        ("furniture", "bed-frame"),
        any_keywords=("bed frame", "platform bed", "headboard"),
        taxonomy_search="bed frames",
        taxonomy_path_tokens=("beds",),
        allow_category_update=False,
    ),
    CategoryRule(
        None,
        "Canopy Fabrics",
        "canopy-fabrics",
        ("outdoor-living", "canopy"),
        any_keywords=("tent fabric without frame",),
        taxonomy_search="canopy fabrics",
        taxonomy_path_tokens=("canopy",),
        allow_category_update=False,
    ),
    CategoryRule(
        None,
        "Patio Bench Cushions",
        "patio-bench-cushions",
        ("outdoor-living", "cushion", "patio"),
        any_keywords=("bench cushion", "swing chair cushion", "patio sofa couch", "replacement tufted bench cushion"),
        taxonomy_search="patio bench cushions",
        taxonomy_path_tokens=("cushions", "patio"),
        allow_category_update=True,
    ),
    CategoryRule(
        None,
        "Display Cabinets",
        "display-cabinets",
        ("furniture", "cabinet", "display"),
        any_keywords=("display cabinet", "glass doors", "adjustable shelves", "wall mounted"),
        taxonomy_search="display cabinets",
        taxonomy_path_tokens=("cabinets",),
        allow_category_update=True,
    ),
    CategoryRule(
        None,
        "Food Choppers",
        "food-choppers",
        ("kitchen", "food-prep", "chopper"),
        any_keywords=("food hand chopper", "hand chopper", "cutter slicer peeler dicer", "onion garlic"),
        taxonomy_search="food choppers",
        taxonomy_path_tokens=("choppers",),
        allow_category_update=True,
    ),
    CategoryRule(
        None,
        "Vacuum Filters",
        "vacuum-filters",
        ("household", "vacuum", "filter"),
        any_keywords=("vacuum filter", "shop vac pleated filter", "wet dry washable vacuum", "replacement ridgid"),
        taxonomy_search="vacuum filters",
        taxonomy_path_tokens=("vacuum", "filters"),
        allow_category_update=True,
    ),
    CategoryRule(
        None,
        "Patio Umbrellas",
        "patio-umbrellas",
        ("outdoor-living", "umbrella", "patio"),
        any_keywords=("patio umbrella", "umbrella with base stand", "offset hanging outdoor patio umbrella"),
        taxonomy_search="patio umbrellas",
        taxonomy_path_tokens=("umbrellas", "patio"),
        allow_category_update=True,
    ),
    CategoryRule(
        None,
        "Fence Posts",
        "fence-posts",
        ("garden", "fencing", "post"),
        any_keywords=("fence post", "u channel", "fence stakes"),
        taxonomy_search="fence posts",
        taxonomy_path_tokens=("fence", "posts"),
        allow_category_update=True,
    ),
    CategoryRule(
        None,
        "Under-Desk Ellipticals",
        "exercise-ellipticals",
        ("fitness", "home-office", "cardio"),
        any_keywords=("under desk elliptical", "mini pedal exerciser", "quiet mini pedal exerciser"),
        taxonomy_search="under desk ellipticals",
        taxonomy_path_tokens=("elliptical",),
        allow_category_update=True,
    ),
    CategoryRule(
        None,
        "Storage Baskets",
        "storage-baskets",
        ("storage", "organization", "basket"),
        any_keywords=("storage basket", "fruit vegetable storage basket", "rotating kitchen storage shelf"),
        taxonomy_search="storage baskets",
        taxonomy_path_tokens=("baskets",),
        allow_category_update=True,
    ),
]

PRODUCTS_QUERY = """
query VendorProducts($first: Int!, $after: String, $query: String!) {
  products(first: $first, after: $after, query: $query) {
    pageInfo { hasNextPage endCursor }
    edges {
      node {
        id
        title
        vendor
        status
        productType
        tags
        descriptionHtml
        category { id fullName }
        resourcePublicationsV2(first: 20, onlyPublished: true) {
          edges { node { publication { id name } } }
        }
      }
    }
  }
}
"""

PUBLICATIONS_QUERY = """
query PublicationsList {
  publications(first: 50) {
    edges {
      node {
        id
        name
      }
    }
  }
}
"""

PRODUCT_BY_ID_QUERY = """
query ProductById($id: ID!) {
  product(id: $id) {
    id
    title
    vendor
    status
    productType
    tags
    descriptionHtml
    category { id fullName }
    resourcePublicationsV2(first: 20, onlyPublished: true) {
      edges { node { publication { id name } } }
    }
  }
}
"""

TAXONOMY_CATEGORY_SEARCH_QUERY = """
query SearchTaxonomyCategories($search: String!) {
  taxonomy {
    categories(first: 50, search: $search) {
      nodes {
        id
        fullName
        isLeaf
        isArchived
        name
      }
    }
  }
}
"""

COLLECTIONS_QUERY = """
query CollectionByTitle($query: String!) {
  collections(first: 10, query: $query) {
    edges {
      node {
        id
        title
        handle
      }
    }
  }
}
"""

COLLECTION_CREATE = """
mutation CreateCollection($input: CollectionInput!) {
  collectionCreate(input: $input) {
    collection {
      id
      title
      handle
    }
    userErrors {
      field
      message
    }
  }
}
"""

COLLECTION_ADD_PRODUCTS = """
mutation AddProductsToCollection($id: ID!, $productIds: [ID!]!) {
  collectionAddProducts(id: $id, productIds: $productIds) {
    collection {
      id
      title
    }
    userErrors {
      field
      message
    }
  }
}
"""

UPDATE_PRODUCT_FIELDS = """
mutation UpdateProductFields($product: ProductUpdateInput!) {
  productUpdate(product: $product) {
    product {
      id
      productType
      tags
      category { id fullName }
    }
    userErrors { field message }
  }
}
"""

PUBLISH_PRODUCT = """
mutation PublishProduct($id: ID!, $input: [PublicationInput!]!) {
  publishablePublish(id: $id, input: $input) {
    publishable {
      resourcePublicationsCount { count }
    }
    userErrors { field message }
  }
}
"""

UPSERT_PRODUCT_SOURCE_METAFIELDS = """
mutation UpsertProductSourceMetafields($metafields: [MetafieldsSetInput!]!) {
  metafieldsSet(metafields: $metafields) {
    metafields {
      namespace
      key
    }
    userErrors {
      field
      message
      code
    }
  }
}
"""


def publish_vendor_catalog(
    *,
    vendor: str = "Doba",
    publication_names: list[str] | None = None,
    report_path: str = "docs/audits/vendor-catalog-publish-report.json",
    stop_on_failure: bool = False,
    max_products: int | None = None,
    resume_from_report: bool = False,
    skip_fully_published: bool = False,
) -> dict:
    settings = get_settings()
    client = ShopifyAuthClient.from_settings(settings)
    target_names = publication_names or list(TARGET_PUBLICATION_NAMES)
    print(f"[publish_vendor_catalog] loading publications for vendor={vendor}")
    publication_map = _get_publication_map(client)
    new_arrivals_collection = _ensure_collection(client, NEW_ARRIVALS_COLLECTION_TITLE)
    publish_inputs = [
        {"publicationId": publication_map[name]["id"]}
        for name in target_names
        if name in publication_map
    ]

    taxonomy_cache: dict[str, str | None] = {}
    llm_client, deepseek_runtime_status = _get_deepseek_client()
    print(f"[publish_vendor_catalog] deepseek_status={deepseek_runtime_status}")
    all_products = _get_vendor_products(client, vendor)
    existing_report = _load_existing_report(report_path) if resume_from_report else {}
    existing_results = list(existing_report.get("results") or [])
    processed_ids = {
        str(item.get("id") or "").strip()
        for item in existing_results
        if str(item.get("id") or "").strip()
    }
    fully_published_before = 0
    products: list[dict] = []
    for product in all_products:
        product_id = str(product.get("id") or "").strip()
        if product_id and product_id in processed_ids:
            continue
        if skip_fully_published and not _missing_publications(product, target_names):
            fully_published_before += 1
            continue
        products.append(product)
    if max_products is not None:
        products = products[: max(0, max_products)]

    results = list(existing_results)
    total_products = len(products)
    total_discovered = len(all_products)
    pending_after_filter = max(total_discovered - len(processed_ids) - fully_published_before, 0)
    print(
        "[publish_vendor_catalog] "
        f"fetched={total_discovered} resume_processed={len(processed_ids)} "
        f"already_published={fully_published_before} selected={total_products}"
    )
    for index, product in enumerate(products, start=1):
        safe_title = str(product.get("title") or "").replace("\r", " ").replace("\n", " ")
        print(f"[publish_vendor_catalog] {index}/{total_products} optimizing {product['id']} :: {safe_title[:100]}")
        resolution = _resolve_category(product)
        hydrated = _hydrate_resolution(client, resolution, taxonomy_cache) if resolution else None
        attribute_suggestions = _extract_attribute_suggestions(product, hydrated)
        llm_suggestion = None
        item_llm_status = "not_run"
        llm_error = ""
        llm_response_text = ""
        category_error = None
        source_field_error = None
        publish_error = None
        collection_error = None
        added_to_collection = False
        category_after = product.get("category")
        source_fields_after = {
            "productType": product.get("productType") or "",
            "tags": list(product.get("tags") or []),
        }
        category_action = "no_match"
        skip_failure = False

        if llm_client:
            llm_result = _classify_with_deepseek(
                llm_client=llm_client,
                product=product,
                client=client,
                taxonomy_cache=taxonomy_cache,
            )
            item_llm_status = llm_result.status
            llm_suggestion = llm_result.suggestion
            llm_error = llm_result.error
            llm_response_text = llm_result.response_text
            if llm_suggestion:
                attribute_suggestions = _merge_attribute_suggestions(
                    attribute_suggestions,
                    llm_suggestion.attributes,
                )
            if llm_suggestion and _should_apply_llm_source_fields(
                resolution=hydrated,
                llm_suggestion=llm_suggestion,
                product=product,
            ):
                llm_resolution = _build_resolution_from_llm(llm_suggestion)
                if _should_apply_llm_suggestion(hydrated, llm_suggestion):
                    hydrated = llm_resolution
                elif hydrated is None or not (product.get("productType") or "").strip():
                    hydrated = llm_resolution

        if hydrated:
            merged_tags = _merge_tags(product, hydrated.tags, hydrated.category_label, not hydrated.category_id)
            category_action = "source_fields_only"
            clear_existing_category = _should_clear_existing_category(
                existing_category=product.get("category"),
                resolution=hydrated,
            )
            try:
                update_result = _update_product_fields(
                    client=client,
                    product_id=product["id"],
                    product_type=hydrated.product_type,
                    tags=merged_tags,
                    category_id=hydrated.category_id if hydrated.allow_category_update else None,
                    clear_category=clear_existing_category,
                )
                updated_product = update_result.get("product") or {}
                user_errors = update_result.get("userErrors") or []
                if user_errors:
                    category_error = user_errors
                else:
                    category_after = updated_product.get("category") or category_after
                    if clear_existing_category and not hydrated.allow_category_update:
                        category_after = None
                    source_fields_after = {
                        "productType": updated_product.get("productType") or "",
                        "tags": list(updated_product.get("tags") or []),
                    }
                    if hydrated.category_id and hydrated.allow_category_update:
                        category_action = "category_applied"
                    elif hydrated.category_id and not hydrated.allow_category_update:
                        category_action = "category_suggested_review"
                    else:
                        category_action = "needs_shopify_suggestion"
                    if hydrated.matched_rule.startswith("llm:") and hydrated.category_id is None:
                        category_action = "llm_suggested_review"
            except ShopifyGraphQLError as exc:
                category_error = str(exc)
                try:
                    retry_result = _update_product_fields(
                        client=client,
                        product_id=product["id"],
                        product_type=hydrated.product_type,
                        tags=merged_tags,
                    )
                    updated_product = retry_result.get("product") or {}
                    source_fields_after = {
                        "productType": updated_product.get("productType") or hydrated.product_type,
                        "tags": list(updated_product.get("tags") or merged_tags),
                    }
                except ShopifyGraphQLError as retry_exc:
                    source_field_error = str(retry_exc)

            try:
                metafield_errors = _update_source_metafields(
                    client=client,
                    product=product,
                    resolution=hydrated,
                    category_action=category_action,
                    attribute_suggestions=attribute_suggestions,
                    llm_suggestion=llm_suggestion,
                    llm_status=item_llm_status,
                    llm_error=llm_error,
                    llm_response_text=llm_response_text,
                )
                if metafield_errors:
                    source_field_error = metafield_errors
            except ShopifyGraphQLError as exc:
                source_field_error = str(exc)

            if _is_missing_resource_error(category_error) or _is_missing_resource_error(source_field_error):
                category_action = "skipped_missing_product"
                category_error = None
                source_field_error = None
                skip_failure = True

        if not skip_failure:
            if new_arrivals_collection:
                try:
                    collection_errors = _add_product_to_collection(
                        client=client,
                        collection_id=new_arrivals_collection["id"],
                        product_id=product["id"],
                    )
                    if collection_errors:
                        collection_error = collection_errors
                    else:
                        added_to_collection = True
                except ShopifyGraphQLError as exc:
                    collection_error = str(exc)

            try:
                publish_result = client.graphql(
                    PUBLISH_PRODUCT,
                    {"id": product["id"], "input": publish_inputs},
                )["publishablePublish"]
                user_errors = publish_result.get("userErrors") or []
                if user_errors:
                    publish_error = user_errors
            except ShopifyGraphQLError as exc:
                publish_error = str(exc)
                if _is_missing_resource_error(publish_error):
                    category_action = "skipped_missing_product"
                    publish_error = None
                    skip_failure = True

        refreshed = _get_product_by_id(client, product["id"]) or product
        if (
            not skip_failure
            and hydrated
            and category_action == "category_applied"
            and not _is_category_consistent_with_resolution(
                category=refreshed.get("category") or category_after,
                resolution=hydrated,
            )
        ):
            try:
                rollback_result = _update_product_fields(
                    client=client,
                    product_id=product["id"],
                    product_type=source_fields_after.get("productType") or hydrated.product_type,
                    tags=source_fields_after.get("tags") or _merge_tags(
                        product,
                        hydrated.tags,
                        hydrated.category_label,
                        True,
                    ),
                    clear_category=True,
                )
                rollback_product = rollback_result.get("product") or {}
                source_fields_after = {
                    "productType": rollback_product.get("productType") or source_fields_after.get("productType") or "",
                    "tags": list(rollback_product.get("tags") or source_fields_after.get("tags") or []),
                }
                category_after = None
                category_action = _derive_review_action(hydrated)
                refreshed = _get_product_by_id(client, product["id"]) or refreshed
            except ShopifyGraphQLError:
                category_action = _derive_review_action(hydrated)
        missing_publications = _missing_publications(refreshed, target_names)
        if publish_error is None and missing_publications and not skip_failure:
            retry_inputs = [
                {"publicationId": publication_map[name]["id"]}
                for name in missing_publications
                if name in publication_map
            ]
            if retry_inputs:
                try:
                    retry_publish = client.graphql(
                        PUBLISH_PRODUCT,
                        {"id": product["id"], "input": retry_inputs},
                    )["publishablePublish"]
                    retry_errors = retry_publish.get("userErrors") or []
                    if retry_errors:
                        publish_error = retry_errors
                    else:
                        refreshed = _get_product_by_id(client, product["id"]) or refreshed
                except ShopifyGraphQLError as exc:
                    publish_error = str(exc)
        result_item = {
            "id": product["id"],
            "title": product["title"],
            "vendor": product["vendor"],
            "status": product["status"],
            "progress": {
                "current_in_run": index,
                "total_in_run": total_products,
                "remaining_in_run": max(total_products - index, 0),
                "processed_total_after_item": len(results) + 1,
            },
            "category_before": product.get("category"),
            "category_rule": hydrated.matched_rule if hydrated else None,
            "category_action": category_action,
            "category_after": refreshed.get("category") or category_after,
            "category_error": category_error,
            "source_fields_before": {
                "productType": product.get("productType") or "",
                "tags": list(product.get("tags") or []),
            },
            "source_fields_after": source_fields_after,
            "source_field_error": source_field_error,
            "attribute_suggestions": attribute_suggestions,
            "llm_status": item_llm_status,
            "llm_error": llm_error or None,
            "llm_response_text": llm_response_text or None,
            "llm_suggestion": _serialize_llm_suggestion(llm_suggestion),
            "new_arrivals_collection": NEW_ARRIVALS_COLLECTION_TITLE if new_arrivals_collection else None,
            "added_to_new_arrivals": added_to_collection,
            "collection_error": collection_error,
            "publish_error": publish_error,
            "published_to_current": _get_publication_names(refreshed),
        }
        results.append(result_item)
        _log_result_detail(
            index=index,
            total_products=total_products,
            result_item=result_item,
            target_names=target_names,
        )
        print(
            "[publish_vendor_catalog] "
            f"{index}/{total_products} done action={category_action} "
            f"collection={'yes' if added_to_collection else 'no'} "
            f"publish_error={'yes' if publish_error else 'no'} "
            f"source_error={'yes' if source_field_error else 'no'}"
        )

        report = _build_report(
            vendor=vendor,
            target_names=target_names,
            results=results,
            stopped=bool(stop_on_failure and (category_error or source_field_error or publish_error or collection_error)),
            llm_status=deepseek_runtime_status,
            total_discovered=total_discovered,
            processed_before_run=len(processed_ids),
            fully_published_before_run=fully_published_before,
            selected_for_run=total_products,
            pending_after_filter=pending_after_filter,
        )
        path = _write_report(report_path, report)
        report["report_path"] = str(path.resolve())

        if stop_on_failure and (category_error or source_field_error or publish_error or collection_error):
            report["stop_reason"] = {
                "product_id": product["id"],
                "title": product["title"],
                "category_error": category_error,
                "source_field_error": source_field_error,
                "collection_error": collection_error,
                "publish_error": publish_error,
            }
            _write_report(report_path, report)
            return report

    report = _build_report(
        vendor=vendor,
        target_names=target_names,
        results=results,
        stopped=False,
        llm_status=deepseek_runtime_status,
        total_discovered=total_discovered,
        processed_before_run=len(processed_ids),
        fully_published_before_run=fully_published_before,
        selected_for_run=total_products,
        pending_after_filter=pending_after_filter,
    )
    path = _write_report(report_path, report)
    report["report_path"] = str(path.resolve())
    return report


def _get_vendor_products(client: ShopifyAuthClient, vendor: str) -> list[dict]:
    products = []
    after = None
    query = f"vendor:{vendor}"
    page = 0
    while True:
        page += 1
        print(f"[publish_vendor_catalog] fetching product page {page} for query={query}")
        data = client.graphql(PRODUCTS_QUERY, {"first": 50, "after": after, "query": query})
        connection = data["products"]
        for edge in connection["edges"]:
            products.append(edge["node"])
        if not connection["pageInfo"]["hasNextPage"]:
            break
        after = connection["pageInfo"]["endCursor"]
    return products


def _get_product_by_id(client: ShopifyAuthClient, product_gid: str) -> dict:
    data = client.graphql(PRODUCT_BY_ID_QUERY, {"id": product_gid})
    product = data.get("product")
    if product:
        return product

    numeric_id = product_gid.split("/")[-1]
    data = client.graphql(PRODUCTS_QUERY, {"first": 1, "after": None, "query": f"id:{numeric_id}"})
    edges = data.get("products", {}).get("edges", [])
    if edges:
        return edges[0].get("node") or {}
    return {}


def _get_publication_map(client: ShopifyAuthClient) -> dict[str, dict]:
    data = client.graphql(PUBLICATIONS_QUERY)
    publications = {}
    for edge in data["publications"]["edges"]:
        node = edge["node"]
        publications[node["name"]] = node
    return publications


def _ensure_collection(client: ShopifyAuthClient, title: str) -> dict[str, Any] | None:
    data = client.graphql(COLLECTIONS_QUERY, {"query": f'title:"{title}"'})
    edges = data.get("collections", {}).get("edges", [])
    for edge in edges:
        node = edge.get("node") or {}
        if str(node.get("title") or "").strip().lower() == title.lower():
            return node

    created = client.graphql(COLLECTION_CREATE, {"input": {"title": title}})["collectionCreate"]
    user_errors = created.get("userErrors") or []
    if user_errors:
        raise ShopifyGraphQLError(str(user_errors))
    return created.get("collection")


def _add_product_to_collection(
    *,
    client: ShopifyAuthClient,
    collection_id: str,
    product_id: str,
) -> list[dict] | None:
    result = client.graphql(
        COLLECTION_ADD_PRODUCTS,
        {"id": collection_id, "productIds": [product_id]},
    )["collectionAddProducts"]
    user_errors = result.get("userErrors") or []
    ignorable = []
    fatal = []
    for error in user_errors:
        message = str((error or {}).get("message") or "")
        if "already exists" in message.lower() or "already in collection" in message.lower():
            ignorable.append(error)
        else:
            fatal.append(error)
    return fatal or None


def _get_publication_names(product: dict) -> list[str]:
    return [
        edge["node"]["publication"]["name"]
        for edge in (product.get("resourcePublicationsV2") or {}).get("edges", [])
    ]


def _format_category_name(category: dict | None) -> str:
    if not category:
        return "-"
    return str(category.get("fullName") or category.get("id") or "-").replace("\r", " ").replace("\n", " ")


def _format_product_type(value: str | None) -> str:
    return str(value or "").replace("\r", " ").replace("\n", " ").strip() or "-"


def _sanitize_log_text(value: Any) -> str:
    return str(value or "").replace("\r", " ").replace("\n", " ").strip()


def _format_llm_summary(result_item: dict) -> str:
    llm_status = result_item.get("llm_status") or "not_run"
    llm_suggestion = result_item.get("llm_suggestion") or {}
    if not llm_suggestion:
        return llm_status
    product_type = _format_product_type(llm_suggestion.get("product_type"))
    category_label = _sanitize_log_text(llm_suggestion.get("category_label")) or "-"
    confidence = llm_suggestion.get("confidence")
    confidence_text = f"{confidence:.2f}" if isinstance(confidence, float) else str(confidence or "-")
    return f"{llm_status} pt={product_type} label={category_label} conf={confidence_text}"


def _log_result_detail(
    *,
    index: int,
    total_products: int,
    result_item: dict,
    target_names: list[str],
) -> None:
    category_before = _format_category_name(result_item.get("category_before"))
    category_after = _format_category_name(result_item.get("category_after"))
    source_before = result_item.get("source_fields_before") or {}
    source_after = result_item.get("source_fields_after") or {}
    product_type_before = _format_product_type(source_before.get("productType"))
    product_type_after = _format_product_type(source_after.get("productType"))
    published = result_item.get("published_to_current") or []
    missing = [name for name in target_names if name not in published]
    attr_keys = sorted(_sanitize_log_text(key) for key in (result_item.get("attribute_suggestions") or {}).keys())
    rule_text = _sanitize_log_text(result_item.get("category_rule")) or "-"
    print(
        "[publish_vendor_catalog] "
        f"{index}/{total_products} detail "
        f"category={category_before} -> {category_after} | "
        f"productType={product_type_before} -> {product_type_after}",
        flush=True,
    )
    print(
        "[publish_vendor_catalog] "
        f"{index}/{total_products} detail "
        f"llm={_format_llm_summary(result_item)} | "
        f"rule={rule_text} | "
        f"attrs={','.join(attr_keys) if attr_keys else '-'}",
        flush=True,
    )
    print(
        "[publish_vendor_catalog] "
        f"{index}/{total_products} detail "
        f"collection={'yes' if result_item.get('added_to_new_arrivals') else 'no'} | "
        f"published={', '.join(published) if published else '-'} | "
        f"missing={', '.join(missing) if missing else '-'}",
        flush=True,
    )
    if result_item.get("llm_error"):
        print(f"[publish_vendor_catalog] {index}/{total_products} detail llm_error={_sanitize_log_text(result_item['llm_error'])}", flush=True)
    if result_item.get("category_error"):
        print(f"[publish_vendor_catalog] {index}/{total_products} detail category_error={_sanitize_log_text(result_item['category_error'])}", flush=True)
    if result_item.get("source_field_error"):
        print(f"[publish_vendor_catalog] {index}/{total_products} detail source_error={_sanitize_log_text(result_item['source_field_error'])}", flush=True)
    if result_item.get("collection_error"):
        print(f"[publish_vendor_catalog] {index}/{total_products} detail collection_error={_sanitize_log_text(result_item['collection_error'])}", flush=True)
    if result_item.get("publish_error"):
        print(f"[publish_vendor_catalog] {index}/{total_products} detail publish_error={_sanitize_log_text(result_item['publish_error'])}", flush=True)


def _missing_publications(product: dict, target_names: list[str]) -> list[str]:
    current = set(_get_publication_names(product))
    return [name for name in target_names if name not in current]


def _resolve_category_id(title: str) -> str | None:
    resolution = _resolve_category({"title": title})
    return resolution.category_id if resolution else None


def _resolve_category(product: dict | str) -> CategoryResolution | None:
    if isinstance(product, str):
        product = {"title": product}

    title = product.get("title") or ""
    normalized_title = _normalize_text(title)
    if "garden dining set" in normalized_title:
        return _rule_to_resolution(
            CategoryRule(
                category_id="gid://shopify/TaxonomyCategory/fr-15-2",
                product_type="Outdoor Dining Sets",
                category_label="outdoor-dining-sets",
                tags=("outdoor-living", "patio", "dining"),
                taxonomy_search="outdoor dining furniture",
                taxonomy_path_tokens=("outdoor", "furniture", "sets"),
                allow_category_update=True,
            ),
            "priority:garden-dining-set",
        )

    exact_match = CATEGORY_OVERRIDES.get(title)
    if exact_match is None:
        exact_match = NORMALIZED_CATEGORY_OVERRIDES.get(normalized_title)
    if exact_match:
        return _rule_to_resolution(exact_match, f"exact:{title[:80]}")

    search_blob = _build_category_search_blob(product)
    scored_rules: list[tuple[int, CategoryRule]] = []
    for rule in CATEGORY_KEYWORD_RULES:
        if rule.blocked_keywords and any(keyword in search_blob for keyword in rule.blocked_keywords):
            continue

        score = 0
        if rule.all_keywords and all(keyword in search_blob for keyword in rule.all_keywords):
            score += 3 * len(rule.all_keywords)
        if rule.any_keywords:
            score += sum(1 for keyword in rule.any_keywords if keyword in search_blob)
        if score:
            scored_rules.append((score, rule))

    if not scored_rules:
        return None

    scored_rules.sort(key=lambda item: item[0], reverse=True)
    best_rule = scored_rules[0][1]
    return _rule_to_resolution(best_rule, f"keyword:{best_rule.category_label}")


def _rule_to_resolution(rule: CategoryRule, matched_rule: str) -> CategoryResolution:
    return CategoryResolution(
        category_id=rule.category_id,
        product_type=rule.product_type,
        category_label=rule.category_label,
        tags=rule.tags,
        matched_rule=matched_rule,
        taxonomy_search=rule.taxonomy_search,
        taxonomy_path_tokens=rule.taxonomy_path_tokens,
        allow_category_update=rule.allow_category_update,
    )


def _hydrate_resolution(
    client: ShopifyAuthClient,
    resolution: CategoryResolution,
    taxonomy_cache: dict[str, str | None],
) -> CategoryResolution:
    resolved_category_id = resolution.category_id
    if resolution.taxonomy_search and not resolved_category_id:
        cache_key = f"{resolution.category_label}:{resolution.taxonomy_search}"
        if cache_key not in taxonomy_cache:
            taxonomy_cache[cache_key] = _search_taxonomy_category_id(
                client=client,
                category_label=resolution.category_label,
                search=resolution.taxonomy_search,
                path_tokens=resolution.taxonomy_path_tokens,
            )
        resolved_category_id = taxonomy_cache[cache_key] or resolved_category_id

    if resolution.allow_category_update and not resolved_category_id:
        return CategoryResolution(
            category_id=None,
            product_type=resolution.product_type,
            category_label=resolution.category_label,
            tags=resolution.tags,
            matched_rule=resolution.matched_rule,
            taxonomy_search=resolution.taxonomy_search,
            taxonomy_path_tokens=resolution.taxonomy_path_tokens,
            allow_category_update=False,
        )

    return CategoryResolution(
        category_id=resolved_category_id,
        product_type=resolution.product_type,
        category_label=resolution.category_label,
        tags=resolution.tags,
        matched_rule=resolution.matched_rule,
        taxonomy_search=resolution.taxonomy_search,
        taxonomy_path_tokens=resolution.taxonomy_path_tokens,
        allow_category_update=resolution.allow_category_update,
    )


def _search_taxonomy_category_id(
    *,
    client: ShopifyAuthClient,
    category_label: str = "",
    search: str,
    path_tokens: tuple[str, ...],
) -> str | None:
    search_variants = []
    for candidate in (
        search,
        " ".join(path_tokens),
        search.replace("-", " "),
    ):
        cleaned = str(candidate or "").strip()
        if cleaned and cleaned not in search_variants:
            search_variants.append(cleaned)

    expected_tokens = _build_expected_taxonomy_tokens(search, path_tokens)
    best_score = -1
    best_id = None
    seen_ids: set[str] = set()
    normalized_search = _normalize_text(search)
    for variant in search_variants:
        data = client.graphql(TAXONOMY_CATEGORY_SEARCH_QUERY, {"search": variant})
        nodes = (data.get("taxonomy") or {}).get("categories", {}).get("nodes", [])
        for node in nodes:
            node_id = str(node.get("id") or "")
            if not node_id or node_id in seen_ids or node.get("isArchived"):
                continue
            seen_ids.add(node_id)
            full_name = _normalize_text(node.get("fullName") or "")
            node_name = _normalize_text(node.get("name") or "")
            if _has_disallowed_taxonomy_tokens(
                category_label=category_label,
                full_name=full_name,
                node_name=node_name,
            ):
                continue
            token_matches = sum(
                1 for token in expected_tokens if token in full_name or token in node_name
            )
            if expected_tokens and token_matches == 0:
                continue
            score = 0
            if node.get("isLeaf"):
                score += 3
            score += token_matches * 4
            if normalized_search and normalized_search in full_name:
                score += 2
            if normalized_search and normalized_search == node_name:
                score += 5
            elif normalized_search and normalized_search in node_name:
                score += 3
            if score > best_score:
                best_score = score
                best_id = node_id
    return best_id


def _has_disallowed_taxonomy_tokens(
    *,
    category_label: str,
    full_name: str,
    node_name: str,
) -> bool:
    disallowed_tokens = TAXONOMY_DISALLOWED_TOKENS.get(category_label) or ()
    haystack = f"{full_name} {node_name}"
    return any(token in haystack for token in disallowed_tokens)


def _build_expected_taxonomy_tokens(search: str, path_tokens: tuple[str, ...]) -> tuple[str, ...]:
    expected_tokens: list[str] = []
    for value in (search, *path_tokens):
        for token in _normalize_text(value).split():
            if token in TAXONOMY_SEARCH_STOPWORDS:
                continue
            if len(token) <= 2 and token != "tv":
                continue
            if token not in expected_tokens:
                expected_tokens.append(token)
    return tuple(expected_tokens)


def _get_deepseek_client() -> tuple[Any | None, str]:
    try:
        settings = get_settings()
        if not settings.deepseek_api_key:
            return None, "disabled:no_api_key"
        return get_llm(provider="deepseek"), f"enabled:model={settings.deepseek_model}"
    except Exception as exc:
        return None, f"disabled:error={type(exc).__name__}"


def _classify_with_deepseek(
    *,
    llm_client: Any,
    product: dict,
    client: ShopifyAuthClient,
    taxonomy_cache: dict[str, str | None],
) -> LLMClassificationResult:
    try:
        response = llm_client.generate(
            _build_deepseek_fallback_prompt(product),
            temperature=0,
            text={"format": {"type": "json_object"}},
        )
        response_text = str(response.get("text", "") or "").strip()
    except Exception as exc:
        return LLMClassificationResult(
            status="request_error",
            error=f"{type(exc).__name__}: {exc}",
        )

    if not response_text:
        return LLMClassificationResult(status="empty_response")

    try:
        suggestion = _parse_deepseek_fallback_response(response_text)
    except Exception as exc:
        return LLMClassificationResult(
            status="parse_error",
            response_text=response_text[:4000],
            error=f"{type(exc).__name__}: {exc}",
        )

    if not suggestion.taxonomy_search:
        return LLMClassificationResult(
            status="parsed",
            suggestion=suggestion,
            response_text=response_text[:4000],
        )

    cache_key = f"llm:{suggestion.category_label}:{suggestion.taxonomy_search}"
    if cache_key not in taxonomy_cache:
        taxonomy_cache[cache_key] = _search_taxonomy_category_id(
            client=client,
            category_label=suggestion.category_label,
            search=suggestion.taxonomy_search,
            path_tokens=suggestion.path_tokens,
        )
    hydrated_suggestion = LLMFallbackSuggestion(
        product_type=suggestion.product_type,
        category_label=suggestion.category_label,
        taxonomy_search=suggestion.taxonomy_search,
        tags=suggestion.tags,
        path_tokens=suggestion.path_tokens,
        attributes=suggestion.attributes,
        confidence=suggestion.confidence,
        reason=suggestion.reason,
        category_id=taxonomy_cache[cache_key],
    )
    return LLMClassificationResult(
        status="parsed",
        suggestion=hydrated_suggestion,
        response_text=response_text[:4000],
    )


def _build_resolution_from_llm(llm_suggestion: LLMFallbackSuggestion) -> CategoryResolution:
    return CategoryResolution(
        category_id=llm_suggestion.category_id,
        product_type=llm_suggestion.product_type,
        category_label=llm_suggestion.category_label,
        tags=llm_suggestion.tags,
        matched_rule=f"llm:{llm_suggestion.category_label}",
        taxonomy_search=llm_suggestion.taxonomy_search,
        taxonomy_path_tokens=llm_suggestion.path_tokens,
        allow_category_update=_should_allow_llm_category_update(llm_suggestion),
    )


def _should_apply_llm_source_fields(
    *,
    resolution: CategoryResolution | None,
    llm_suggestion: LLMFallbackSuggestion,
    product: dict,
) -> bool:
    if not llm_suggestion.product_type or not llm_suggestion.category_label:
        return False
    if resolution is None:
        return True
    if not resolution.allow_category_update and llm_suggestion.category_id:
        return True
    if (
        resolution.category_label in LLM_OVERRIDEABLE_RULE_LABELS
        and llm_suggestion.category_label != resolution.category_label
        and llm_suggestion.confidence >= 0.85
    ):
        return True
    if not resolution.category_id:
        return True
    if not (product.get("productType") or "").strip():
        return True
    return False


def _should_apply_llm_suggestion(
    resolution: CategoryResolution | None,
    llm_suggestion: LLMFallbackSuggestion,
) -> bool:
    if resolution is None:
        return True
    if not resolution.allow_category_update and llm_suggestion.category_id:
        return True
    if (
        resolution.category_label in LLM_OVERRIDEABLE_RULE_LABELS
        and llm_suggestion.category_label != resolution.category_label
        and llm_suggestion.confidence >= 0.85
    ):
        return True
    if not resolution.category_id:
        return True
    return False


def _should_allow_llm_category_update(llm_suggestion: LLMFallbackSuggestion) -> bool:
    return bool(llm_suggestion.category_id)


def _should_clear_existing_category(
    *,
    existing_category: dict | None,
    resolution: CategoryResolution,
) -> bool:
    return False


def _build_resolution_expected_tokens(resolution: CategoryResolution) -> tuple[str, ...]:
    tokens: list[str] = []
    for token in resolution.category_label.split("-"):
        normalized = _normalize_text(token)
        if normalized and normalized not in GENERIC_CATEGORY_TOKENS and normalized not in tokens:
            tokens.append(normalized)
    for token in resolution.taxonomy_path_tokens:
        normalized = _normalize_text(token)
        for part in normalized.split():
            if part and part not in GENERIC_CATEGORY_TOKENS and part not in tokens:
                tokens.append(part)
    for token in _normalize_text(resolution.product_type).split():
        if token and token not in GENERIC_CATEGORY_TOKENS and token not in tokens:
            tokens.append(token)
    return tuple(tokens)


def _is_category_consistent_with_resolution(
    *,
    category: dict | None,
    resolution: CategoryResolution,
) -> bool:
    if not category:
        return False
    full_name = _normalize_text(category.get("fullName") or "")
    node_name = _normalize_text(str(full_name.split(">")[-1]).strip())
    if _has_disallowed_taxonomy_tokens(
        category_label=resolution.category_label,
        full_name=full_name,
        node_name=node_name,
    ):
        return False
    if resolution.category_id and category.get("id") == resolution.category_id:
        return True
    expected_tokens = _build_resolution_expected_tokens(resolution)
    if not expected_tokens:
        return bool(category.get("id") or category.get("fullName"))
    return any(token in full_name for token in expected_tokens)


def _derive_review_action(resolution: CategoryResolution) -> str:
    if resolution.matched_rule.startswith("llm:"):
        return "llm_suggested_review"
    return "category_suggested_review"


def _build_deepseek_fallback_prompt(product: dict) -> str:
    clean_description = _strip_html(product.get("descriptionHtml") or "")
    return (
        "You classify Shopify catalog products for a Doba importer.\n"
        "Use the title, tags, and description to infer the best product type, category label, taxonomy search phrase, "
        "path tokens, tags, and product attributes.\n"
        "Return JSON only with keys: product_type, category_label, taxonomy_search, path_tokens, tags, attributes, confidence, reason.\n"
        "Rules:\n"
        "- confidence must be 0 to 1.\n"
        "- category_label must be lowercase kebab-case.\n"
        "- taxonomy_search should be a short Shopify taxonomy search phrase.\n"
        "- path_tokens must be a short list of category path hints.\n"
        "- tags must be short lowercase tags.\n"
        "- attributes must be an object of string arrays.\n"
        "- reason must be a short English sentence.\n\n"
        f"title: {product.get('title') or ''}\n"
        f"vendor: {product.get('vendor') or ''}\n"
        f"existing_product_type: {product.get('productType') or ''}\n"
        f"tags: {json.dumps(product.get('tags') or [], ensure_ascii=False)}\n"
        f"description: {clean_description[:4000]}\n"
    )


def _parse_deepseek_fallback_response(text: str) -> LLMFallbackSuggestion:
    payload = json.loads(text)
    product_type = str(payload.get("product_type", "")).strip()
    category_label = _slugify_label(str(payload.get("category_label", "")).strip())
    taxonomy_search = str(payload.get("taxonomy_search", "")).strip()
    tags = tuple(_normalize_tag_list(payload.get("tags")))
    path_tokens = tuple(_normalize_string_list(payload.get("path_tokens")))
    confidence = max(0.0, min(1.0, float(payload.get("confidence", 0))))
    reason = str(payload.get("reason", "")).strip() or "deepseek-empty-reason"
    attributes = _normalize_attribute_payload(payload.get("attributes"))
    return LLMFallbackSuggestion(
        product_type=product_type,
        category_label=category_label,
        taxonomy_search=taxonomy_search,
        tags=tags,
        path_tokens=path_tokens,
        attributes=attributes,
        confidence=round(confidence, 2),
        reason=reason,
        category_id=None,
    )


def _build_search_blob(product: dict | str) -> str:
    if isinstance(product, str):
        product = {"title": product}

    parts = [
        product.get("title") or "",
        product.get("productType") or "",
        " ".join(product.get("tags") or []),
        _strip_html(product.get("descriptionHtml") or ""),
    ]
    return _normalize_text(" ".join(part for part in parts if part))


def _build_category_search_blob(product: dict | str) -> str:
    if isinstance(product, str):
        product = {"title": product}

    sanitized_tags = [
        tag
        for tag in (product.get("tags") or [])
        if not any(str(tag).lower().startswith(prefix) for prefix in EXCLUDED_CATEGORY_TAG_PREFIXES)
    ]
    parts = [
        product.get("title") or "",
        " ".join(sanitized_tags),
        _strip_html(product.get("descriptionHtml") or ""),
    ]
    return _normalize_text(" ".join(part for part in parts if part))


def _normalize_text(value: str) -> str:
    normalized = value.lower().replace('"', " ").replace("'", " ")
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


for _override_title, _override_rule in CATEGORY_OVERRIDES.items():
    NORMALIZED_CATEGORY_OVERRIDES.setdefault(_normalize_text(_override_title), _override_rule)


def _slugify_label(value: str) -> str:
    normalized = _normalize_text(value)
    return normalized.replace(" ", "-")


def _strip_html(value: str) -> str:
    return re.sub(r"<[^>]+>", " ", value)


def _merge_tags(
    product: dict,
    rule_tags: tuple[str, ...],
    category_label: str,
    review_required: bool,
) -> list[str]:
    clean_tags = []
    seen = set()
    additions = [
        *(product.get("tags") or []),
        "doba-import",
        "hermes-category-optimized",
        f"category:{category_label}",
        *(("needs-shopify-category-suggestion",) if review_required else ()),
        *rule_tags,
    ]
    for tag in additions:
        clean_tag = str(tag or "").strip()
        if not clean_tag:
            continue
        lowered = clean_tag.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        clean_tags.append(clean_tag[:255])
    return clean_tags[:250]


def _extract_attribute_suggestions(product: dict, resolution: CategoryResolution | None) -> dict[str, list[str]]:
    title_text = _normalize_text(product.get("title") or "")
    description_text = _normalize_text(_strip_html(product.get("descriptionHtml") or ""))
    search_blob = f"{title_text} {description_text}".strip()
    suggestions: dict[str, list[str]] = {}

    colors = _find_terms(title_text, COMMON_COLORS)
    if colors:
        suggestions["color"] = colors

    materials = _find_terms(title_text, COMMON_MATERIALS)
    if not materials:
        materials = _find_terms(description_text, COMMON_MATERIALS)
    if materials:
        suggestions["material"] = materials

    propulsion = []
    if _contains_term(title_text, "push"):
        propulsion.append("Push")
    if _contains_term(title_text, "self propelled") or _contains_term(title_text, "self propelled"):
        propulsion.append("Self-propelled")
    if propulsion:
        suggestions["propulsion_type"] = propulsion

    power_source = []
    if _contains_term(search_blob, "battery") or _contains_term(search_blob, "rechargeable"):
        power_source.append("Battery")
    if _contains_term(search_blob, "solar"):
        power_source.append("Solar")
    if _contains_term(search_blob, "ac power") or _contains_term(search_blob, "plug in") or _contains_term(search_blob, "electric"):
        power_source.append("AC Power")
    if power_source:
        suggestions["power_source"] = _dedupe(power_source)

    seating_capacity = re.findall(r"(\d+)[-\s]?person", title_text)
    if seating_capacity:
        suggestions["seating_capacity"] = [seating_capacity[0]]

    piece_counts = re.findall(r"set of (\d+)|(\d+)\s*pcs?", title_text)
    pieces = [value for group in piece_counts for value in group if value]
    if pieces:
        suggestions["piece_count"] = [pieces[0]]

    if resolution and resolution.category_label.startswith("halloween"):
        suggestions.setdefault("season", []).append("Halloween")

    return {key: _dedupe(values) for key, values in suggestions.items() if values}


def _find_terms(text: str, candidates: tuple[str, ...]) -> list[str]:
    return [candidate.title() for candidate in candidates if _contains_term(text, candidate)]


def _contains_term(text: str, candidate: str) -> bool:
    normalized_candidate = _normalize_text(candidate)
    if not normalized_candidate:
        return False
    pattern = r"(?<![a-z0-9])" + re.escape(normalized_candidate) + r"(?![a-z0-9])"
    return re.search(pattern, text) is not None


def _dedupe(values: list[str]) -> list[str]:
    output = []
    seen = set()
    for value in values:
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        output.append(value)
    return output


def _normalize_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    cleaned: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text:
            cleaned.append(text)
    return cleaned


def _normalize_tag_list(value: Any) -> list[str]:
    return [_slugify_label(item) for item in _normalize_string_list(value) if _slugify_label(item)]


def _normalize_attribute_payload(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        return {}
    output: dict[str, list[str]] = {}
    for key, items in value.items():
        clean_key = _slugify_label(str(key or "")).replace("-", "_")
        if not clean_key:
            continue
        clean_values = _normalize_string_list(items)
        if clean_values:
            output[clean_key] = _dedupe(clean_values)
    return output


def _merge_attribute_suggestions(
    base: dict[str, list[str]],
    extra: dict[str, list[str]],
) -> dict[str, list[str]]:
    merged = {key: list(values) for key, values in base.items()}
    for key, values in extra.items():
        merged[key] = _dedupe([*(merged.get(key) or []), *values])
    return merged


def _serialize_llm_suggestion(suggestion: LLMFallbackSuggestion | None) -> dict[str, Any] | None:
    if suggestion is None:
        return None
    return {
        "product_type": suggestion.product_type,
        "category_label": suggestion.category_label,
        "taxonomy_search": suggestion.taxonomy_search,
        "path_tokens": list(suggestion.path_tokens),
        "tags": list(suggestion.tags),
        "attributes": suggestion.attributes,
        "confidence": suggestion.confidence,
        "reason": suggestion.reason,
        "category_id": suggestion.category_id,
    }


def _is_missing_resource_error(value: Any) -> bool:
    if not value:
        return False
    if isinstance(value, str):
        lowered = value.lower()
        return any(message in lowered for message in MISSING_RESOURCE_MESSAGES)
    if isinstance(value, list):
        return any(_is_missing_resource_error(item) for item in value)
    if isinstance(value, dict):
        return any(_is_missing_resource_error(item) for item in value.values())
    return False


def _update_product_fields(
    *,
    client: ShopifyAuthClient,
    product_id: str,
    product_type: str,
    tags: list[str],
    category_id: str | None = None,
    clear_category: bool = False,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": product_id,
        "productType": product_type,
        "tags": tags,
    }
    if category_id:
        payload["category"] = category_id
    elif clear_category:
        payload["category"] = None
    return client.graphql(UPDATE_PRODUCT_FIELDS, {"product": payload})["productUpdate"]


def _update_source_metafields(
    *,
    client: ShopifyAuthClient,
    product: dict,
    resolution: CategoryResolution,
    category_action: str,
    attribute_suggestions: dict[str, list[str]],
    llm_suggestion: LLMFallbackSuggestion | None,
    llm_status: str,
    llm_error: str,
    llm_response_text: str,
) -> list[dict] | None:
    metafields = [
        {
            "ownerId": product["id"],
            "namespace": "hermes",
            "key": "source_vendor",
            "type": "single_line_text_field",
            "value": str(product.get("vendor") or "Doba"),
        },
        {
            "ownerId": product["id"],
            "namespace": "hermes",
            "key": "source_title",
            "type": "single_line_text_field",
            "value": str(product.get("title") or "")[:255],
        },
        {
            "ownerId": product["id"],
            "namespace": "hermes",
            "key": "derived_category_label",
            "type": "single_line_text_field",
            "value": resolution.category_label,
        },
        {
            "ownerId": product["id"],
            "namespace": "hermes",
            "key": "derived_product_type",
            "type": "single_line_text_field",
            "value": resolution.product_type[:255],
        },
        {
            "ownerId": product["id"],
            "namespace": "hermes",
            "key": "category_rule",
            "type": "single_line_text_field",
            "value": resolution.matched_rule[:255],
        },
        {
            "ownerId": product["id"],
            "namespace": "hermes",
            "key": "category_action",
            "type": "single_line_text_field",
            "value": category_action,
        },
        {
            "ownerId": product["id"],
            "namespace": "hermes",
            "key": "attribute_suggestions",
            "type": "json",
            "value": json.dumps(attribute_suggestions, ensure_ascii=False),
        },
        {
            "ownerId": product["id"],
            "namespace": "hermes",
            "key": "llm_status",
            "type": "single_line_text_field",
            "value": llm_status[:255],
        },
    ]
    if llm_error:
        metafields.append(
            {
                "ownerId": product["id"],
                "namespace": "hermes",
                "key": "llm_error",
                "type": "single_line_text_field",
                "value": llm_error[:255],
            }
        )
    if llm_response_text:
        metafields.append(
            {
                "ownerId": product["id"],
                "namespace": "hermes",
                "key": "llm_response_text",
                "type": "multi_line_text_field",
                "value": llm_response_text[:5000],
            }
        )
    if llm_suggestion is not None:
        metafields.extend(
            [
                {
                    "ownerId": product["id"],
                    "namespace": "hermes",
                    "key": "llm_category_confidence",
                    "type": "number_decimal",
                    "value": str(llm_suggestion.confidence),
                },
                {
                    "ownerId": product["id"],
                    "namespace": "hermes",
                    "key": "llm_category_reason",
                    "type": "single_line_text_field",
                    "value": llm_suggestion.reason[:255],
                },
                {
                    "ownerId": product["id"],
                    "namespace": "hermes",
                    "key": "llm_category_payload",
                    "type": "json",
                    "value": json.dumps(_serialize_llm_suggestion(llm_suggestion), ensure_ascii=False),
                },
            ]
        )
    result = client.graphql(
        UPSERT_PRODUCT_SOURCE_METAFIELDS,
        {"metafields": metafields},
    )["metafieldsSet"]
    user_errors = result.get("userErrors") or []
    return user_errors or None


def _load_existing_report(report_path: str) -> dict:
    path = Path(report_path)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _build_report(
    *,
    vendor: str,
    target_names: list[str],
    results: list[dict],
    stopped: bool,
    llm_status: str,
    total_discovered: int,
    processed_before_run: int,
    fully_published_before_run: int,
    selected_for_run: int,
    pending_after_filter: int,
) -> dict:
    processed_this_run = max(len(results) - processed_before_run, 0)
    remaining_after_run = max(
        total_discovered - len(results) - fully_published_before_run,
        0,
    )
    def _action(item: dict) -> str:
        return str(item.get("category_action") or "")

    def _category_error(item: dict) -> Any:
        return item.get("category_error")

    def _source_error(item: dict) -> Any:
        return item.get("source_field_error")

    def _publish_error(item: dict) -> Any:
        return item.get("publish_error")

    def _published_to_current(item: dict) -> list[str]:
        return list(item.get("published_to_current") or [])

    return {
        "vendor": vendor,
        "target_publications": target_names,
        "stopped_early": stopped,
        "llm_status": llm_status,
        "progress": {
            "total_discovered": total_discovered,
            "processed_before_run": processed_before_run,
            "selected_for_run": selected_for_run,
            "processed_this_run": processed_this_run,
            "fully_published_before_run": fully_published_before_run,
            "pending_after_filter_before_run": pending_after_filter,
            "remaining_after_run": remaining_after_run,
            "resume_enabled": processed_before_run > 0,
        },
        "summary": {
            "total_products": len(results),
            "category_updated_ok": sum(1 for item in results if _action(item) == "category_applied" and not _category_error(item)),
            "category_update_failed": sum(1 for item in results if _category_error(item)),
            "source_fields_updated_ok": sum(1 for item in results if item.get("category_rule") and not _source_error(item)),
            "source_fields_update_failed": sum(1 for item in results if _source_error(item)),
            "needs_shopify_category_suggestion": sum(1 for item in results if _action(item) in {"needs_shopify_suggestion", "category_suggested_review", "llm_suggested_review"}),
            "skipped_missing_products": sum(1 for item in results if _action(item) == "skipped_missing_product"),
            "llm_suggestions_generated": sum(1 for item in results if item.get("llm_suggestion")),
            "llm_status_parsed": sum(1 for item in results if item.get("llm_status") == "parsed"),
            "llm_status_parse_error": sum(1 for item in results if item.get("llm_status") == "parse_error"),
            "llm_status_request_error": sum(1 for item in results if item.get("llm_status") == "request_error"),
            "llm_status_empty_response": sum(1 for item in results if item.get("llm_status") == "empty_response"),
            "attribute_suggestions_generated": sum(1 for item in results if item.get("attribute_suggestions")),
            "added_to_new_arrivals_count": sum(1 for item in results if item.get("added_to_new_arrivals")),
            "collection_failed": sum(1 for item in results if item.get("collection_error")),
            "publish_requested_ok": sum(1 for item in results if not _publish_error(item)),
            "publish_failed": sum(1 for item in results if _publish_error(item)),
            "all_target_publications_count": sum(
                1 for item in results if set(target_names).issubset(set(_published_to_current(item)))
            ),
        },
        "results": results,
    }


def _write_report(report_path: str, report: dict) -> Path:
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
