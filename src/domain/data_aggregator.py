"""Data aggregation module for summarizing or return detailed transaction of Monefy Data"""
import csv
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterator

from sanic.log import logger

from utils import NotAcceptable


@dataclass
class MonefyBalance:
    """Dataclass for calculating Monefy balance"""

    categories: dict[str, int]
    income: int = 0
    expense: int = 0
    balance: int = 0

    def __init__(self, summarized_monefy_data: dict[str, int]):
        logger.info("creating monefy balance instance")
        self.categories = summarized_monefy_data
        self.calculate_current_balance()

    def calculate_current_balance(self) -> None:
        """Calculate total income, expenses and
        current balance by provided Monefy data"""
        logger.info("calculate monefy income, expense and balance")
        income_fields = ("salary", "savings", "deposits")
        for monefy_category, category_balance in self.categories.items():
            if monefy_category.lower() in income_fields:
                self.income += category_balance
            elif monefy_category:
                self.expense += category_balance
            self.balance = self.income + self.expense


class MonefyDataAggregator:
    """Monefy Data aggregation class that responsible for creating summarized
    or detailed transaction info for provided income and spending's"""

    monefy_csv_directory_path = os.path.join(
        os.getcwd(), "monefy_csv_files"
    )  # delimiter char -  , ; and  decimal separator . ,
    monefy_json_directory_path = os.path.join(os.getcwd(), "monefy_json_files")
    accepted_file_formats = ("json", "csv")

    def __init__(self, result_file_format: str, summarize_balance: str):
        self.result_file_format = result_file_format
        self.summarize_balance = summarize_balance

    def convert_csv_to_json(self) -> dict[str, list[dict[str, str]]]:
        """Method for converting csv Monefy data to json like object"""
        logger.info("converting csv to json")
        monefy_json: dict[str, list[dict[str, str]]] = {}
        monefy_csv_file = self.get_latest_monefy_csv_file()

        with open(
            os.path.join(self.monefy_csv_directory_path, monefy_csv_file),
            encoding="utf-8-sig",
        ) as monefy_csv_data:
            monefy_csv_data_reader = csv.DictReader(monefy_csv_data)
            self.monefy_csv_file_to_json_object(
                monefy_csv_file, monefy_csv_data_reader, monefy_json
            )
        return monefy_json

    def write_json_file(self, file_name: str, json_data: dict[Any, Any]) -> str:
        """Method for writing json files. Can accept file name and json_data as parameters"""
        logger.info("writing json file")
        os.makedirs(self.monefy_json_directory_path, exist_ok=True)
        monefy_json_file_path = os.path.join(
            self.monefy_json_directory_path, f"{os.path.splitext(file_name)[0]}.json"
        )
        with open(
            monefy_json_file_path, mode="w", encoding="utf-8-sig"
        ) as monefy_json_file:
            monefy_json_file.write(json.dumps(json_data, indent=4))

        return monefy_json_file_path

    def write_csv_file(self, file_name: str, json_object: dict[str, int]) -> str:
        """Method for writing csv files from json.
        Accept file name and json like object as parameters"""
        logger.info("writing csv file")
        os.makedirs(self.monefy_csv_directory_path, exist_ok=True)
        monefy_csv_file_path = os.path.join(self.monefy_csv_directory_path, file_name)
        with open(
            monefy_csv_file_path, "w", newline="", encoding="utf-8-sig"
        ) as monefy_summarized_file:
            monefy_csv_writer = csv.DictWriter(
                monefy_summarized_file, json_object.keys()
            )
            monefy_csv_writer.writeheader()
            monefy_csv_writer.writerow(json_object)
        return monefy_csv_file_path

    @staticmethod
    def monefy_csv_file_to_json_object(
        monefy_csv_file_name: str,
        monefy_csv_data: Iterator[dict[str, str]],
        monefy_json_object: dict[Any, Any],
    ) -> None:
        """Method for converting Monefy csv backup file to json like object"""
        logger.info("creating monefy json object from csv file")
        monefy_file = []
        for transaction in monefy_csv_data:
            monefy_file.append(transaction)

        monefy_json_object[monefy_csv_file_name] = monefy_file

    @staticmethod
    def unify_csv_header(monefy_csv_file_path: str) -> None:
        """Method for unifying csv file header for further use in json like object"""
        logger.info("unifying csv file headers")
        edited_header = (
            "date,account,category,amount,currency,"
            "converted amount,converted currency,description\n"
        )

        with open(monefy_csv_file_path, "r", encoding="utf-8-sig") as monefy_csv_data:
            monefy_edited_csv_data = monefy_csv_data.readlines()
            monefy_edited_csv_data[0] = edited_header

        with open(
            monefy_csv_file_path, "w", encoding="utf-8-sig"
        ) as monefy_edited_csv_file:
            monefy_edited_csv_file.writelines(monefy_edited_csv_data)

    def get_latest_monefy_csv_file(self) -> str:
        """Method that returns actual Monefy csv file by date"""
        logger.info("getting latest monefy csv file")
        monefy_csv_files = os.listdir(self.monefy_csv_directory_path)
        latest_monefy_datetime = max(
            map(
                lambda list_of_csv_files: datetime.strptime(
                    re.search("monefy-(.+?).csv", list_of_csv_files).group(1),
                    "%Y-%m-%d_%H-%M-%S",
                ),
                monefy_csv_files,
            )
        ).strftime("%Y-%m-%d_%H-%M-%S")
        monefy_csv_file = f"monefy-{latest_monefy_datetime}.csv"
        self.unify_csv_header(
            os.path.join(self.monefy_csv_directory_path, monefy_csv_file)
        )
        return monefy_csv_file

    def get_latest_monefy_csv_path(self) -> str:
        """Method that returns absolute path to latest Monefy csv file"""
        logger.info("getting latest monefy csv file path")
        return os.path.join(
            self.monefy_csv_directory_path, self.get_latest_monefy_csv_file()
        )

    def get_result_file(self) -> str:
        """Method for returning result file that depends on provided response headers.
        Result file can be summarized or detailed with each Monefy transaction"""
        logger.info("getting result file")
        result_file = ""
        if self.result_file_format in self.accepted_file_formats:
            if self.result_file_format == "csv":
                if self.summarize_balance:
                    logger.info("getting summarized monefy data in csv")
                    result_file = self.write_csv_file(
                        f"summarized_{self.get_latest_monefy_csv_file()}",
                        self.summarize_monefy_data(),
                    )
                else:
                    logger.info("getting monefy transactions data in csv")
                    result_file = self.get_latest_monefy_csv_path()
            elif self.result_file_format == "json":
                csv_file_name = self.get_latest_monefy_csv_file()
                if self.summarize_balance:
                    logger.info("getting summarized monefy data in json")
                    result_file = self.write_json_file(
                        f"summarized_{csv_file_name}", self.summarize_monefy_data()
                    )
                else:
                    logger.info("getting monefy transactions data in json")
                    result_file = self.write_json_file(
                        csv_file_name, self.convert_csv_to_json()
                    )
            return result_file
        logger.info(f"{self.result_file_format} format not supported")
        raise NotAcceptable(f"{self.result_file_format} not supported")

    def summarize_monefy_data(self) -> dict[str, int]:
        """Method that summarize detailed income and spending's from provided Monefy data"""
        logger.info("summarizing monefy data")
        monefy_json = self.convert_csv_to_json()
        summarized_monefy_data = {}
        monefy_file_name = self.get_latest_monefy_csv_file()
        for transaction in monefy_json[monefy_file_name]:
            if transaction["category"] not in summarized_monefy_data:
                summarized_monefy_data[transaction["category"]] = 0
            summarized_monefy_data[transaction["category"]] += int(
                transaction["amount"]
            )
        return summarized_monefy_data

    def create_monefy_balance(self) -> MonefyBalance:
        """Method that return dataclass instance of actual Monefy Balance"""
        monefy_balance = MonefyBalance(self.summarize_monefy_data())
        return monefy_balance
