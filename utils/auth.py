from functools import wraps

from flask import redirect, session, url_for


def is_admin():
    return session.get("admin") is True


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_admin():
            return redirect(url_for("admin.login"))
        return f(*args, **kwargs)

    return decorated
