import os
import time
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Load .env file if present (keeps the API key out of source code)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed — rely on environment variable

app = Flask(__name__)
CORS(app)

# ── IBM Configuration ──────────────────────────────────────────────────────
# Set IBM_API_KEY in your .env file or as an environment variable.
# Never hard-code or commit the key.
IBM_API_KEY = os.environ.get("IBM_API_KEY", "")
IBM_URL     = "https://us-south.ml.cloud.ibm.com/ml/v1/text/chat?version=2023-05-29"
# Primary model — llama-3-3-70b has a higher free-tier quota than granite-4
MODEL_ID    = "meta-llama/llama-3-3-70b-instruct"
FALLBACK_MODEL = "ibm/granite-4-h-small"
PROJECT_ID  = "eed5989a-84db-4b6d-953b-b14958a0f0d0"
IAM_URL     = "https://iam.cloud.ibm.com/identity/token"

_cached_token = None
_token_expiry = 0


def get_iam_token():
    global _cached_token, _token_expiry
    if not IBM_API_KEY:
        raise RuntimeError("IBM_API_KEY is not set. Add it to your .env file.")
    if _cached_token and time.time() < _token_expiry:
        return _cached_token
    r = requests.post(
        IAM_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": IBM_API_KEY},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    _cached_token = data["access_token"]
    _token_expiry = time.time() + data.get("expires_in", 3600) - 300
    return _cached_token


SYSTEM_PROMPT = (
    "You are an expert India Travel Planner AI assistant. Your role is to help travelers "
    "plan amazing trips across India.\n\n"
    "You specialize in:\n"
    "- Crafting detailed day-by-day travel itineraries for any Indian destination\n"
    "- Suggesting the best time to visit different regions of India\n"
    "- Recommending must-see attractions, hidden gems, and off-beat destinations\n"
    "- Advising on budget planning (budget, mid-range, luxury)\n"
    "- Providing information on local cuisine, cultural etiquette, and customs\n"
    "- Transport options: flights, trains (IRCTC), buses, taxis\n"
    "- Hotel and accommodation recommendations\n"
    "- Safety tips and travel advisories\n"
    "- Festival and event-based travel planning\n\n"
    "Popular destinations you know well include: Rajasthan, Kerala, Goa, Himachal Pradesh, "
    "Uttarakhand, Tamil Nadu, Karnataka, Maharashtra, Ladakh, Andaman & Nicobar Islands, "
    "Northeast India (Meghalaya, Sikkim, Assam), Varanasi, Agra, Delhi, Mumbai, Kolkata, "
    "Jaipur, Udaipur, Rishikesh, Hampi, Coorg, Munnar, Ooty, and many more.\n\n"
    "Always respond in a friendly, enthusiastic, and helpful manner. Format itineraries "
    "clearly with day-by-day breakdowns. Include estimated costs when asked. Highlight "
    "UNESCO World Heritage Sites and national parks when relevant."
)

QUICK_PROMPTS = [
    "Plan a 7-day trip to Rajasthan with heritage forts and desert safari",
    "Best time to visit Kerala backwaters and a 5-day itinerary",
    "Budget trip to Goa for 4 days under Rs.15,000",
    "Himalayan adventure: Manali to Leh road trip itinerary",
    "Family trip to Agra, Jaipur and Delhi (Golden Triangle) in 6 days",
    "Hidden gems of Northeast India — Meghalaya and Sikkim",
    "Spiritual journey: Varanasi, Rishikesh and Haridwar in 5 days",
    "Beach hopping in Andaman Islands — 7-day itinerary",
]


# ── Routes ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    body = request.get_json(force=True)
    if not body or "messages" not in body:
        return jsonify({"error": "Missing 'messages' in request body"}), 400

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + body["messages"]

    try:
        token = get_iam_token()
    except Exception as e:
        return jsonify({"error": "IBM authentication failed", "detail": str(e)}), 502

    for model in [MODEL_ID, FALLBACK_MODEL]:
        for attempt in range(2):
            try:
                r = requests.post(
                    IBM_URL,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                    json={
                        "model_id":   model,
                        "project_id": PROJECT_ID,
                        "messages":   messages,
                        "parameters": {
                            "max_new_tokens":     1024,
                            "temperature":        0.7,
                            "top_p":              0.9,
                            "repetition_penalty": 1.1,
                        },
                    },
                    timeout=60,
                )

                # Rate limit — wait briefly and retry once, then try fallback model
                if r.status_code == 429:
                    time.sleep(4)
                    continue

                r.raise_for_status()
                choices = r.json().get("choices", [])
                if choices:
                    return jsonify({"reply": choices[0]["message"]["content"].strip()})
                return jsonify({"error": "Empty response from IBM API"}), 502

            except requests.exceptions.HTTPError as e:
                detail = ""
                try:    detail = e.response.json()
                except: detail = e.response.text if e.response else str(e)
                return jsonify({"error": f"IBM API error {e.response.status_code}", "detail": str(detail)}), 502
            except requests.exceptions.RequestException as e:
                return jsonify({"error": "Network error reaching IBM API", "detail": str(e)}), 502
        # both attempts hit 429 — try next model

    return jsonify({"error": "Service is busy. Please wait a moment and try again."}), 429


@app.route("/api/suggestions", methods=["GET"])
def suggestions():
    return jsonify({"suggestions": QUICK_PROMPTS})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model": MODEL_ID, "fallback": FALLBACK_MODEL})


if __name__ == "__main__":
    if not IBM_API_KEY:
        print("WARNING: IBM_API_KEY not set. Add it to your .env file.")
    port = int(os.environ.get("PORT", 5000))
    print(f"Travel Planner Agent running at http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
