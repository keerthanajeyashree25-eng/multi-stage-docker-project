"""Flask application package and Gunicorn entry point."""

from flask import Flask

from app.routes import bp


def create_app():
    application = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    application.config["MAX_CONTENT_LENGTH"] = 16 * 1024
    application.register_blueprint(bp)
    return application


app = create_app()