import random

def get_market_info(crop_name: str) -> dict:
    """Mocked market service"""
    # Just to show realistic sample responses
    trends = ["increasing", "stable", "decreasing"]
    trend = random.choice(trends)
    price = round(random.uniform(10.0, 50.0), 2)
    
    return {
        "crop": crop_name,
        "current_price": f"${price} per kg",
        "trend": trend
    }
