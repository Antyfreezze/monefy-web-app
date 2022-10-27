"""Dropbox utils module for Monefy Web application"""
import csv
import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from io import StringIO

from dropbox import Dropbox, DropboxOAuth2Flow
from dropbox.oauth import (BadRequestException, BadStateException,
                           CsrfException, NotApprovedException,
                           ProviderException)
from dropbox.users import FullAccount
from sanic.exceptions import NotFound
from sanic.log import logger

from src.common.utils import get_monefied_app


@dataclass
class DropboxUser:
    """Dropbox User info dataclass"""

    user_uuid = str(uuid.uuid4())
    account_type: str
    user_country: str
    user_email: str | None
    user_paired: bool
    user_locale: str
    user_name: str
    user_surname: str
    user_abbreviated_name: str
    user_profile_photo_url: str
    user_ref_link: str
    user_home_namespace_id: str
    user_root_namespace_id: str
    user_team: str | None
    user_team_member: str | None

    def __init__(self, dropbox_user_info: FullAccount) -> None:
        self.dropbox_user_info = dropbox_user_info
        self.set_user_info()

    def set_user_info(self) -> None:
        """Method that format Dropbox user response string to dataclass"""

        if self.dropbox_user_info.account_type.is_basic():
            self.account_type = "basic"
        elif self.dropbox_user_info.account_type.is_business():
            self.account_type = "business"
        elif self.dropbox_user_info.account_type.is_pro():
            self.account_type = "pro"
        self.account_type = self.dropbox_user_info.account_type.is_basic()
        self.user_country = self.dropbox_user_info.country
        self.user_email = (
            self.dropbox_user_info.email
            if self.dropbox_user_info.email_verified
            else None
        )
        self.user_paired = self.dropbox_user_info.is_paired
        self.user_locale = self.dropbox_user_info.locale
        self.user_name = self.dropbox_user_info.name.given_name
        self.user_surname = self.dropbox_user_info.name.surname
        self.user_abbreviated_name = self.dropbox_user_info.name.abbreviated_name
        self.user_profile_photo_url = self.dropbox_user_info.profile_photo_url
        self.user_ref_link = self.dropbox_user_info.referral_link
        self.user_home_namespace_id = self.dropbox_user_info.root_info.home_namespace_id
        self.user_root_namespace_id = self.dropbox_user_info.root_info.root_namespace_id
        self.user_team = self.dropbox_user_info.team
        self.user_team_member = self.dropbox_user_info.team_member_id


class DropboxClient:
    """
    Dropbox Client to interact with users information
    and Monefy backup files in Storage
    """

    monefy_backup_files_folder: str = os.environ.get("DROPBOX_PATH", "")
    csv_directory_path = os.path.join(os.getcwd(), "monefy_csv_files")
    json_directory_path = os.path.join(os.getcwd(), "monefy_json_files")

    def __init__(self, token: str) -> None:
        access_token = self.decrypt_access_token(token)
        self.dropbox_client = Dropbox(oauth2_access_token=access_token)

    @staticmethod
    def decrypt_access_token(token: str) -> str:
        """Decrypt existed user Dropbox access token from database"""
        monefied_app = get_monefied_app()

        return monefied_app.ctx.token_cryptography.decrypt(token).decode()

    def get_monefy_info(
        self,
    ) -> list[dict[str, str]]:
        """
        Get latest Monefy backup csv file from user Dropbox storage
        and transform it to JSON object
        """
        latest_monefy_backup_file = self.get_latest_monefy_csv_file()

        logger.info(f"reading: {latest_monefy_backup_file}")
        _, response = self.dropbox_client.files_download(
            self.monefy_backup_files_folder + latest_monefy_backup_file
        )
        monefy_data_response = response.content.decode(encoding="utf-8-sig").replace(
            "date,account,category,amount,currency,converted amount,currency,description",
            "date,account,category,amount,currency,converted amount,converted currency,description",
        )
        monefy_data_io = StringIO(monefy_data_response)
        csv_data = csv.DictReader(
            monefy_data_io, delimiter=","
        )  # delimiter char -  , ; and  decimal separator . ,
        return self.csv_file_to_json_object(csv_data)

    def download_monefy_info(self, file_name: str) -> str:
        """Save latest csv file with monefy transactions to local EC2 storage"""
        os.makedirs("monefy_csv_files", exist_ok=True)
        try:
            with open(f"monefy_csv_files/{file_name}", "wb") as monefy_file:
                _, response = self.dropbox_client.files_download(
                    self.monefy_backup_files_folder + file_name
                )
                logger.info(f"writing {file_name}")
                monefy_file.write(response.content)
        except IOError as io_error:
            logger.error(f"raised error: {io_error}")

        return file_name

    def get_latest_monefy_csv_file(self) -> str:
        """
        Get latest monefy backup csv file
        from existing csv files in Dropbox storage
        """
        file_names = [
            entry.name
            for entry in self.dropbox_client.files_list_folder(
                self.monefy_backup_files_folder
            ).entries
            if re.match("monefy-(.+?).csv", entry.name)
        ]
        if not file_names:
            logger.warning("user don't have monefy backup files")
            raise NotFound(
                f"Monefy csv backup file not found in Dropbox storage."
                f" Please upload Your Monefy backup file to {self.monefy_backup_files_folder}"
            )
        latest_monefy_datetime = max(
            map(
                lambda list_of_csv_files: datetime.strptime(
                    re.search("monefy-(.+?).csv", list_of_csv_files).group(1),
                    "%Y-%m-%d_%H-%M-%S",
                ),
                file_names,
            ),
            default=datetime.now(),
        ).strftime("%Y-%m-%d_%H-%M-%S")
        monefy_csv_file = f"monefy-{latest_monefy_datetime}.csv"
        logger.info(f"get file from dropbox: {monefy_csv_file}")
        return monefy_csv_file

    def upload_summarized_file(self, file_name: str) -> None:
        """Upload summarized monefy backup file information to Dropbox storage"""
        file_from = os.path.join(self.csv_directory_path, file_name)
        file_to = (
            f"{self.monefy_backup_files_folder}summarized_{os.path.basename(file_name)}"
        )
        with open(file_from, "rb") as binary_file:
            self.dropbox_client.files_upload(binary_file.read(), file_to)

    def get_dropbox_user_info(self) -> DropboxUser:
        """Get authorized Dropbox user information"""
        dp_user_info = self.dropbox_client.users_get_current_account()
        dp_user = DropboxUser(dp_user_info)
        return dp_user

    @staticmethod
    def csv_file_to_json_object(csv_data: csv.DictReader) -> list[dict[str, str]]:
        """Method for converting Monefy csv backup file to json like object"""
        logger.info("creating monefy json object from csv file")
        file_data = []
        for transaction in csv_data:
            file_data.append(transaction)
        return file_data


class DropboxAuthenticator:
    """
    Dropbox OAuth authentication class
    """

    app_key = os.environ.get("DROPBOX_APP_KEY")
    app_secret = os.environ.get("DROPBOX_APP_SECRET")
    app_uri = (
        "http://127.0.0.1:8000/auth"
        if os.environ.get("SANIC_LOCAL")
        else "https://monefied.xyz/auth"
    )

    def __init__(self) -> None:
        self.dropbox_auth_flow = DropboxOAuth2Flow(
            consumer_key=self.app_key,
            consumer_secret=self.app_secret,
            redirect_uri=self.app_uri,
            session={},
            csrf_token_session_key="dropbox-auth-csrf-token",
            token_access_type="online",
        )

    def start_dropbox_authentication(self) -> str:
        """
        Start user Dropbox OAuth2
        redirect user to allow application access to user storage
        """
        return self.dropbox_auth_flow.start()

    def finish_dropbox_authentication(self, parameters: dict[str, str]) -> str:
        """
        Method for finish Dropbox OAuth2
        redirect user back to application
        """
        try:
            authentication_result = self.dropbox_auth_flow.finish(
                query_params=parameters
            )
            return authentication_result
        except BadRequestException as bad_request_error:
            logger.error(f"Bad request error - {bad_request_error}")
            raise bad_request_error
        except BadStateException as bad_state_error:
            logger.error(f"Bad state error - {bad_state_error}")
            raise bad_state_error
        except CsrfException as csrf_error:
            logger.error(f"CSRF error  - {csrf_error}")
            raise csrf_error
        except NotApprovedException as not_approved_error:
            logger.error(f"Not approved error - {not_approved_error}")
            raise not_approved_error
        except ProviderException as provider_error:
            logger.error(f"Provided error {provider_error}")
            raise provider_error
