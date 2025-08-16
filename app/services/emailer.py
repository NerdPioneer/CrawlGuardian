import os
from email.message import EmailMessage
from typing import Optional

import aiosmtplib


async def send_email(subject: str, body: str, to: Optional[str] = None) -> None:
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    starttls = os.getenv("SMTP_STARTTLS", "true").lower() == "true"

    email_from = os.getenv("EMAIL_FROM", user or "")
    email_to = to or os.getenv("EMAIL_TO", "")

    if not host or not email_to:
        return

    msg = EmailMessage()
    msg["From"] = email_from
    msg["To"] = email_to
    msg["Subject"] = subject
    msg.set_content(body)

    await aiosmtplib.send(
        msg,
        hostname=host,
        port=port,
        username=user,
        password=password,
        start_tls=starttls,
    )