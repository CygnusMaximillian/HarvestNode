from pydantic import BaseModel
from typing import Optional


class VisionResponse(BaseModel):
    crop: str
    disease: str
    confidence: float
    summary: str


class DiagnoseRequest(BaseModel):
    image_url: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class HealthResponse(BaseModel):
    status: str
