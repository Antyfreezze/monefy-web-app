"""Unittests for implemented Dropbox client in Monefy Application"""
import logging
import shutil


def test_dropbox_get_monefy_csv(monkeypatch, dropbox_client):
    """Unittests get file from Dropbox storage"""
    csv_files = dropbox_client.get_monefy_info()

    assert list(csv_files.keys()) == ["test.csv"]


def test_dropbox_write_monefy_csv(dropbox_client):
    """Unittests writing monefy info to Dropbox"""
    csv_files = dropbox_client.write_monefy_info()
    assert csv_files == ["test.csv"]


def test_dropbox_write_monefy_io_error(dropbox_error_client, caplog):
    """Unittests exception raise for writing monefy information to Dropbox"""
    caplog.set_level(logging.ERROR)
    dropbox_error_client.write_monefy_info()
    assert "ERROR" in caplog.text

    shutil.rmtree("monefy_csv_files")
