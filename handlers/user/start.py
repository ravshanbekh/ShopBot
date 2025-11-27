"""
Start va asosiy user handlerlari - To'liq versiya
FAQ, Aloqa, Buyurtmalar tarixi
"""

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import config
from keyboars.user_kb import get_main_menu, get_faq_keyboard, get_orders_history_keyboard
from database.json_db import db

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """
    Start buyrug'i - Botga /start yuborganida
    Deep link: /start order_123 - to'g'ri buyurtma formasi
    """
    # Holatni tozalash
    await state.clear()

    # Foydalanuvchini bazaga qo'shish/yangilash
    db.add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )

    # Deep link parametrini tekshirish
    args = message.text.split()
    if len(args) > 1 and args[1].startswith('order_'):
        # Tovar ID ni olish
        try:
            product_id = int(args[1].replace('order_', ''))

            # Tovarni olish
            product = db.get_product(product_id)

            if product and product.get('is_available'):
                # To'g'ridan-to'g'ri buyurtma formasi
                from handlers.user.order import OrderForm
                from keyboars.user_kb import get_cancel_keyboard

                await state.update_data(product_id=product_id)
                await state.set_state(OrderForm.waiting_for_name)

                await message.answer(
                    "📝 <b>Buyurtma berish</b>\n\n"
                    f"📦 Tovar: <b>{product['name']}</b>\n"
                    f"💰 Narx: <b>{product['price']:,.0f} so'm</b>\n\n"
                    "1️⃣ Iltimos, <b>ismingizni</b> kiriting:\n\n"
                    "Masalan: Abdulloh yoki Dilorom",
                    reply_markup=get_cancel_keyboard()
                )
                return
            else:
                await message.answer(
                    "❌ Bu tovar mavjud emas yoki o'chirilgan.\n\n"
                    "Boshqa tovarlarni ko'ring:",
                    reply_markup=get_main_menu()
                )
                return
        except (ValueError, IndexError):
            pass

    # Oddiy start xabari
    welcome_text = config.MESSAGES['start']

    # Agar ismini bilsak, shaxsiy murojaat
    if message.from_user.first_name:
        welcome_text = f"👋 Salom, <b>{message.from_user.first_name}</b>!\n\n" + welcome_text

    await message.answer(
        welcome_text,
        reply_markup=get_main_menu()
    )


@router.message(F.text == "📞 Aloqa")
async def contact_info(message: Message):
    """
    Aloqa ma'lumotlarini ko'rsatish
    """
    await message.answer(
        config.FAQ_ANSWERS['aloqa'],
        disable_web_page_preview=True
    )


@router.message(F.text == "❓ FAQ")
async def faq_menu(message: Message):
    """
    FAQ (Tez-tez so'raladigan savollar) menyusi
    """
    await message.answer(
        "❓ <b>Tez-tez so'raladigan savollar</b>\n\n"
        "Quyidagi mavzulardan birini tanlang:",
        reply_markup=get_faq_keyboard()
    )


@router.callback_query(F.data.startswith("faq:"))
async def faq_answer(callback: CallbackQuery):
    """
    FAQ javoblarini ko'rsatish
    """
    # FAQ turini ajratib olish
    faq_type = callback.data.split(":")[1]

    # Javobni olish
    answer = config.FAQ_ANSWERS.get(faq_type, "❌ Ma'lumot topilmadi")

    # FAQ sarlavhalarini qo'shish
    faq_titles = {
        'yetkazish': '🚚 Yetkazib berish',
        'tolov': '💳 Tolov',
        'aloqa': '📞 Aloqa'
    }

    title = faq_titles.get(faq_type, 'Ma\'lumot')

    # Javobni ko'rsatish
    await callback.message.edit_text(
        f"<b>{title}</b>\n\n{answer}",
        reply_markup=get_faq_keyboard(),
        disable_web_page_preview=True
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    """
    Asosiy menyuga qaytish
    """
    # Holatni tozalash
    await state.clear()

    # Xabarni o'chirish
    await callback.message.delete()

    # Asosiy menyu
    await callback.message.answer(
        "Asosiy menyu:",
        reply_markup=get_main_menu()
    )
    await callback.answer()


@router.message(F.text == "📦 Mening buyurtmalarim")
async def my_orders(message: Message):
    """
    Foydalanuvchi buyurtmalari tarixi
    """
    # Foydalanuvchi buyurtmalarini olish
    orders = db.get_user_orders(message.from_user.id)

    if not orders:
        await message.answer(
            "📭 <b>Sizda buyurtmalar yo'q</b>\n\n"
            "Birinchi buyurtmangizni bering:\n"
            "🛍 Tovarlar → Kategoriya → Tovar → Buyurtma berish"
        )
        return

    # Buyurtmalar haqida qisqacha ma'lumot
    text = f"📦 <b>Sizning buyurtmalaringiz</b> ({len(orders)} ta)\n\n"

    # Oxirgi 5 ta buyurtma haqida ma'lumot
    for order in orders[:5]:
        # Tovar ma'lumotlarini olish
        product = db.get_product(order['product_id'])
        product_name = product['name'] if product else "Tovar topilmadi"

        # Status emoji
        status_emoji = {
            'yangi': '🆕',
            'tasdiqlandi': '✅',
            'yetkazilmoqda': '🚚',
            'yetkazildi': '✔️',
            'bekor': '❌'
        }.get(order['status'], '❓')

        # Status nomi
        status_name = {
            'yangi': 'Yangi',
            'tasdiqlandi': 'Tasdiqlangan',
            'yetkazilmoqda': 'Yetkazilmoqda',
            'yetkazildi': 'Yetkazilgan',
            'bekor': 'Bekor qilingan'
        }.get(order['status'], 'Noma\'lum')

        # Buyurtma ma'lumotlari
        text += f"{status_emoji} <b>{order['order_number']}</b>\n"
        text += f"📦 {product_name}\n"
        text += f"📅 {order['created_at']}\n"
        text += f"📊 Status: {status_name}\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n\n"

    # Agar ko'proq buyurtma bo'lsa
    if len(orders) > 5:
        text += f"... va yana {len(orders) - 5} ta buyurtma\n\n"

    text += "📋 Batafsil ma'lumot uchun buyurtma raqamiga bosing."

    await message.answer(
        text,
        reply_markup=get_orders_history_keyboard(orders)
    )


@router.callback_query(F.data.startswith("view_order:"))
async def view_order_detail(callback: CallbackQuery):
    """
    Buyurtma tafsilotlarini ko'rish
    """
    # Buyurtma ID ni olish
    order_id = int(callback.data.split(":")[1])

    # Buyurtmani olish
    order = db.get_order(order_id)

    if not order:
        await callback.answer("❌ Buyurtma topilmadi", show_alert=True)
        return

    # Tovar ma'lumotlarini olish
    product = db.get_product(order['product_id'])

    if not product:
        await callback.answer("❌ Tovar topilmadi", show_alert=True)
        return

    # Umumiy narx
    total_price = product['price'] * order['quantity']

    # Status emoji
    status_emoji = {
        'yangi': '🆕',
        'tasdiqlandi': '✅',
        'yetkazilmoqda': '🚚',
        'yetkazildi': '✔️',
        'bekor': '❌'
    }.get(order['status'], '❓')

    # Status nomi
    status_name = {
        'yangi': 'Yangi',
        'tasdiqlandi': 'Tasdiqlangan',
        'yetkazilmoqda': 'Yetkazilmoqda',
        'yetkazildi': 'Yetkazilgan',
        'bekor': 'Bekor qilingan'
    }.get(order['status'], 'Noma\'lum')

    # Batafsil ma'lumot
    detail_text = f"""
{status_emoji} <b>BUYURTMA TAFSILOTLARI</b>

━━━━━━━━━━━━━━━━━━━━

📋 <b>Buyurtma raqami:</b>
<code>{order['order_number']}</code>

📅 <b>Sana:</b> {order['created_at']}
📊 <b>Status:</b> {status_name}

━━━━━━━━━━━━━━━━━━━━

📦 <b>TOVAR:</b>
• Nomi: {product['name']}
• Kategoriya: {product['category']}
• Narxi: {product['price']:,.0f} so'm
• Miqdor: {order['quantity']} dona
• <b>JAMI: {total_price:,.0f} so'm</b>

━━━━━━━━━━━━━━━━━━━━

👤 <b>YETKAZISH MA'LUMOTLARI:</b>
• Ism: {order['customer_name']}
• Telefon: {order['phone']}
• Manzil: {order['address']}

━━━━━━━━━━━━━━━━━━━━
    """

    # Agar tovar rasmi bo'lsa
    if product.get('photo_id'):
        try:
            await callback.message.delete()
            await callback.bot.send_photo(
                chat_id=callback.message.chat.id,
                photo=product['photo_id'],
                caption=detail_text
            )
        except Exception:
            await callback.message.edit_text(detail_text)
    else:
        await callback.message.edit_text(detail_text)

    await callback.answer()


@router.message(Command("help"))
async def cmd_help(message: Message):
    """
    Yordam buyrug'i
    """
    help_text = """
📖 <b>Bot haqida ma'lumot</b>

━━━━━━━━━━━━━━━━━━━━

<b>🛍 TOVARLAR</b>
Barcha tovarlarni kategoriyalar bo'yicha ko'ring va buyurtma bering.

<b>🔎 QIDIRISH</b>
Kerakli tovarni toping (tez orada!)

<b>📦 BUYURTMALAR</b>
O'z buyurtmalaringiz tarixini ko'ring va statusini kuzating.

<b>❓ FAQ</b>
Tez-tez so'raladigan savollar va javoblar.

<b>📞 ALOQA</b>
Biz bilan bog'lanish ma'lumotlari.

━━━━━━━━━━━━━━━━━━━━

<b>📝 BUYURTMA BERISH:</b>

1️⃣ 🛍 Tovarlar → Kategoriyani tanlang
2️⃣ Tovarni tanlang
3️⃣ "Buyurtma berish" tugmasini bosing
4️⃣ Formani to'ldiring:
   • Ismingiz
   • Telefon raqamingiz
   • Yetkazish manzili
   • Miqdor
5️⃣ Ma'lumotlarni tasdiqlang

✅ Tayyor! Operator siz bilan bog'lanadi.

━━━━━━━━━━━━━━━━━━━━

Savollar bo'lsa:
📞 Aloqa → Biz bilan bog'laning
❓ FAQ → Ko'p so'raladigan savollar

Xaridingiz uchun rahmat! 🎉
    """

    await message.answer(help_text)


@router.message(Command("id"))
async def cmd_id(message: Message):
    """
    Foydalanuvchi ID ni ko'rsatish (debug uchun)
    """
    await message.answer(
        f"🆔 <b>Sizning ma'lumotlaringiz:</b>\n\n"
        f"• User ID: <code>{message.from_user.id}</code>\n"
        f"• Username: @{message.from_user.username or 'yoq'}\n"
        f"• Ism: {message.from_user.first_name or 'yoq'}\n\n"
        f"<i>Admin bo'lish uchun bu ID ni bot egasiga yuboring</i>"
    )


# unknown_message handlerini olib tashladik - catalog.py ishlasin