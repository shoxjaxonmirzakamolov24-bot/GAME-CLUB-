import logging
import sys
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from config import BOT_TOKEN
from database import init_db
from scheduler import setup_scheduler

from handlers.common import start_cmd, help_cmd, my_bookings, send_location
from handlers.booking import get_booking_conv_handler
from handlers.admin import (
    admin_start, admin_menu_callback, admin_actions_callback,
    get_admin_block_conv_handler
)

# Working directory ni to'g'ri o'rnatish
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Logging sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Health Check Server (Render uchun)
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        return # Loglarni to'ldirmaslik uchun

def run_health_server():
    server_address = ('', 10000)
    httpd = HTTPServer(server_address, HealthCheckHandler)
    logger.info("✅ Health server 10000-portda ishga tushdi.")
    httpd.serve_forever()

async def post_init(application):
    await init_db()
    setup_scheduler(application)
    logger.info("Database va Scheduler muvaffaqiyatli ishga tushdi.")

def main():
    try:
        if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            logger.error("Iltimos config.py da BOT_TOKEN ni o'rnating!")
            return

        # Health serverni alohida thread da boshlash
        health_thread = threading.Thread(target=run_health_server, daemon=True)
        health_thread.start()

        application = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

        # ── Asosiy menyu tugmalari ──────────────────────────────
        application.add_handler(CommandHandler("start", start_cmd))
        application.add_handler(CommandHandler("help", help_cmd))
        application.add_handler(MessageHandler(filters.Regex('Mening bronlarim'), my_bookings))
        application.add_handler(MessageHandler(filters.Regex('Manzil'), send_location))
        application.add_handler(MessageHandler(filters.Regex('Yordam'), help_cmd))

        # ── Bron qilish conversation ─────────────────────────────
        application.add_handler(get_booking_conv_handler())

        # ── Admin paneli ─────────────────────────────────────────
        application.add_handler(CommandHandler("admin", admin_start))
        application.add_handler(get_admin_block_conv_handler())
        application.add_handler(CallbackQueryHandler(admin_menu_callback, pattern='^adm_(back|bookings|complete|cancel|unblock|stats)$'))
        application.add_handler(CallbackQueryHandler(admin_actions_callback, pattern='^adm_(cpl_|cnl_|do_unblock_|cancel_all)'))

        logger.info("🚀 Bot muvaffaqiyatli ishga tushdi! Polling boshlandi...")
        
        # Conflict xatosini oldini olish va Render uchun polling sozlamalari
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=[]
        )

    except Exception as e:
        logger.error(f"Bot da jiddiy xatolik: {e}", exc_info=True)

if __name__ == '__main__':
    main()
