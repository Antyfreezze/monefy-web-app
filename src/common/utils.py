"""Common utilities for application"""
import json
from decimal import Decimal

from sanic import Sanic


def get_monefied_app() -> Sanic:
    """Get sanic monefy application instance"""
    return Sanic.get_app("Monefy-Web-App")


class DecimalEncoder(json.JSONEncoder):
    """Extend JSONEncoder with Decimal type checking"""

    def default(self, o):

        if isinstance(o, Decimal):
            return str(o)

        return json.JSONEncoder.default(self, o)
