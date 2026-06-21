from openai import OpenAI
from app.core.config import settings
from app.schemas.schemas import VisionResponse

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def generate_recommendation(diagnosis: VisionResponse, weather: dict, market: dict) -> str:
    prompt = f"""
You are an expert agricultural assistant.
Based on the following data, generate a concise, farmer-friendly recommendation.

Disease Diagnosis:
- Disease: {diagnosis.disease}
- Confidence: {diagnosis.confidence}
- Summary: {diagnosis.summary}

Weather Data:
- Temperature: {weather.get('temperature')}
- Humidity: {weather.get('humidity')}
- Forecast: {weather.get('rain_forecast')}

Market Data:
- Crop: {market.get('crop', 'Unknown')}
- Price: {market.get('current_price')}
- Trend: {market.get('trend')}

Provide treatment advice, risk assessment, and harvest recommendation.
Maximum length: 300 words. Be direct and helpful.
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful agricultural expert."},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content.strip()
