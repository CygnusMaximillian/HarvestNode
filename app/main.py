from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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

# Serve static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root():
    return FileResponse(str(static_dir / "index.html"))
