from unittest.mock import Mock, patch

import httpx

from shared.clients.doba import DobaClient


def test_doba_client_retries_transport_errors_before_success():
    client = DobaClient(
        base_url="https://openapi.doba.test",
        app_key="app-key",
        sign_type="RSA2",
        private_key="-----BEGIN PRIVATE KEY-----\nMIIBVwIBADANBgkqhkiG9w0BAQEFAASCAT8wggE7AgEAAkEAx\n-----END PRIVATE KEY-----",
    )

    success_response = Mock()
    success_response.raise_for_status.return_value = None

    mock_http_client = Mock()
    mock_http_client.__enter__ = Mock(return_value=mock_http_client)
    mock_http_client.__exit__ = Mock(return_value=False)
    mock_http_client.request.side_effect = [
        httpx.ConnectError("boom"),
        success_response,
    ]

    with patch("shared.clients.doba.httpx.Client", return_value=mock_http_client):
        with patch.object(client, "build_headers", return_value={"x": "1"}):
            response = client.get("/api/test")

    assert response is success_response
    assert mock_http_client.request.call_count == 2
