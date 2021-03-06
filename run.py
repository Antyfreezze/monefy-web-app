"""Monefy-web-app - analyze and visualize data from Monefy App
 that will be parsed from csv formatted backup created in Monefy mobile application"""
import click
from sanic import Sanic, Blueprint

from config import LOGGING_CONFIG_CUSTOM
from src.resources.monefy_service import MonefyInfo, DropboxWebhook, HealthCheck

app = Sanic("Monefy-parser", log_config=LOGGING_CONFIG_CUSTOM)

monefy_bp = Blueprint("monefy_bp")
dropbox_bp = Blueprint("dropbox_bp")
healthcheck_bp = Blueprint("healthcheck_bp")

healthcheck_bp.add_route(HealthCheck.as_view(), "/healthcheck")
monefy_bp.add_route(MonefyInfo.as_view(), "/monefy_info")
dropbox_bp.add_route(DropboxWebhook.as_view(), "/dropbox_webhook")

app.blueprint(monefy_bp, url_prefix="/monefy")
app.blueprint(dropbox_bp, url_prefix="/dropbox")
app.blueprint(healthcheck_bp)


@click.command()
@click.option("--host", default="0.0.0.0")
@click.option("--port", default=1337)
@click.option("--auto-reload", default=False)
@click.option("--debug", default=False)
@click.option("--access_log", default=False)
def run_server(
    host="0.0.0.0", port=1337, auto_reload=False, debug=False, access_log=False
):
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
