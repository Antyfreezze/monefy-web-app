"""Dropbox utils module for Monefy Web application"""
import csv
import os
from io import StringIO

from dropbox import Dropbox
from sanic.log import logger

from src.domain.data_aggregator import MonefyDataAggregator


class DropboxClient:
    """Dropbox Client to interact with Monefy backup files in Storage"""

    _token: str = os.environ["DROPBOX_TOKEN"]
    folder: str = os.environ["DROPBOX_PATH"]

    def __init__(self) -> None:
        self.dropbox_client = Dropbox(self._token)

    def get_monefy_info(self) -> dict[str, str]:
        """Read existing csv files with monefy transactions history"""
        file_names = self.get_file_names()

        monefy_csv_backup_file: dict[str, str] = {}

        for file_name in file_names:
            logger.info(f"reading: {file_name}")
            _, response = self.dropbox_client.files_download(self.folder + file_name)
            csv_data = csv.DictReader(
                StringIO(response.content.decode(encoding="utf-8-sig"))
            )
            MonefyDataAggregator.monefy_csv_file_to_json_object(
                file_name, csv_data, monefy_csv_backup_file
            )

        return monefy_csv_backup_file

    def write_monefy_info(self) -> list[str]:
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
                    logger.info(f"writing {file_name}")
                    monefy_file.write(response.content)
                    saved_csv_files.append(file_name)
        except IOError as io_error:
            logger.error(f"raised error: {io_error}")

        return saved_csv_files

    def get_file_names(self) -> list[str]:
        """List existing csv files from Dropbox cloud"""
        file_names = [
            entry.name
            for entry in self.dropbox_client.files_list_folder(self.folder).entries
            if entry.name.endswith(".csv")
        ]
        logger.info(f"get files from dropbox: {file_names}")
        return file_names
