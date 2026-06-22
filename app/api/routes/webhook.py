from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from app.core.security import verify_twilio_signature
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

# Rate-limit window in seconds (one request per farmer per window)
RATE_LIMIT_SECONDS = 60


@router.post("/webhook/whatsapp", dependencies=[Depends(verify_twilio_signature)])
async def whatsapp_webhook(
    From: str = Form(...),
    NumMedia: str = Form("0"),
    MediaUrl0: Optional[str] = Form(None),
    Latitude: Optional[str] = Form(None),
    Longitude: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    sender_number = From
    try:
        # ── 1. Upsert farmer ────────────────────────────────────────────────
        farmer = db.query(Farmer).filter(Farmer.phone_number == sender_number).first()
        if not farmer:
            farmer = Farmer(phone_number=sender_number)
            db.add(farmer)
            db.commit()
            db.refresh(farmer)

        # ── 2. Rate limiting ─────────────────────────────────────────────────
        now = datetime.now(timezone.utc)
        if farmer.last_request_at:
            elapsed = (now - farmer.last_request_at.replace(tzinfo=timezone.utc)).total_seconds()
            if elapsed < RATE_LIMIT_SECONDS:
                wait = int(RATE_LIMIT_SECONDS - elapsed)
                await send_whatsapp_message(
                    sender_number,
                    f"Please wait {wait} seconds before sending another request.",
                )
                return {"status": "rate_limited"}

        # ── 3. Require an image ──────────────────────────────────────────────
        if int(NumMedia) == 0 or not MediaUrl0:
            await send_whatsapp_message(
                sender_number,
                "Please send a clear image of your crop to get a diagnosis.",
            )
            return {"status": "ok"}

        # Update last_request_at before the pipeline to prevent concurrent abuse
        farmer.last_request_at = now
        db.commit()

        # ── 4. Run pipeline concurrently ─────────────────────────────────────
        import asyncio

        lat = float(Latitude) if Latitude else 0.0
        lon = float(Longitude) if Longitude else 0.0

        vision_result, weather_data = await asyncio.gather(
            diagnose_image(MediaUrl0),
            get_weather(lat, lon),
        )
        market_data = await get_market_info(vision_result.crop)
        recommendation = await generate_recommendation(vision_result, weather_data, market_data)

        # ── 5. Build and send reply ───────────────────────────────────────────
        reply = (
            f"🌿 *Crop*: {vision_result.crop}\n"
            f"🔬 *Disease*: {vision_result.disease} ({int(vision_result.confidence * 100)}% confidence)\n"
            f"📋 *Symptoms*: {vision_result.summary}\n\n"
            f"🌤️ *Weather*: {weather_data['temperature']}, {weather_data['humidity']}, "
            f"{weather_data['rain_forecast']}\n\n"
            f"📈 *Market*: {market_data['crop']} — {market_data['current_price']} ({market_data['trend']})\n\n"
            f"💊 *Recommendation*:\n{recommendation}"
        )
        await send_whatsapp_message(sender_number, reply)

        # ── 6. Persist interaction ────────────────────────────────────────────
        interaction = Interaction(
            farmer_id=farmer.id,
            image_url=MediaUrl0,
            crop=vision_result.crop,
            disease=vision_result.disease,
            confidence=vision_result.confidence,
            recommendation=recommendation,
        )
        db.add(interaction)
        db.commit()

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Webhook error for {sender_number}: {e}", exc_info=True)
        await send_whatsapp_message(
            sender_number,
            "Sorry, something went wrong processing your request. Please try again shortly.",
        )
        return {"status": "error"}
