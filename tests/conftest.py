from unittest.mock import MagicMock

import pytest

from run import app
from src.domain import dropbox_utils
from src.domain.dropbox_utils import DropboxClient


csv_file = MagicMock()
csv_file.name = "test.csv"

test_file = MagicMock()
test_file.entries = [csv_file]

content_mock = MagicMock
content_mock.content = b'\xef\xbb\xbfdate,account,category,amount,currency,converted amount,currency,description' \
                       b'\r\n12/12/2021,Cash,Salary,1111,USD,1111,USD'


class MockDropbox:

    @staticmethod
    def files_list_folder(*args, **kwargs):
        return test_file

    @staticmethod
    def files_download(*args, **kwargs):
        return "test", content_mock


class MockDropboxIOError(MockDropbox):

    @staticmethod
    def files_download(*args, **kwargs):
        raise IOError("Test IOError")


class MockDropboxClient:

    @staticmethod
    def get_monefy_info():
        return {"monefy.csv": "test"}

    @staticmethod
    def write_monefy_info():
        return ["monefy.csv"]


class MockDropbox404Error(MockDropboxClient):

    @staticmethod
    def get_monefy_info():
        return {}


@pytest.fixture()
def monefy_app():
    monefy_test_app = app
    return monefy_test_app


@pytest.fixture()
def dropbox_client(monkeypatch):
    def mock_dropbox(*args, **kwargs):
        return MockDropbox()
    monkeypatch.setattr(dropbox_utils, "Dropbox", mock_dropbox)
    dropbox_client = DropboxClient()
    dropbox_client._folder = "test_folder"
    return dropbox_client


@pytest.fixture()
def dropbox_error_client(monkeypatch):
    def mock_dropbox(*args, **kwargs):
        return MockDropboxIOError()
    monkeypatch.setattr(dropbox_utils, "Dropbox", mock_dropbox)
    dropbox_client = DropboxClient()
    dropbox_client._folder = "test_folder"
    return dropbox_client
