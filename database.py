import aiosqlite
import logging
from config import DB_PATH

logger = logging.getLogger(__name__)

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY,
            room_number INTEGER UNIQUE,
            name TEXT,          
            type TEXT,          
            price INTEGER       
        )''')
        
        await db.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY,
            room_id INTEGER REFERENCES rooms(id),
            device_label TEXT,  
            device_type TEXT,   
            price INTEGER,      
            is_blocked INTEGER DEFAULT 0,
            block_reason TEXT
        )''')

        await db.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            full_name TEXT,
            device_id INTEGER REFERENCES devices(id),
            booked_for TEXT,    
            duration_hours INTEGER DEFAULT 1,
            status TEXT DEFAULT 'active',  
            notified INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )''')

        await db.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            username TEXT,
            added_at TEXT DEFAULT (datetime('now'))
        )''')

        await db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            username TEXT,
            full_name TEXT,
            joined_at TEXT DEFAULT (datetime('now'))
        )''')
        
        cursor = await db.execute("SELECT COUNT(*) FROM rooms")
        count = await cursor.fetchone()
        if count[0] == 0:
            await seed_data(db)
        
        # Migration: duration_hours ustuni yo'q bo'lsa qo'shamiz
        try:
            await db.execute("ALTER TABLE bookings ADD COLUMN duration_hours INTEGER DEFAULT 1")
            logger.info("Migration: duration_hours ustuni qo'shildi.")
        except Exception:
            pass  # Ustun allaqachon mavjud bo'lsa xatolikni e'tiborsiz qoldiramiz
        
        await db.commit()

async def seed_data(db):
    rooms_data = [
        (1, 1, "1-xona", "ps3", 20000),
        (2, 2, "2-xona", "pc", 10000),
        (3, 3, "3-xona", "ps3", 20000),
        (4, 4, "4-xona", "pc", 10000),
        (5, 5, "5-xona", "pc", 12000),
        (6, 6, "6-xona", "ps3", 20000),
        (7, 7, "7-xona", "ps3", 20000),
        (8, 8, "8-xona", "ps3", 20000),
        (9, 9, "9-xona", "karaoke", 80000),
        (10, 10, "10-xona", "pc", 10000),
        (11, 11, "11-xona", "ps3", 30000),
        (12, 12, "12-xona", "ps5", 30000),
        (13, 13, "13-xona (Combo)", "combo", 0),
        (14, 14, "14-xona", "ps3", 20000),
    ]
    await db.executemany("INSERT INTO rooms (id, room_number, name, type, price) VALUES (?, ?, ?, ?, ?)", rooms_data)
    
    devices_data = []
    for i in range(1, 11):
        devices_data.append((2, f"{i}-kompyuter", "pc", 10000))
    for i in range(11, 21):
        devices_data.append((4, f"{i}-kompyuter", "pc", 10000))
    for i in range(21, 31):
        devices_data.append((5, f"{i}-kompyuter", "pc", 12000))
    for i in range(31, 41):
        devices_data.append((10, f"{i}-kompyuter", "pc", 10000))
    
    ps3_rooms = [1, 3, 6, 7, 8, 11, 14]
    for r in ps3_rooms:
        price = 30000 if r == 11 else 20000
        devices_data.append((r, "PS3", "ps3", price))
    
    devices_data.append((12, "PS5", "ps5", 30000))
    devices_data.append((9, "Karaoke", "karaoke", 80000))
    devices_data.append((13, "PS5", "ps5", 40000))
    devices_data.append((13, "Karaoke", "karaoke", 80000))

    await db.executemany("INSERT INTO devices (room_id, device_label, device_type, price) VALUES (?, ?, ?, ?)", devices_data)
    logger.info("Database seeded with initial rooms and devices.")

async def add_user(user_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)", (user_id, username, full_name))
        await db.commit()

async def get_rooms_by_type(room_type: str):
    async with aiosqlite.connect(DB_PATH) as db:
        if room_type == 'ps5':
            cursor = await db.execute("SELECT id, name, price FROM rooms WHERE type = 'ps5' OR type = 'combo'")
        elif room_type == 'karaoke':
            cursor = await db.execute("SELECT id, name, price FROM rooms WHERE type = 'karaoke' OR type = 'combo'")
        else:
            cursor = await db.execute("SELECT id, name, price FROM rooms WHERE type = ?", (room_type,))
        return await cursor.fetchall()

async def get_devices_by_room_and_type(room_id: int, device_type: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        if device_type:
            cursor = await db.execute("SELECT id, device_label, device_type, price, is_blocked, block_reason FROM devices WHERE room_id = ? AND device_type = ?", (room_id, device_type))
        else:
            cursor = await db.execute("SELECT id, device_label, device_type, price, is_blocked, block_reason FROM devices WHERE room_id = ?", (room_id,))
        return await cursor.fetchall()

async def get_device(device_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT d.id, d.device_label, d.price, r.name, r.id 
            FROM devices d 
            JOIN rooms r ON d.room_id = r.id 
            WHERE d.id = ?
        """, (device_id,))
        return await cursor.fetchone()

async def get_bookings_for_device_time(device_id: int, booked_for: str):
    """Faqat boshlanish vaqtini tekshiradi (eski mantiq uchun)."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id FROM bookings WHERE device_id = ? AND booked_for = ? AND status = 'active'", (device_id, booked_for))
        return await cursor.fetchone()

async def get_booked_times_for_device(device_id: int, day: str) -> list:
    """Berilgan qurilma uchun band 30-daqiqalik vaqtlarni ISO formatida qaytaradi."""
    from datetime import datetime, timedelta
    async with aiosqlite.connect(DB_PATH) as db:
        if day == 'today':
            date_filter = "date(booked_for) = date('now', 'localtime')"
        else:
            date_filter = "date(booked_for) = date('now', '+1 day', 'localtime')"
        
        cursor = await db.execute(
            f"SELECT booked_for, duration_hours FROM bookings WHERE device_id = ? AND status = 'active' AND {date_filter}",
            (device_id,)
        )
        rows = await cursor.fetchall()
        
        booked_slots = set()
        for start_iso, duration in rows:
            start_dt = datetime.fromisoformat(start_iso)
            # Har bir 30 minutlik slotni qo'shib chiqamiz
            for i in range(int(duration * 2)):
                slot = start_dt + timedelta(minutes=30 * i)
                booked_slots.add(slot.isoformat())
                
        return list(booked_slots)

async def check_range_availability(device_id: int, start_iso: str, duration_hours: int):
    """Tanlangan vaqt oralig'i bo'shligini tekshiradi."""
    from datetime import datetime, timedelta
    
    start_dt = datetime.fromisoformat(start_iso)
    end_dt = start_dt + timedelta(hours=duration_hours)
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Tekshiramiz: yangi bronning boshi boshqa bronning ichiga tushmaydimi 
        # YOKI yangi bron boshqa bronni o'z ichiga olmaydimi?
        # Sodda mantiq: barcha faol bronlarni olib, 30 min slotlar orqali tekshiramiz
        cursor = await db.execute(
            "SELECT booked_for, duration_hours FROM bookings WHERE device_id = ? AND status = 'active'",
            (device_id,)
        )
        rows = await cursor.fetchall()
        
        for b_start_iso, b_duration in rows:
            b_start = datetime.fromisoformat(b_start_iso)
            b_end = b_start + timedelta(hours=b_duration)
            
            # Kesishish sharti: (StartA < EndB) AND (EndA > StartB)
            if start_dt < b_end and end_dt > b_start:
                return False # Band
                
        return True # Bo'sh

async def add_booking(user_id: int, username: str, full_name: str, device_id: int, booked_for: str, duration_hours: int = 1):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO bookings (user_id, username, full_name, device_id, booked_for, duration_hours) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, username, full_name, device_id, booked_for, duration_hours)
        )
        await db.commit()
        return cursor.lastrowid

async def get_user_bookings(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT b.id, d.device_label, r.name, b.booked_for, d.price, b.duration_hours
            FROM bookings b
            JOIN devices d ON b.device_id = d.id
            JOIN rooms r ON d.room_id = r.id
            WHERE b.user_id = ? AND b.status = 'active'
            ORDER BY b.booked_for
        """, (user_id,))
        return await cursor.fetchall()

async def is_admin(user_id: int) -> bool:
    from config import INITIAL_ADMIN_IDS
    if user_id in INITIAL_ADMIN_IDS:
        return True
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id FROM admins WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return row is not None

async def get_all_active_bookings():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT b.id, b.full_name, b.username, d.device_label, r.name, b.booked_for, b.user_id, r.id
            FROM bookings b
            JOIN devices d ON b.device_id = d.id
            JOIN rooms r ON d.room_id = r.id
            WHERE b.status = 'active'
            ORDER BY r.id, b.booked_for
        """)
        return await cursor.fetchall()

async def update_booking_status(booking_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE bookings SET status = ? WHERE id = ?", (status, booking_id))
        await db.commit()

async def cancel_group_bookings(user_id: int, room_id: int, booked_for: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE bookings 
            SET status = 'cancelled' 
            WHERE user_id = ? AND booked_for = ? AND status = 'active'
            AND device_id IN (SELECT id FROM devices WHERE room_id = ?)
        """, (user_id, booked_for, room_id))
        await db.commit()

async def cancel_all_bookings():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE bookings SET status = 'cancelled' WHERE status = 'active'")
        await db.commit()

async def block_device(device_id: int, reason: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE devices SET is_blocked = 1, block_reason = ? WHERE id = ?", (reason, device_id))
        await db.commit()

async def get_blocked_devices():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT d.id, d.device_label, r.name, d.block_reason
            FROM devices d
            JOIN rooms r ON d.room_id = r.id
            WHERE d.is_blocked = 1
        """)
        return await cursor.fetchall()

async def unblock_device(device_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE devices SET is_blocked = 0, block_reason = NULL WHERE id = ?", (device_id,))
        await db.commit()

async def add_admin(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user_id,))
        await db.commit()

async def get_today_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled
            FROM bookings
            WHERE date(created_at) = date('now')
        """)
        return await cursor.fetchone()

async def get_unnotified_upcoming_bookings():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT b.id, b.user_id, d.device_label, r.name, b.booked_for
            FROM bookings b
            JOIN devices d ON b.device_id = d.id
            JOIN rooms r ON d.room_id = r.id
            WHERE b.status = 'active' 
            AND b.notified = 0 
            AND datetime(b.booked_for) BETWEEN datetime('now') AND datetime('now', '+10 minutes')
        """)
        return await cursor.fetchall()

async def mark_notified(booking_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE bookings SET notified = 1 WHERE id = ?", (booking_id,))
        await db.commit()

async def get_all_admins():
    from config import INITIAL_ADMIN_IDS
    admins = set(INITIAL_ADMIN_IDS)
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT user_id FROM admins")
        rows = await cursor.fetchall()
        for row in rows:
            admins.add(row[0])
    return list(admins)
