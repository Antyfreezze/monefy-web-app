"""Module for additional configuration for application instance"""
import os
import sqlite3
from typing import Any, AnyStr, Callable, Dict, Optional, Type

from cryptography.fernet import Fernet
from sanic import Sanic
from sanic.config import SANIC_PREFIX, Config
from sanic.handlers import ErrorHandler
from sanic.request import Request
from sanic.router import Router
from sanic.signals import SignalRouter

from src.domain.dropbox_utils import DropboxAuthenticator
from src.resources.monefy_service import (data_aggregation_bp,
                                          dropbox_authentication_bp,
                                          dropbox_webhook_bp, healthcheck_bp,
                                          homepage_bp, monefy_info_bp)


class ApplicationLauncher(Sanic):
    """Application launcher class for additional configuration"""

    def __init__(
        self,
        name: str = "",
        config: Optional[Config] = None,
        ctx: Optional[Any] = None,
        router: Optional[Router] = None,
        signal_router: Optional[SignalRouter] = None,
        error_handler: Optional[ErrorHandler] = None,
        env_prefix: Optional[str] = SANIC_PREFIX,
        request_class: Optional[Type[Request]] = None,
        strict_slashes: bool = False,
        log_config: Optional[Dict[str, Any]] = None,
        configure_logging: bool = True,
        dumps: Optional[Callable[..., AnyStr]] = None,
        loads: Optional[Callable[..., Any]] = None,
        inspector: bool = False,
    ):
        super().__init__(
            name,
            config,
            ctx,
            router,
            signal_router,
            error_handler,
            env_prefix,
            request_class,
            strict_slashes,
            log_config,
            configure_logging,
            dumps,
            loads,
            inspector,
        )
        self.setup_app_config()
        self.setup_app_context()
        self.setup_app_blueprints()

    def setup_app_config(self) -> None:
        """Method that adds or edit application configuration variables"""
        self.config.FALLBACK_ERROR_FORMAT = "text"
        self.config.CORS_ORIGINS = (
            "http://localhost:8000"
            if self.config.get("LOCAL")
            else "https://monefied.xyz"
        )
        self.config.ALLOWED_ORIGINS = [
            "http://localhost:8000",
            "https://monefied.xyz",
            "https://www.dropbox.com/",
        ]
        self.config.SECRET = Fernet.generate_key()

    def setup_app_context(self) -> None:
        """Method that attach properties and data to ctx object"""
        db_path = f"{os.getcwd()}/monefy.db"
        self.ctx.dropbox_authenticator = DropboxAuthenticator()
        self.ctx.sqlite_connection = sqlite3.connect(db_path)
        self.ctx.sqlite_cursor = self.ctx.sqlite_connection.cursor()
        self.ctx.token_cryptography = Fernet(Fernet.generate_key())

        self.ctx.sqlite_cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT,
            account_id TEXT,
            access_token TEXT,
            username TEXT,
            photo TEXT
        )
            """
        )

    def setup_app_blueprints(self) -> None:
        """Method that adds existed blueprints to application"""
        app_blueprints = (
            homepage_bp,
            monefy_info_bp,
            data_aggregation_bp,
            healthcheck_bp,
            dropbox_webhook_bp,
            dropbox_authentication_bp,
        )
        for app_blueprint in app_blueprints:
            self.blueprint(app_blueprint)
