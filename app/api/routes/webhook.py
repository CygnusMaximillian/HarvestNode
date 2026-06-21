from fastapi import APIRouter, Depends, Request, Form
from sqlalchemy.orm import Session
from typing import Optional
from app.db.database import get_db
from app.models.models import Farmer, Interaction
from app.services.vision import diagnose_image
from app.services.weather import get_weather
from app.services.market import get_market_info
from app.services.recommendation import generate_recommendation
from app.services.twilio_client import send_whatsapp_message
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/webhook/whatsapp")
async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    NumMedia: str = Form("0"),
    MediaUrl0: Optional[str] = Form(None),
    Latitude: Optional[str] = Form(None),
    Longitude: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    try:
        sender_number = From
        
        # Check if farmer exists
        farmer = db.query(Farmer).filter(Farmer.phone_number == sender_number).first()
        if not farmer:
            farmer = Farmer(phone_number=sender_number)
            db.add(farmer)
            db.commit()
            db.refresh(farmer)

        # 1. Detect image
        if int(NumMedia) == 0 or not MediaUrl0:
            msg = "Please send a clear image of your crop to get a diagnosis."
            send_whatsapp_message(sender_number, msg)
            return {"status": "ok"}

        # 2. Process Image -> Vision Service
        vision_result = diagnose_image(MediaUrl0)

        # 3. Weather Service
        # If user sent location, use it. Otherwise, use mock location.
        lat = float(Latitude) if Latitude else 0.0
        lon = float(Longitude) if Longitude else 0.0
        weather_data = get_weather(lat, lon)

        # 4. Market Service
        market_data = get_market_info("Tomato") # Use default crop or extract from vision if possible
        
        # 5. Recommendation Service
        recommendation = generate_recommendation(vision_result, weather_data, market_data)

        # Combine response
        combined_response = f"""Disease:
{vision_result.disease} ({int(vision_result.confidence * 100)}% confidence)

Weather:
{weather_data['temperature']}, {weather_data['humidity']}, {weather_data['rain_forecast']}

Market:
{market_data['crop']} prices are {market_data['trend']}.

Recommendation:
{recommendation}
"""
        
        # 6. Send reply
        send_whatsapp_message(sender_number, combined_response)

        # 7. Store interaction
        interaction = Interaction(
            farmer_id=farmer.id,
            image_url=MediaUrl0,
            disease=vision_result.disease,
            confidence=vision_result.confidence,
            recommendation=recommendation
        )
        db.add(interaction)
        db.commit()

        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error in webhook: {e}")
        send_whatsapp_message(From, "Sorry, something went wrong processing your request. Please try again.")
        return {"status": "error"}
