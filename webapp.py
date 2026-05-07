import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from config import BOT_TOKEN, WEBHOOK_URL
from database import init_db
from scheduler import setup_scheduler

from handlers.common import start_cmd, help_cmd, my_bookings, send_location
from handlers.booking import get_booking_conv_handler
from handlers.admin import (
    admin_start, admin_menu_callback, admin_actions_callback,
    get_admin_block_conv_handler
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# PTB applicationni global yaratamiz (webhook rejimi uchun updater=None)
ptb_app = ApplicationBuilder().token(BOT_TOKEN).updater(None).build()

def register_handlers(app):
    # ── Asosiy menyu tugmalari ─────────────────────────────
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.Regex('Mening bronlarim'), my_bookings))
    app.add_handler(MessageHandler(filters.Regex('Manzil'), send_location))
    app.add_handler(MessageHandler(filters.Regex('Yordam'), help_cmd))

    # ── Bron qilish conversation ──────────────────────────
    app.add_handler(get_booking_conv_handler())

    # ── Admin paneli ──────────────────────────────────────
    app.add_handler(CommandHandler("admin", admin_start))
    app.add_handler(get_admin_block_conv_handler())
    app.add_handler(CallbackQueryHandler(admin_menu_callback, pattern='^adm_(back|bookings|complete|cancel|unblock|stats)$'))
    app.add_handler(CallbackQueryHandler(admin_actions_callback, pattern='^adm_(cpl_|cnl_|do_unblock_|cancel_all)'))

register_handlers(ptb_app)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────
    await init_db()
    await ptb_app.initialize()
    setup_scheduler(ptb_app)

    webhook_path = f"/webhook/{BOT_TOKEN}"
    full_url = f"{WEBHOOK_URL.rstrip('/')}{webhook_path}"
    await ptb_app.bot.set_webhook(url=full_url)
    logger.info(f"✅ Webhook o'rnatildi: {full_url}")

    await ptb_app.start()
    yield

    # ── Shutdown ──────────────────────────────────────────
    await ptb_app.bot.delete_webhook()
    await ptb_app.stop()
    await ptb_app.shutdown()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def health_check():
    return {"status": "ok", "message": "GameClub Bot is running!"}

@app.post(f"/webhook/{BOT_TOKEN}")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, ptb_app.bot)
    await ptb_app.process_update(update)
    return Response(status_code=200)
