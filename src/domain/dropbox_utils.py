"""Dropbox utils module for Monefy Web application"""
import os
import csv
from io import StringIO

from dropbox import Dropbox
from sanic.log import logger


class DropboxClient:
    """Dropbox Client to interact with Monefy backup files in Storage"""

    _token: str = os.environ.get("DROPBOX_TOKEN")
    folder: str = os.environ.get("DROPBOX_PATH")

    def __init__(self):
        self.dropbox_client = Dropbox(self._token)

    def get_monefy_info(self) -> dict:
        """Read existing csv files with monefy transactions history"""
        file_names = self.get_file_names()

        monefy_csv_backup_file = {}

        for file_name in file_names:
            logger.info("reading: %s", file_name)
            _, response = self.dropbox_client.files_download(self.folder + file_name)
            csv_data = csv.DictReader(
                StringIO(response.content.decode(encoding="utf-8-sig"))
            )
            monefy_file = []
            for transaction in csv_data:
                monefy_file.append(transaction)

            monefy_csv_backup_file[file_name] = monefy_file

        return monefy_csv_backup_file

    def write_monefy_info(self) -> list:
        """Save csv files with monefy transactions to instance"""
        file_names = self.get_file_names()
        saved_csv_files = []
        os.makedirs("monefy_csv_files", exist_ok=True)
        try:
            for file_name in file_names:
                with open(f"monefy_csv_files/{file_name}", "wb") as monefy_file:
                    _, response = self.dropbox_client.files_download(
                        self.folder + file_name
                    )
                    logger.info("writing %s", file_name)
                    monefy_file.write(response.content)
                    saved_csv_files.append(file_name)
        except IOError as io_error:
            logger.error("raised error: %s", io_error)

        return saved_csv_files

    def get_file_names(self) -> list:
        """List existing csv files from Dropbox cloud"""
        file_names = [
            entry.name
            for entry in self.dropbox_client.files_list_folder(self.folder).entries
            if entry.name.endswith(".csv")
        ]
        logger.info("get files from dropbox: %s", file_names)
        return file_names
