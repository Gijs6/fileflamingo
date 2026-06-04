import os

from dotenv import load_dotenv
from flask import Flask, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix

from models import db
from routes import register_routes
from utils.filters import register_filters

load_dotenv(override=True)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.secret_key = os.getenv("SECRET_KEY", os.urandom(256).hex())
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DB_URI", "sqlite:///fileflamingo.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join(app.instance_path, "uploads")
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_UPLOAD_MB", "2048")) * 1024 * 1024

db.init_app(app)
register_filters(app)
register_routes(app)

os.makedirs(app.instance_path, exist_ok=True)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

with app.app_context():
    db.create_all()


@app.before_request
def method_override():
    if request.method == "POST":
        method = request.form.get("_method", "").upper()
        if method in ("PUT", "PATCH", "DELETE"):
            request.environ["REQUEST_METHOD"] = method


@app.errorhandler(404)
def not_found(_e):
    return render_template("error.jinja", code=404, title="Not found"), 404


@app.errorhandler(410)
def gone(_e):
    return render_template("error.jinja", code=410, title="Transfer expired"), 410


@app.errorhandler(413)
def too_large(_e):
    return render_template("error.jinja", code=413, title="File too large"), 413


if __name__ == "__main__":
    app.run(debug=True, port=5000)
