"""
Admin tovar boshqaruvi - Oddiy va ishlaydigan versiya
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import config
from keyboars.admin_kb import (
    get_categories_admin_keyboard,
    get_products_list_keyboard,
    get_product_manage_keyboard,
    get_confirm_delete_keyboard,
    get_admin_main_menu
)
from database.json_db import db
from middlewares.admin_check import AdminFilter

router = Router()
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


class AddProduct(StatesGroup):
    """Tovar qo'shish holatlari"""
    category = State()
    name = State()
    price = State()
    description = State()
    size = State()
    photo = State()


@router.message(F.text == "➕ Tovar qo'shish")
async def start_add_product(message: Message, state: FSMContext):
    """Tovar qo'shishni boshlash"""
    categories = db.get_categories()

    if not categories:
        await message.answer(
            "❌ Avval kategoriya qo'shish kerak!\n\n"
            "📂 Kategoriyalar menyusiga o'ting."
        )
        return

    await state.set_state(AddProduct.category)
    await message.answer(
        "➕ <b>Yangi tovar qo'shish</b>\n\n"
        "1️⃣ Kategoriyani tanlang:",
        reply_markup=get_categories_admin_keyboard(categories, action="select")
    )


@router.callback_query(AddProduct.category, F.data.startswith("admin_category:"))
async def select_category(callback: CallbackQuery, state: FSMContext):
    """Kategoriyani tanlash"""
    category = callback.data.split(":", 1)[1]
    await state.update_data(category=category)
    await state.set_state(AddProduct.name)

    await callback.message.edit_text(
        f"➕ <b>Yangi tovar qo'shish</b>\n\n"
        f"📂 Kategoriya: {category}\n\n"
        "2️⃣ Tovar nomini kiriting:"
    )
    await callback.answer()


@router.message(AddProduct.name)
async def input_name(message: Message, state: FSMContext):
    """Tovar nomini kiritish"""
    if len(message.text) < 2:
        await message.answer("❌ Nom kamida 2 ta belgidan iborat bo'lishi kerak:")
        return

    await state.update_data(name=message.text)
    await state.set_state(AddProduct.price)

    await message.answer(
        "3️⃣ Tovar narxini kiriting (faqat raqam, so'm):\n\n"
        "Masalan: 50000"
    )


@router.message(AddProduct.price)
async def input_price(message: Message, state: FSMContext):
    """Narxni kiritish"""
    try:
        price = float(message.text.replace(",", "").replace(" ", ""))
        if price <= 0:
            await message.answer("❌ Narx musbat son bo'lishi kerak:")
            return
    except ValueError:
        await message.answer("❌ Noto'g'ri format! Faqat raqam kiriting:")
        return

    await state.update_data(price=price)
    await state.set_state(AddProduct.description)

    await message.answer(
        "4️⃣ Tovar tavsifini kiriting:\n\n"
        "(yoki o'tkazib yuborish uchun \"-\" yozing)"
    )


@router.message(AddProduct.description)
async def input_description(message: Message, state: FSMContext):
    """Tavsifni kiritish"""
    description = None if message.text == "-" else message.text
    await state.update_data(description=description)
    await state.set_state(AddProduct.size)

    await message.answer(
        "5️⃣ O'lcham/Rang/Variant kiriting:\n\n"
        "Masalan: M, L, XL yoki Qora, Oq\n"
        "(yoki o'tkazib yuborish uchun \"-\" yozing)"
    )


@router.message(AddProduct.size)
async def input_size(message: Message, state: FSMContext):
    """O'lchamni kiritish"""
    size = None if message.text == "-" else message.text
    await state.update_data(size=size)
    await state.set_state(AddProduct.photo)

    await message.answer(
        "6️⃣ Tovar rasmini yuboring:\n\n"
        "(yoki o'tkazib yuborish uchun \"-\" yozing)"
    )


@router.message(AddProduct.photo, F.photo)
async def input_photo(message: Message, state: FSMContext):
    """Rasmni qabul qilish"""
    photo_id = message.photo[-1].file_id

    # Barcha ma'lumotlarni olish
    data = await state.get_data()

    # Tovarni qo'shish
    product = db.add_product(
        category=data['category'],
        name=data['name'],
        description=data.get('description'),
        price=data['price'],
        size=data.get('size'),
        photo_id=photo_id
    )

    await state.clear()

    # Tasdiqlash xabari
    text = f"""
{config.MESSAGES['product_added']}

📦 <b>{product['name']}</b>
📂 Kategoriya: {product['category']}
💰 Narxi: {product['price']:,.0f} so'm
    """

    await message.answer_photo(
        photo=photo_id,
        caption=text,
        reply_markup=get_admin_main_menu()
    )


@router.message(AddProduct.photo)
async def input_no_photo(message: Message, state: FSMContext):
    """Rasmsiz tovar qo'shish"""
    if message.text != "-":
        await message.answer(
            "❌ Iltimos, rasm yuboring yoki o'tkazib yuborish uchun \"-\" yozing:"
        )
        return

    # Barcha ma'lumotlarni olish
    data = await state.get_data()

    # Tovarni qo'shish
    product = db.add_product(
        category=data['category'],
        name=data['name'],
        description=data.get('description'),
        price=data['price'],
        size=data.get('size'),
        photo_id=None
    )

    await state.clear()

    # Tasdiqlash xabari
    text = f"""
{config.MESSAGES['product_added']}

📦 <b>{product['name']}</b>
📂 Kategoriya: {product['category']}
💰 Narxi: {product['price']:,.0f} so'm
    """

    await message.answer(text, reply_markup=get_admin_main_menu())


@router.message(F.text == "📋 Tovarlar ro'yxati")
async def show_products_list(message: Message):
    """Tovarlar ro'yxati"""
    products = db.get_all_products()

    if not products:
        await message.answer(config.MESSAGES['no_products'])
        return

    await message.answer(
        f"📋 Jami tovarlar: {len(products)}\n\n"
        "Tovarni tanlang:",
        reply_markup=get_products_list_keyboard(products)
    )


@router.callback_query(F.data.startswith("admin_product:"))
async def show_product_detail(callback: CallbackQuery):
    """Tovar tafsilotlari"""
    product_id = int(callback.data.split(":")[1])
    product = db.get_product(product_id)

    if not product:
        await callback.answer("❌ Tovar topilmadi", show_alert=True)
        return

    text = f"""
📦 <b>{product['name']}</b>

📂 <b>Kategoriya:</b> {product['category']}
💰 <b>Narxi:</b> {product['price']:,.0f} so'm
"""

    if product.get('size'):
        text += f"📏 <b>O'lcham/Rang:</b> {product['size']}\n"

    if product.get('description'):
        text += f"\n📝 <b>Tavsif:</b>\n{product['description']}\n"

    text += f"\n📊 <b>Status:</b> {'✅ Mavjud' if product['is_available'] else '❌ Mavjud emas'}"
    text += f"\n🆔 <b>ID:</b> {product['id']}"
    text += f"\n📅 <b>Qo'shilgan:</b> {product['created_at']}"

    if product.get('photo_id'):
        try:
            await callback.message.delete()
            await callback.bot.send_photo(
                chat_id=callback.message.chat.id,
                photo=product['photo_id'],
                caption=text,
                reply_markup=get_product_manage_keyboard(product_id)
            )
        except Exception:
            await callback.message.edit_text(
                text,
                reply_markup=get_product_manage_keyboard(product_id)
            )
    else:
        await callback.message.edit_text(
            text,
            reply_markup=get_product_manage_keyboard(product_id)
        )

    await callback.answer()


@router.callback_query(F.data.startswith("admin_toggle:"))
async def toggle_availability(callback: CallbackQuery):
    """Mavjudlikni o'zgartirish"""
    product_id = int(callback.data.split(":")[1])
    db.toggle_product_availability(product_id)

    await callback.answer("✅ Mavjudlik o'zgartirildi", show_alert=True)

    # Qayta ko'rsatish
    await show_product_detail(callback)


@router.callback_query(F.data.startswith("admin_delete:"))
async def confirm_delete_product(callback: CallbackQuery):
    """O'chirishni tasdiqlash"""
    product_id = int(callback.data.split(":")[1])
    product = db.get_product(product_id)

    if not product:
        await callback.answer("❌ Tovar topilmadi", show_alert=True)
        return

    try:
        await callback.message.delete()
    except:
        pass

    await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text=f"⚠️ <b>O'chirish tasdigi</b>\n\n"
             f"Haqiqatan ham \"{product['name']}\" tovarini o'chirmoqchimisiz?\n\n"
             f"Bu amalni qaytarib bo'lmaydi!",
        reply_markup=get_confirm_delete_keyboard(product_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_confirm_delete:"))
async def delete_product(callback: CallbackQuery):
    """Tovarni o'chirish"""
    product_id = int(callback.data.split(":")[1])
    product = db.get_product(product_id)
    product_name = product['name'] if product else "Noma'lum"

    # O'chirish
    db.delete_product(product_id)

    await callback.message.edit_text(
        f"✅ {config.MESSAGES['product_deleted']}\n\n"
        f"📦 {product_name}"
    )

    await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text="Admin panel:",
        reply_markup=get_admin_main_menu()
    )
    await callback.answer("🗑 O'chirildi", show_alert=True)


@router.callback_query(F.data == "admin_products_list")
async def back_to_products_list(callback: CallbackQuery):
    """Tovarlar ro'yxatiga qaytish"""
    products = db.get_all_products()

    await callback.message.delete()
    await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text=f"📋 Jami tovarlar: {len(products)}\n\nTovarni tanlang:",
        reply_markup=get_products_list_keyboard(products)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_page:"))
async def change_page(callback: CallbackQuery):
    """Sahifani o'zgartirish"""
    page = int(callback.data.split(":")[1])
    products = db.get_all_products()

    await callback.message.edit_text(
        f"📋 Jami tovarlar: {len(products)}\n\nTovarni tanlang:",
        reply_markup=get_products_list_keyboard(products, page)
    )
    await callback.answer()


# TAHRIRLASH - yangi
@router.callback_query(F.data.startswith("admin_edit:"))
async def edit_product_start(callback: CallbackQuery):
    """Tahrirlashni boshlash - xabar yuborish"""
    product_id = int(callback.data.split(":")[1])

    await callback.answer(
        "✏️ Tahrirlash funksiyasi hozircha ishlab chiqilmoqda.\n\n"
        "Hozircha tovarni o'chirib, qaytadan qo'shishingiz mumkin.",
        show_alert=True
    )