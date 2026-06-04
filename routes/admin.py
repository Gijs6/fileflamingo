import os

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

from models import Transfer, db
from utils.auth import admin_required, is_admin

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/login")
def login():
    if is_admin():
        return redirect(url_for("admin.dashboard"))
    return render_template("admin/login.jinja")


@admin_bp.post("/login")
def do_login():
    password = request.form.get("password", "")
    stored_hash = os.getenv("PASSWORD_HASH", "")

    if stored_hash and check_password_hash(stored_hash, password):
        session["admin"] = True
        return redirect(url_for("admin.dashboard"))

    flash("Incorrect password.", "error")
    return redirect(url_for("admin.login"))


@admin_bp.post("/logout")
@admin_required
def logout():
    session.clear()
    return redirect(url_for("admin.login"))


@admin_bp.get("/")
@admin_required
def dashboard():
    transfers = Transfer.query.order_by(Transfer.created_at.desc()).all()
    total_size = sum(t.total_size for t in transfers)
    total_files = sum(len(t.files) for t in transfers)
    return render_template(
        "admin/dashboard.jinja",
        transfers=transfers,
        total_size=total_size,
        total_files=total_files,
    )


@admin_bp.get("/transfers")
@admin_required
def transfers_table():
    transfers = Transfer.query.order_by(Transfer.created_at.desc()).all()
    total_size = sum(t.total_size for t in transfers)
    total_files = sum(len(t.files) for t in transfers)
    return render_template(
        "admin/transfers_table.jinja",
        transfers=transfers,
        total_size=total_size,
        total_files=total_files,
    )


@admin_bp.delete("/transfers/<transfer_id>")
@admin_required
def delete_transfer(transfer_id):
    transfer = db.session.get(Transfer, transfer_id)
    if transfer is None:
        return "", 404

    folder = current_app.config["UPLOAD_FOLDER"]
    for f in transfer.files:
        path = os.path.join(folder, f.stored_name)
        if os.path.exists(path):
            os.remove(path)

    db.session.delete(transfer)
    db.session.commit()

    return "", 200
