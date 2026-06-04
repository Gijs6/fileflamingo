import secrets
import string
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def generate_id(length=8):
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


class Transfer(db.Model):
    __tablename__ = "transfers"

    id = db.Column(db.String(8), primary_key=True, default=generate_id)
    status = db.Column(db.String(20), default="pending", nullable=False)
    message = db.Column(db.Text)
    recipient_email = db.Column(db.String(255))
    expires_at = db.Column(db.DateTime)
    download_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    files = db.relationship(
        "TransferFile", back_populates="transfer", cascade="all, delete-orphan"
    )

    @property
    def is_expired(self):
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    @property
    def total_size(self):
        return sum(f.size for f in self.files)


class TransferFile(db.Model):
    __tablename__ = "transfer_files"

    id = db.Column(db.String(8), primary_key=True, default=generate_id)
    transfer_id = db.Column(db.String(8), db.ForeignKey("transfers.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    stored_name = db.Column(db.String(64), nullable=False, unique=True)
    mime_type = db.Column(db.String(100))
    size = db.Column(db.BigInteger, nullable=False)

    transfer = db.relationship("Transfer", back_populates="files")
