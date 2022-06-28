"""Services for Monefy Web Application"""
import hmac
import os
from hashlib import sha256
from http import HTTPStatus

from sanic.exceptions import Forbidden, NotFound
from sanic.log import logger
from sanic.request import Request
from sanic.response import HTTPResponse, file, json, text
from sanic.views import HTTPMethodView

from src.domain.data_aggregator import MonefyDataAggregator
from src.domain.dropbox_utils import DropboxClient
from utils import NotAcceptable


class ViewWithDropboxClient(HTTPMethodView):
    """Sanic View for Dropbox Client"""

    def __init__(self) -> None:
        super().__init__()
        self.dropbox_client = DropboxClient()
        self.secret = os.environ.get("DROPBOX_APP_SECRET", "EMPTY")


class HealthCheck(HTTPMethodView):
    """View for Smoke test"""

    @staticmethod
    async def get(request: Request) -> HTTPResponse:
        """Function for smoke test"""
        return json({"message": "Hello world!"})


class MonefyInfo(ViewWithDropboxClient):
    """View for Monefy Web Application"""

    async def get(self, request: Request) -> HTTPResponse:
        """Returns JSON formatted monefy transactions from csv files"""
        monefy_stats = self.dropbox_client.get_monefy_info()
        if not monefy_stats:
            raise NotFound("Monefy csv files not found")
        return json(monefy_stats)

    async def post(self, request: Request) -> HTTPResponse:
        """Write existing monefy csv files with transaction to instance"""
        write_result = self.dropbox_client.write_monefy_info()
        return json({"message": write_result}, status=HTTPStatus.OK)


class DropboxWebhook(ViewWithDropboxClient):
    """View for Dropbox Webhook"""

    @staticmethod
    async def get(request: Request) -> HTTPResponse:
        """Respond to the webhook verification (GET request)
        by echoing back the challenge parameter"""
        logger.info("verify dropbox webhook")
        resp = request.args.get("challenge")
        return text(
            resp,
            headers={"Content-Type": "text/plain", "X-Content-Type-Options": "nosniff"},
            status=HTTPStatus.OK,
        )

    async def post(self, request: Request) -> HTTPResponse:
        """Write csv files stored in Dropbox storage to instance"""
        logger.info(f"write files by dropbox webhook {str(request.body)}")
        # Make sure this is a valid request from Dropbox
        signature = request.headers.get("X-Dropbox-Signature", "InvalidSignature")
        if not hmac.compare_digest(
            signature, hmac.new(self.secret.encode(), request.body, sha256).hexdigest()
        ):
            logger.error("Dropbox webhook validation check failed: Request forbidden")
            raise Forbidden("Request forbidden", status_code=HTTPStatus.FORBIDDEN)
        result = self.dropbox_client.write_monefy_info()
        return json({"message": result}, status=HTTPStatus.OK)


class MonefyDataAggregatorView(ViewWithDropboxClient):
    """View for Monefy Data Aggregation"""

    @staticmethod
    async def get(request: Request) -> HTTPResponse:
        """Return Monefy file with spending's in json/csv format"""
        logger.info(
            f"request data aggregation in "
            f"{request.args.get('format')} format, "
            f"summarized - {request.args.get('summarized')}"
        )
        data_aggregator = MonefyDataAggregator(
            request.args.get("format"), request.args.get("summarized")
        )
        try:
            result_file = data_aggregator.get_result_file()
            return await file(
                result_file, headers={"Content-Disposition": "attachment"}
            )
        except NotAcceptable:
            logger.error(
                f"{request.args.get('format')} format doesn't supported for data aggregation"
            )
            return json(
                {
                    "message": f"Provided format ({request.args.get('format')}) "
                    f"not supported for data aggregation."
                    f" Acceptable arguments - 'format - csv or json' and 'summarized (optional)' "
                },
                status=HTTPStatus.NOT_ACCEPTABLE,
            )
