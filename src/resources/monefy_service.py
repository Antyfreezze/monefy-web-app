"""Services for Monefy Web Application"""
import os
import hmac
from hashlib import sha256
from http import HTTPStatus

from sanic.log import logger
from sanic.views import HTTPMethodView
from sanic.response import json, text, HTTPResponse
from sanic.exceptions import Forbidden, NotFound

from src.domain.dropbox_utils import DropboxClient


class ViewWithDropboxClient(HTTPMethodView):
    """Sanic View for Dropbox Client"""

    def __init__(self):
        super().__init__()
        self.dropbox_client = DropboxClient()
        self.secret = os.environ.get("DROPBOX_APP_SECRET")


class HealthCheck(HTTPMethodView):
    """View for Smoke test"""

    async def get(self, request) -> HTTPResponse:
        """Function for smoke test"""
        return json({"message": "Hello world!"})


class MonefyInfo(ViewWithDropboxClient):
    """View for Monefy Web Application"""

    async def get(self, request) -> HTTPResponse:
        """Returns JSON formatted monefy transactions from csv files"""
        monefy_stats = self.dropbox_client.get_monefy_info()
        if not monefy_stats:
            raise NotFound("Monefy csv files not found")
        return json(monefy_stats)

    async def post(self, request) -> HTTPResponse:
        """Write existing monefy csv files with transaction to instance"""
        write_result = self.dropbox_client.write_monefy_info()
        return json({"message": write_result}, status=HTTPStatus.OK)


class DropboxWebhook(ViewWithDropboxClient):
    """View for Dropbox Webhook"""

    async def get(self, request) -> HTTPResponse:
        """Respond to the webhook verification (GET request)
        by echoing back the challenge parameter"""
        logger.info("verify dropbox webhook")
        resp = request.args.get("challenge")
        return text(
            resp,
            headers={"Content-Type": "text/plain", "X-Content-Type-Options": "nosniff"},
            status=HTTPStatus.OK,
        )

    async def post(self, request) -> HTTPResponse:
        """Write csv files stored in Dropbox storage to instance"""
        logger.info("write files by dropbox webhook %s", request.body)
        # Make sure this is a valid request from Dropbox
        signature = request.headers.get("X-Dropbox-Signature", "InvalidSignature")
        if not hmac.compare_digest(
            signature, hmac.new(self.secret.encode(), request.body, sha256).hexdigest()
        ):
            logger.error("Dropbox webhook validation check failed: Request forbidden")
            raise Forbidden("Request forbidden", status_code=HTTPStatus.FORBIDDEN)
        result = self.dropbox_client.write_monefy_info()
        return json({"message": result}, status=HTTPStatus.OK)
