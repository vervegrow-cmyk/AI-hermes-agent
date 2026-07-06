from __future__ import annotations

import json

import bootstrap
from src.modules.shopify_listing import query_shop_connection


def main() -> None:
    print(json.dumps(query_shop_connection(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
