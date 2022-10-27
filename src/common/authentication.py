"""
Module for user authentication in monefy application

OAuth is an authorization protocol, not an authentication protocol.
! Dropbox should not be used as an identity provider.

Auth flow:
user make post request to /auth route to auth by Dropbox
The new endpoint sets some CSRF cookies and then forwards the user to the Dropbox Sign-On page
Once user allow access application to user Dropbox - user are redirected back to the app

User send the code that Dropbox generated to the auth endpoint.
That endpoint executes the authenticate handler

What does handler?
First, the handler does some checking to make sure it has the correct context and the Dropbox code
Once it has that code, it can take the next step in the Dropbox authentication flow
by sending auth_code and auth_state along
with the app_key and app_secret that Dropbox developer app console provides
Upon a successful exchange,
Dropbox will issue an access_token that can be used to send authenticated request to the Dropbox API

After this request is complete, the app needs to send a request
to fetch the user detail form Dropbox

With the user data in hand, the authenticate handler can take its final step
- fetch a user from the database or create a new user

When this is complete - we now have the ability to issue tokens from JWT
These tokens will provide access to the app, both directly to the API
using an Authorization header and through secure cookies
"""
from functools import wraps
from typing import Any, Callable

import jwt
from dropbox.oauth import OAuth2FlowResult
from sanic.exceptions import Unauthorized
from sanic.log import logger
from sanic.request import Request
from sanic.response import HTTPResponse, redirect
from sanic_ext import render

from src.common.cookies import set_cookie
from src.common.utils import get_monefied_app
from src.domain.dropbox_utils import DropboxClient, DropboxUser


class Authenticator:
    """Class for monefy application authentication"""

    @staticmethod
    def encrypt_access_token(token: str) -> str:
        """Encrypt authorized user Dropbox access token"""

        monefied_app = get_monefied_app()

        return monefied_app.ctx.token_cryptography.encrypt(token.encode()).decode(
            "utf-8"
        )

    @staticmethod
    def start_dropbox_authentication_request(request: Request) -> HTTPResponse:
        """Start user authentication process"""
        logger.info("start dropbox authentication")
        auth_url = request.app.ctx.dropbox_authenticator.start_dropbox_authentication()
        redirect_response = redirect(auth_url)
        return redirect_response

    async def finish_dropbox_authentication_request(
        self, request: Request
    ) -> HTTPResponse:
        """Finish authentication process and redirect to application homepage"""

        if (auth_code := request.args.get("code")) and (
            auth_state := request.args.get("state")
        ):
            logger.info("finish dropbox authentication")
            auth_query_parameters = {"code": auth_code, "state": auth_state}
            auth_user_info = (
                request.app.ctx.dropbox_authenticator.finish_dropbox_authentication(
                    auth_query_parameters
                )
            )
            return await self.get_authenticated_response(request, auth_user_info)
        logger.warning("get dropbox authentication route without required parameters")
        return redirect("/")

    async def get_authenticated_response(
        self, request: Request, user_auth_info: OAuth2FlowResult
    ) -> HTTPResponse:
        """Authenticate existed user or authenticate new one"""

        auth_info = {
            "access_token": self.encrypt_access_token(user_auth_info.access_token),
            "account_id": user_auth_info.account_id,
            "expires_at": user_auth_info.expires_at,
            "scope": user_auth_info.scope,
        }

        if user_info := self.get_user_if_exist(auth_info):
            self.update_user(auth_info)
            _, user_uuid, _, _, name, avatar = user_info
            logger.info(f"user {user_uuid} already exist, update user token")

            jwt_token = self.get_encoded_jwt_token(
                request, user_uuid, name, avatar, auth_info
            )
            response = await self.render_authenticated_response(
                request, auth_info, jwt_token
            )
            return response
        logger.info("authenticate new user")
        dropbox_client = self.get_user_dropbox_client(
            request, auth_info["access_token"]
        )
        dropbox_user_info = dropbox_client.get_dropbox_user_info()
        jwt_token = self.get_encoded_jwt_token(
            request,
            dropbox_user_info.user_uuid,
            dropbox_user_info.user_name,
            dropbox_user_info.user_profile_photo_url,
            auth_info,
        )
        self.create_user(dropbox_user_info, auth_info)
        response = await self.render_authenticated_response(
            request, auth_info, jwt_token
        )
        return response

    @staticmethod
    def get_user_if_exist(user_info: dict[str, str]) -> list[str] | None:
        """Check if user account id exist in database"""

        monefied_app = get_monefied_app()

        account_id = user_info["account_id"]
        existed_user_info = monefied_app.ctx.sqlite_cursor.execute(
            f"""
            SELECT * FROM users
            WHERE account_id = '{account_id}'
            """
        ).fetchone()
        return existed_user_info

    @staticmethod
    def get_encoded_jwt_token(
        request: Request,
        user_uuid: str,
        name: str,
        avatar: str,
        authentication_info: dict[str, str],
    ) -> str:
        """Encode user jwt token"""
        logger.info("encode user jwt token")
        jwt_token = jwt.encode(
            {
                "user_uuid": user_uuid,
                "user_name": name,
                "user_photo": avatar,
                "exp": authentication_info["expires_at"],
            },
            request.app.config.SECRET,
        )
        return jwt_token

    @staticmethod
    def create_user(
        dropbox_user_information: DropboxUser, authentication_info: dict[str, str]
    ) -> None:
        """Create new user in database"""
        monefied_app = get_monefied_app()

        logger.info("create new user in db")

        monefied_app.ctx.sqlite_cursor.execute(
            f"""
                    INSERT INTO users (uuid, account_id, access_token, username, photo)
                    VALUES (
                        '{dropbox_user_information.user_uuid}',
                        '{authentication_info["account_id"]}',
                        '{authentication_info["access_token"]}',
                        '{dropbox_user_information.user_name}',
                        '{dropbox_user_information.user_profile_photo_url}'
                    )
                    """
        )
        monefied_app.ctx.sqlite_connection.commit()

    @staticmethod
    def update_user(authentication_info: dict[Any, Any]) -> None:
        """Update user access token in database"""
        monefied_app = get_monefied_app()

        logger.info("update user info in db")
        monefied_app.ctx.sqlite_cursor.execute(
            f"""
                    UPDATE users
                    SET access_token = '{authentication_info["access_token"]}'
                    WHERE account_id = '{authentication_info["account_id"]}';
                    """
        )
        monefied_app.ctx.sqlite_connection.commit()

    @staticmethod
    async def render_authenticated_response(
        request: Request, authentication_info: dict[Any, Any], jwt_token: str
    ) -> HTTPResponse:
        """Render response after authentication"""
        response = await render(
            "auth.html",
            content_type="text/html; charset=utf-8",
            context={"message": "success auth with web app"},
        )
        set_cookie(
            response=response,
            domain="127.0.0.1" if request.app.config.get("LOCAL") else "monefied.xyz",
            key="jwt_token",
            value=jwt_token,
            httponly=True,
            samesite="strict",
            secure=True,
            expires=authentication_info["expires_at"],
        )
        return response

    def get_user_dropbox_client(
        self, request: Request, new_access_token: str | None = None
    ) -> DropboxClient:
        """Get user dropbox client after authentication or from existed jwt token"""
        monefied_app = get_monefied_app()

        if new_access_token:
            return DropboxClient(new_access_token)
        jwt_data = self.get_decoded_jwt_token(request)
        user_access_token = monefied_app.ctx.sqlite_cursor.execute(
            f"""
                    SELECT access_token FROM users
                    WHERE uuid = '{jwt_data["user_uuid"]}'
                    """
        ).fetchone()[0]
        return DropboxClient(user_access_token)

    @staticmethod
    def get_decoded_jwt_token(request: Request) -> dict[str, str]:
        """Decode user jwt token"""
        token = request.cookies.get("jwt_token", "")
        try:
            data = jwt.decode(token, request.app.config.SECRET, algorithms=["HS256"])
        except jwt.exceptions.InvalidSignatureError as invalid_signature_error:
            raise Unauthorized("invalid signature") from invalid_signature_error
        except jwt.exceptions.InvalidTokenError as invalid_token_error:
            raise Unauthorized("invalid token") from invalid_token_error
        else:
            return data

    async def render_homepage_for_user_or_guest(self, request: Request) -> HTTPResponse:
        """Method that render homepage response
        depends on user authentication status"""
        if request.cookies.get("jwt_token"):
            try:
                dp_client = self.get_user_dropbox_client(request)
            except Unauthorized:
                response = redirect("/")
                del response.cookies["jwt_token"]
                return response
            user_info = dp_client.get_dropbox_user_info()
            response = await render(
                "home.html",
                content_type="text/html; charset=utf-8",
                context={
                    "message": f"Hello {user_info.user_name}",
                    "avatar": user_info.user_profile_photo_url,
                    "name": user_info.user_name,
                    "authenticated": True,
                },
            )
            return response
        return await render(
            "home.html",
            context={
                "message": "Please authenticate with Dropbox",
                "authenticated": False,
            },
        )


def check_jwt_token(request: Request) -> bool:
    """Function that check if user cookies contain jwt token"""
    if not request.cookies.get("jwt_token"):
        return False

    try:
        jwt.decode(
            request.cookies.get("jwt_token", ""),
            request.app.config.SECRET,
            algorithms=["HS256"],
        )
    except jwt.exceptions.InvalidTokenError:
        return False
    else:
        return True


def require_jwt_authentication(
    wrapped: Callable[[Any, Any, Any], Any]
) -> Callable[[Any, Any, Any], Any]:
    """Decorator for application views
    that check if user authenticated"""

    def authentication_wrapper(
        route: Callable[[Any, Any, Any], Any]
    ) -> Callable[[Any, Any, Any], Any]:
        @wraps(route)
        async def check_user_authentication(
            request: Request, *args: Any, **kwargs: Any
        ) -> HTTPResponse:
            is_authenticated = check_jwt_token(request)
            if is_authenticated:
                response = await route(request, *args, **kwargs)
                return response
            return redirect("/")

        return check_user_authentication

    return authentication_wrapper(wrapped)
