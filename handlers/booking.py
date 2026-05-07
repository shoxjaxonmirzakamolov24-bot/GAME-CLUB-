import logging
import aiosqlite
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    CallbackQueryHandler, MessageHandler, filters
)
from datetime import datetime

import database
from config import DB_PATH
from states import (
    SELECT_CATEGORY, SELECT_ROOM, SELECT_DAY,
    SELECT_DEVICE_COMBO, SELECT_TIME, SELECT_DEVICE, 
    CONFIRM_BOOKING, SELECT_DURATION, SELECT_PC_TYPE
)
from keyboards.markup import (
    categories_keyboard, rooms_keyboard, combo_devices_keyboard,
    day_picker_keyboard, time_picker_keyboard, devices_keyboard,
    confirm_booking_keyboard, main_menu_keyboard, duration_keyboard,
    pc_booking_type_keyboard
)

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# ENTRY
# ──────────────────────────────────────────────

async def start_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Nima o'ynamoqchisiz?",
        reply_markup=categories_keyboard()
    )
    return SELECT_CATEGORY

async def cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    if update.message:
        await update.message.reply_text("Asosiy menyu:", reply_markup=main_menu_keyboard())
    return ConversationHandler.END

# ──────────────────────────────────────────────
# FALLBACK HANDLERS (menu buttons work mid-conversation)
# ──────────────────────────────────────────────

async def fallback_my_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Conversation ichida 'Mening bronlarim' bosilganda."""
    from handlers.common import my_bookings
    context.user_data.clear()
    await my_bookings(update, context)
    return ConversationHandler.END

async def fallback_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Conversation ichida 'Yordam' bosilganda."""
    from handlers.common import help_cmd
    context.user_data.clear()
    await help_cmd(update, context)
    return ConversationHandler.END

async def fallback_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Conversation ichida 'Manzil' bosilganda."""
    from handlers.common import send_location
    context.user_data.clear()
    await send_location(update, context)
    return ConversationHandler.END

# ──────────────────────────────────────────────
# 1. KATEGORIYA
# ──────────────────────────────────────────────

async def handle_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    cat = query.data.split('_')[1]
    
    if cat == 'pc':
        await query.edit_message_text(
            "Qanday bron qilmoqchisiz?",
            reply_markup=pc_booking_type_keyboard()
        )
        return SELECT_PC_TYPE

    context.user_data['category'] = cat
    context.user_data['booking_type'] = 'single'

    rooms = await database.get_rooms_by_type(cat)
    await query.edit_message_text(
        "Qaysi xonani tanlaysiz?",
        reply_markup=rooms_keyboard(rooms)
    )
    return SELECT_ROOM

async def handle_pc_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_main_cat":
        await query.edit_message_text("Nima o'ynamoqchisiz?", reply_markup=categories_keyboard())
        return SELECT_CATEGORY

    context.user_data['category'] = 'pc'
    if query.data == "pc_type_single":
        context.user_data['booking_type'] = 'single'
        rooms = await database.get_rooms_by_type('pc')
        await query.edit_message_text("Qaysi xonani tanlaysiz?", reply_markup=rooms_keyboard(rooms))
    elif query.data == "pc_type_full":
        context.user_data['booking_type'] = 'full_room'
        rooms = await database.get_rooms_by_type('pc')
        await query.edit_message_text("Qaysi xonani to'liq band qilmoqchisiz?", reply_markup=rooms_keyboard(rooms))
    
    return SELECT_ROOM

# ──────────────────────────────────────────────
# 2. XONA
# ──────────────────────────────────────────────

async def handle_room(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "back_category":
        cat = context.user_data.get('category')
        if cat == 'pc':
            await query.edit_message_text("Qanday bron qilmoqchisiz?", reply_markup=pc_booking_type_keyboard())
            return SELECT_PC_TYPE
        else:
            await query.edit_message_text("Nima o'ynamoqchisiz?", reply_markup=categories_keyboard())
            return SELECT_CATEGORY

    room_id = int(query.data.split('_')[1])
    context.user_data['room_id'] = room_id

    if room_id == 13:
        cat = context.user_data.get('category')
        if cat in ['ps5', 'karaoke']:
            context.user_data['device_type'] = cat
            await query.edit_message_text("Kunni tanlang:", reply_markup=day_picker_keyboard())
            return SELECT_DAY
        else:
            await query.edit_message_text("Qurilmani tanlang:", reply_markup=combo_devices_keyboard(room_id))
            return SELECT_DEVICE_COMBO
    else:
        context.user_data['device_type'] = context.user_data.get('category')
        if context.user_data.get('booking_type') == 'full_room':
            await query.edit_message_text("Butun xonani band qilish uchun kunni tanlang:", reply_markup=day_picker_keyboard())
        else:
            await query.edit_message_text("Kunni tanlang:", reply_markup=day_picker_keyboard())
        return SELECT_DAY

# ──────────────────────────────────────────────
# 3. COMBO QURILMA (faqat 13-xona uchun)
# ──────────────────────────────────────────────

async def handle_combo_device(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "back_rooms":
        cat = context.user_data.get('category')
        rooms = await database.get_rooms_by_type(cat)
        await query.edit_message_text("Qaysi xonani tanlaysiz?", reply_markup=rooms_keyboard(rooms))
        return SELECT_ROOM

    parts = query.data.split('_')
    dev_type = parts[2]
    context.user_data['device_type'] = dev_type

    await query.edit_message_text("Kunni tanlang:", reply_markup=day_picker_keyboard())
    return SELECT_DAY

# ──────────────────────────────────────────────
# 4. KUN TANLASH
# ──────────────────────────────────────────────

async def handle_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "back_room_day":
        room_id = context.user_data.get('room_id')
        if room_id == 13:
            cat = context.user_data.get('category')
            if cat in ['ps5', 'karaoke']:
                rooms = await database.get_rooms_by_type(cat)
                await query.edit_message_text("Qaysi xonani tanlaysiz?", reply_markup=rooms_keyboard(rooms))
                return SELECT_ROOM
            else:
                await query.edit_message_text("Qurilmani tanlang:", reply_markup=combo_devices_keyboard(room_id))
                return SELECT_DEVICE_COMBO
        else:
            cat = context.user_data.get('category')
            rooms = await database.get_rooms_by_type(cat)
            await query.edit_message_text("Qaysi xonani tanlaysiz?", reply_markup=rooms_keyboard(rooms))
            return SELECT_ROOM

    day = 'today' if query.data == 'day_today' else 'tomorrow'
    context.user_data['selected_day'] = day
    
    room_id = context.user_data['room_id']
    device_type = context.user_data['device_type']
    day_label = "Bugun" if day == 'today' else "Ertaga"

    if context.user_data.get('booking_type') == 'full_room':
        devices = await database.get_devices_by_room_and_type(room_id, device_type)
        if not devices:
            await query.answer("Bu xonada qurilmalar topilmadi!", show_alert=True)
            return SELECT_DAY
            
        all_booked_times = set()
        for d in devices:
            d_id = d[0]
            b_times = await database.get_booked_times_for_device(d_id, day)
            all_booked_times.update(b_times)
            
        kb = time_picker_keyboard(day, booked_times=list(all_booked_times), back_data="back_room_day")
        
        rows_without_back = [r for r in kb.inline_keyboard if not any(
            (btn.callback_data or '') == "back_room_day" for btn in r
        )]
        if not rows_without_back:
            await query.answer("Bu kun uchun butun xona bo'sh emas!", show_alert=True)
            return SELECT_DAY
            
        await query.edit_message_text(
            f"🏠 Butun xona uchun {day_label} vaqtini tanlang:",
            reply_markup=kb
        )
        return SELECT_TIME
    else:
        devices = await database.get_devices_by_room_and_type(room_id, device_type)

        if not devices:
            await query.answer("Bu turdagi qurilmalar topilmadi!", show_alert=True)
            return SELECT_DAY

        await query.edit_message_text(
            f"📅 {day_label} uchun qurilmani tanlang:",
            reply_markup=devices_keyboard(devices, [])
        )
        return SELECT_DEVICE

# ──────────────────────────────────────────────
# 5. QURILMA TANLASH
# ──────────────────────────────────────────────

async def handle_ignore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("Bu qurilma band yoki bloklangan", show_alert=True)

async def handle_ignore_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("Bu vaqt allaqachon band!", show_alert=True)

async def handle_device(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    logger.info(f"handle_device called with data: {query.data}")
    try:
        if query.data == "back_to_day":
            await query.edit_message_text("Kunni tanlang:", reply_markup=day_picker_keyboard())
            return SELECT_DAY

        device_id = int(query.data.split('_')[1])
        context.user_data['device_id'] = device_id

        day = context.user_data.get('selected_day', 'today')
        day_label = "Bugun" if day == 'today' else "Ertaga"

        device = await database.get_device(device_id)
        if not device:
            await query.edit_message_text("Qurilma topilmadi. Iltimos qaytadan boshlang.", reply_markup=main_menu_keyboard())
            context.user_data.clear()
            return ConversationHandler.END

        d_id, label, price, room_name, r_id = device

        booked_times = await database.get_booked_times_for_device(device_id, day)
        kb = time_picker_keyboard(day, booked_times=booked_times)
        
        rows_without_back = [r for r in kb.inline_keyboard if not any(
            (btn.callback_data or '') == "back_to_device" for btn in r
        )]
        if not rows_without_back:
            await query.answer("Bu kun uchun bo'sh vaqt yo'q!", show_alert=True)
            return SELECT_DEVICE

        await query.edit_message_text(
            f"🖥 {label} uchun {day_label} vaqtini tanlang:",
            reply_markup=kb
        )
        return SELECT_TIME
    except Exception as e:
        logger.error(f"Error in handle_device: {e}", exc_info=True)
        await query.edit_message_text("Xatolik yuz berdi. Iltimos /start dan qaytadan boshlang.")
        context.user_data.clear()
        return ConversationHandler.END

# ──────────────────────────────────────────────
# 6. VAQT TANLASH
# ──────────────────────────────────────────────

async def handle_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "back_to_device":
        room_id = context.user_data['room_id']
        device_type = context.user_data['device_type']
        day = context.user_data.get('selected_day', 'today')
        day_label = "Bugun" if day == 'today' else "Ertaga"

        devices = await database.get_devices_by_room_and_type(room_id, device_type)
        await query.edit_message_text(
            f"📅 {day_label} uchun qurilmani tanlang:",
            reply_markup=devices_keyboard(devices, [])
        )
        return SELECT_DEVICE
        
    if query.data == "back_room_day":
        await query.edit_message_text("Butun xonani band qilish uchun kunni tanlang:", reply_markup=day_picker_keyboard())
        return SELECT_DAY

    time_str = query.data[5:]  # "time_" prefiksini olib tashlaymiz
    context.user_data['booked_for'] = time_str
    
    if context.user_data.get('booking_type') == 'full_room':
        await query.edit_message_text("Necha soat o'ynaysiz?", reply_markup=duration_keyboard(back_data="back_room_day_time"))
    else:
        await query.edit_message_text("Necha soat o'ynaysiz?", reply_markup=duration_keyboard())
    return SELECT_DURATION

# ──────────────────────────────────────────────
# 7. DAVOMIYLIK
# ──────────────────────────────────────────────

async def handle_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "back_room_day_time":
        day = context.user_data['selected_day']
        room_id = context.user_data['room_id']
        devices = await database.get_devices_by_room_and_type(room_id, 'pc')
        all_booked_times = set()
        for d in devices:
            all_booked_times.update(await database.get_booked_times_for_device(d[0], day))
        day_label = "Bugun" if day == 'today' else "Ertaga"
        kb = time_picker_keyboard(day, booked_times=list(all_booked_times), back_data="back_room_day")
        await query.edit_message_text(f"🏠 Butun xona uchun {day_label} vaqtini tanlang:", reply_markup=kb)
        return SELECT_TIME

    if query.data == "back_to_time":
        device_id = context.user_data.get('device_id')
        day = context.user_data.get('selected_day', 'today')
        booked_times = await database.get_booked_times_for_device(device_id, day)
        device = await database.get_device(device_id)
        label = device[1] if device else "Qurilma"
        day_label = "Bugun" if day == 'today' else "Ertaga"
        
        await query.edit_message_text(
            f"🖥 {label} uchun {day_label} vaqtini tanlang:",
            reply_markup=time_picker_keyboard(day, booked_times=booked_times)
        )
        return SELECT_TIME

    duration = int(query.data.split('_')[1])
    context.user_data['duration'] = duration
    
    time_str = context.user_data['booked_for']
    dt = datetime.fromisoformat(time_str)
    day_str = "Bugun" if dt.date() == datetime.now().date() else "Ertaga"
    
    if context.user_data.get('booking_type') == 'full_room':
        room_id = context.user_data['room_id']
        devices = await database.get_devices_by_room_and_type(room_id, 'pc')
        
        for d in devices:
            if not await database.check_range_availability(d[0], time_str, duration):
                await query.answer("Kechirasiz, tanlangan vaqt oralig'ida ayrim qurilmalar band! Kamroq vaqt tanlang.", show_alert=True)
                return SELECT_DURATION
                
        total_price = sum(d[3] for d in devices) * duration
        
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT name FROM rooms WHERE id = ?", (room_id,))
            row = await cursor.fetchone()
            room_name = row[0] if row else "Noma'lum xona"
            
        text = (f"✅ Tasdiqlaysizmi?\n"
                f"📍 Xona: {room_name} (Butun xona)\n"
                f"🖥 Qurilmalar soni: {len(devices)} ta\n"
                f"🕐 Vaqt: {day_str} {dt.strftime('%H:%M')}\n"
                f"⏳ Davomiyligi: {duration} soat\n"
                f"💰 Umumiy narx: {total_price:,} so'm".replace(',', ' '))
    else:
        device_id = context.user_data['device_id']
        
        is_available = await database.check_range_availability(device_id, time_str, duration)
        if not is_available:
            await query.answer("Kechirasiz, tanlangan vaqtdan keyingi soatlar band! Kamroq vaqt tanlang yoki boshqa vaqtni ko'ring.", show_alert=True)
            return SELECT_DURATION

        device = await database.get_device(device_id)
        d_id, label, price, room_name, r_id = device
        
        total_price = price * duration

        text = (f"✅ Tasdiqlaysizmi?\n"
                f"📍 Xona: {room_name}\n"
                f"🖥 Qurilma: {label}\n"
                f"🕐 Vaqt: {day_str} {dt.strftime('%H:%M')}\n"
                f"⏳ Davomiyligi: {duration} soat\n"
                f"💰 Umumiy narx: {total_price:,} so'm".replace(',', ' '))

    await query.edit_message_text(text, reply_markup=confirm_booking_keyboard())
    return CONFIRM_BOOKING

# ──────────────────────────────────────────────
# 8. TASDIQLASH
# ──────────────────────────────────────────────

async def handle_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "confirm_no":
        await query.edit_message_text("Bron qilish bekor qilindi.")
        context.user_data.clear()
        return ConversationHandler.END

    user = update.effective_user
    booked_for = context.user_data['booked_for']
    duration = context.user_data.get('duration', 1)
    
    booking_ids = []
    
    if context.user_data.get('booking_type') == 'full_room':
        room_id = context.user_data['room_id']
        devices = await database.get_devices_by_room_and_type(room_id, 'pc')
        
        for d in devices:
            if not await database.check_range_availability(d[0], booked_for, duration):
                await query.edit_message_text("Kechirasiz, bu vaqt oralig'ida ayrim qurilmalar band bo'lib qoldi. Boshqa vaqt tanlang.")
                context.user_data.clear()
                return ConversationHandler.END
                
        for d in devices:
            b_id = await database.add_booking(
                user.id, user.username, user.full_name, d[0], booked_for, duration
            )
            booking_ids.append(b_id)
            
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT name FROM rooms WHERE id = ?", (room_id,))
            row = await cursor.fetchone()
            room_name = row[0] if row else "Noma'lum xona"
            
        booking_msg = f"🎉 Butun xona bron qilindi! Bron IDlar: #{', #'.join(map(str, booking_ids))}"
        admin_text = (f"🚨 YANGI BRON (Butun Xona)!\n"
                      f"👤 Foydalanuvchi: {user.full_name} (@{user.username})\n"
                      f"📍 Xona: {room_name}\n"
                      f"🕐 Vaqt: {booked_for}\n"
                      f"⏳ Davomiyligi: {duration} soat")
    else:
        device_id = context.user_data['device_id']
        is_available = await database.check_range_availability(device_id, booked_for, duration)
        if not is_available:
            await query.edit_message_text("Kechirasiz, bu vaqt oralig'ida qurilma band bo'lib qoldi. Boshqa vaqt tanlang.")
            context.user_data.clear()
            return ConversationHandler.END

        b_id = await database.add_booking(
            user.id, user.username, user.full_name, device_id, booked_for, duration
        )
        booking_ids.append(b_id)
        
        device = await database.get_device(device_id)
        label = device[1]
        room_name = device[3]
        booking_msg = f"🎉 Bron qilindi! Bron ID: #{b_id}"
        admin_text = (f"🚨 YANGI BRON!\n"
                      f"👤 Foydalanuvchi: {user.full_name} (@{user.username})\n"
                      f"📍 Xona: {room_name}\n"
                      f"🖥 Qurilma: {label}\n"
                      f"🕐 Vaqt: {booked_for}\n"
                      f"⏳ Davomiyligi: {duration} soat")

    await query.edit_message_text(
        f"{booking_msg}\n"
        f"Belgilangan vaqtdan 10 daqiqa oldin eslatma yuboriladi."
    )
    
    # Adminga xabar yuborish
    admins = await database.get_all_admins()
    for admin_id in admins:
        try:
            await context.bot.send_message(chat_id=admin_id, text=admin_text)
        except Exception as e:
            logger.error(f"Error sending notification to admin {admin_id}: {e}")
            
    context.user_data.clear()
    return ConversationHandler.END

# ──────────────────────────────────────────────
# CONVERSATION HANDLER
# ──────────────────────────────────────────────

def get_booking_conv_handler():
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('Bron qilish'), start_booking)],
        states={
            SELECT_CATEGORY: [
                CallbackQueryHandler(handle_category, pattern='^cat_')
            ],
            SELECT_PC_TYPE: [
                CallbackQueryHandler(handle_pc_type, pattern='^pc_type_'),
                CallbackQueryHandler(handle_pc_type, pattern='^back_main_cat$')
            ],
            SELECT_ROOM: [
                CallbackQueryHandler(handle_room, pattern='^room_'),
                CallbackQueryHandler(handle_room, pattern='^back_category$')
            ],
            SELECT_DEVICE_COMBO: [
                CallbackQueryHandler(handle_combo_device, pattern='^combo_'),
                CallbackQueryHandler(handle_combo_device, pattern='^back_rooms$')
            ],
            SELECT_DAY: [
                CallbackQueryHandler(handle_day, pattern='^day_'),
                CallbackQueryHandler(handle_day, pattern='^back_room_day$')
            ],
            SELECT_DEVICE: [
                CallbackQueryHandler(handle_ignore, pattern='^ignore$'),
                CallbackQueryHandler(handle_device, pattern='^device_'),
                CallbackQueryHandler(handle_device, pattern='^back_to_day$')
            ],
            SELECT_TIME: [
                CallbackQueryHandler(handle_ignore_time, pattern='^ignore_time$'),
                CallbackQueryHandler(handle_time, pattern='^time_'),
                CallbackQueryHandler(handle_time, pattern='^back_to_device$'),
                CallbackQueryHandler(handle_time, pattern='^back_room_day$')
            ],
            SELECT_DURATION: [
                CallbackQueryHandler(handle_duration, pattern='^dur_'),
                CallbackQueryHandler(handle_duration, pattern='^back_to_time$'),
                CallbackQueryHandler(handle_duration, pattern='^back_room_day_time$')
            ],
            CONFIRM_BOOKING: [
                CallbackQueryHandler(handle_confirm, pattern='^confirm_')
            ]
        },
        fallbacks=[
            CommandHandler('cancel', cancel_booking),
            CommandHandler('start', cancel_booking),
            MessageHandler(filters.Regex('Mening bronlarim'), fallback_my_bookings),
            MessageHandler(filters.Regex('Yordam'), fallback_help),
            MessageHandler(filters.Regex('Manzil'), fallback_location),
        ],
        allow_reentry=True
    )
