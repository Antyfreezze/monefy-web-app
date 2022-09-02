"""Configuration for Sanic Application"""
import os

from sanic.log import LOGGING_CONFIG_DEFAULTS

os.makedirs(name="logs", exist_ok=True)

LOGGING_CONFIG_CUSTOM = LOGGING_CONFIG_DEFAULTS

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
