import httpx
import base64
from app.core.config import settings


async def send_whatsapp_message(to_number: str, message: str) -> str | None:
    """
    Send a WhatsApp message via Twilio Messaging API (async).
    Falls back to console logging when credentials are not configured.
    """
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        print(f"[Mock WhatsApp → {to_number}]\n{message}\n{'─' * 60}")
        return None

    # Ensure the whatsapp: prefix is present
    from_number = (
        settings.TWILIO_WHATSAPP_NUMBER
        if settings.TWILIO_WHATSAPP_NUMBER.startswith("whatsapp:")
        else f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}"
    )
    if not to_number.startswith("whatsapp:"):
        to_number = f"whatsapp:{to_number}"

    url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
    auth = base64.b64encode(
        f"{settings.TWILIO_ACCOUNT_SID}:{settings.TWILIO_AUTH_TOKEN}".encode()
    ).decode()

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            url,
            headers={"Authorization": f"Basic {auth}"},
            data={"From": from_number, "To": to_number, "Body": message},
        )
        response.raise_for_status()
        return response.json().get("sid")
