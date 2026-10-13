from functools import wraps

from flask import session, url_for

from utils.toasts import htmx_redirect


def is_admin():
    return session.get("admin") is True


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_admin():
            return htmx_redirect(url_for("admin.login"))
        return f(*args, **kwargs)

    return decorated
