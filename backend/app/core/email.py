import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> bool:
    """Send a plain-text email via SMTP. Returns False (and logs) instead of
    raising when SMTP isn't configured, so callers (e.g. Celery tasks) can
    keep running in environments without mail set up."""
    if not settings.SMTP_HOST:
        logger.warning("SMTP not configured, skipping email", extra={"to": to, "subject": subject})
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to
    msg.set_content(body)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
            smtp.starttls()
            if settings.SMTP_USER:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception:
        logger.exception("Failed to send email", extra={"to": to, "subject": subject})
        return False
