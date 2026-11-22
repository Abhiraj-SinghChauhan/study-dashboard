"""
app.py - Application factory. Assembles the Flask app from blueprints and
registers error handlers. Run `python app.py` to start the dev server.
"""
import os

from flask import Flask, render_template

from routes.main import main_bp
from routes.api import api_bp


def create_app(testing: bool = False) -> Flask:
    app = Flask(__name__)
    # Needed for flash(). Override with the SECRET_KEY env var outside local dev.
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    app.config["TESTING"] = testing

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.error("Unhandled server error: %s", e)
        return render_template("500.html"), 500

    return app


if __name__ == "__main__":
    # debug=True is for local development ONLY (it exposes an interactive debugger).
    create_app().run(debug=True)