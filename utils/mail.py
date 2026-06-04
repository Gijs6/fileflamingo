import logging
import os
from email.mime.text import MIMEText
from smtplib import SMTP_SSL as SMTP

logger = logging.getLogger("mail")


def send_transfer_email(recipient_email, download_url, message=None):
    server = os.getenv("SMTP_SERVER")
    sender = os.getenv("SMTP_SENDER")
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")

    if not server or not sender:
        logger.warning("SMTP not configured, skipping email to %s", recipient_email)
        return False

    body_parts = ["Someone shared files with you via FileFlamingo."]
    if message:
        body_parts.append(f"\nMessage from sender:\n{message}")
    body_parts.append(f"\nDownload your files here:\n{download_url}")
    body_parts.append("\nThis link may expire - download your files before then.")
    content = "\n".join(body_parts)

    try:
        msg = MIMEText(content, "plain")
        msg["Subject"] = "Someone shared files with you from FileFlamingo"
        msg["From"] = sender
        msg["To"] = recipient_email

        conn = SMTP(server)
        conn.set_debuglevel(False)
        conn.login(username, password)
        try:
            conn.sendmail(sender, [recipient_email], msg.as_string())
        finally:
            conn.quit()

        logger.info("Transfer email sent to %s", recipient_email)
        return True

    except Exception:
        logger.exception("Failed to send transfer email to %s", recipient_email)
        return False
