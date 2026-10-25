from flask import Blueprint, flash, render_template

from models import Transfer, db
from utils.transfers import delete_transfer as delete_transfer_files

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


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
def dashboard():
    return render_template("admin/dashboard.jinja", **transfers_context())


@admin_bp.get("/transfers")
def transfers_table():
    return render_template("admin/transfers_table.jinja", **transfers_context())


@admin_bp.delete("/transfers/<transfer_id>")
def delete_transfer(transfer_id):
    transfer = db.session.get(Transfer, transfer_id)
    if transfer is None:
        return "", 404

    delete_transfer_files(transfer)
    flash(f"Deleted transfer {transfer_id}.", "success")

    return "", 200
