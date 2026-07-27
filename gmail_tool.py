"""
Gmail tool — send emails via the Gmail API.
"""

import base64
from email.mime.text import MIMEText

from googleapiclient.discovery import build

from google_auth import get_google_credentials


def _get_service():
    return build("gmail", "v1", credentials=get_google_credentials())


def send_email(to: str, subject: str, body: str) -> str:
    """Send an email via Gmail.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Plain-text body of the email.

    Returns a spoken confirmation.
    """
    try:
        service = _get_service()

        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        send_body = {"raw": raw}

        service.users().messages().send(userId="me", body=send_body).execute()

        return f"Done! I've sent an email to {to} with the subject '{subject}'."

    except Exception as e:
        return f"Sorry, I couldn't send that email. {e}"
