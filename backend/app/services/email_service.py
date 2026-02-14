"""SMTP email service with HTML template rendering."""

import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Optional

import aiosmtplib
from jinja2 import Environment, FileSystemLoader

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Jinja2 template env
_template_dir = Path(__file__).resolve().parent.parent / "templates"
_jinja_env = Environment(loader=FileSystemLoader(str(_template_dir)), autoescape=True)


async def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    from_email: Optional[str] = None,
) -> bool:
    """Send an email via SMTP. Returns True on success."""
    sender = from_email or f"{settings.SMTP_FROM_NAME} <{settings.SMTP_USER}>"

    msg = MIMEMultipart("alternative")
    msg["From"] = sender
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        if settings.SMTP_USE_TLS:
            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                use_tls=True,
            )
        else:
            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                start_tls=True,
            )
        logger.info("Email sent to %s", to_email)
        return True
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to_email, exc)
        return False


def render_digest_email(
    papers: list[dict],
    subscription_name: str,
    research_interest: str,
    user_token: str,
    base_url: str,
    frontend_url: str,
) -> str:
    """Render the digest email HTML from the template."""
    template = _jinja_env.get_template("email_template.html")
    return template.render(
        papers=papers,
        subscription_name=subscription_name,
        research_interest=research_interest,
        user_token=user_token,
        base_url=base_url,
        frontend_url=frontend_url,
    )
