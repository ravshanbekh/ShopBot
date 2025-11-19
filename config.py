"""
Telegram Shop Bot - Konfiguratsiya fayli (JSON versiya)
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Bot tokeni
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Admin ID'lar ro'yxati
ADMINS = [
    7485738561,  # Birinchi admin
    5606706053,  # Ikkinchi admin
]

# Kanal va guruh ID'lari
CHANNEL_ID = -1003371130387  # @yourchannel
GROUP_ID = -5045327244    # Guruh ID

# JSON fayllar yo'llari
DATA_DIR = "data"
PRODUCTS_FILE = f"{DATA_DIR}/products.json"
ORDERS_FILE = f"{DATA_DIR}/orders.json"
USERS_FILE = f"{DATA_DIR}/users.json"
CATEGORIES_FILE = f"{DATA_DIR}/categories.json"

# Avtomatik post vaqtlari (24-soatlik format)
AUTO_POST_TIMES = [
    "11:00",
    "15:00",
    "20:00"
]

# Kuniga post qilinadigan tovarlar soni
DAILY_POSTS_COUNT = 3

# FAQ javoblari
FAQ_ANSWERS = {
    "yetkazish": "🚚 Yetkazib berish Toshkent bo'ylab - 15,000 so'm\n🌍 Viloyatlarga - 25,000 so'm\n⏱ Yetkazish muddati: 1-3 kun",
    "tolov": "💳 To'lov turlari:\n• Naqd pul\n• Plastik karta\n• Payme\n• Click\n• Uzum",
    "qaytarish": "🔄 Tovarni qaytarish:\n• 14 kun ichida\n• Tovar ishlatilmagan bo'lishi kerak\n• Chek mavjud bo'lishi shart",
    "aloqa": "📞 Biz bilan bog'lanish:\n📱 Telefon: +998 90 123 45 67\n📧 Email: info@shop.uz\n⏰ Ish vaqti: 9:00 - 21:00"
}

# Xabarlar
MESSAGES = {
    "start": """
👋 Xush kelibsiz!

🛍 Bizning internet do'konimizga xush kelibsiz!

Menyu orqali tovarlarni ko'ring va buyurtma bering.
    """,
    "order_success": "✅ Buyurtmangiz qabul qilindi! Tez orada operator siz bilan bog'lanadi.",
    "order_cancel": "❌ Buyurtma bekor qilindi.",
    "admin_panel": "👨‍💼 Admin panel",
    "no_products": "📭 Hozircha tovarlar yo'q",
    "product_added": "✅ Tovar muvaffaqiyatli qo'shildi!",
    "product_deleted": "🗑 Tovar o'chirildi",
    "invalid_input": "❌ Noto'g'ri ma'lumot kiritildi. Qaytadan urinib ko'ring.",
    "category_added": "✅ Kategoriya qo'shildi!",
    "category_deleted": "🗑 Kategoriya o'chirildi",
}