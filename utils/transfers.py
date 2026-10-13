import os

from flask import current_app

from models import db


def delete_transfer(transfer):
    folder = current_app.config["UPLOAD_FOLDER"]
    for f in transfer.files:
        path = os.path.join(folder, f.stored_name)
        if os.path.exists(path):
            os.remove(path)
    db.session.delete(transfer)
    db.session.commit()
