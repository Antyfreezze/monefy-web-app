"""Configuration for Sanic Application"""
import logging
import os
from logging import LogRecord

from sanic import Request
from sanic.exceptions import SanicException
from sanic.log import LOGGING_CONFIG_DEFAULTS

os.makedirs(name="logs", exist_ok=True)
LOGGING_CONFIG_CUSTOM = LOGGING_CONFIG_DEFAULTS

LOGGING_FORMAT = (
    "%(asctime)s - (%(name)s)[%(levelname)s][%(host)s]: "
    "%(request_id)s %(request)s %(message)s %(status)d %(byte)d"
)

old_factory = logging.getLogRecordFactory()


def record_factory(*args: str, **kwargs: str) -> LogRecord:
    """Function that return request id for log messages"""
    record = old_factory(*args, **kwargs)
    record.request_id = ""

    try:
        request = Request.get_current()
    except SanicException:
        ...
    else:
        record.request_id = str(request.id)

    return record


logging.setLogRecordFactory(record_factory)

LOGGING_CONFIG_CUSTOM["formatters"]["access"]["format"] = LOGGING_FORMAT

LOGGING_CONFIG_CUSTOM["handlers"]["internalFile"] = {
    "class": "logging.FileHandler",
    "formatter": "generic",
    "filename": "logs/monefy_app.log",
}
LOGGING_CONFIG_CUSTOM["handlers"]["accessFile"] = {
    "class": "logging.FileHandler",
    "formatter": "access",
    "filename": "logs/monefy_app.log",
}
LOGGING_CONFIG_CUSTOM["handlers"]["errorFile"] = {
    "class": "logging.FileHandler",
    "formatter": "generic",
    "filename": "logs/monefy_app.log",
}

LOGGING_CONFIG_CUSTOM["loggers"]["sanic.root"]["handlers"].append("internalFile")
LOGGING_CONFIG_CUSTOM["loggers"]["sanic.error"]["handlers"].append("errorFile")
LOGGING_CONFIG_CUSTOM["loggers"]["sanic.access"]["handlers"].append("accessFile")
