"""
Admin uchun klaviaturalar - To'liq versiya
"""

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from typing import List, Dict


def get_admin_main_menu() -> ReplyKeyboardMarkup:
    """
    Admin asosiy menyu klaviaturasi
    """
    builder = ReplyKeyboardBuilder()

    # Birinchi qator - tovar boshqaruvi
    builder.row(
        KeyboardButton(text="➕ Tovar qo'shish"),
        KeyboardButton(text="📋 Tovarlar ro'yxati")
    )

    # Ikkinchi qator - kategoriya va buyurtmalar
    builder.row(
        KeyboardButton(text="📂 Kategoriyalar"),
        KeyboardButton(text="📦 Buyurtmalar")
    )

    # Uchinchi qator - statistika va yuklash
    builder.row(
        KeyboardButton(text="📊 Statistika"),
        KeyboardButton(text="🔄 Eski tovarlarni yuklash")
    )

    # To'rtinchi qator - xabar va chiqish
    builder.row(
        KeyboardButton(text="✉️ Xabar yuborish"),
        KeyboardButton(text="👤 Foydalanuvchi rejimi")
    )

    return builder.as_markup(
        resize_keyboard=True,
        input_field_placeholder="Admin buyrug'ini tanlang..."
    )


def get_categories_admin_keyboard(categories: List[str], action: str = "select") -> InlineKeyboardMarkup:
    """
    Admin kategoriyalar klaviaturasi

    Args:
        categories: Kategoriyalar ro'yxati
        action: "select", "manage", "delete"

    Returns:
        InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder()

    # Har bir kategoriya uchun tugma
    for category in categories:
        if action == "select":
            # Tovar qo'shish uchun kategoriya tanlash
            callback = f"admin_category:{category}"
            text = category
        elif action == "manage":
            # Kategoriyani boshqarish
            callback = f"admin_manage_category:{category}"
            text = category
        elif action == "delete":
            # Kategoriyani o'chirish
            callback = f"admin_delete_category:{category}"
            text = f"🗑 {category}"
        else:
            callback = f"admin_category:{category}"
            text = category

        builder.row(
            InlineKeyboardButton(text=text, callback_data=callback)
        )

    # Qo'shimcha tugmalar
    if action == "manage":
        builder.row(
            InlineKeyboardButton(
                text="➕ Yangi kategoriya qo'shish",
                callback_data="admin_add_category"
            )
        )

    # Bekor qilish
    builder.row(
        InlineKeyboardButton(
            text="❌ Bekor qilish",
            callback_data="admin_cancel"
        )
    )

    return builder.as_markup()


def get_category_manage_keyboard(category: str) -> InlineKeyboardMarkup:
    """
    Kategoriyani boshqarish klaviaturasi

    Args:
        category: Kategoriya nomi
    """
    builder = InlineKeyboardBuilder()

    # Tahrirlash
    builder.row(
        InlineKeyboardButton(
            text="✏️ Nomini o'zgartirish",
            callback_data=f"admin_edit_category:{category}"
        )
    )

    # O'chirish
    builder.row(
        InlineKeyboardButton(
            text="🗑 O'chirish",
            callback_data=f"admin_confirm_delete_category:{category}"
        )
    )

    # Orqaga
    builder.row(
        InlineKeyboardButton(
            text="« Orqaga",
            callback_data="admin_categories_menu"
        )
    )

    return builder.as_markup()


def get_product_manage_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """
    Tovarni boshqarish klaviaturasi

    Args:
        product_id: Tovar ID
    """
    builder = InlineKeyboardBuilder()

    # Tahrirlash
    builder.row(
        InlineKeyboardButton(
            text="✏️ Tahrirlash",
            callback_data=f"admin_edit:{product_id}"
        )
    )

    # Mavjudlikni o'zgartirish
    builder.row(
        InlineKeyboardButton(
            text="📦 Mavjudlikni o'zgartirish",
            callback_data=f"admin_toggle:{product_id}"
        )
    )

    # O'chirish
    builder.row(
        InlineKeyboardButton(
            text="🗑 O'chirish",
            callback_data=f"admin_delete:{product_id}"
        )
    )

    # Orqaga
    builder.row(
        InlineKeyboardButton(
            text="« Orqaga",
            callback_data="admin_products_list"
        )
    )

    return builder.as_markup()


def get_products_list_keyboard(products: List[Dict], page: int = 0, per_page: int = 10) -> InlineKeyboardMarkup:
    """
    Tovarlar ro'yxati klaviaturasi (sahifalash bilan)

    Args:
        products: Tovarlar ro'yxati
        page: Joriy sahifa (0 dan boshlanadi)
        per_page: Har bir sahifada nechta tovar
    """
    builder = InlineKeyboardBuilder()

    # Sahifalash
    start = page * per_page
    end = start + per_page
    page_products = products[start:end]

    # Har bir tovar uchun tugma
    for product in page_products:
        # Status emoji
        status = "✅" if product.get('is_available', True) else "❌"

        # Tugma teksti
        text = f"{status} {product['name']} ({product['price']:,.0f} so'm)"

        builder.row(
            InlineKeyboardButton(
                text=text,
                callback_data=f"admin_product:{product['id']}"
            )
        )

    # Sahifalash tugmalari
    nav_buttons = []

    # Oldingi sahifa
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Oldingi",
                callback_data=f"admin_page:{page - 1}"
            )
        )

    # Sahifa raqami
    total_pages = (len(products) + per_page - 1) // per_page
    nav_buttons.append(
        InlineKeyboardButton(
            text=f"📄 {page + 1}/{total_pages}",
            callback_data="admin_page_info"
        )
    )

    # Keyingi sahifa
    if end < len(products):
        nav_buttons.append(
            InlineKeyboardButton(
                text="Keyingi ➡️",
                callback_data=f"admin_page:{page + 1}"
            )
        )

    if nav_buttons:
        builder.row(*nav_buttons)

    # Orqaga
    builder.row(
        InlineKeyboardButton(
            text="« Admin panel",
            callback_data="admin_menu"
        )
    )

    return builder.as_markup()


def get_order_status_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """
    Buyurtma statusini o'zgartirish klaviaturasi

    Args:
        order_id: Buyurtma ID
    """
    builder = InlineKeyboardBuilder()

    # Har bir status uchun tugma
    statuses = [
        ("✅ Tasdiqlash", "tasdiqlandi"),
        ("🚚 Yetkazilmoqda", "yetkazilmoqda"),
        ("✔️ Yetkazildi", "yetkazildi"),
        ("❌ Bekor qilish", "bekor")
    ]

    for text, status in statuses:
        builder.row(
            InlineKeyboardButton(
                text=text,
                callback_data=f"admin_order_status:{order_id}:{status}"
            )
        )

    # Orqaga
    builder.row(
        InlineKeyboardButton(
            text="« Buyurtmalarga qaytish",
            callback_data="admin_orders"
        )
    )

    return builder.as_markup()


def get_orders_list_keyboard(orders: List[Dict], limit: int = 20) -> InlineKeyboardMarkup:
    """
    Buyurtmalar ro'yxati klaviaturasi

    Args:
        orders: Buyurtmalar ro'yxati
        limit: Ko'rsatiladigan maksimal buyurtmalar soni
    """
    builder = InlineKeyboardBuilder()

    # Faqat eng yangi buyurtmalar
    recent_orders = orders[:limit]

    for order in recent_orders:
        # Status emoji
        status_emoji = {
            'yangi': '🆕',
            'tasdiqlandi': '✅',
            'yetkazilmoqda': '🚚',
            'yetkazildi': '✔️',
            'bekor': '❌'
        }.get(order.get('status', 'yangi'), '❓')

        # Tugma teksti
        text = f"{status_emoji} {order['order_number']}"

        builder.row(
            InlineKeyboardButton(
                text=text,
                callback_data=f"admin_order:{order['id']}"
            )
        )

    # Orqaga
    builder.row(
        InlineKeyboardButton(
            text="« Admin panel",
            callback_data="admin_menu"
        )
    )

    return builder.as_markup()


def get_confirm_delete_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """
    O'chirishni tasdiqlash klaviaturasi

    Args:
        product_id: Tovar ID
    """
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="✅ Ha, o'chirish",
            callback_data=f"admin_confirm_delete:{product_id}"
        ),
        InlineKeyboardButton(
            text="❌ Yo'q",
            callback_data=f"admin_product:{product_id}"
        )
    )

    return builder.as_markup()


def get_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    """
    Xabar yuborishni tasdiqlash klaviaturasi
    """
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="✅ Ha, yuborish",
            callback_data="admin_confirm_broadcast"
        ),
        InlineKeyboardButton(
            text="❌ Bekor qilish",
            callback_data="admin_cancel"
        )
    )

    return builder.as_markup()


def get_edit_product_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """
    Tovarni tahrirlash klaviaturasi

    Args:
        product_id: Tovar ID
    """
    builder = InlineKeyboardBuilder()

    # Har bir maydon uchun tugma
    builder.row(
        InlineKeyboardButton(
            text="📝 Nomini o'zgartirish",
            callback_data=f"admin_edit_name:{product_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="💰 Narxini o'zgartirish",
            callback_data=f"admin_edit_price:{product_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📄 Tavsifni o'zgartirish",
            callback_data=f"admin_edit_desc:{product_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📏 O'lchamni o'zgartirish",
            callback_data=f"admin_edit_size:{product_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🖼 Rasmni o'zgartirish",
            callback_data=f"admin_edit_photo:{product_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📂 Kategoriyani o'zgartirish",
            callback_data=f"admin_edit_category:{product_id}"
        )
    )

    # Orqaga
    builder.row(
        InlineKeyboardButton(
            text="« Orqaga",
            callback_data=f"admin_product:{product_id}"
        )
    )

    return builder.as_markup()