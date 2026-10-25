import os
from urllib.parse import urlparse

from dotenv import load_dotenv
from flask import Flask, abort, flash, render_template, request, session

from models import db
from routes import register_routes
from utils.auth import init_auth
from utils.errors import register_errors
from utils.filters import register_filters
from utils.headers import register_headers
from utils.proxy import TrustedProxyFix
from utils.toasts import register_toasts
from utils.version import register_version

load_dotenv(override=True)

app = Flask(__name__)
app.jinja_env.autoescape = True
app.wsgi_app = TrustedProxyFix(
    app.wsgi_app, os.getenv("TRUSTED_PROXIES", "router").split(",")
)

app.secret_key = os.getenv("SECRET_KEY", os.urandom(256).hex())
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DB_URI", "sqlite:///fileflamingo.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = True
app.config["UPLOAD_FOLDER"] = os.path.join(app.instance_path, "uploads")
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_UPLOAD_MB", "500")) * 1024 * 1024

db.init_app(app)
init_auth(app, home="admin.dashboard", scope="admin")
register_filters(app)
register_routes(app)
register_toasts(app)
register_headers(app)
register_version(app, "bird")
register_errors(
    app, "bird", user=lambda: "admin" if session.get("authenticated") else None
)

os.makedirs(app.instance_path, exist_ok=True)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

with app.app_context():
    db.create_all()


@app.before_request
def guard():
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        fetch_site = request.headers.get("Sec-Fetch-Site")
        origin = request.headers.get("Origin")
        if fetch_site and fetch_site not in ("same-origin", "none"):
            abort(403)
        if origin and origin != "null" and urlparse(origin).netloc != request.host:
            abort(403)


@app.before_request
def method_override():
    if request.method == "POST":
        method = request.form.get("_method", "").upper()
        if method in ("PUT", "PATCH", "DELETE"):
            request.environ["REQUEST_METHOD"] = method


@app.errorhandler(404)
def not_found(_e):
    return render_template(
        "error.jinja",
        code=404,
        title="Not found",
        description="The page or transfer you're looking for doesn't exist.",
    ), 404


@app.errorhandler(410)
def gone(_e):
    return render_template(
        "error.jinja",
        code=410,
        title="Transfer expired",
        description="This transfer has expired and its files have been deleted.",
    ), 410


@app.errorhandler(413)
def too_large(_e):
    if request.headers.get("HX-Request"):
        flash(
            f"The upload is larger than the server allows ({app.config['MAX_CONTENT_LENGTH'] // 1024 // 1024:,} MB). Try fewer or smaller files.",
            "error",
        )
        return "", 413
    return render_template(
        "error.jinja",
        code=413,
        title="File too large",
        description="The upload is larger than the server allows. Try fewer or smaller files.",
    ), 413


@app.errorhandler(500)
def server_error(_e):
    return render_template(
        "error.jinja",
        code=500,
        title="Server error",
        description="Something went wrong on our end. Try again later.",
    ), 500


if __name__ == "__main__":
    app.config["SESSION_COOKIE_SECURE"] = False
    app.run(host="0.0.0.0", port=4000, debug=True)
