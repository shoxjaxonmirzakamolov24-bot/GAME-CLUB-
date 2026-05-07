import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "8776526267:AAGn3B0sDaZN2iw87QvIDRsssXTpjI2uLvQ")
INITIAL_ADMIN_IDS = [6664092910, 1134823495]
DB_PATH = os.getenv("DB_PATH", "gameclub.db")

# Render deployment settings
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")   # e.g. https://your-app.onrender.com
PORT = int(os.getenv("PORT", 8000))
