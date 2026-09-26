"""One-time codes for password reset.

Codes are 6 digits, valid for 10 minutes, max 5 wrong tries, single use.
Only a hash of the code is stored. Delivery:
  - SMTP_HOST set  -> emailed
  - otherwise      -> logged to the server console (and returned in the API
                      response when OTP_DEMO_MODE=true, so live demos never
                      depend on email delivery)
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import smtplib
from email.message import EmailMessage

log = logging.getLogger("stocksense.otp")

OTP_TTL_MINUTES = 10
OTP_MAX_ATTEMPTS = 5


def new_code() -> str:
    return f"{secrets.randbelow(10**6):06d}"


def hash_code(code: str, secret: str) -> str:
    return hmac.new(secret.encode(), code.strip().encode(), hashlib.sha256).hexdigest()


def codes_match(code: str, stored_hash: str, secret: str) -> bool:
    return hmac.compare_digest(hash_code(code, secret), stored_hash)


def send_code(email: str, code: str, settings) -> bool:
    """Returns True if the code was emailed, False if it was only logged."""
    if not settings.smtp_host:
        log.warning("Password reset code for %s: %s (no SMTP configured)", email, code)
        print(f"[StockSense] Password reset code for {email}: {code}", flush=True)
        return False

    msg = EmailMessage()
    msg["Subject"] = "Your StockSense password reset code"
    msg["From"] = settings.smtp_from or settings.smtp_user
    msg["To"] = email
    msg.set_content(
        f"Your StockSense password reset code is: {code}\n\n"
        f"It expires in {OTP_TTL_MINUTES} minutes. If you didn't ask for this, ignore this email."
    )
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as s:
            s.starttls()
            if settings.smtp_user:
                s.login(settings.smtp_user, settings.smtp_password)
            s.send_message(msg)
        return True
    except Exception:
        log.exception("Could not send reset email to %s; code logged instead", email)
        print(f"[StockSense] Password reset code for {email}: {code}", flush=True)
        return False
