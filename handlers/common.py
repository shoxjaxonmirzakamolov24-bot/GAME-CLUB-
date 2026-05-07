import logging
from telegram import Update
from telegram.ext import ContextTypes
from keyboards.markup import main_menu_keyboard
import database
from datetime import datetime

logger = logging.getLogger(__name__)

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"start_cmd called by {update.effective_user.id}")
    user = update.effective_user
    await database.add_user(user.id, user.username, user.full_name)
    await update.message.reply_text(
        "Xush kelibsiz! Asosiy menyudan kerakli bo'limni tanlang:",
        reply_markup=main_menu_keyboard()
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"help_cmd called by {update.effective_user.id}")
    help_text = (
        "ℹ️ <b>Yordam bo'limi</b>\n\n"
        "1. <b>Adminga murojaat qilish:</b> @mlbbtigril @Xusanboy030\n"
        "2. <b>Botdan foydalanish video qo'llanma:</b> https://t.me/+D8o1vaU7_YkyNjAy"
    )
    await update.message.reply_text(help_text, parse_mode='HTML')

async def my_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"my_bookings called by {update.effective_user.id}")
    user_id = update.effective_user.id
    bookings = await database.get_user_bookings(user_id)
    if not bookings:
        await update.message.reply_text("Sizda faol bronlar yo'q.")
        return
    
    text = "📋 Mening faol bronlarim:\n\n"
    for b in bookings:
        b_id, label, room_name, booked_for, price, duration = b
        dt = datetime.fromisoformat(booked_for)
        day_str = "Bugun" if dt.date() == datetime.now().date() else dt.strftime("%d.%m.%Y")
        total_price = price * duration
        text += (f"#{b_id} — {label} ({room_name})\n"
                 f"🕐 {day_str} {dt.strftime('%H:%M')}\n"
                 f"⏳ Davomiyligi: {duration} soat\n"
                 f"💰 Umumiy narx: {total_price:,} so'm\n\n".replace(',', ' '))
    await update.message.reply_text(text)

async def send_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location_url = "https://maps.app.goo.gl/gdixWbvPg3s1DGp89"
    await update.message.reply_text(
        f"📍 Bizning manzilimiz:\n{location_url}"
    )
