"""
Buyurtma berish handleri - To'liq versiya
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import re

import config
from keyboars.user_kb import (
    get_cancel_keyboard,
    get_phone_keyboard,
    get_main_menu,
    get_order_confirm_keyboard
)
from database.json_db import db

router = Router()


class OrderForm(StatesGroup):
    """Buyurtma shakli holatlari"""
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_address = State()
    waiting_for_quantity = State()


@router.callback_query(F.data.startswith("order:"))
async def start_order(callback: CallbackQuery, state: FSMContext):
    """
    Buyurtma jarayonini boshlash
    Tovar tafsilotidan "Buyurtma berish" tugmasi bosilganda ishlaydi
    """
    product_id = int(callback.data.split(":")[1])

    # Tovarni tekshirish
    product = db.get_product(product_id)

    if not product:
        await callback.answer("❌ Tovar topilmadi", show_alert=True)
        return

    if not product.get('is_available', True):
        await callback.answer(
            "❌ Bu tovar hozirda mavjud emas\n\n"
            "Keyinroq qaytib ko'ring yoki boshqa tovarlarni ko'ring.",
            show_alert=True
        )
        return

    # Holatga tovar ID ni saqlash
    await state.update_data(product_id=product_id)
    await state.set_state(OrderForm.waiting_for_name)

    # Buyurtma formasi boshlanishi
    await callback.message.answer(
        "📝 <b>Buyurtma berish</b>\n\n"
        f"📦 Tovar: <b>{product['name']}</b>\n"
        f"💰 Narx: <b>{product['price']:,.0f} so'm</b>\n\n"
        "1️⃣ Iltimos, <b>ismingizni</b> kiriting:\n\n"
        "Masalan: Abdulloh yoki Dilorom",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(OrderForm.waiting_for_name, F.text == "❌ Bekor qilish")
async def cancel_order_name(message: Message, state: FSMContext):
    """Ismni kiritishda bekor qilish"""
    await state.clear()
    await message.answer(
        config.MESSAGES['order_cancel'],
        reply_markup=get_main_menu()
    )


@router.message(OrderForm.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """
    Ismni qabul qilish va validatsiya
    """
    name = message.text.strip()

    # Validatsiya
    if len(name) < 2:
        await message.answer(
            "❌ Ism juda qisqa!\n\n"
            "Iltimos, kamida 2 ta harfdan iborat ismingizni kiriting:"
        )
        return

    if len(name) > 50:
        await message.answer(
            "❌ Ism juda uzun!\n\n"
            "Iltimos, 50 ta belgidan kam ismingizni kiriting:"
        )
        return

    # Faqat raqamlarni qabul qilmaslik
    if name.isdigit():
        await message.answer(
            "❌ Ism faqat raqamlardan iborat bo'lishi mumkin emas!\n\n"
            "Iltimos, to'g'ri ismingizni kiriting:"
        )
        return

    # Holatga saqlash
    await state.update_data(customer_name=name)
    await state.set_state(OrderForm.waiting_for_phone)

    # Telefon raqam so'rash
    await message.answer(
        f"✅ Ism qabul qilindi: <b>{name}</b>\n\n"
        "2️⃣ Endi <b>telefon raqamingizni</b> kiriting:\n\n"
        "Format: +998901234567\n"
        "yoki tugma orqali ulashing 👇",
        reply_markup=get_phone_keyboard()
    )


@router.message(OrderForm.waiting_for_phone, F.text == "❌ Bekor qilish")
async def cancel_order_phone(message: Message, state: FSMContext):
    """Telefon kiritishda bekor qilish"""
    await state.clear()
    await message.answer(
        config.MESSAGES['order_cancel'],
        reply_markup=get_main_menu()
    )


@router.message(OrderForm.waiting_for_phone, F.contact)
async def process_contact(message: Message, state: FSMContext):
    """
    Kontakt orqali telefon raqamni qabul qilish
    """
    phone = message.contact.phone_number

    # + belgisini qo'shish
    if not phone.startswith('+'):
        phone = f"+{phone}"

    # Holatga saqlash
    await state.update_data(phone=phone)
    await state.set_state(OrderForm.waiting_for_address)

    # Manzil so'rash
    await message.answer(
        f"✅ Telefon qabul qilindi: <b>{phone}</b>\n\n"
        "3️⃣ Endi <b>yetkazib berish manzilini</b> kiriting:\n\n"
        "To'liq manzilni yozing:\n"
        "• Shahar/viloyat\n"
        "• Tuman\n"
        "• Ko'cha va uy raqami\n\n"
        "Masalan: Toshkent sh., Chilonzor tumani, 12-kvartal, 5-uy, 23-xonadon",
        reply_markup=get_cancel_keyboard()
    )


@router.message(OrderForm.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    """
    Matn orqali telefon raqamni qabul qilish va validatsiya
    """
    phone = message.text.strip()

    # Bo'sh joylarni olib tashlash
    phone = phone.replace(" ", "").replace("-", "")

    # + belgisini qo'shish (agar 998 bilan boshlansa)
    if phone.startswith('998') and not phone.startswith('+'):
        phone = f"+{phone}"

    # Validatsiya - +998 bilan boshlanishi kerak
    if not phone.startswith('+998'):
        await message.answer(
            "❌ Noto'g'ri format!\n\n"
            "Telefon raqam <b>+998</b> bilan boshlanishi kerak.\n\n"
            "To'g'ri format:\n"
            "• +998901234567\n"
            "• +998 90 123 45 67\n\n"
            "Qaytadan kiriting:"
        )
        return

    # Raqamlarni sanash
    digits = ''.join(filter(str.isdigit, phone))

    if len(digits) != 12:
        await message.answer(
            "❌ Noto'g'ri raqam!\n\n"
            "Telefon raqam 12 ta raqamdan iborat bo'lishi kerak.\n\n"
            "To'g'ri format: +998901234567\n\n"
            "Qaytadan kiriting:"
        )
        return

    # Operator kodini tekshirish (90, 91, 93, 94, 95, 97, 98, 99, 33, 88)
    operator_code = digits[3:5]
    valid_codes = ['90', '91', '93', '94', '95', '97', '98', '99', '33', '88']

    if operator_code not in valid_codes:
        await message.answer(
            "⚠️ Operator kodi noto'g'ri ko'rinadi.\n\n"
            "To'g'ri operator kodlari:\n"
            "90, 91, 93, 94, 95, 97, 98, 99, 33, 88\n\n"
            "Davom ettirasizmi? (Ha/Yo'q)"
        )

    # Holatga saqlash
    await state.update_data(phone=phone)
    await state.set_state(OrderForm.waiting_for_address)

    # Manzil so'rash
    await message.answer(
        f"✅ Telefon qabul qilindi: <b>{phone}</b>\n\n"
        "3️⃣ Endi <b>yetkazib berish manzilini</b> kiriting:\n\n"
        "To'liq manzilni yozing:\n"
        "• Shahar/viloyat\n"
        "• Tuman\n"
        "• Ko'cha va uy raqami\n\n"
        "Masalan: Toshkent sh., Chilonzor tumani, 12-kvartal, 5-uy, 23-xonadon",
        reply_markup=get_cancel_keyboard()
    )


@router.message(OrderForm.waiting_for_address, F.text == "❌ Bekor qilish")
async def cancel_order_address(message: Message, state: FSMContext):
    """Manzil kiritishda bekor qilish"""
    await state.clear()
    await message.answer(
        config.MESSAGES['order_cancel'],
        reply_markup=get_main_menu()
    )


@router.message(OrderForm.waiting_for_address)
async def process_address(message: Message, state: FSMContext):
    """
    Manzilni qabul qilish va validatsiya
    """
    address = message.text.strip()

    # Validatsiya
    if len(address) < 10:
        await message.answer(
            "❌ Manzil juda qisqa!\n\n"
            "Iltimos, to'liq manzilni kiriting:\n"
            "• Shahar yoki viloyat\n"
            "• Tuman\n"
            "• Ko'cha va uy raqami\n\n"
            "Masalan: Toshkent sh., Chilonzor tumani, 12-kvartal, 5-uy"
        )
        return

    if len(address) > 200:
        await message.answer(
            "❌ Manzil juda uzun!\n\n"
            "Iltimos, 200 ta belgidan kam manzilni kiriting:"
        )
        return

    # Holatga saqlash
    await state.update_data(address=address)
    await state.set_state(OrderForm.waiting_for_quantity)

    # Miqdor so'rash
    await message.answer(
        f"✅ Manzil qabul qilindi\n\n"
        "4️⃣ <b>Miqdorni</b> kiriting:\n\n"
        "Nechta buyurtma qilmoqchisiz? (1 dan 100 gacha)\n\n"
        "Faqat raqam kiriting, masalan: 1 yoki 5",
        reply_markup=get_cancel_keyboard()
    )


@router.message(OrderForm.waiting_for_quantity, F.text == "❌ Bekor qilish")
async def cancel_order_quantity(message: Message, state: FSMContext):
    """Miqdor kiritishda bekor qilish"""
    await state.clear()
    await message.answer(
        config.MESSAGES['order_cancel'],
        reply_markup=get_main_menu()
    )


@router.message(OrderForm.waiting_for_quantity)
async def process_quantity(message: Message, state: FSMContext):
    """
    Miqdorni qabul qilish va buyurtmani yakunlash
    """
    # Raqamga o'girish
    try:
        quantity = int(message.text.strip())
    except ValueError:
        await message.answer(
            "❌ Noto'g'ri format!\n\n"
            "Iltimos, faqat <b>raqam</b> kiriting:\n\n"
            "Masalan: 1, 2, 5, 10"
        )
        return

    # Validatsiya
    if quantity < 1:
        await message.answer(
            "❌ Miqdor kamida <b>1</b> bo'lishi kerak!\n\n"
            "Qaytadan kiriting:"
        )
        return

    if quantity > 100:
        await message.answer(
            "❌ Miqdor <b>100</b> dan oshmasligi kerak!\n\n"
            "Katta hajmdagi buyurtmalar uchun bizga qo'ng'iroq qiling:\n"
            "+998 90 123 45 67"
        )
        return

    # Barcha ma'lumotlarni olish
    data = await state.get_data()
    product_id = data['product_id']
    customer_name = data['customer_name']
    phone = data['phone']
    address = data['address']

    # Tovar ma'lumotlarini olish
    product = db.get_product(product_id)

    if not product:
        await message.answer(
            "❌ Tovar topilmadi!\n\n"
            "Iltimos, qaytadan urinib ko'ring.",
            reply_markup=get_main_menu()
        )
        await state.clear()
        return

    # Buyurtmani bazaga saqlash
    order = db.create_order(
        user_id=message.from_user.id,
        username=message.from_user.username or "noma'lum",
        product_id=product_id,
        customer_name=customer_name,
        phone=phone,
        address=address,
        quantity=quantity
    )

    # Umumiy narxni hisoblash
    total_price = product['price'] * quantity

    # Buyurtma ma'lumotlarini ko'rsatish
    order_text = f"""
✅ <b>Buyurtma ma'lumotlarini tasdiqlang</b>

━━━━━━━━━━━━━━━━━━━━

📦 <b>TOVAR:</b>
{product['name']}
💰 Narxi: {product['price']:,.0f} so'm
🔢 Miqdor: {quantity} dona
💵 <b>JAMI:</b> {total_price:,.0f} so'm

━━━━━━━━━━━━━━━━━━━━

👤 <b>MIJOZ MA'LUMOTLARI:</b>
• Ism: {customer_name}
• Telefon: {phone}
• Manzil: {address}

━━━━━━━━━━━━━━━━━━━━

Ma'lumotlar to'g'rimi?
    """

    await message.answer(
        order_text,
        reply_markup=get_order_confirm_keyboard(order['id'])
    )

    # Holatni tozalash
    await state.clear()


@router.callback_query(F.data.startswith("confirm_order:"))
async def confirm_order(callback: CallbackQuery):
    """
    Buyurtmani tasdiqlash va adminlarga yuborish
    """
    order_id = int(callback.data.split(":")[1])
    order = db.get_order(order_id)

    if not order:
        await callback.answer("❌ Buyurtma topilmadi", show_alert=True)
        return

    product = db.get_product(order['product_id'])
    total_price = product['price'] * order['quantity']

    # Adminlarga xabar tayyorlash
    admin_text = f"""
🆕 <b>YANGI BUYURTMA!</b>

━━━━━━━━━━━━━━━━━━━━

📋 <b>Buyurtma raqami:</b> <code>{order['order_number']}</code>

📦 <b>TOVAR:</b>
• Nomi: {product['name']}
• Kategoriya: {product['category']}
• Narxi: {product['price']:,.0f} so'm
• Miqdor: {order['quantity']} dona
• <b>JAMI: {total_price:,.0f} so'm</b>

━━━━━━━━━━━━━━━━━━━━

👤 <b>MIJOZ:</b>
• Ism: {order['customer_name']}
• Telefon: {order['phone']}
• Manzil: {order['address']}

━━━━━━━━━━━━━━━━━━━━

🆔 User ID: <code>{order['user_id']}</code>
👤 Username: @{order['username']}
📅 Sana: {order['created_at']}

━━━━━━━━━━━━━━━━━━━━

⚡️ Tezroq javob bering!
    """

    # Har bir adminga yuborish
    for admin_id in config.ADMINS:
        try:
            if product.get('photo_id'):
                await callback.bot.send_photo(
                    chat_id=admin_id,
                    photo=product['photo_id'],
                    caption=admin_text
                )
            else:
                await callback.bot.send_message(
                    chat_id=admin_id,
                    text=admin_text
                )
        except Exception as e:
            print(f"Adminga xabar yuborishda xatolik ({admin_id}): {e}")

    # Mijozga tasdiqlash xabari
    await callback.message.edit_text(
        f"{config.MESSAGES['order_success']}\n\n"
        f"📋 <b>Buyurtma raqami:</b> <code>{order['order_number']}</code>\n\n"
        f"Buyurtmangiz qabul qilindi va tez orada operatorimiz siz bilan bog'lanadi.\n\n"
        f"📦 Buyurtma holati: <b>Yangi</b>\n"
        f"📅 Sana: {order['created_at']}\n\n"
        f"Buyurtmalar tarixini ko'rish: /start → Mening buyurtmalarim",
        reply_markup=None
    )

    await callback.message.answer(
        "Asosiy menyu:",
        reply_markup=get_main_menu()
    )
    await callback.answer("✅ Buyurtma tasdiqlandi!", show_alert=True)


@router.callback_query(F.data == "cancel_order")
async def cancel_order_callback(callback: CallbackQuery):
    """
    Buyurtmani bekor qilish
    """
    await callback.message.edit_text(
        f"{config.MESSAGES['order_cancel']}\n\n"
        "Buyurtma bekor qilindi. Boshqa tovarlarni ko'rishingiz mumkin."
    )

    await callback.message.answer(
        "Asosiy menyu:",
        reply_markup=get_main_menu()
    )
    await callback.answer("Buyurtma bekor qilindi")