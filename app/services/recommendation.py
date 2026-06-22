from openai import AsyncOpenAI
from app.core.config import settings
from app.schemas.schemas import VisionResponse

_client: AsyncOpenAI | None = None


def _get_openai_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


_MOCK_RECOMMENDATION = (
    "Mock recommendation: Apply copper-based fungicide to affected areas. "
    "Ensure adequate drainage and avoid overhead watering. "
    "Monitor closely over the next 7 days."
)


async def generate_recommendation(
    diagnosis: VisionResponse, weather: dict, market: dict
) -> str:
    """Generate a concise, farmer-friendly recommendation using GPT-4o."""
    if not settings.OPENAI_API_KEY:
        return _MOCK_RECOMMENDATION

    prompt = f"""
You are an expert agricultural assistant helping smallholder farmers.
Based on the data below, write a concise, practical recommendation in plain language.

Crop & Disease Diagnosis:
- Crop: {diagnosis.crop}
- Disease: {diagnosis.disease}
- Confidence: {int(diagnosis.confidence * 100)}%
- Symptoms: {diagnosis.summary}

Current Weather:
- Temperature: {weather.get('temperature')}
- Humidity: {weather.get('humidity')}
- Forecast: {weather.get('rain_forecast')}

Market Conditions:
- Crop: {market.get('crop', 'Unknown')}
- Price: {market.get('current_price')}
- Trend: {market.get('trend')}

Provide:
1. Immediate treatment steps (2–3 bullet points)
2. Risk level (Low / Medium / High)
3. Harvest recommendation (proceed, delay, or salvage)

Keep the total response under 200 words. Be direct and actionable.
"""

    openai_client = _get_openai_client()
    response = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful agricultural expert advising smallholder farmers."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()
