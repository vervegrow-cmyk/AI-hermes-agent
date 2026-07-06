from functools import lru_cache

import httpx


@lru_cache(maxsize=1)
def get_http_client() -> httpx.Client:
    return httpx.Client(timeout=30.0)

