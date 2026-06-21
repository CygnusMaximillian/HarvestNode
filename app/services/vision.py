import base64
import json
import requests
from openai import OpenAI
from app.core.config import settings
from app.schemas.schemas import VisionResponse

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def encode_image_from_url(image_url: str) -> str:
    try:
        # If it's a Twilio URL, we might need auth.
        response = requests.get(image_url, auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN))
        response.raise_for_status()
        return base64.b64encode(response.content).decode('utf-8')
    except Exception as e:
        print(f"Failed to download image with auth: {e}")
        # fallback to no auth
        response = requests.get(image_url)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode('utf-8')
        raise

def diagnose_image(image_url: str) -> VisionResponse:
    base64_image = encode_image_from_url(image_url)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={ "type": "json_object" },
        messages=[
            {
                "role": "system",
                "content": "You are an agricultural expert. Analyze the crop image and diagnose any disease. Respond ONLY in JSON format with exactly three keys: 'disease' (string), 'confidence' (float between 0 and 1), and 'summary' (string explaining symptoms)."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
    )
    
    content = response.choices[0].message.content
    data = json.loads(content)
    
    return VisionResponse(
        disease=data.get("disease", "Unknown"),
        confidence=float(data.get("confidence", 0.0)),
        summary=data.get("summary", "No summary provided.")
    )
