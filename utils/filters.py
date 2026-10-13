from datetime import timezone


def ensure_tz(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def strftime_filter(value, fmt="%-d %b %Y, %H:%M"):
    value = ensure_tz(value)
    if value is None:
        return ""
    return value.strftime(fmt)


def to_iso_filter(value):
    value = ensure_tz(value)
    if value is None:
        return ""
    return value.isoformat()


def filesize_filter(value):
    if value is None:
        return ""
    if value < 1024:
        return f"{value} B"
    if value < 1024 * 1024:
        return f"{value / 1024:.1f} KB"
    if value < 1024 * 1024 * 1024:
        return f"{value / (1024 * 1024):.1f} MB"
    return f"{value / (1024 * 1024 * 1024):.1f} GB"


FILTERS = {
    "strftime": strftime_filter,
    "to_iso": to_iso_filter,
    "filesize": filesize_filter,
}


def register_filters(app):
    for name, fn in FILTERS.items():
        app.template_filter(name)(fn)
