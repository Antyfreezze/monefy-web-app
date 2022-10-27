"""Services for Monefy Web Application"""
import hmac
import os
from hashlib import sha256
from http import HTTPStatus

from sanic import Blueprint
from sanic.exceptions import Forbidden
from sanic.log import logger
from sanic.request import Request
from sanic.response import HTTPResponse, file, json, redirect, text
from sanic.views import HTTPMethodView
from sanic_ext import render

from src.common.authentication import Authenticator, require_jwt_authentication
from src.common.http_codes import NotAcceptable
from src.domain.data_aggregator import MonefyDataAggregator
from src.domain.dropbox_utils import DropboxClient

homepage_bp = Blueprint("homepage_bp")
monefy_info_bp = Blueprint("monefy_info_bp")
dropbox_webhook_bp = Blueprint("dropbox_webhook_bp")
healthcheck_bp = Blueprint("healthcheck_bp")
data_aggregation_bp = Blueprint("data_aggregation_bp")
dropbox_authentication_bp = Blueprint("dropbox_authentication_bp")


class HealthCheck(HTTPMethodView, attach=healthcheck_bp, uri="/healthcheck"):
    """View for Smoke test"""

    @staticmethod
    async def get(request: Request) -> HTTPResponse:
        """Function for smoke test"""
        return json({"message": "Hello world!"})


class MonefyApplicationView(HTTPMethodView):
    """HTTP Method View child class with application authenticator"""

    authenticator = Authenticator()


class HomePageView(MonefyApplicationView, attach=homepage_bp, uri="/"):
    """Home page View"""

    async def get(self, request: Request) -> HTTPResponse:
        """Homepage route for guest and authenticated user"""
        return await self.authenticator.render_homepage_for_user_or_guest(request)

    async def post(self, request: Request) -> HTTPResponse:
        """Post request route for Dropbox authentication process"""
        return redirect("/auth", status=HTTPStatus.TEMPORARY_REDIRECT)


class DropboxAuthentication(
    MonefyApplicationView, attach=dropbox_authentication_bp, uri="/auth"
):
    """View for Dropbox Authentication"""

    async def get(self, request: Request) -> HTTPResponse:
        """Finish dropbox authentication process after redirect"""
        return await self.authenticator.finish_dropbox_authentication_request(request)

    async def post(self, request: Request) -> HTTPResponse:
        """Start Dropbox authentication process after post request"""
        response = self.authenticator.start_dropbox_authentication_request(request)
        return response


class MonefyInfo(MonefyApplicationView, attach=monefy_info_bp, uri="/info"):
    """View for Monefy Web Application"""

    decorators = [require_jwt_authentication]

    async def get(self, request: Request) -> HTTPResponse:
        """Returns JSON formatted monefy transactions from csv files"""
        dp_client = self.authenticator.get_user_dropbox_client(request)
        monefy_stats = dp_client.get_monefy_info()
        return await render("info.html", context={"monefy_data": monefy_stats})


class DropboxWebhook(HTTPMethodView, attach=dropbox_webhook_bp, uri="/dropbox-webhook"):
    """View for Dropbox Webhook"""

    @staticmethod
    async def get(request: Request) -> HTTPResponse:
        """Respond to the webhook verification (GET request)
        by echoing back the challenge parameter"""
        logger.info("verify dropbox webhook")
        if webhook_response := request.args.get("challenge"):
            return text(
                webhook_response,
                headers={
                    "Content-Type": "text/plain",
                    "X-Content-Type-Options": "nosniff",
                },
                status=HTTPStatus.OK,
            )
        raise Forbidden("Manual Dropbox Webhook request is forbidden")

    async def post(self, request: Request) -> HTTPResponse:
        """Write csv files stored in Dropbox storage to instance"""
        logger.info(f"write files by dropbox webhook {str(request.body)}")
        # Make sure this is a valid request from Dropbox
        signature = request.headers.get("X-Dropbox-Signature", "InvalidSignature")
        if not hmac.compare_digest(
            signature,
            hmac.new(
                os.environ.get("DROPBOX_APP_SECRET", "").encode(), request.body, sha256
            ).hexdigest(),
        ):
            logger.error("Dropbox webhook validation check failed: Request forbidden")
            raise Forbidden("Request forbidden", status_code=HTTPStatus.FORBIDDEN)
        logger.info(f"webhook post {request.body=}")
        if accounts := request.json.get("list_folder").get("accounts"):
            for account in accounts:
                # We need to respond quickly to the webhook request, so we do the
                # actual work in a separate thread. For more robustness, it's a
                # good idea to add the work to a reliable queue and process the queue
                # in a worker process.
                logger.info(account)
                user_access_token = request.app.ctx.sqlite_cursor.execute(
                    f"""
                                SELECT access_token FROM users
                                WHERE account_id = '{account}'
                                """
                ).fetchone()[0]
                dp_client = DropboxClient(user_access_token)
                data_aggregator = MonefyDataAggregator(dp_client, "csv", True)
                result_file = data_aggregator.get_result_file_data()
                dp_client.upload_summarized_file(result_file)

            return json({"message": "test webhook"})
        return json({"message": "no users in list folder"})


class MonefyDataAggregatorView(
    MonefyApplicationView, attach=data_aggregation_bp, uri="/aggregation"
):
    """View for Monefy Data Aggregation"""

    decorators = [require_jwt_authentication]

    async def get(self, request: Request) -> HTTPResponse:
        """Return Monefy file with spending's in json/csv format"""
        dp_client = self.authenticator.get_user_dropbox_client(request)

        logger.info(
            f"request data aggregation in "
            f"{request.args.get('format')} format"
            f"{', summarized' if request.args.get('summarized') else '.'}"
        )
        data_aggregator = MonefyDataAggregator(
            dp_client, request.args.get("format"), request.args.get("summarized")
        )
        try:
            result_file_path = data_aggregator.get_result_file_data()
            logger.info(f"--- result file name - {os.path.basename(result_file_path)}")
            return await file(
                result_file_path, filename=os.path.basename(result_file_path)
            )
        except NotAcceptable:
            logger.error(
                f"{request.args.get('format')} format is not supported for data aggregation"
            )
            return json(
                {
                    "message": f"Provided format ({request.args.get('format')}) "
                    f"not supported for data aggregation."
                    f" Acceptable arguments - 'format - csv or json' and 'summarized (optional)'"
                    f" Example: /aggregation?format=FORMAT&summarized=True "
                },
                status=HTTPStatus.NOT_ACCEPTABLE,
            )
