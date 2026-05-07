from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
import database

def admin_required(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if not await database.is_admin(user_id):
            if update.message:
                await update.message.reply_text("⛔️ Bu buyruq faqat adminlar uchun.")
            elif update.callback_query:
                await update.callback_query.answer("⛔️ Bu buyruq faqat adminlar uchun.", show_alert=True)
            return
        return await func(update, context, *args, **kwargs)
    return wrapper
