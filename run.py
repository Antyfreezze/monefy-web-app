"""Monefy-web-app - analyze and visualize data from Monefy App
 that will be parsed from csv formatted backup created in Monefy mobile application"""
import click
from sanic import Blueprint, Sanic
from sanic_openapi import swagger_blueprint

from config import LOGGING_CONFIG_CUSTOM
from src.resources.monefy_service import (
    DropboxWebhook,
    HealthCheck,
    MonefyDataAggregatorView,
    MonefyInfo,
)

app = Sanic("Monefy-parser", log_config=LOGGING_CONFIG_CUSTOM)

monefy_bp = Blueprint("monefy_bp")
dropbox_bp = Blueprint("dropbox_bp")
healthcheck_bp = Blueprint("healthcheck_bp")
data_aggregation_bp = Blueprint("data_aggregation_bp")

healthcheck_bp.add_route(HealthCheck.as_view(), "/healthcheck")
monefy_bp.add_route(MonefyInfo.as_view(), "/monefy_info")
dropbox_bp.add_route(DropboxWebhook.as_view(), "/dropbox_webhook")
data_aggregation_bp.add_route(MonefyDataAggregatorView.as_view(), "/monefy_aggregation")

app.blueprint(monefy_bp, url_prefix="/monefy")
app.blueprint(dropbox_bp, url_prefix="/dropbox")
app.blueprint(healthcheck_bp)
app.blueprint(data_aggregation_bp)
app.blueprint(swagger_blueprint)


@click.command()
@click.option("--host", default="0.0.0.0")
@click.option("--port", default=1337)
@click.option("--auto-reload", default=False)
@click.option("--debug", default=False)
@click.option("--access_log", default=False)
def run_server(
    host: str = "0.0.0.0",
    port: int = 1337,
    auto_reload: bool = False,
    debug: bool = False,
    access_log: bool = False,
) -> None:
    """Run server with provided configuration"""
    app.run(
        host=host,
        port=port,
        auto_reload=auto_reload,
        debug=debug,
        access_log=access_log,
    )


if __name__ == "__main__":
    run_server()
