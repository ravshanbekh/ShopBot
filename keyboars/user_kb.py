"""
Foydalanuvchilar uchun klaviaturalar - To'liq versiya
"""

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from typing import List, Dict


def get_main_menu() -> ReplyKeyboardMarkup:
    """
    Asosiy menyu klaviaturasi
    Foydalanuvchi botga /start yuborganida ko'rsatiladi
    """
    builder = ReplyKeyboardBuilder()

    # Birinchi qator - tovarlar va qidirish
    builder.row(
        KeyboardButton(text="🛍 Tovarlar"),
        KeyboardButton(text="🔎 Qidirish")
    )

    # Ikkinchi qator - buyurtmalar va FAQ
    builder.row(
        KeyboardButton(text="📦 Mening buyurtmalarim"),
        KeyboardButton(text="❓ FAQ")
    )

    # Uchinchi qator - aloqa
    builder.row(
        KeyboardButton(text="📞 Aloqa")
    )

    return builder.as_markup(
        resize_keyboard=True,
        input_field_placeholder="Menyudan tanlang..."
    )


def get_categories_keyboard(categories: List[str]) -> InlineKeyboardMarkup:
    """
    Kategoriyalar klaviaturasi (Inline)

    Args:
        categories: Kategoriyalar ro'yxati

    Returns:
        InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder()

    # Har bir kategoriya uchun tugma
    for category in categories:
        builder.row(
            InlineKeyboardButton(
                text=category,
                callback_data=f"category:{category}"
            )
        )

    # Orqaga tugmasi
    builder.row(
        InlineKeyboardButton(
            text="« Orqaga",
            callback_data="back_to_menu"
        )
    )

    return builder.as_markup()


def get_products_keyboard(products: List[Dict], category: str) -> InlineKeyboardMarkup:
    """
    Kategoriya ichidagi tovarlar klaviaturasi

    Args:
        products: Tovarlar ro'yxati (dict list)
        category: Kategoriya nomi

    Returns:
        InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder()

    # Har bir tovar uchun tugma
    for product in products:
        # Tovar nomi va narxi
        text = f"{product['name']} - {product['price']:,.0f} so'm"

        builder.row(
            InlineKeyboardButton(
                text=text,
                callback_data=f"product:{product['id']}"
            )
        )

    # Orqaga tugmasi - kategoriyalarga
    builder.row(
        InlineKeyboardButton(
            text="« Kategoriyalarga qaytish",
            callback_data="back_to_categories"
        )
    )

    return builder.as_markup()


def get_product_detail_keyboard(product_id: int, is_available: bool = True) -> InlineKeyboardMarkup:
    """
    Tovar tafsiloti klaviaturasi

    Args:
        product_id: Tovar ID
        is_available: Tovar mavjudmi

    Returns:
        InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder()

    # Agar tovar mavjud bo'lsa, buyurtma tugmasini ko'rsatish
    if is_available:
        builder.row(
            InlineKeyboardButton(
                text="🛒 Buyurtma berish",
                callback_data=f"order:{product_id}"
            )
        )
    else:
        # Mavjud emas tugmasi (disabled holatda)
        builder.row(
            InlineKeyboardButton(
                text="❌ Mavjud emas",
                callback_data="product_unavailable"
            )
        )

    # Orqaga tugmasi
    builder.row(
        InlineKeyboardButton(
            text="« Orqaga",
            callback_data="back_to_products"
        )
    )

    return builder.as_markup()


def get_order_confirm_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """
    Buyurtmani tasdiqlash klaviaturasi

    Args:
        order_id: Buyurtma ID

    Returns:
        InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder()

    # Tasdiqlash va bekor qilish tugmalari
    builder.row(
        InlineKeyboardButton(
            text="✅ Tasdiqlash",
            callback_data=f"confirm_order:{order_id}"
        ),
        InlineKeyboardButton(
            text="❌ Bekor qilish",
            callback_data="cancel_order"
        )
    )

    return builder.as_markup()


def get_faq_keyboard() -> InlineKeyboardMarkup:
    """
    FAQ (Tez-tez so'raladigan savollar) klaviaturasi
    """
    builder = InlineKeyboardBuilder()

    # Har bir FAQ mavzusi uchun tugma
    builder.row(
        InlineKeyboardButton(
            text="🚚 Yetkazib berish",
            callback_data="faq:yetkazish"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="💳 To'lov",
            callback_data="faq:tolov"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📞 Aloqa",
            callback_data="faq:aloqa"
        )
    )

    # Orqaga tugmasi
    builder.row(
        InlineKeyboardButton(
            text="« Orqaga",
            callback_data="back_to_menu"
        )
    )

    return builder.as_markup()


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """
    Bekor qilish klaviaturasi (buyurtma berish jarayonida)
    """
    builder = ReplyKeyboardBuilder()

    builder.row(
        KeyboardButton(text="❌ Bekor qilish")
    )

    return builder.as_markup(
        resize_keyboard=True,
        input_field_placeholder="Yoki bekor qilish..."
    )


def get_phone_keyboard() -> ReplyKeyboardMarkup:
    """
    Telefon raqamini yuborish klaviaturasi
    Contact sharing funksiyasi bilan
    """
    builder = ReplyKeyboardBuilder()

    # Telefon raqamni ulashish tugmasi
    builder.row(
        KeyboardButton(
            text="📱 Telefon raqamni yuborish",
            request_contact=True
        )
    )

    # Bekor qilish tugmasi
    builder.row(
        KeyboardButton(text="❌ Bekor qilish")
    )

    return builder.as_markup(
        resize_keyboard=True,
        input_field_placeholder="Telefon raqamni ulashing..."
    )


def get_orders_history_keyboard(orders: List[Dict]) -> InlineKeyboardMarkup:
    """
    Buyurtmalar tarixi klaviaturasi

    Args:
        orders: Buyurtmalar ro'yxati

    Returns:
        InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder()

    # Har bir buyurtma uchun tugma
    for order in orders[:10]:  # Faqat oxirgi 10 ta
        status_emoji = {
            'yangi': '🆕',
            'tasdiqlandi': '✅',
            'yetkazilmoqda': '🚚',
            'yetkazildi': '✔️',
            'bekor': '❌'
        }.get(order['status'], '❓')

        text = f"{status_emoji} {order['order_number']}"

        builder.row(
            InlineKeyboardButton(
                text=text,
                callback_data=f"view_order:{order['id']}"
            )
        )

    # Orqaga
    builder.row(
        InlineKeyboardButton(
            text="« Orqaga",
            callback_data="back_to_menu"
        )
    )

    return builder.as_markup()


def get_location_keyboard() -> ReplyKeyboardMarkup:
    """
    Joylashuvni yuborish klaviaturasi (ixtiyoriy)
    """
    builder = ReplyKeyboardBuilder()

    builder.row(
        KeyboardButton(
            text="📍 Joylashuvni yuborish",
            request_location=True
        )
    )
    builder.row(
        KeyboardButton(text="✍️ Qo'lda kiritish")
    )
    builder.row(
        KeyboardButton(text="❌ Bekor qilish")
    )

    return builder.as_markup(
        resize_keyboard=True,
        input_field_placeholder="Manzilni yuboring..."
    )