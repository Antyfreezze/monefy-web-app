"""Monefy Application unittests for Monefy Service resources"""
from src.resources import monefy_service
from tests.conftest import MockDropboxClient, MockDropbox404Error


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
    assert response.body == b'{"monefy.csv":"test"}'
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
    assert response.body == b'{"message":["monefy.csv"]}'
    assert response.status == 200
