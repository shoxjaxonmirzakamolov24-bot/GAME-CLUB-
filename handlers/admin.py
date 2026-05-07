import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
)

import database
from states import ADMIN_BLOCK_ROOM, ADMIN_BLOCK_DEVICE, ADMIN_BLOCK_REASON
from keyboards.markup import (
    admin_menu_keyboard, admin_cancel_complete_keyboard, 
    admin_unblock_keyboard, admin_rooms_block_keyboard, admin_devices_block_keyboard
)
from utils.decorators import admin_required

logger = logging.getLogger(__name__)

@admin_required
async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Admin panelga xush kelibsiz:", reply_markup=admin_menu_keyboard())

@admin_required
async def admin_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "adm_back":
        await query.edit_message_text("Admin panelga xush kelibsiz:", reply_markup=admin_menu_keyboard())
        return

    if data == "adm_bookings":
        bookings = await database.get_all_active_bookings()
        if not bookings:
            await query.edit_message_text("Faol bronlar yo'q.", reply_markup=admin_menu_keyboard())
            return
        
        text = "📊 Barcha faol bronlar:\n\n"
        current_room = None
        for b in bookings:
            b_id, full_name, username, label, room_name, booked_for, user_id, r_id = b
            if current_room != room_name:
                text += f"\n📍 {room_name}:\n"
                current_room = room_name
            import datetime
            dt = datetime.datetime.fromisoformat(booked_for)
            uname_str = f"(@{username})" if username else ""
            text += f"👤 {full_name} {uname_str} → {label} | 🕐 {dt.strftime('%H:%M')} (ID: #{b_id})\n"
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="adm_back")]]))
        
    elif data == "adm_complete":
        bookings = await database.get_all_active_bookings()
        if not bookings:
            await query.edit_message_text("Faol bronlar yo'q.", reply_markup=admin_menu_keyboard())
            return
        await query.edit_message_text("Yakunlash uchun bronni tanlang:", reply_markup=admin_cancel_complete_keyboard(bookings, "cpl"))

    elif data == "adm_cancel":
        bookings = await database.get_all_active_bookings()
        if not bookings:
            await query.edit_message_text("Faol bronlar yo'q.", reply_markup=admin_menu_keyboard())
            return
            
        grouped = {}
        for b in bookings:
            key = (b[6], b[7], b[5]) # (user_id, room_id, booked_for)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(b)
        
        final_bookings = []
        for key, group in grouped.items():
            user_id, room_id, booked_for = key
            room_devices = await database.get_devices_by_room_and_type(room_id)
            if len(group) == len(room_devices) and len(room_devices) > 1:
                fake_b = (f"grp_{user_id}_{room_id}_{booked_for}", group[0][1], group[0][2], "(Butun xona)", group[0][4], booked_for, user_id, room_id)
                final_bookings.append(fake_b)
            else:
                final_bookings.extend(group)
                
        await query.edit_message_text("Bekor qilish uchun bronni tanlang:", reply_markup=admin_cancel_complete_keyboard(final_bookings, "cnl"))

    elif data == "adm_unblock":
        devices = await database.get_blocked_devices()
        if not devices:
            await query.edit_message_text("Bloklangan qurilmalar yo'q.", reply_markup=admin_menu_keyboard())
            return
        await query.edit_message_text("Blokni yechish uchun qurilmani tanlang:", reply_markup=admin_unblock_keyboard(devices))

    elif data == "adm_stats":
        stats = await database.get_today_stats()
        text = (f"📈 Bugungi statistika:\n\n"
                f"▫️ Jami bronlar: {stats[0] or 0}\n"
                f"▫️ Faol bronlar: {stats[1] or 0}\n"
                f"▫️ Yakunlangan: {stats[2] or 0}\n"
                f"▫️ Bekor qilingan: {stats[3] or 0}")
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="adm_back")]]))

@admin_required
async def admin_actions_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("adm_cpl_"):
        b_id = int(data.split('_')[2])
        await database.update_booking_status(b_id, "completed")
        await query.edit_message_text(f"✅ #{b_id} bron yakunlandi.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="adm_back")]]))
        
    elif data == "adm_cancel_all":
        await database.cancel_all_bookings()
        await query.edit_message_text("🗑 Barcha faol bronlar bekor qilindi.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="adm_back")]]))

    elif data.startswith("adm_cnl_"):
        data_part = data[8:]
        if data_part.startswith("grp_"):
            parts = data_part.split('_')
            user_id = int(parts[1])
            room_id = int(parts[2])
            booked_for = "_".join(parts[3:])
            
            await database.cancel_group_bookings(user_id, room_id, booked_for)
            await query.edit_message_text("🗑 Butun xona bandlovi bekor qilindi.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="adm_back")]]))
            
            try:
                import datetime
                import aiosqlite
                from config import DB_PATH
                dt = datetime.datetime.fromisoformat(booked_for)
                admin_uname = update.effective_user.username or "admin"
                async with aiosqlite.connect(DB_PATH) as db:
                    cursor = await db.execute("SELECT name FROM rooms WHERE id = ?", (room_id,))
                    room_name = (await cursor.fetchone())[0]
                msg = (f"❌ Sizning butun xona broningiz bekor qilindi.\n"
                       f"📍 {room_name} | 🕐 {dt.strftime('%H:%M')}\n"
                       f"Murojaat uchun: @{admin_uname}")
                await context.bot.send_message(chat_id=user_id, text=msg)
            except Exception as e:
                logger.error(f"Failed to send group cancellation to {user_id}: {e}")
        else:
            b_id = int(data_part)
            bookings = await database.get_all_active_bookings()
            booking = next((b for b in bookings if b[0] == b_id), None)
            
            await database.update_booking_status(b_id, "cancelled")
            await query.edit_message_text(f"❌ #{b_id} bron bekor qilindi.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="adm_back")]]))
            
            if booking:
                b_id, full_name, username, label, room_name, booked_for, user_id, r_id = booking
                import datetime
                dt = datetime.datetime.fromisoformat(booked_for)
                admin_uname = update.effective_user.username or "admin"
                msg = (f"❌ Sizning broningiz bekor qilindi.\n"
                       f"📍 {label} ({room_name}) | 🕐 {dt.strftime('%H:%M')}\n"
                       f"Murojaat uchun: @{admin_uname}")
                try:
                    await context.bot.send_message(chat_id=user_id, text=msg)
                except Exception as e:
                    logger.error(f"Failed to send cancellation to {user_id}: {e}")

    elif data.startswith("adm_do_unblock_"):
        d_id = int(data.split('_')[3])
        await database.unblock_device(d_id)
        await query.edit_message_text("🔓 Qurilma bloki yechildi.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="adm_back")]]))

@admin_required
async def block_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    import aiosqlite
    from config import DB_PATH
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id, name, price FROM rooms ORDER BY id")
        rooms = await cursor.fetchall()
        
    await query.edit_message_text("Qaysi xonani tanlaysiz?", reply_markup=admin_rooms_block_keyboard(rooms))
    return ADMIN_BLOCK_ROOM

@admin_required
async def block_room(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "adm_back":
        await query.edit_message_text("Admin panelga xush kelibsiz:", reply_markup=admin_menu_keyboard())
        return ConversationHandler.END
        
    room_id = int(query.data.split('_')[3])
    context.user_data['block_room_id'] = room_id
    
    devices = await database.get_devices_by_room_and_type(room_id)
    await query.edit_message_text("Qaysi qurilmani bloklaysiz?", reply_markup=admin_devices_block_keyboard(devices))
    return ADMIN_BLOCK_DEVICE

@admin_required
async def block_device(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "adm_bookings_back_rooms":
        import aiosqlite
        from config import DB_PATH
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT id, name, price FROM rooms ORDER BY id")
            rooms = await cursor.fetchall()
        await query.edit_message_text("Qaysi xonani tanlaysiz?", reply_markup=admin_rooms_block_keyboard(rooms))
        return ADMIN_BLOCK_ROOM
        
    device_id = int(query.data.split('_')[3])
    context.user_data['block_device_id'] = device_id
    device = await database.get_device(device_id)
    context.user_data['block_device_label'] = device[1]
    
    await query.edit_message_text("Sababni yozing:")
    return ADMIN_BLOCK_REASON

@admin_required
async def block_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reason = update.message.text
    device_id = context.user_data['block_device_id']
    label = context.user_data['block_device_label']
    
    await database.block_device(device_id, reason)
    await update.message.reply_text(f"🔒 {label} bloklandi. Sabab: {reason}")
    context.user_data.clear()
    return ConversationHandler.END

def get_admin_block_conv_handler():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(block_start, pattern='^adm_block$')],
        states={
            ADMIN_BLOCK_ROOM: [
                CallbackQueryHandler(block_room, pattern='^adm_blk_room_'),
                CallbackQueryHandler(block_room, pattern='^adm_back$')
            ],
            ADMIN_BLOCK_DEVICE: [
                CallbackQueryHandler(block_device, pattern='^adm_blk_dev_'),
                CallbackQueryHandler(block_device, pattern='^adm_bookings_back_rooms$')
            ],
            ADMIN_BLOCK_REASON: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, block_reason)
            ]
        },
        fallbacks=[CommandHandler('cancel', lambda u,c: ConversationHandler.END)],
        allow_reentry=True
    )
