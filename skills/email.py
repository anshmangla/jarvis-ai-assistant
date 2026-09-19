import smtplib
import imaplib
import email as email_lib
import email.message
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from typing import Any

from skills.base import BaseSkill
from utils.logger import logger

# ---- Gmail Configuration ---------------------------------------------------
# You must create an App Password in your Google Account settings.
# Enable 2-Step Verification, then generate an App Password.
# Then set in your .env file:
#   EMAIL_ADDRESS=yourname@gmail.com
#   EMAIL_APP_PASSWORD=your_google_app_password
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
IMAP_SERVER = "imap.gmail.com"

# ---------------------------------------------------------------------------


class EmailSkill(BaseSkill):
    """Skill to send, read, and summarize Gmail emails via SMTP/IMAP."""

    name = "email"
    description = (
        "Send an email, read the latest inbox messages, or summarize recent emails."
    )
    parameters = {
        "action": {
            "type": "string",
            "description": "Action to perform: 'send', 'read', or 'summarize'.",
        },
        "to": {
            "type": "string",
            "description": "Recipient email address (required for 'send').",
            "default": "",
        },
        "subject": {
            "type": "string",
            "description": "Email subject (required for 'send').",
            "default": "",
        },
        "body": {
            "type": "string",
            "description": "Email body text (required for 'send').",
            "default": "",
        },
        "count": {
            "type": "integer",
            "description": "Number of recent emails to read or summarize (default: 5).",
            "default": 5,
        },
    }

    def _get_credentials(self) -> tuple[str, str]:
        """Fetch current email credentials from environment variables."""
        return os.getenv("EMAIL_ADDRESS", "").strip(), os.getenv("EMAIL_APP_PASSWORD", "").strip()

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def run(self, **kwargs: Any) -> str:
        action: str = str(kwargs.get("action", ""))

        if action == "send":
            return self._send_email(
                to=str(kwargs.get("to", "")),
                subject=str(kwargs.get("subject", "")),
                body=str(kwargs.get("body", "")),
            )
        elif action == "read":
            return self._read_inbox(count=int(str(kwargs.get("count", 5))))
        elif action == "summarize":
            return self._summarize_emails(count=int(str(kwargs.get("count", 5))))
        else:
            return f"Unknown action '{action}'. Use 'send', 'read', or 'summarize'."

    # ------------------------------------------------------------------
    # Send email via SMTP
    # ------------------------------------------------------------------

    def _send_email(self, to: str, subject: str, body: str) -> str:
        email_address, app_password = self._get_credentials()
        if not to or not subject or not body:
            return "Error: 'to', 'subject', and 'body' are all required for sending an email."
        if not email_address or not app_password:
            return (
                "Error: EMAIL_ADDRESS or EMAIL_APP_PASSWORD not set in environment variables."
            )

        try:
            msg = MIMEMultipart()
            msg["From"] = email_address
            msg["To"] = to
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(email_address, app_password)
                server.sendmail(email_address, to, msg.as_string())

            logger.info(f"Email successfully sent from {email_address} to {to}")
            return f"Email successfully sent from {email_address} to {to} with subject '{subject}'."
        except smtplib.SMTPAuthenticationError:
            return "Authentication failed. Please check your EMAIL_ADDRESS and EMAIL_APP_PASSWORD in .env."
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return f"Failed to send email: {e}"

    # ------------------------------------------------------------------
    # Internal helpers: IMAP connection and fetching
    # ------------------------------------------------------------------

    def _connect_imap(self) -> imaplib.IMAP4_SSL:
        """Establish and return an authenticated IMAP SSL connection."""
        email_address, app_password = self._get_credentials()
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(email_address, app_password)
        return mail

    def _fetch_messages(self, count: int) -> list:
        """Fetch the most recent `count` messages from INBOX, returning parsed email objects."""
        email_address, app_password = self._get_credentials()
        if not email_address or not app_password:
            return []

        mail = self._connect_imap()
        mail.select("INBOX")

        # Get all message IDs and take the last `count`
        _, message_ids = mail.search(None, "ALL")
        ids = message_ids[0].split()
        ids_to_fetch = ids[-count:]

        messages = []
        for uid in reversed(ids_to_fetch):
            _, msg_data = mail.fetch(uid, "(RFC822)")
            raw = msg_data[0]
            if isinstance(raw, tuple):
                msg = email_lib.message_from_bytes(raw[1])
                messages.append(msg)

        mail.logout()
        return messages

    @staticmethod
    def _decode_header_value(raw_value: str) -> str:
        """Decode an RFC-2047 encoded email header value to a plain string."""
        decoded, charset = decode_header(raw_value)[0]
        if isinstance(decoded, bytes):
            return decoded.decode(charset or "utf-8", errors="replace")
        return str(decoded)

    @staticmethod
    def _get_body(msg: email.message.Message) -> str:
        """Extract the plaintext body from an email.message.Message."""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain" and part.get("Content-Disposition") is None:
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        return payload.decode(errors="replace")
        else:
            payload = msg.get_payload(decode=True)
            if isinstance(payload, bytes):
                return payload.decode(errors="replace")
        return ""

    # ------------------------------------------------------------------
    # Read inbox
    # ------------------------------------------------------------------

    def _read_inbox(self, count: int = 5) -> str:
        try:
            messages = self._fetch_messages(count)
            if not messages:
                return "No email credentials configured or no messages found."

            lines = [f"Here are your latest {len(messages)} emails:\n"]
            for i, msg in enumerate(messages, 1):
                sender = self._decode_header_value(msg.get("From", "Unknown"))
                subject = self._decode_header_value(msg.get("Subject", "(No subject)"))
                date = msg.get("Date", "Unknown date")
                lines.append(f"{i}. From: {sender}\n   Subject: {subject}\n   Date: {date}")

            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Failed to read inbox: {e}")
            return f"Failed to read inbox: {e}"

    # ------------------------------------------------------------------
    # Summarize emails (short snippet per message)
    # ------------------------------------------------------------------

    def _summarize_emails(self, count: int = 5) -> str:
        try:
            messages = self._fetch_messages(count)
            if not messages:
                return "No email credentials configured or no messages found."

            summaries = []
            for i, msg in enumerate(messages, 1):
                sender = self._decode_header_value(msg.get("From", "Unknown"))
                subject = self._decode_header_value(msg.get("Subject", "(No subject)"))
                body_full = self._get_body(msg)
                body_snippet = body_full[:200].replace("\n", " ").strip()
                summaries.append(
                    f"{i}. [{subject}] from {sender}:\n   \"{body_snippet}...\""
                )

            return "Email summary:\n" + "\n\n".join(summaries)
        except Exception as e:
            logger.error(f"Failed to summarize emails: {e}")
            return f"Failed to summarize emails: {e}"
