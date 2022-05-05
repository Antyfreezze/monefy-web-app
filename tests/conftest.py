"""PyTests configuration for Sanic Application"""
import shutil
from unittest.mock import MagicMock

import pytest_asyncio

from run import app
from src.domain import dropbox_utils
from src.domain.dropbox_utils import DropboxClient

csv_file = MagicMock()
csv_file.name = "monefy-2022-01-01_01-01-01.csv"

test_file = MagicMock()
test_file.entries = [csv_file]

ContentMock = MagicMock
ContentMock.content = (
    b"\xef\xbb\xbfdate,account,category,amount,"
    b"currency,converted amount,currency,description"
    b"\r\n12/12/2021,Cash,Salary,1111,USD,1111,USD,"
)


class MockDropbox:
    """Mock data for Dropbox utils tests"""

    @staticmethod
    def files_list_folder(*args, **kwargs):
        """Mocked test file for Unittests"""
        return test_file

    @staticmethod
    def files_download(*args, **kwargs):
        """Mock download method for Dropbox client"""
        return "test", ContentMock


class MockDropboxIOError(MockDropbox):
    """Mock IOError for Unittests"""

    @staticmethod
    def files_download(*args, **kwargs):
        raise IOError("Test IOError")


class MockDropboxClient:
    """Mocked Dropbox Client for Unittests"""

    @staticmethod
    def get_monefy_info():
        """Mocked Dropbox client get_monefy_info method for Unittests"""
        return {csv_file.name: "test"}

    @staticmethod
    def write_monefy_info():
        """Mocked Dropbox client write_monefy_info method for Unittests"""
        with open(f"monefy_csv_files/{csv_file.name}", "wb") as monefy_file:
            monefy_file.write(ContentMock.content)
        return [csv_file.name]


class MockDropbox404Error(MockDropboxClient):
    """Mock 404 Error raise exception for Unittests"""

    @staticmethod
    def get_monefy_info():
        """Mocked empty get monefy information from Dropbox Client"""
        return {}


@pytest_asyncio.fixture()
def monefy_app():
    """Mocked monefy app for Unittests"""
    monefy_test_app = app
    return monefy_test_app


@pytest_asyncio.fixture()
def dropbox_client(monkeypatch):
    """Mocked Dropbox Client for Unittests"""

    def mock_dropbox(*args, **kwargs):
        return MockDropbox()

    monkeypatch.setattr(dropbox_utils, "Dropbox", mock_dropbox)
    mocked_dropbox_client = DropboxClient()
    mocked_dropbox_client.folder = "test_folder"
    return mocked_dropbox_client


@pytest_asyncio.fixture()
def dropbox_error_client(monkeypatch):
    """Mock Dropbox Client with raised error for Unittests"""

    def mock_dropbox(*args, **kwargs):
        return MockDropboxIOError()

    monkeypatch.setattr(dropbox_utils, "Dropbox", mock_dropbox)
    mocked_dropbox_client = DropboxClient()
    mocked_dropbox_client.folder = "test_folder"
    return mocked_dropbox_client


@pytest_asyncio.fixture(autouse=True, scope="session")
def cleanup_on_teardown():
    """Cleanup logs' directory after tests session"""
    yield
    shutil.rmtree("logs")
    shutil.rmtree("monefy_csv_files")
    shutil.rmtree("monefy_json_files")
