from src.shared.contracts.product import DobaProductInput


def fetch_candidate_products(payload: dict) -> list[DobaProductInput]:
    products = payload.get("products", [])
    return [item if isinstance(item, DobaProductInput) else DobaProductInput.model_validate(item) for item in products]
