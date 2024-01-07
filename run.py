"""Monefy-web-app - analyze and visualize data from Monefy App
 that will be parsed from csv formatted backup created in Monefy mobile application"""
from src.common.app_setup import ApplicationLauncher
from src.common.logger_config import LOGGING_CONFIG_CUSTOM

monefy_web_app = ApplicationLauncher("Monefy-Web-App", log_config=LOGGING_CONFIG_CUSTOM)
