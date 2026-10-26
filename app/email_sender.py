"""
Local SMTP Email Dispatcher for Quanteinstein Outbound Engine.
Sends real cold outreach emails from the user's Gmail, Outlook, or custom SMTP account.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)


class EmailDispatcher:
    """Dispatches cold outreach emails directly from the user's local email account."""

    @staticmethod
    def send_email(
        recipient_email: str,
        subject: str,
        body: str,
        sender_email: Optional[str] = None,
        smtp_password: Optional[str] = None,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Sends an email using standard SMTP with TLS.
        Works seamlessly with:
        - Gmail (smtp.gmail.com:587) using a 16-character Google App Password
        - Outlook (smtp.office365.com:587)
        - Custom SMTP server
        """
        user = (sender_email or getattr(settings, "SMTP_USER", "")).strip()
        pwd = (smtp_password or getattr(settings, "SMTP_PASSWORD", "")).strip()
        if " " in pwd and len(pwd.replace(" ", "")) == 16:
            pwd = pwd.replace(" ", "")

        host = smtp_host or getattr(settings, "SMTP_HOST", "smtp.gmail.com")
        port = smtp_port or getattr(settings, "SMTP_PORT", 587)

        if not user or not pwd:
            return {
                "success": False,
                "message": "SMTP credentials not provided. Set SMTP_USER and SMTP_PASSWORD in .env or pass them directly."
            }


        try:
            msg = MIMEMultipart()
            msg["From"] = user
            msg["To"] = recipient_email
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "plain", "utf-8"))

            # Connect via STARTTLS
            server = smtplib.SMTP(host, int(port), timeout=15)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(user, pwd)
            server.sendmail(user, recipient_email, msg.as_string())
            server.quit()

            logger.info(f"Email successfully sent to {recipient_email} via {user}")
            return {
                "success": True,
                "message": f"Email successfully sent to {recipient_email} from {user}!"
            }
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication Error: {e}")
            return {
                "success": False,
                "message": "Authentication failed. For Gmail, please use an App Password (not your normal password)."
            }
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {e}")
            return {
                "success": False,
                "message": f"SMTP sending error: {str(e)}"
            }

    @staticmethod
    def test_connection(
        sender_email: Optional[str] = None,
        smtp_password: Optional[str] = None,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None
    ) -> Dict[str, Any]:
        """Tests the SMTP connection and login authentication."""
        user = (sender_email or getattr(settings, "SMTP_USER", "")).strip()
        pwd = (smtp_password or getattr(settings, "SMTP_PASSWORD", "")).strip()
        if " " in pwd and len(pwd.replace(" ", "")) == 16:
            pwd = pwd.replace(" ", "")

        host = smtp_host or getattr(settings, "SMTP_HOST", "smtp.gmail.com")
        port = smtp_port or getattr(settings, "SMTP_PORT", 587)


        if not user or not pwd:
            return {
                "connected": False,
                "user": user,
                "message": "SMTP credentials missing. Please set SMTP_USER and SMTP_PASSWORD in .env."
            }

        try:
            server = smtplib.SMTP(host, int(port), timeout=10)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(user, pwd)
            server.quit()
            return {
                "connected": True,
                "user": user,
                "host": host,
                "port": port,
                "message": f"Successfully connected and authenticated as {user}!"
            }
        except smtplib.SMTPAuthenticationError as e:
            return {
                "connected": False,
                "user": user,
                "message": "SMTP Authentication failed. For Gmail, 2-Step Verification must be enabled and an App Password must be used."
            }
        except Exception as e:
            return {
                "connected": False,
                "user": user,
                "message": f"Connection error to {host}:{port} - {str(e)}"
            }

