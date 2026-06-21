from twilio.rest import Client
from app.core.config import settings

def send_whatsapp_message(to_number: str, message: str):
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        print(f"Mock sending WhatsApp to {to_number}:\n{message}")
        return

    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    
    # Twilio sandbox requires 'whatsapp:' prefix
    from_number = f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}"
    if not to_number.startswith("whatsapp:"):
        to_number = f"whatsapp:{to_number}"

    message = client.messages.create(
        body=message,
        from_=from_number,
        to=to_number
    )
    return message.sid
