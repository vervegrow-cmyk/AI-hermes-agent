from shared.clients import DobaClient, build_doba_signature, build_doba_signing_string

def _generate_private_key_body() -> str:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    return (
        pem.replace("-----BEGIN PRIVATE KEY-----", "")
        .replace("-----END PRIVATE KEY-----", "")
        .strip()
    )


def test_build_doba_signing_string_is_stable():
    value = build_doba_signing_string("app-1", "RSA2", 1610501018721)
    assert value == "appKey=app-1&signType=RSA2&timestamp=1610501018721"


def test_build_doba_signature_returns_base64():
    private_key = _generate_private_key_body()
    signature = build_doba_signature(
        app_key="app-1",
        sign_type="RSA2",
        timestamp_ms=1610501018721,
        private_key=private_key,
    )
    assert isinstance(signature, str)
    assert len(signature) > 20


def test_doba_client_builds_headers_and_url():
    private_key = _generate_private_key_body()
    client = DobaClient(
        base_url="https://openapi.doba.com",
        app_key="app-1",
        sign_type="RSA2",
        private_key=private_key,
    )
    headers = client.build_headers(timestamp_ms=1610501018721)
    assert headers["appKey"] == "app-1"
    assert headers["signType"] == "RSA2"
    assert headers["timestamp"] == "1610501018721"
    assert headers["sign"]
    assert client.build_url("/api/category/doba/list") == "https://openapi.doba.com/api/category/doba/list"
