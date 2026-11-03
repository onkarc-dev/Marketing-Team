"""
Local SMTP Email Dispatcher for Quanteinstein Outbound Engine.
Sends real cold outreach emails from the user's Gmail, Outlook, or custom SMTP account.
"""

import os
import smtplib
import logging
import mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, Dict, Any, List
from app.config import settings

logger = logging.getLogger(__name__)

# Default collateral attached to institutional cold emails
DEFAULT_ATTACHMENTS = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "attachments", "Quanteinstein_Enterprise_OS_v3.0_Architecture_Brief.pdf"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "attachments", "Quanteinstein_Execution_Engine_Demo.mp4")
]


class EmailDispatcher:
    """Dispatches cold outreach emails directly from the user's local email account."""

    @staticmethod
    def get_available_attachments() -> List[Dict[str, Any]]:
        """Returns metadata about available attachments for email campaigns."""
        attachments_info = []
        for path in DEFAULT_ATTACHMENTS:
            if os.path.exists(path):
                size_bytes = os.path.getsize(path)
                size_mb = round(size_bytes / (1024 * 1024), 2)
                filename = os.path.basename(path)
                attachments_info.append({
                    "filename": filename,
                    "path": path,
                    "size_bytes": size_bytes,
                    "size_formatted": f"{size_mb} MB" if size_mb >= 1.0 else f"{round(size_bytes / 1024, 1)} KB",
                    "url": f"/attachments/{filename}"
                })
        return attachments_info

    @staticmethod
    def send_email(
        recipient_email: str,
        subject: str,
        body: str,
        sender_email: Optional[str] = None,
        smtp_password: Optional[str] = None,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        attachments: Optional[List[str]] = None,
        include_default_attachments: bool = True
    ) -> Dict[str, Any]:
        """
        Sends an email using standard SMTP with TLS, supporting attachments.
        Works seamlessly with:
        - Gmail (smtp.gmail.com:587) using a 16-character Google App Password
        - Outlook (smtp.office365.com:587)
        - Custom SMTP server
        """
        user = (sender_email if sender_email is not None else getattr(settings, "SMTP_USER", "")).strip()
        pwd = (smtp_password if smtp_password is not None else getattr(settings, "SMTP_PASSWORD", "")).strip()
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

            # Email text body
            msg.attach(MIMEText(body, "plain", "utf-8"))

            # Determine attachments
            files_to_attach = []
            if attachments is not None:
                files_to_attach.extend(attachments)
            elif include_default_attachments:
                files_to_attach.extend([p for p in DEFAULT_ATTACHMENTS if os.path.exists(p)])

            attached_names = []
            for file_path in files_to_attach:
                resolved_path = file_path
                if not os.path.isabs(resolved_path):
                    candidate = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "attachments", file_path)
                    if os.path.exists(candidate):
                        resolved_path = candidate

                if os.path.exists(resolved_path):
                    filename = os.path.basename(resolved_path)
                    ctype, encoding = mimetypes.guess_type(resolved_path)
                    if ctype is None or encoding is not None:
                        ctype = "application/octet-stream"
                    maintype, subtype = ctype.split("/", 1)

                    with open(resolved_path, "rb") as fp:
                        part = MIMEBase(maintype, subtype)
                        part.set_payload(fp.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f'attachment; filename="{filename}"'
                    )
                    msg.attach(part)
                    attached_names.append(filename)
                else:
                    logger.warning(f"Attachment file not found: {file_path}")

            # Connect via STARTTLS
            server = smtplib.SMTP(host, int(port), timeout=30)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(user, pwd)
            server.sendmail(user, recipient_email, msg.as_string())
            server.quit()

            att_info = f" with {len(attached_names)} attachment(s): {', '.join(attached_names)}" if attached_names else ""
            logger.info(f"Email successfully sent to {recipient_email} via {user}{att_info}")
            return {
                "success": True,
                "message": f"Email successfully sent to {recipient_email} from {user}{att_info}!",
                "attachments_sent": attached_names
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
        user = (sender_email if sender_email is not None else getattr(settings, "SMTP_USER", "")).strip()
        pwd = (smtp_password if smtp_password is not None else getattr(settings, "SMTP_PASSWORD", "")).strip()
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

