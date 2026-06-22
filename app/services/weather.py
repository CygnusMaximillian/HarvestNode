import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

_MOCK_WEATHER = {
    "temperature": "25°C",
    "humidity": "60%",
    "rain_forecast": "No rain expected",
}

_WEATHER_ERROR = {
    "temperature": "Unknown",
    "humidity": "Unknown",
    "rain_forecast": "Unknown",
}


async def get_weather(lat: float, lon: float) -> dict:
    """Fetch real-time weather from OpenWeatherMap. Falls back to mock if key is absent."""
    if not settings.WEATHER_API_KEY:
        return _MOCK_WEATHER

    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&appid={settings.WEATHER_API_KEY}&units=metric"
    )
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        temp = data.get("main", {}).get("temp", "N/A")
        humidity = data.get("main", {}).get("humidity", "N/A")
        weather_desc = data.get("weather", [{}])[0].get("description", "Unknown")

        return {
            "temperature": f"{temp}°C",
            "humidity": f"{humidity}%",
            "rain_forecast": weather_desc,
        }
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return _WEATHER_ERROR
