"""Media Cleaner — Flask application factory."""
import config  # noqa: F401 — load .env before other imports

from flask import Flask

from routes.api import api_bp
from routes.main import main_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
