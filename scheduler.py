import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.ext import Application
from datetime import datetime

import database

logger = logging.getLogger(__name__)

async def check_notifications(app: Application):
    try:
        bookings = await database.get_unnotified_upcoming_bookings()
        for b in bookings:
            b_id, user_id, label, room_name, booked_for = b
            dt = datetime.fromisoformat(booked_for)
            
            msg = (f"⏰ Eslatma! Sizning broningiz 10 daqiqadan keyin boshlanadi.\n"
                   f"📍 {label} ({room_name})\n"
                   f"🕐 {dt.strftime('%H:%M')}\n"
                   f"Tayyor bo'ling!")
            try:
                await app.bot.send_message(chat_id=user_id, text=msg)
                await database.mark_notified(b_id)
                logger.info(f"Notification sent for booking #{b_id} to user {user_id}")
            except Exception as e:
                logger.error(f"Failed to send notification to {user_id} for booking #{b_id}: {e}")
    except Exception as e:
        logger.error(f"Error in check_notifications job: {e}")

def setup_scheduler(app: Application):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_notifications, 'interval', seconds=60, args=[app])
    scheduler.start()
    return scheduler
