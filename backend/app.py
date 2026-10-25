"""
Pharmacy Intelligence -- backend entry point
--------------------------------------------
Run with:
    python backend/app.py

Serves:
    - the frontend (static files) at /
    - the API blueprint at /api/*

The demo mode does NOT require a live upload to explore: the backend loads
the synthetic dataset in data/ at startup and serves it through /api/*.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, send_from_directory  # noqa: E402
from flask_cors import CORS  # noqa: E402

from backend.routes.api import api  # noqa: E402
from backend.data_processing import loader  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(ROOT, "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
app.json.ensure_ascii = False
CORS(app)
app.register_blueprint(api)

# Warm the dataset cache at startup so the first request isn't slow.
loader.load_all()


@app.get("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/<path:path>")
def static_proxy(path):
    full_path = os.path.join(FRONTEND_DIR, path)
    if os.path.isfile(full_path):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Pharmacy Intelligence backend running: http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
