import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.schemas import DiagnoseRequest
from app.db.database import get_db
from app.models.models import Farmer, Interaction
from app.services.vision import diagnose_image
from app.services.weather import get_weather
from app.services.market import get_market_info
from app.services.recommendation import generate_recommendation

router = APIRouter()


@router.post("/diagnose-test")
async def diagnose_test(request: DiagnoseRequest, db: Session = Depends(get_db)):
    """
    Test endpoint: runs the full diagnosis pipeline via a JSON payload.
    No Twilio required — useful for local development and CI testing.
    """
    try:
        lat = request.latitude or 0.0
        lon = request.longitude or 0.0

        # Run vision and weather concurrently
        vision_result, weather_data = await asyncio.gather(
            diagnose_image(request.image_url),
            get_weather(lat, lon),
        )

        # Market lookup uses the dynamically detected crop
        market_data = await get_market_info(vision_result.crop)
        recommendation = await generate_recommendation(vision_result, weather_data, market_data)

        return {
            "status": "success",
            "vision": vision_result.model_dump(),
            "weather": weather_data,
            "market": market_data,
            "recommendation": recommendation,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
