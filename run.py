import click
from sanic import Sanic, Blueprint

from src.resources.monefy_service import MonefyInfo, DropboxWebhook, HealthCheck

app = Sanic("Monefy-parser")

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
def run_server(host, port, auto_reload, debug, access_log):
    """Run server with provided configuration"""
    app.run(
        host=host,
        port=port,
        auto_reload=auto_reload,
        debug=debug,
        access_log=access_log
    )


if __name__ == "__main__":
    run_server()
