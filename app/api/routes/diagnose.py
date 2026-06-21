from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.schemas import DiagnoseRequest
from app.db.database import get_db
from app.models.models import Farmer, Interaction
from app.services.vision import diagnose_image
from app.services.weather import get_weather
from app.services.market import get_market_info
from app.services.recommendation import generate_recommendation
from app.services.twilio_client import send_whatsapp_message

router = APIRouter()

@router.post("/diagnose-test")
def diagnose_test(request: DiagnoseRequest, db: Session = Depends(get_db)):
    try:
        # 1. Vision Service
        vision_result = diagnose_image(request.image_url)
        
        # 2. Weather Service
        lat = request.latitude or 0.0 # Default mock location
        lon = request.longitude or 0.0
        weather_data = get_weather(lat, lon)
        
        # 3. Market Service
        market_data = get_market_info("Tomato") # Mock crop
        
        # 4. Recommendation Service
        recommendation = generate_recommendation(vision_result, weather_data, market_data)
        
        # Combine response
        combined_response = f"""Disease:
{vision_result.disease} ({int(vision_result.confidence * 100)}% confidence)

Weather:
{weather_data['temperature']}, {weather_data['humidity']}, {weather_data['rain_forecast']}

Market:
{market_data['crop']} is {market_data['current_price']} ({market_data['trend']})

Recommendation:
{recommendation}
"""
        
        return {
            "status": "success",
            "message": combined_response,
            "vision": vision_result.model_dump(),
            "weather": weather_data,
            "market": market_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
