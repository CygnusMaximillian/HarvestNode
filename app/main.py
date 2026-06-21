from fastapi import FastAPI
import logging
from app.db.database import Base, engine
from app.api.routes import health, webhook, diagnose
from app.core.config import settings

# Setup logging
logging.basicConfig(level=settings.LOG_LEVEL.upper())

# Create tables (for MVP, auto-create)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="HarvestNode MVP", version="1.0.0")

app.include_router(health.router)
app.include_router(webhook.router)
app.include_router(diagnose.router)
