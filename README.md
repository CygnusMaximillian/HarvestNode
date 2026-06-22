# 🌿 HarvestNode

> AI-powered crop disease diagnosis via WhatsApp — built for smallholder farmers.

A farmer sends a photo of their crop on WhatsApp. HarvestNode replies in seconds with:
- **Disease diagnosis** (GPT-4o Vision)
- **Current weather** at the farmer's location (OpenWeatherMap)
- **Live commodity prices** (World Bank API)
- **Actionable recommendation** — treatment, risk level, harvest advice (GPT-4o)

---

## Architecture

```
Farmer (WhatsApp)
      │
      ▼
Twilio ──POST /webhook/whatsapp──► FastAPI
                                      │
                         ┌────────────┴────────────┐
                         ▼                         ▼
                   vision.py              weather.py
                (GPT-4o Vision)       (OpenWeatherMap)
                         │
                         ▼
                    market.py
                (World Bank API)
                         │
                         ▼
               recommendation.py
                  (GPT-4o Chat)
                         │
                         ▼
               twilio_client.py ──► WhatsApp reply
                         │
                         ▼
                    PostgreSQL
              (farmers + interactions)
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API Framework | FastAPI (async) |
| AI Vision | OpenAI GPT-4o |
| Messaging | Twilio WhatsApp Sandbox |
| Weather | OpenWeatherMap API |
| Market Data | World Bank Commodity Prices API |
| Database | PostgreSQL via SQLAlchemy |
| HTTP Client | httpx (async) |
| Containerisation | Docker + docker-compose |

---

## Project Structure

```
HarvestNode/
├── app/
│   ├── api/routes/
│   │   ├── health.py          # GET /health
│   │   ├── webhook.py         # POST /webhook/whatsapp  ← main entry
│   │   └── diagnose.py        # POST /diagnose-test     ← dev/test
│   ├── core/
│   │   ├── config.py          # Pydantic settings (env vars)
│   │   └── security.py        # Twilio signature validation
│   ├── db/
│   │   └── database.py        # SQLAlchemy engine + session
│   ├── models/
│   │   └── models.py          # Farmer, Interaction tables
│   ├── schemas/
│   │   └── schemas.py         # Pydantic request/response models
│   ├── services/
│   │   ├── vision.py          # GPT-4o image diagnosis
│   │   ├── weather.py         # OpenWeatherMap fetch
│   │   ├── market.py          # World Bank commodity prices
│   │   ├── recommendation.py  # GPT-4o recommendation
│   │   └── twilio_client.py   # WhatsApp reply sender
│   └── main.py                # FastAPI app entrypoint
├── .env.example               # Environment variable template
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Quick Start

### 1. Clone & Configure

```bash
git clone https://github.com/CygnusMaximillian/HarvestNode.git
cd HarvestNode
cp .env.example .env
```

Edit `.env` with your keys:

```env
# Required
DATABASE_URL=postgresql://harvestnode:password@db:5432/harvestnode

# Optional — leave blank to use mock/fallback responses in dev
OPENAI_API_KEY=sk-...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_NUMBER=+14155238886
WEATHER_API_KEY=...
```

> **All API keys are optional for local development.**  
> The app starts and runs in mock mode without any keys.

### 2. Start with Docker

```bash
docker compose up -d --build
```

This starts:
- `app` — FastAPI on **http://localhost:8000**
- `db` — PostgreSQL on **localhost:5432**

### 3. Run Locally (without Docker)

Requires Python 3.12+ and a running PostgreSQL instance.

```bash
pip install -r requirements.txt

# Point DATABASE_URL at your local postgres in .env, then:
uvicorn app.main:app --reload
```

---

## Testing

### ✅ 1. Health Check (verify the server is running)

```bash
curl http://localhost:8000/health
```

**Expected:**
```json
{"status": "healthy"}
```

---

### ✅ 2. Full Pipeline Test — No Twilio Required

The `/diagnose-test` endpoint runs the complete pipeline (vision → weather → market → recommendation) from a JSON body, skipping WhatsApp entirely.

```bash
curl -X POST http://localhost:8000/diagnose-test \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/Tomato_leaf_blight.jpg/800px-Tomato_leaf_blight.jpg",
    "latitude": 28.61,
    "longitude": 77.20
  }'
```

**Expected response shape:**
```json
{
  "status": "success",
  "vision": {
    "crop": "Tomato",
    "disease": "Early Blight",
    "confidence": 0.92,
    "summary": "Dark concentric rings on lower leaves..."
  },
  "weather": {
    "temperature": "32°C",
    "humidity": "65%",
    "rain_forecast": "light rain"
  },
  "market": {
    "crop": "Tomato",
    "current_price": "$22.50 per mt",
    "trend": "stable"
  },
  "recommendation": "..."
}
```

> Without an `OPENAI_API_KEY`, vision and recommendation return mock data so you can still verify the pipeline structure.

---

### ✅ 3. Interactive API Docs

FastAPI ships with built-in Swagger UI. Open in your browser:

```
http://localhost:8000/docs
```

You can hit `/diagnose-test` directly from the browser UI — no curl needed.

---

### ✅ 4. WhatsApp End-to-End Test

**Prerequisites:** Twilio account + WhatsApp Sandbox configured.

**Step 1 — Expose port 8000 to the internet:**

```bash
# Using ngrok
ngrok http 8000
```

Copy the generated HTTPS URL, e.g. `https://abcd1234.ngrok.app`

**Step 2 — Configure Twilio Webhook:**

1. Go to [Twilio Console → Messaging → Try it out → Send a WhatsApp message](https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn)
2. Under **Sandbox Settings**, set:
   - **When a message comes in:** `https://abcd1234.ngrok.app/webhook/whatsapp`
   - Method: `HTTP POST`
3. Save.

**Step 3 — Send a test message:**

From your phone, send the sandbox join code (e.g. `join <word>-<word>`) to the Twilio sandbox number, then send any **image of a crop**.

**Expected WhatsApp reply:**
```
🌿 Crop: Tomato
🔬 Disease: Early Blight (92% confidence)
📋 Symptoms: Dark concentric rings visible on lower leaves...

🌤️ Weather: 32°C, 65%, light rain

📈 Market: Tomato — $22.50 per mt (stable)

💊 Recommendation:
• Apply copper-based fungicide immediately...
• Risk Level: Medium
• Harvest: Delay by 5–7 days
```

---

### ✅ 5. Rate Limit Test

Send two requests from the same number within 60 seconds — the second should be rejected:

```bash
# Simulate two rapid webhook POSTs (replace with your number)
curl -X POST http://localhost:8000/webhook/whatsapp \
  -d "From=whatsapp:+919999999999&NumMedia=0"

curl -X POST http://localhost:8000/webhook/whatsapp \
  -d "From=whatsapp:+919999999999&NumMedia=0"
```

> The second call returns `{"status": "rate_limited"}` and sends a WhatsApp message saying how many seconds to wait.  
> In dev mode (no `TWILIO_AUTH_TOKEN`), Twilio signature validation is skipped so these curl commands work directly.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Liveness check |
| `POST` | `/webhook/whatsapp` | Twilio WhatsApp webhook (production) |
| `POST` | `/diagnose-test` | Dev/test pipeline endpoint |
| `GET` | `/docs` | Swagger UI |
| `GET` | `/redoc` | ReDoc UI |

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `OPENAI_API_KEY` | Optional | GPT-4o Vision + Chat. Mock fallback if absent. |
| `TWILIO_ACCOUNT_SID` | Optional | Twilio account. Mock console output if absent. |
| `TWILIO_AUTH_TOKEN` | Optional | Used for signature validation + sending messages. |
| `TWILIO_WHATSAPP_NUMBER` | Optional | Your Twilio sandbox number. |
| `WEATHER_API_KEY` | Optional | OpenWeatherMap. Returns mock 25°C/60% if absent. |
| `APP_ENV` | Optional | `development` (default) or `production` |
| `LOG_LEVEL` | Optional | `info` (default), `debug`, `warning` |

---

## Security

- **Twilio Signature Validation** — every `POST /webhook/whatsapp` request is validated using HMAC-SHA1 against the `X-Twilio-Signature` header per [Twilio's spec](https://www.twilio.com/docs/usage/security). Invalid requests get `403 Forbidden`. Disabled automatically in dev when `TWILIO_AUTH_TOKEN` is not set.
- **Rate Limiting** — each farmer (phone number) is limited to one request per 60 seconds, preventing OpenAI cost abuse.

---

## Contributing

```bash
git checkout -b your-feature
# make changes
git push origin your-feature
# open a pull request → main
```
