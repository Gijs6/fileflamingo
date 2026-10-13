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

    if current_app.debug or (
        stored_hash and check_password_hash(stored_hash, password)
    ):
        session.clear()
        session["admin"] = True
        return redirect(url_for("admin.dashboard"))

    flash("Incorrect password.", "error")
    return redirect(url_for("admin.login"))


@admin_bp.post("/logout")
@admin_required
def logout():
    session.clear()
    if current_app.debug:
        session["dev_signed_out"] = True
    return redirect(url_for("admin.login"))


def transfers_context():
    transfers = Transfer.query.order_by(Transfer.created_at.desc()).all()
    expired = [t for t in transfers if t.is_expired]
    pending = [t for t in transfers if not t.is_expired and t.status == "pending"]
    active = [t for t in transfers if not t.is_expired and t.status != "pending"]
    active.sort(key=lambda t: (t.expires_at is None, t.expires_at or t.created_at))
    expired.sort(key=lambda t: t.expires_at, reverse=True)
    sections = [
        (label, items)
        for label, items in (
            ("Active", active),
            ("Pending", pending),
            ("Expired", expired),
        )
        if items
    ]
    return {
        "transfers": transfers,
        "sections": sections,
        "expired_count": len(expired),
        "total_size": sum(t.total_size for t in transfers),
        "total_files": sum(len(t.files) for t in transfers),
    }


@admin_bp.get("/")
@admin_required
def dashboard():
    return render_template("admin/dashboard.jinja", **transfers_context())


@admin_bp.get("/transfers")
@admin_required
def transfers_table():
    return render_template("admin/transfers_table.jinja", **transfers_context())


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
    flash(f"Deleted transfer {transfer_id}.", "success")

    return "", 200
