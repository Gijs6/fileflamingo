import io
import mimetypes
import os
import uuid
import zipfile
from datetime import datetime, timedelta

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from werkzeug.utils import secure_filename

from models import Transfer, TransferFile, db
from utils.mail import send_transfer_email

transfers_bp = Blueprint("transfers", __name__)


def _htmx_redirect(dest):
    if request.headers.get("HX-Request"):
        r = make_response("", 200)
        r.headers["HX-Redirect"] = dest
        return r
    return redirect(dest)


@transfers_bp.get("/")
def index():
    return render_template("index.jinja")


@transfers_bp.post("/transfers")
def create():
    files = [f for f in request.files.getlist("files[]") if f.filename]
    if not files:
        flash("Select at least one file.", "error")
        return redirect(url_for("transfers.index"))

    transfer = Transfer(status="pending")
    db.session.add(transfer)
    db.session.flush()

    folder = current_app.config["UPLOAD_FOLDER"]
    for f in files:
        name = secure_filename(f.filename)
        ext = os.path.splitext(name)[1]
        stored = uuid.uuid4().hex + ext
        f.save(os.path.join(folder, stored))
        db.session.add(
            TransferFile(
                transfer_id=transfer.id,
                filename=name,
                stored_name=stored,
                mime_type=mimetypes.guess_type(name)[0] or f.mimetype or None,
                size=os.path.getsize(os.path.join(folder, stored)),
            )
        )

    db.session.commit()
    return _htmx_redirect(url_for("transfers.message", transfer_id=transfer.id))


@transfers_bp.get("/transfers/<transfer_id>/message")
def message(transfer_id):
    transfer = db.session.get(Transfer, transfer_id)
    if transfer is None or transfer.status != "pending":
        abort(404)
    return render_template("transfers/message.jinja", transfer=transfer)


@transfers_bp.route("/transfers/<transfer_id>/message", methods=["POST", "PATCH"])
def save_message(transfer_id):
    transfer = db.session.get(Transfer, transfer_id)
    if transfer is None or transfer.status != "pending":
        abort(404)

    transfer.message = request.form.get("message", "").strip() or None
    transfer.recipient_email = request.form.get("email", "").strip() or None
    db.session.commit()

    return _htmx_redirect(url_for("transfers.details", transfer_id=transfer.id))


@transfers_bp.get("/transfers/<transfer_id>/details")
def details(transfer_id):
    transfer = db.session.get(Transfer, transfer_id)
    if transfer is None or transfer.status != "pending":
        abort(404)
    return render_template("transfers/details.jinja", transfer=transfer)


@transfers_bp.route("/transfers/<transfer_id>", methods=["POST", "PATCH"])
def configure(transfer_id):
    transfer = db.session.get(Transfer, transfer_id)
    if transfer is None or transfer.status != "pending":
        abort(404)

    try:
        days = int(request.form.get("expiry", "7"))
    except ValueError:
        days = 7

    transfer.expires_at = datetime.now() + timedelta(days=days) if days > 0 else None
    transfer.status = "ready"
    db.session.commit()

    download_url = url_for("transfers.view", transfer_id=transfer.id, _external=True)
    if transfer.recipient_email:
        send_transfer_email(transfer.recipient_email, download_url, transfer.message)

    return _htmx_redirect(url_for("transfers.success", transfer_id=transfer.id))


@transfers_bp.get("/transfers/<transfer_id>/success")
def success(transfer_id):
    transfer = db.session.get(Transfer, transfer_id)
    if transfer is None:
        abort(404)
    url = url_for("transfers.view", transfer_id=transfer.id, _external=True)
    return render_template(
        "transfers/success.jinja", transfer=transfer, download_url=url
    )


@transfers_bp.get("/transfers/<transfer_id>")
def view(transfer_id):
    transfer = db.session.get(Transfer, transfer_id)
    if transfer is None or transfer.status != "ready":
        abort(404)
    return render_template("transfers/view.jinja", transfer=transfer)


@transfers_bp.get("/transfers/<transfer_id>/files/<file_id>")
def download_file(transfer_id, file_id):
    transfer = db.session.get(Transfer, transfer_id)
    if transfer is None or transfer.status != "ready":
        abort(404)
    if transfer.is_expired:
        abort(410)

    tf = TransferFile.query.filter_by(
        id=file_id, transfer_id=transfer_id
    ).first_or_404()
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], tf.stored_name)
    if not os.path.exists(path):
        abort(404)

    transfer.download_count += 1
    db.session.commit()

    return send_file(path, as_attachment=True, download_name=tf.filename)


@transfers_bp.get("/transfers/<transfer_id>/archive")
def download_archive(transfer_id):
    transfer = db.session.get(Transfer, transfer_id)
    if transfer is None or transfer.status != "ready":
        abort(404)
    if transfer.is_expired:
        abort(410)

    folder = current_app.config["UPLOAD_FOLDER"]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in transfer.files:
            p = os.path.join(folder, f.stored_name)
            if os.path.exists(p):
                zf.write(p, f.filename)
    buf.seek(0)

    transfer.download_count += 1
    db.session.commit()

    return send_file(
        buf,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"files-{transfer_id}.zip",
    )
