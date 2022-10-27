"""Module for cookies configuration"""
from datetime import datetime
from typing import Any, Optional

from sanic.response import HTTPResponse


def set_cookie(
    response: HTTPResponse,
    key: str,
    value: Any,
    httponly: bool = False,
    secure: bool = True,
    samesite: str = "lax",
    domain: Optional[str] = None,
    expires: Optional[datetime] = None,
) -> None:
    """Function that setup cookie"""
    response.cookies[key] = value
    response.cookies[key]["httponly"] = httponly
    response.cookies[key]["path"] = "/"
    response.cookies[key]["secure"] = secure
    response.cookies[key]["samesite"] = samesite

    if domain:
        response.cookies[key]["domain"] = domain

    if expires:
        response.cookies[key]["expires"] = expires
