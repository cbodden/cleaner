"""Media Cleaner — Flask application factory."""
import config  # noqa: F401 — load .env before other imports

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from config import DEBUG
from routes.api import api_bp
from routes.main import main_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    @app.errorhandler(Exception)
    def api_json_errors(e):
        """Return JSON for any uncaught exception on /api/* so the frontend never gets HTML.
        For non-API paths (e.g. /favicon.ico), pass through HTTPException so Flask serves 404 etc.
        """
        if not request.path.startswith("/api/"):
            if isinstance(e, HTTPException):
                return e.get_response(request.environ)
            raise e
        if isinstance(e, HTTPException):
            return jsonify(error=e.description or str(e)), e.code
        return jsonify(error=str(e)), 500

    return app


app = create_app()

if __name__ == "__main__":
    if DEBUG:
        app.run(host="0.0.0.0", port=5000, debug=True)
    else:
        import os
        import sys
        os.execv(
            sys.executable,
            [
                sys.executable, "-m", "gunicorn",
                "-w", "4", "-b", "0.0.0.0:5000",
                "wsgi:application",
            ],
        )
