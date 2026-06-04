from datetime import datetime, timezone


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


def timeago_filter(value):
    value = ensure_tz(value)
    if value is None:
        return "never"
    secs = int((datetime.now(timezone.utc) - value).total_seconds())
    if secs < 60:
        return f"{secs}s ago"
    if secs < 3600:
        return f"{secs // 60}m ago"
    if secs < 86400:
        return f"{secs // 3600}h ago"
    return f"{secs // 86400}d ago"


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
        return "fa-file"
    if mime_type.startswith("image/"):
        return "fa-file-image"
    if mime_type.startswith("video/"):
        return "fa-file-video"
    if mime_type.startswith("audio/"):
        return "fa-file-audio"
    if mime_type == "application/pdf":
        return "fa-file-pdf"
    if mime_type in (
        "application/zip",
        "application/x-zip-compressed",
        "application/x-rar-compressed",
        "application/x-7z-compressed",
        "application/gzip",
    ):
        return "fa-file-zipper"
    if "word" in mime_type or "document" in mime_type:
        return "fa-file-word"
    if "excel" in mime_type or "spreadsheet" in mime_type:
        return "fa-file-excel"
    if "presentation" in mime_type or "powerpoint" in mime_type:
        return "fa-file-powerpoint"
    if mime_type.startswith("text/") or "json" in mime_type or "xml" in mime_type:
        return "fa-file-code"
    return "fa-file"


FILTERS = {
    "strftime": strftime_filter,
    "timeago": timeago_filter,
    "filesize": filesize_filter,
    "file_icon": file_icon_filter,
}


def register_filters(app):
    for name, fn in FILTERS.items():
        app.template_filter(name)(fn)
