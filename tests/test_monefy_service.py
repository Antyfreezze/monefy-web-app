"""Monefy Application unittests for Monefy Service resources"""
import hmac
from hashlib import sha256

from src.resources import monefy_service
from tests.conftest import MockDropbox404Error, MockDropboxClient


def test_healthcheck(monefy_app):
    """Smoke test by healthcheck endpoint"""
    request, response = monefy_app.test_client.get("/healthcheck")

    assert request.method == "GET"
    assert response.body == b'{"message":"Hello world!"}'
    assert response.status == 200


def test_get_monefy_info(monefy_app, monkeypatch):
    """Unittests GET monefy information method, body, status"""

    def mock_dropbox():
        return MockDropboxClient()

    monkeypatch.setattr(monefy_service, "DropboxClient", mock_dropbox)
    request, response = monefy_app.test_client.get("/monefy/monefy_info")

    assert request.method == "GET"
    assert response.body == b'{"monefy-2022-01-01_01-01-01.csv":"test"}'
    assert response.status == 200


def test_get_monefy_info_not_found(monefy_app, monkeypatch):
    """Unittests GET method for monefy information method and 404 status"""

    def mock_dropbox():

        return MockDropbox404Error()

    monkeypatch.setattr(monefy_service, "DropboxClient", mock_dropbox)
    request, response = monefy_app.test_client.get("/monefy/monefy_info")

    assert request.method == "GET"
    assert response.status == 404


def test_post_monefy_info(monefy_app, monkeypatch):
    """Unittests that verify POST monefy information method, body and status"""

    def mock_dropbox():
        return MockDropboxClient()

    monkeypatch.setattr(monefy_service, "DropboxClient", mock_dropbox)
    request, response = monefy_app.test_client.post("/monefy/monefy_info")
    assert request.method == "POST"
    assert response.body == b'{"message":["monefy-2022-01-01_01-01-01.csv"]}'
    assert response.status == 200


def test_get_data_aggregation(monefy_app, monkeypatch):
    """Unittest that verify GET monefy data aggregation method with all available valid arguments"""

    def mock_dropbox():
        return MockDropboxClient()

    monkeypatch.setattr(monefy_service, "DropboxClient", mock_dropbox)
    monefy_app.test_client.post("/monefy/monefy_info")
    request, response = monefy_app.test_client.get(
        "/monefy_aggregation", params={"format": "json"}
    )
    assert request.method == "GET"
    assert response.status == 200

    request, response = monefy_app.test_client.get(
        "/monefy_aggregation", params={"format": "csv"}
    )
    assert request.method == "GET"
    assert response.status == 200

    request, response = monefy_app.test_client.get(
        "/monefy_aggregation", params={"format": "json", "summarized": "true"}
    )
    assert request.method == "GET"
    assert response.status == 200

    request, response = monefy_app.test_client.get(
        "/monefy_aggregation", params={"format": "csv", "summarized": "true"}
    )
    assert request.method == "GET"
    assert response.status == 200


def test_get_data_aggregation_not_acceptable(monefy_app, monkeypatch):
    """Unittest that verify GET monefy data aggregation
    method error response for invalid arguments"""

    def mock_dropbox():
        return MockDropboxClient()

    monkeypatch.setattr(monefy_service, "DropboxClient", mock_dropbox)
    monefy_app.test_client.post("/monefy/monefy_info")

    request, response = monefy_app.test_client.get(
        "/monefy_aggregation", params={"format": "xml"}
    )
    assert request.method == "GET"
    assert (
        response.body
        == b'{"message":"Provided format (xml) not supported for data aggregation.'
        b" Acceptable arguments - 'format - csv or json' and 'summarized (optional)' \"}"
    )
    assert response.status == 406

    request, response = monefy_app.test_client.get("/monefy_aggregation")
    assert request.method == "GET"
    assert (
        response.body
        == b'{"message":"Provided format (None) not supported for data aggregation.'
        b" Acceptable arguments - 'format - csv or json' and 'summarized (optional)' \"}"
    )
    assert response.status == 406


def test_get_dropbox_webhook(monefy_app):
    """Unittest for Dropbox signature webhook verification"""

    request, response = monefy_app.test_client.get(
        "/dropbox/dropbox_webhook", params={"challenge": "test_token"}
    )
    assert request.method == "GET"
    assert response.body == b"test_token"
    assert response.status == 200


def test_post_dropbox_webhook_200(monefy_app, monkeypatch):
    """Unittest for Dropbox webhook POST method with success status"""

    def mock_dropbox():
        return MockDropboxClient()

    monkeypatch.setattr(monefy_service, "DropboxClient", mock_dropbox)

    test_signature = hmac.new("TEST".encode(), "".encode(), sha256).hexdigest()
    request, response = monefy_app.test_client.post(
        "/dropbox/dropbox_webhook", headers={"X-Dropbox-Signature": test_signature}
    )
    assert request.method == "POST"
    assert response.body == b'{"message":["monefy-2022-01-01_01-01-01.csv"]}'
    assert response.status == 200


def test_post_dropbox_webhook_403(monefy_app):
    """Unittest for Dropbox webhook POST method with wrong signature comparison"""

    request, response = monefy_app.test_client.post("/dropbox/dropbox_webhook")

    assert request.method == "POST"
    assert response.status == 403
