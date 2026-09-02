from datetime import timezone


def ensure_tz(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def strftime_filter(value, fmt="%d %b %Y"):
    value = ensure_tz(value)
    if value is None:
        return "-"
    return value.strftime(fmt)


def filesize_filter(value):
    if value is None:
        return "-"
    if value < 1024:
        return f"{value} B"
    if value < 1024 * 1024:
        return f"{value / 1024:.1f} KB"
    if value < 1024 * 1024 * 1024:
        return f"{value / (1024 * 1024):.1f} MB"
    return f"{value / (1024 * 1024 * 1024):.1f} GB"


def file_icon_filter(mime_type):
    if not mime_type:
        return "file"
    if mime_type == "application/pdf":
        return "file-text"
    if mime_type.startswith("text/") or "json" in mime_type or "xml" in mime_type:
        return "file-text"
    text_hints = (
        "word",
        "document",
        "excel",
        "spreadsheet",
        "presentation",
        "powerpoint",
    )
    if any(hint in mime_type for hint in text_hints):
        return "file-text"
    return "file"


FILTERS = {
    "strftime": strftime_filter,
    "filesize": filesize_filter,
    "file_icon": file_icon_filter,
}


def register_filters(app):
    for name, fn in FILTERS.items():
        app.template_filter(name)(fn)
