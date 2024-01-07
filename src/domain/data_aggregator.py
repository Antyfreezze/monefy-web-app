"""Data aggregation module for summarizing or return detailed transaction of Monefy Data"""
import csv
import datetime
import json
import os
from decimal import Decimal

from sanic.log import logger

from src.common.http_codes import NotAcceptable
from src.domain.dropbox_utils import DropboxClient
from src.common.utils import DecimalEncoder


class MonefyDataAggregator:
    """Monefy Data aggregation class that responsible for creating summarized
    or detailed transaction info for provided income and spending's"""

    csv_directory_path = os.path.join(os.getcwd(), "monefy_csv_files")
    json_directory_path = os.path.join(os.getcwd(), "monefy_json_files")
    accepted_file_formats = ("json", "csv")

    def __init__(
        self,
        user_dropbox_client: DropboxClient,
        result_file_format: str,
        summarize_balance: bool,
    ):
        self.user_dropbox_client = user_dropbox_client
        self.result_file_format = result_file_format
        self.summarize_balance = summarize_balance

    def _write_json_file(
        self, file_name: str, json_object: list[dict[str, str]] | dict[str, int]
    ) -> str:
        """Method for writing json files. Can accept file name and json_data as parameters"""
        os.makedirs(self.json_directory_path, exist_ok=True)
        json_file_path = os.path.join(self.json_directory_path, f"{file_name}.json")
        with open(json_file_path, mode="w", encoding="utf-8-sig") as json_file:
            json_file.write(json.dumps(json_object, indent=4, cls=DecimalEncoder))

        return json_file_path

    def _write_csv_file(
        self, file_name: str, json_object: list[dict[str, str]] | dict[str, int]
    ) -> str:
        """Method for writing csv files from json.
        Accept file name and json like object as parameters"""
        csv_file_path = os.path.join(self.csv_directory_path, f"{file_name}.csv")
        with open(csv_file_path, "w", newline="", encoding="utf-8-sig") as monefy_file:
            if isinstance(json_object, dict):
                csv_writer = csv.DictWriter(monefy_file, json_object.keys())
                csv_writer.writeheader()
                csv_writer.writerow(json_object)
            elif isinstance(json_object, list):
                csv_writer = csv.DictWriter(monefy_file, json_object[0].keys())
                csv_writer.writeheader()
                csv_writer.writerows(json_object)
        return csv_file_path

    def _write_file(self, json_data: list[dict[str, str]]) -> str:
        """
        Method for writing files from json with provided format.
        Accept file name, json like object and file format as parameters"""
        logger.info(f"writing {self.result_file_format} file")
        file_name = f"monefy-{datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}"
        if self.result_file_format == "csv" and self.summarize_balance:
            summarized_data = self.summarize_data(json_data)
            return self._write_csv_file(f"summarized_{file_name}", summarized_data)
        if self.result_file_format == "json" and self.summarize_balance:
            summarized_data = self.summarize_data(json_data)
            return self._write_json_file(f"summarized_{file_name}", summarized_data)
        if self.result_file_format == "csv":
            return self._write_csv_file(file_name, json_data)
        if self.result_file_format == "json":
            return self._write_json_file(file_name, json_data)
        logger.warning(f"{self.result_file_format} format not supported")
        raise NotAcceptable(f"{self.result_file_format} not supported")

    def get_result_file_data(self) -> str:
        """Method for returning result file data that depends on provided response headers.
        Result file can be summarized or detailed with each Monefy transaction"""
        logger.info(
            f"getting monefy result file in {self.result_file_format}"
            f"{'.' if not self.summarize_balance else ' summarized.'}"
        )
        result_file_data = self._write_file(self.user_dropbox_client.get_monefy_info())
        return result_file_data

    @staticmethod
    def summarize_data(transactions_list: list[dict[str, str]]) -> dict[str, int]:
        """Method that summarize detailed income and spending's from provided Monefy data"""
        logger.info("summarizing monefy data")
        summarized_data = {
            "income": 0,
            "expense": 0,
            "balance": 0
        }
        for transaction in transactions_list:

            if Decimal(transaction["amount"]) < 0:
                summarized_data["expense"] += Decimal(transaction["amount"])
            elif Decimal(transaction["amount"]) > 0:
                summarized_data["income"] += Decimal(transaction["amount"])

            if transaction["category"] not in summarized_data:
                summarized_data[transaction["category"]] = 0
            summarized_data[transaction["category"]] += Decimal(transaction["amount"])

            summarized_data["balance"] = summarized_data["income"] + summarized_data["expense"]
        return summarized_data
