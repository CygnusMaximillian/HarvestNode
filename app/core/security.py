import hmac
import hashlib
import base64
from urllib.parse import urlencode

from fastapi import Request, HTTPException
from app.core.config import settings


async def verify_twilio_signature(request: Request) -> None:
    """
    FastAPI dependency that validates the X-Twilio-Signature header.

    In development mode (no TWILIO_AUTH_TOKEN set) validation is skipped.
    In production, a forged or missing signature results in a 403 response.

    Ref: https://www.twilio.com/docs/usage/security#validating-signatures-from-twilio
    """
    if not settings.TWILIO_AUTH_TOKEN:
        # Dev / mock mode — skip validation
        return

    signature = request.headers.get("X-Twilio-Signature", "")
    if not signature:
        raise HTTPException(status_code=403, detail="Missing Twilio signature.")

    # Reconstruct the full URL Twilio signed
    url = str(request.url)

    # Collect POST params sorted alphabetically and appended to URL
    form_data = await request.form()
    sorted_params = urlencode(sorted(form_data.items()))
    signed_url = url + sorted_params

    # Compute expected signature: HMAC-SHA1 of url+params, keyed by auth token, base64-encoded
    mac = hmac.new(
        settings.TWILIO_AUTH_TOKEN.encode("utf-8"),
        signed_url.encode("utf-8"),
        hashlib.sha1,
    )
    expected = base64.b64encode(mac.digest()).decode("utf-8")

    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature.")
