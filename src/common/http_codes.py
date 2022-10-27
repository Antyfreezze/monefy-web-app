"""Module for create extra HTTP codes that are not included to Sanic standard list"""
from sanic.exceptions import SanicException


class NotAcceptable(SanicException):
    """
    **Status**: 406 Not Acceptable
    """

    status_code = 406
    quiet = True
