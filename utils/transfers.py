import os
from datetime import timedelta

from flask import current_app

from models import Transfer, Upload, db, utcnow

PENDING_LIFETIME = timedelta(days=1)


def delete_transfer(transfer):
    folder = current_app.config["UPLOAD_FOLDER"]
    for f in transfer.files:
        path = os.path.join(folder, f.stored_name)
        if os.path.exists(path):
            os.remove(path)
    db.session.delete(transfer)
    db.session.commit()


def prune():
    now = utcnow()
    stale = Transfer.query.filter(
        db.or_(
            Transfer.expires_at < now,
            db.and_(
                Transfer.status == "pending",
                Transfer.created_at < now - PENDING_LIFETIME,
            ),
        )
    ).all()
    for transfer in stale:
        delete_transfer(transfer)
    Upload.query.filter(Upload.created_at < now - timedelta(days=1)).delete()
    db.session.commit()
