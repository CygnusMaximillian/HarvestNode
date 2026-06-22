import hmac
import hashlib
import base64

from fastapi import Request, HTTPException
from app.core.config import settings


async def verify_twilio_signature(request: Request) -> None:
    """
    FastAPI dependency that validates the X-Twilio-Signature header.

    Twilio's algorithm (https://www.twilio.com/docs/usage/security):
      1. Take the full request URL.
      2. Sort POST params alphabetically by key.
      3. Append each key+value pair (no delimiters) directly to the URL string.
      4. HMAC-SHA1 sign with the AuthToken, then base64-encode.

    In development (no TWILIO_AUTH_TOKEN set) validation is skipped.
    In production a missing or invalid signature returns HTTP 403.
    """
    if not settings.TWILIO_AUTH_TOKEN:
        return  # Dev / mock mode — skip validation

    signature = request.headers.get("X-Twilio-Signature", "")
    if not signature:
        raise HTTPException(status_code=403, detail="Missing X-Twilio-Signature header.")

    # Full URL Twilio used when sending the request
    url = str(request.url)

    # Sort POST params alphabetically and concatenate key+value with NO separators
    form_data = await request.form()
    sorted_concat = "".join(k + v for k, v in sorted(form_data.multi_items()))
    signed_string = url + sorted_concat

    # HMAC-SHA1, keyed by AuthToken, base64-encoded
    mac = hmac.new(
        settings.TWILIO_AUTH_TOKEN.encode("utf-8"),
        signed_string.encode("utf-8"),
        hashlib.sha1,
    )
    expected = base64.b64encode(mac.digest()).decode("utf-8")

    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature.")
