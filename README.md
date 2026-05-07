# Game Club Telegram Bot

Bu Telegram bot orqali o'yin klubidagi xonalar va qurilmalarni (Kompyuter, PS3, PS5, Karaoke) bron qilish tizimi yo'lga qo'yiladi. Bot to'liq O'zbek tilida ishlaydi.

## Xususiyatlari:
- Har bir qurilmani vaqtga qarab (30 daqiqalik oraliq) bron qilish
- Xonalar va ularning turlari (PS, Kompyuter, Combo)
- Admin panel (`/admin`):
  - Barcha faol bronlarni ko'rish
  - Bronni yakunlash (qurilmani bo'shatish)
  - Bronni bekor qilish (mijozga xabar yuboriladi)
  - Qurilmalarni bloklash / blokdan chiqarish (nosozlik holatlarida)
  - Qo'shimcha admin qo'shish
  - Kunlik statistika
- Avtomatik xabarnoma: Bron qilingan vaqtdan 10 daqiqa oldin foydalanuvchiga eslatma yuborish.

## Sozlash va Ishga tushirish

1. Ushbu loyihani yuklab oling.
2. Kerakli kutubxonalarni o'rnating:
   ```bash
   pip install -r requirements.txt
   ```
3. `config.py` faylini ochib, `BOT_TOKEN` ga o'z botingiz tokenini yozing. Shuningdek, `INITIAL_ADMIN_IDS` ro'yxatiga o'zingizning Telegram ID raqamingizni qo'shing.
4. Botni ishga tushiring:
   ```bash
   python bot.py
   ```

Tizim avtomat ravishda `gameclub.db` bazasini yaratadi va barcha 14 ta xona hamda qurilmalarni bazaga kiritadi (faqat birinchi ishga tushishda).
