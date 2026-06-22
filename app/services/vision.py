import base64
import json
import httpx
from openai import AsyncOpenAI
from app.core.config import settings
from app.schemas.schemas import VisionResponse

_client: AsyncOpenAI | None = None


def _get_openai_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


async def _encode_image_from_url(image_url: str, account_sid: str | None, auth_token: str | None) -> str:
    """Download image and return base64 string. Tries Twilio auth first, then no-auth."""
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            if account_sid and auth_token:
                response = await client.get(image_url, auth=(account_sid, auth_token))
                response.raise_for_status()
                return base64.b64encode(response.content).decode("utf-8")
        except Exception:
            pass  # fall through to no-auth
        response = await client.get(image_url)
        response.raise_for_status()
        return base64.b64encode(response.content).decode("utf-8")


async def diagnose_image(image_url: str) -> VisionResponse:
    """Diagnose a crop image using GPT-4o Vision. Returns crop name, disease, confidence, and summary."""
    if not settings.OPENAI_API_KEY:
        # Mock response when no API key is configured
        return VisionResponse(
            crop="Tomato",
            disease="Early Blight (Mock)",
            confidence=0.85,
            summary="Mock diagnosis: early blight detected on lower leaves. Treat promptly.",
        )

    base64_image = await _encode_image_from_url(
        image_url, settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN
    )

    openai_client = _get_openai_client()
    response = await openai_client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert agricultural plant pathologist. "
                    "Analyze the crop image and respond ONLY in JSON with exactly four keys: "
                    "'crop' (string: the crop plant species, e.g. 'Tomato', 'Wheat', 'Rice', 'Maize'), "
                    "'disease' (string: the detected disease or 'Healthy' if no disease), "
                    "'confidence' (float 0.0–1.0: your confidence in the diagnosis), "
                    "'summary' (string: concise explanation of visible symptoms, max 60 words)."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    }
                ],
            },
        ],
    )

    data = json.loads(response.choices[0].message.content)
    return VisionResponse(
        crop=data.get("crop", "Unknown"),
        disease=data.get("disease", "Unknown"),
        confidence=float(data.get("confidence", 0.0)),
        summary=data.get("summary", "No summary provided."),
    )
