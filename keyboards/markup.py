from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, timedelta

def main_menu_keyboard():
    keyboard = [
        [KeyboardButton("🎮 Bron qilish")],
        [KeyboardButton("📋 Mening bronlarim"), KeyboardButton("📍 Manzil")],
        [KeyboardButton("ℹ️ Yordam")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def categories_keyboard():
    keyboard = [
        [InlineKeyboardButton("🖥 Kompyuter", callback_data="cat_pc"),
         InlineKeyboardButton("🎮 PS3", callback_data="cat_ps3")],
        [InlineKeyboardButton("🕹 PS5", callback_data="cat_ps5"),
         InlineKeyboardButton("🎤 Karaoke", callback_data="cat_karaoke")]
    ]
    return InlineKeyboardMarkup(keyboard)

def pc_booking_type_keyboard():
    keyboard = [
        [InlineKeyboardButton("👤 O'zim uchun", callback_data="pc_type_single")],
        [InlineKeyboardButton("🏠 Butun xonani band qilish", callback_data="pc_type_full")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="back_main_cat")]
    ]
    return InlineKeyboardMarkup(keyboard)

def rooms_keyboard(rooms):
    keyboard = []
    for r in rooms:
        r_id, name, price = r
        if price == 0:
            btn_text = f"{name}"
        else:
            btn_text = f"{name} — {price:,} so'm/soat".replace(',', ' ')
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"room_{r_id}")])
    keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_category")])
    return InlineKeyboardMarkup(keyboard)

def combo_devices_keyboard(room_id):
    keyboard = [
        [InlineKeyboardButton("🕹 PS5", callback_data=f"combo_{room_id}_ps5")],
        [InlineKeyboardButton("🎤 Karaoke", callback_data=f"combo_{room_id}_karaoke")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="back_rooms")]
    ]
    return InlineKeyboardMarkup(keyboard)

def day_picker_keyboard():
    keyboard = [
        [InlineKeyboardButton("📅 Bugun", callback_data="day_today"),
         InlineKeyboardButton("📅 Ertaga", callback_data="day_tomorrow")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="back_room_day")]
    ]
    return InlineKeyboardMarkup(keyboard)

def devices_keyboard(devices, booked_device_ids):
    """Qurilmalar ro'yxati — vaqt tanlanmasdan oldin ko'rsatiladi."""
    keyboard = []
    for d in devices:
        d_id, label, dtype, price, is_blocked, block_reason = d
        if is_blocked:
            btn_text = f"🔒 {label} — Bloklangan"
            cb_data = "ignore"
        elif d_id in booked_device_ids:
            btn_text = f"❌ {label} — Band"
            cb_data = "ignore"
        else:
            btn_text = f"✅ {label} — Bo'sh ({price:,} so'm/soat)".replace(',', ' ')
            cb_data = f"device_{d_id}"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=cb_data)])
    keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_day")])
    return InlineKeyboardMarkup(keyboard)

def time_picker_keyboard(day='today', booked_times=None, back_data="back_to_device"):
    """Qurilma tanlangandan keyin vaqt tanlash."""
    if booked_times is None:
        booked_times = []
        
    keyboard = []
    now = datetime.now()

    if day == 'today':
        minutes = (now.minute // 30 + 1) * 30
        start_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(minutes=minutes)
        end_of_day = now.replace(hour=23, minute=30, second=0, microsecond=0)
        slots = []
        current = start_time
        while current <= end_of_day:
            slots.append(current)
            current = current + timedelta(minutes=30)
    else:  # tomorrow
        tomorrow = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        end_of_tomorrow = tomorrow.replace(hour=23, minute=30)
        slots = []
        current = tomorrow
        while current <= end_of_tomorrow:
            slots.append(current)
            current = current + timedelta(minutes=30)

    row = []
    for slot in slots:
        iso_str = slot.isoformat()
        time_str = slot.strftime("%H:%M")
        
        if iso_str in booked_times:
            btn_text = f"❌ {time_str}"
            cb_data = "ignore_time"
        else:
            btn_text = time_str
            cb_data = f"time_{iso_str}"
            
        row.append(InlineKeyboardButton(btn_text, callback_data=cb_data))
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data=back_data)])
    return InlineKeyboardMarkup(keyboard)

def duration_keyboard(back_data="back_to_time"):
    """Necha soat o'ynashni tanlash."""
    keyboard = [
        [InlineKeyboardButton("1 soat", callback_data="dur_1"),
         InlineKeyboardButton("2 soat", callback_data="dur_2")],
        [InlineKeyboardButton("3 soat", callback_data="dur_3"),
         InlineKeyboardButton("4 soat", callback_data="dur_4")],
        [InlineKeyboardButton("5 soat", callback_data="dur_5")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data=back_data)]
    ]
    return InlineKeyboardMarkup(keyboard)

def confirm_booking_keyboard():
    keyboard = [
        [InlineKeyboardButton("✅ Tasdiqlash", callback_data="confirm_yes"),
         InlineKeyboardButton("❌ Bekor qilish", callback_data="confirm_no")]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 Barcha bronlar", callback_data="adm_bookings")],
        [InlineKeyboardButton("🔒 Qurilma bloklash", callback_data="adm_block"),
         InlineKeyboardButton("🔓 Blokni yechish", callback_data="adm_unblock")],
        [InlineKeyboardButton("✅ Bronni yakunlash", callback_data="adm_complete"),
         InlineKeyboardButton("❌ Bronni bekor qilish", callback_data="adm_cancel")],
        [InlineKeyboardButton("📈 Statistika", callback_data="adm_stats")]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_cancel_complete_keyboard(bookings, action):
    keyboard = []
    for b in bookings:
        b_id = b[0]
        full_name = b[1]
        label = b[3]
        room_name = b[4]
        booked_for = b[5]
        dt = datetime.fromisoformat(booked_for)
        text = f"{full_name} | {room_name} {label} | {dt.strftime('%H:%M')}"
        keyboard.append([InlineKeyboardButton(text, callback_data=f"adm_{action}_{b_id}")])
        
    if action == 'cnl' and bookings:
        keyboard.append([InlineKeyboardButton("🗑 Barcha bandlovlarni bekor qilish", callback_data="adm_cancel_all")])
        
    keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="adm_back")])
    return InlineKeyboardMarkup(keyboard)

def admin_unblock_keyboard(devices):
    keyboard = []
    for d in devices:
        d_id, label, room_name, reason = d
        keyboard.append([InlineKeyboardButton(f"{room_name} {label}", callback_data=f"adm_do_unblock_{d_id}")])
    keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="adm_back")])
    return InlineKeyboardMarkup(keyboard)

def admin_rooms_block_keyboard(rooms):
    keyboard = []
    for r in rooms:
        r_id, name, price = r
        keyboard.append([InlineKeyboardButton(name, callback_data=f"adm_blk_room_{r_id}")])
    keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="adm_back")])
    return InlineKeyboardMarkup(keyboard)

def admin_devices_block_keyboard(devices):
    keyboard = []
    for d in devices:
        d_id, label, dtype, price, is_blocked, block_reason = d
        if not is_blocked:
            keyboard.append([InlineKeyboardButton(label, callback_data=f"adm_blk_dev_{d_id}")])
    keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="adm_bookings_back_rooms")])
    return InlineKeyboardMarkup(keyboard)
