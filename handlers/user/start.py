"""
Start va asosiy user handlerlari
"""

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import config
from keyboars.user_kb import get_main_menu, get_faq_keyboard
from database.json_db import db

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Start buyrug'i"""
    # Holatni tozalash
    await state.clear()

    # Foydalanuvchini bazaga qo'shish
    db.add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )

    await message.answer(
        config.MESSAGES['start'],
        reply_markup=get_main_menu()
    )


@router.message(F.text == "📞 Aloqa")
async def contact_info(message: Message):
    """Aloqa ma'lumotlari"""
    await message.answer(config.FAQ_ANSWERS['aloqa'])


@router.message(F.text == "❓ FAQ")
async def faq_menu(message: Message):
    """FAQ menyusi"""
    await message.answer(
        "❓ Tez-tez so'raladigan savollar:\n\nQuyidagi tugmalardan birini tanlang:",
        reply_markup=get_faq_keyboard()
    )


@router.callback_query(F.data.startswith("faq:"))
async def faq_answer(callback: CallbackQuery):
    """FAQ javoblari"""
    faq_type = callback.data.split(":")[1]
    answer = config.FAQ_ANSWERS.get(faq_type, "Ma'lumot topilmadi")

    await callback.message.edit_text(
        answer,
        reply_markup=get_faq_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Asosiy menyuga qaytish"""
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "Asosiy menyu:",
        reply_markup=get_main_menu()
    )
    await callback.answer()


@router.message(F.text == "📦 Mening buyurtmalarim")
async def my_orders(message: Message):
    """Foydalanuvchi buyurtmalari"""
    orders = db.get_user_orders(message.from_user.id)

    if not orders:
        await message.answer("📭 Sizda hali buyurtmalar yo'q")
        return

    text = "📦 <b>Sizning buyurtmalaringiz:</b>\n\n"

    for order in orders:
        product = db.get_product(order['product_id'])
        product_name = product['name'] if product else "Noma'lum tovar"

        status_emoji = {
            'yangi': '🆕',
            'tasdiqlandi': '✅',
            'yetkazilmoqda': '🚚',
            'yetkazildi': '✔️',
            'bekor': '❌'
        }.get(order['status'], '❓')

        text += f"{status_emoji} <b>{order['order_number']}</b>\n"
        text += f"📦 Tovar: {product_name}\n"
        text += f"📅 Sana: {order['created_at']}\n"
        text += f"Status: {order['status'].capitalize()}\n\n"

    await message.answer(text)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Yordam buyrug'i"""
    help_text = """
📖 <b>Bot haqida ma'lumot:</b>

🛍 <b>Tovarlar</b> - Barcha tovarlarni ko'rish
🔎 <b>Qidirish</b> - Tovar qidirish
📦 <b>Buyurtmalarim</b> - Buyurtmalar tarixi
❓ <b>FAQ</b> - Tez-tez so'raladigan savollar
📞 <b>Aloqa</b> - Biz bilan bog'lanish

<b>Buyurtma berish:</b>
1. Tovarni tanlang
2. "Buyurtma berish" tugmasini bosing
3. Ma'lumotlaringizni kiriting
4. Tasdiqlang

Savollaringiz bo'lsa /help buyrug'ini yuboring.
    """
    await message.answer(help_text)