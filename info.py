import os
from dotenv import load_dotenv

# Local testing ke liye .env file load karega
# Render par ye automatically dashboard se variables lega
load_dotenv()

# --- BOT TOKENS & WEBHOOK ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
PORT = int(os.environ.get("PORT", 10000))

# --- DATABASE (The main part for your error) ---
# Render dashboard par "MONGO_URI" name se variable hona chahiye
MONGO_URI = os.environ.get("MONGO_URI", "")

# --- ADMINS & LOGS ---
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", 0))
# Admin IDs ko list mein convert karega (Comma-separated: 1234,5678)
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x]

# --- AI MODELS (OpenRouter) ---
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
MODELS = {
    "model_1": os.environ.get("MODEL_1", "openai/gpt-4o-mini"),
    "model_2": os.environ.get("MODEL_2", "anthropic/claude-3-haiku"),
    "model_3": os.environ.get("MODEL_3", "mistralai/mixtral-8x7b")
}

# --- SHORTENER & MONETIZATION ---
SHORTENER_API_URL = os.environ.get("SHORTENER_API_URL", "https://shrinkme.io/api")
SHORTENER_API_TOKEN = os.environ.get("SHORTENER_API_TOKEN", "")

# --- PREMIUM SYSTEM (India UPI) ---
UPI_ID = os.environ.get("UPI_ID", "")
QR_IMAGE_URL = os.environ.get("QR_IMAGE_URL", "")

# --- UI ASSETS ---
WELCOME_IMAGE_URL = os.environ.get("WELCOME_IMAGE_URL", "")
MORE_BOTS_URL = os.environ.get("MORE_BOTS_URL", "")
