from __future__ import annotations

import bootstrap
from cryptography.hazmat.primitives import serialization

from shared.config import get_settings


def _to_private_pem(key_body: str) -> bytes:
    cleaned = key_body.strip().replace("\\n", "\n")
    if "BEGIN " in cleaned:
        return cleaned.encode("utf-8")
    return f"-----BEGIN PRIVATE KEY-----\n{cleaned}\n-----END PRIVATE KEY-----".encode("utf-8")


def main() -> None:
    settings = get_settings()
    if not settings.doba_private_key:
        raise SystemExit("DOBA_PRIVATE_KEY is empty.")

    private_key = serialization.load_pem_private_key(
        _to_private_pem(settings.doba_private_key),
        password=None,
    )
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    public_body = "".join(
        line.strip()
        for line in public_pem.splitlines()
        if "BEGIN PUBLIC KEY" not in line and "END PUBLIC KEY" not in line
    )

    print("DOBA App Key:")
    print(settings.doba_app_key)
    print()
    print("Derived Public Key PEM:")
    print(public_pem)
    print("Derived Public Key Body:")
    print(public_body)


if __name__ == "__main__":
    main()
