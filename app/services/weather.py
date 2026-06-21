import requests
from app.core.config import settings

def get_weather(lat: float, lon: float) -> dict:
    # If API key missing, return mock
    if not settings.WEATHER_API_KEY:
        return {
            "temperature": "25°C",
            "humidity": "60%",
            "rain_forecast": "No rain expected"
        }

    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={settings.WEATHER_API_KEY}&units=metric"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        temp = data.get("main", {}).get("temp", "N/A")
        humidity = data.get("main", {}).get("humidity", "N/A")
        weather_desc = data.get("weather", [{}])[0].get("description", "Unknown")
        
        return {
            "temperature": f"{temp}°C",
            "humidity": f"{humidity}%",
            "rain_forecast": weather_desc
        }
    except Exception as e:
        print(f"Weather API error: {e}")
        return {
            "temperature": "Unknown",
            "humidity": "Unknown",
            "rain_forecast": "Unknown"
        }
