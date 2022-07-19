"""Data aggregation module for summarizing or return detailed transaction of Monefy Data"""
import csv
import json
import os
import re
from datetime import datetime
from typing import Any, Iterator

from sanic.log import logger

from utils import NotAcceptable


class MonefyDataAggregator:
    """Monefy Data aggregation class that responsible for creating summarized
    or detailed transaction info for provided income and spending's"""

    csv_directory_path = os.path.join(
        os.getcwd(), "monefy_csv_files"
    )  # delimiter char -  , ; and  decimal separator . ,
    json_directory_path = os.path.join(os.getcwd(), "monefy_json_files")
    accepted_file_formats = ("json", "csv")

    def __init__(self, result_file_format: str, summarize_balance: str):
        self.result_file_format = result_file_format
        self.summarize_balance = summarize_balance

    def convert_csv_to_json(self) -> dict[str, list[dict[str, str]]]:
        """Method for converting csv Monefy data to json like object"""
        logger.info("converting csv to json")
        json_object: dict[str, list[dict[str, str]]] = {}
        csv_file = self.get_latest_csv_file()

        with open(
            os.path.join(self.csv_directory_path, csv_file),
            encoding="utf-8-sig",
        ) as csv_data:
            csv_data_reader = csv.DictReader(csv_data)
            self.csv_file_to_json_object(
                csv_file, csv_data_reader, json_object
            )
        return json_object

    def _write_json_file(self, file_name: str, json_object: dict[Any, Any]) -> str:
        """Method for writing json files. Can accept file name and json_data as parameters"""
        json_file_path = os.path.join(
            self.json_directory_path, f"{os.path.splitext(file_name)[0]}.json"
        )
        with open(
            json_file_path, mode="w", encoding="utf-8-sig"
        ) as json_file:
            json_file.write(json.dumps(json_object, indent=4))

        return json_file_path

    def _write_csv_file(self, file_name: str, json_object: dict[str, int]) -> str:
        """Method for writing csv files from json.
        Accept file name and json like object as parameters"""
        csv_file_path = os.path.join(
            self.csv_directory_path, file_name
        )
        with open(
            csv_file_path, "w", newline="", encoding="utf-8-sig"
        ) as summarized_file:
            csv_writer = csv.DictWriter(
                summarized_file, json_object.keys()
            )
            csv_writer.writeheader()
            csv_writer.writerow(json_object)
        return csv_file_path

    def _write_file(self, file_name: str, json_data: dict[Any, Any]) -> str:
        """Method for writing files from json with provided format.
        Accept file name, json like object and file format as parameters"""
        logger.info(f"writing {self.result_file_format} file")
        if self.result_file_format == "csv" and not self.summarize_balance:
            return self.get_latest_csv_path()
        if self.result_file_format == "csv":
            os.makedirs(self.csv_directory_path, exist_ok=True)
            return self._write_csv_file(file_name, json_data)
        if self.result_file_format == "json":
            os.makedirs(self.json_directory_path, exist_ok=True)
            return self._write_json_file(file_name, json_data)
        logger.info(f"{self.result_file_format} format not supported")
        raise NotAcceptable(f"{self.result_file_format} not supported")

    @staticmethod
    def csv_file_to_json_object(
        csv_file_name: str,
        csv_data: Iterator[dict[str, str]],
        json_object: dict[Any, Any],
    ) -> None:
        """Method for converting Monefy csv backup file to json like object"""
        logger.info("creating monefy json object from csv file")
        file = []
        for transaction in csv_data:
            file.append(transaction)

        json_object[csv_file_name] = file

    @staticmethod
    def unify_csv_header(csv_file_path: str) -> None:
        """Method for unifying csv file header for further use in json like object"""
        logger.info("unifying csv file headers")
        edited_header = (
            "date,account,category,amount,currency,"
            "converted amount,converted currency,description\n"
        )

        with open(csv_file_path, "r", encoding="utf-8-sig") as csv_data:
            edited_csv_data = csv_data.readlines()
            edited_csv_data[0] = edited_header

        with open(
            csv_file_path, "w", encoding="utf-8-sig"
        ) as edited_csv_file:
            edited_csv_file.writelines(edited_csv_data)

    def get_latest_csv_file(self) -> str:
        """Method that returns actual Monefy csv file by date"""
        logger.info("getting latest monefy csv file")
        monefy_csv_files = os.listdir(self.csv_directory_path)
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
            os.path.join(self.csv_directory_path, monefy_csv_file)
        )
        return monefy_csv_file

    def get_latest_csv_path(self) -> str:
        """Method that returns absolute path to latest Monefy csv file"""
        logger.info("getting latest monefy csv file path")
        return os.path.join(
            self.csv_directory_path, self.get_latest_csv_file()
        )

    def get_result_file(self) -> str:
        """Method for returning result file that depends on provided response headers.
        Result file can be summarized or detailed with each Monefy transaction"""
        logger.info(
            f"getting monefy result file in {self.result_file_format}."
            f" summarized - {self.summarize_balance}"
        )
        if self.summarize_balance:
            result_file = self._write_file(
                f"summarized_{self.get_latest_csv_file()}",
                self.summarize_data(),
            )
        else:
            logger.info("getting monefy transactions data in json")
            result_file = self._write_file(
                self.get_latest_csv_file(), self.convert_csv_to_json()
            )
        return result_file

    def summarize_data(self) -> dict[str, int]:
        """Method that summarize detailed income and spending's from provided Monefy data"""
        logger.info("summarizing monefy data")
        json_object = self.convert_csv_to_json()
        summarized_data = {}
        file_name = self.get_latest_csv_file()
        for transaction in json_object[file_name]:
            if transaction["category"] not in summarized_data:
                summarized_data[transaction["category"]] = 0
            summarized_data[transaction["category"]] += int(
                transaction["amount"]
            )
        return summarized_data
