import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

# Mapping common crop names to World Bank commodity indicator codes
# Ref: https://api.worldbank.org/v2/en/indicator/
_CROP_INDICATORS: dict[str, str] = {
    "Tomato": "PTOMT_USD",
    "Wheat": "PWHEAMT_USD",
    "Rice": "PRICENPQ_USD",
    "Maize": "PMAIZMMT_USD",
    "Corn": "PMAIZMMT_USD",
    "Soybean": "PSOYBSM_USD",
    "Sugar": "PSUGAISAUSDM",
    "Cotton": "PCOTTINDUSDM",
}

_STATIC_FALLBACK: dict[str, dict] = {
    "Tomato": {"current_price": "$22.50 per 100 kg", "trend": "stable"},
    "Wheat": {"current_price": "$215.00 per mt", "trend": "decreasing"},
    "Rice": {"current_price": "$490.00 per mt", "trend": "stable"},
    "Maize": {"current_price": "$185.00 per mt", "trend": "increasing"},
    "Corn": {"current_price": "$185.00 per mt", "trend": "increasing"},
    "Soybean": {"current_price": "$410.00 per mt", "trend": "stable"},
}

_DEFAULT_FALLBACK = {"current_price": "N/A", "trend": "unknown"}


async def get_market_info(crop_name: str) -> dict:
    """
    Fetch the latest commodity price for the given crop from the World Bank API.
    Falls back to a static estimate if the crop is not in the indicator map or the API fails.
    """
    indicator = _CROP_INDICATORS.get(crop_name)
    if indicator:
        try:
            url = (
                f"https://api.worldbank.org/v2/en/indicator/{indicator}"
                f"?format=json&mrv=2&per_page=2"
            )
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url)
                response.raise_for_status()
                payload = response.json()

            # World Bank response: [metadata_dict, [data_entry, ...]]
            entries = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
            values = [e["value"] for e in entries if e.get("value") is not None]

            if len(values) >= 2:
                latest, previous = values[0], values[1]
                if latest > previous:
                    trend = "increasing"
                elif latest < previous:
                    trend = "decreasing"
                else:
                    trend = "stable"
                return {
                    "crop": crop_name,
                    "current_price": f"${latest:.2f} per mt",
                    "trend": trend,
                }
            elif len(values) == 1:
                return {
                    "crop": crop_name,
                    "current_price": f"${values[0]:.2f} per mt",
                    "trend": "unknown",
                }
        except Exception as e:
            logger.error(f"World Bank market API error for {crop_name}: {e}")

    # Fallback to static estimates
    fallback = _STATIC_FALLBACK.get(crop_name, _DEFAULT_FALLBACK)
    return {
        "crop": crop_name,
        "current_price": fallback["current_price"],
        "trend": fallback["trend"],
    }
