"""
Tovarlar katalogi handleri - To'liq versiya
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import config
from keyboars.user_kb import (
    get_categories_keyboard,
    get_products_keyboard,
    get_product_detail_keyboard
)
from database.json_db import db

router = Router()


@router.message(F.text == "🛍 Tovarlar")
async def show_categories(message: Message, state: FSMContext):
    """
    Kategoriyalarni ko'rsatish
    Asosiy menyudan "Tovarlar" tugmasi bosilganda
    """
    # Holatni tozalash
    await state.clear()

    # Kategoriyalarni olish
    categories = db.get_categories()

    if not categories:
        await message.answer(
            "📭 <b>Kategoriyalar mavjud emas</b>\n\n"
            "Hozircha kategoriyalar qo'shilmagan.\n"
            "Keyinroq qaytib ko'ring!"
        )
        return

    # Kategoriyalar sonini hisoblash
    await message.answer(
        f"📂 <b>Kategoriyalar</b> ({len(categories)} ta)\n\n"
        "Qiziqtirgan kategoriyani tanlang:",
        reply_markup=get_categories_keyboard(categories)
    )


@router.callback_query(F.data.startswith("category:"))
async def show_products_in_category(callback: CallbackQuery, state: FSMContext):
    """
    Tanlangan kategoriya ichidagi tovarlarni ko'rsatish
    """
    # Kategoriya nomini ajratib olish
    category = callback.data.split(":", 1)[1]

    # Kategoriya bo'yicha tovarlarni olish
    products = db.get_products_by_category(category)

    if not products:
        await callback.answer(
            f"❌ {category} kategoriyasida hozircha tovarlar yo'q.\n\n"
            "Boshqa kategoriyalarni ko'rib chiqing!",
            show_alert=True
        )
        return

    # Holatda kategoriyani saqlash (orqaga qaytish uchun)
    await state.update_data(current_category=category)

    # Tovarlar ro'yxatini ko'rsatish
    await callback.message.edit_text(
        f"📦 <b>{category}</b> ({len(products)} ta tovar)\n\n"
        "Quyidagi tovarlardan birini tanlang:",
        reply_markup=get_products_keyboard(products, category)
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery, state: FSMContext):
    """
    Kategoriyalar ro'yxatiga qaytish
    """
    # Holatni tozalash
    await state.clear()

    # Kategoriyalarni olish
    categories = db.get_categories()

    await callback.message.edit_text(
        f"📂 <b>Kategoriyalar</b> ({len(categories)} ta)\n\n"
        "Qiziqtirgan kategoriyani tanlang:",
        reply_markup=get_categories_keyboard(categories)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("product:"))
async def show_product_detail(callback: CallbackQuery, state: FSMContext):
    """
    Tovar tafsilotlarini ko'rsatish
    """
    # Tovar ID ni olish
    product_id = int(callback.data.split(":")[1])

    # Tovarni bazadan olish
    product = db.get_product(product_id)

    if not product:
        await callback.answer(
            "❌ Tovar topilmadi yoki o'chirilgan",
            show_alert=True
        )
        return

    # Tovar haqida batafsil ma'lumot tayyorlash
    caption = f"""
<b>📦 {product['name']}</b>

━━━━━━━━━━━━━━━━━━━━

📂 <b>Kategoriya:</b> {product['category']}
💰 <b>Narx:</b> {product['price']:,.0f} so'm
"""

    # O'lcham/Rang mavjud bo'lsa
    if product.get('size'):
        caption += f"📏 <b>O'lcham/Rang:</b> {product['size']}\n"

    # Tavsif mavjud bo'lsa
    if product.get('description'):
        caption += f"\n📝 <b>Tavsif:</b>\n{product['description']}\n"

    # Mavjudlik holati
    caption += f"\n━━━━━━━━━━━━━━━━━━━━\n\n"
    if product.get('is_available', True):
        caption += "✅ <b>Mavjud</b>"
    else:
        caption += "❌ <b>Hozirda mavjud emas</b>"

    # Holatda tovar ID ni saqlash
    await state.update_data(current_product_id=product_id)

    # Agar tovar rasmi bo'lsa
    if product.get('photo_id'):
        try:
            # Eski xabarni o'chirish
            await callback.message.delete()

            # Yangi xabar rasm bilan yuborish
            await callback.bot.send_photo(
                chat_id=callback.message.chat.id,
                photo=product['photo_id'],
                caption=caption,
                reply_markup=get_product_detail_keyboard(
                    product_id,
                    product.get('is_available', True)
                )
            )
        except Exception as e:
            # Agar rasm topilmasa, matn yuborish
            print(f"Rasm yuborishda xatolik: {e}")
            await callback.message.edit_text(
                caption,
                reply_markup=get_product_detail_keyboard(
                    product_id,
                    product.get('is_available', True)
                )
            )
    else:
        # Rasm bo'lmasa, faqat matn
        await callback.message.edit_text(
            caption,
            reply_markup=get_product_detail_keyboard(
                product_id,
                product.get('is_available', True)
            )
        )

    await callback.answer()


@router.callback_query(F.data == "product_unavailable")
async def product_unavailable_alert(callback: CallbackQuery):
    """
    Mavjud bo'lmagan tovar haqida ogohlantirish
    """
    await callback.answer(
        "❌ Bu tovar hozirda mavjud emas\n\n"
        "Keyinroq qaytib ko'ring yoki boshqa tovarlarni ko'rib chiqing.",
        show_alert=True
    )


@router.callback_query(F.data == "back_to_products")
async def back_to_products(callback: CallbackQuery, state: FSMContext):
    """
    Tovarlar ro'yxatiga qaytish
    """
    # Holatdan kategoriyani olish
    data = await state.get_data()
    category = data.get('current_category')

    if category:
        # Kategoriya ma'lum bo'lsa, o'sha kategoriya tovarlarini ko'rsatish
        products = db.get_products_by_category(category)

        # Eski xabarni o'chirish
        await callback.message.delete()

        # Yangi xabar yuborish
        await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            text=f"📦 <b>{category}</b> ({len(products)} ta tovar)\n\n"
                 "Quyidagi tovarlardan birini tanlang:",
            reply_markup=get_products_keyboard(products, category)
        )
    else:
        # Kategoriya noma'lum bo'lsa, kategoriyalar ro'yxatiga qaytish
        categories = db.get_categories()

        await callback.message.delete()

        await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            text=f"📂 <b>Kategoriyalar</b> ({len(categories)} ta)\n\n"
                 "Qiziqtirgan kategoriyani tanlang:",
            reply_markup=get_categories_keyboard(categories)
        )

    await callback.answer()


@router.message(F.text == "🔎 Qidirish")
async def search_products(message: Message, state: FSMContext):
    """
    Tovar qidirish funksiyasi
    Hozircha oddiy versiya, keyinchalik kengaytiriladi
    """
    await message.answer(
        "🔍 <b>Qidirish funksiyasi</b>\n\n"
        "Bu funksiya hozircha ishlab chiqilmoqda...\n\n"
        "Hozircha tovarlarni kategoriya bo'yicha ko'rishingiz mumkin:\n"
        "🛍 Tovarlar → Kategoriya tanlang\n\n"
        "Tez orada qidirish ham qo'shiladi! 🚀"
    )


@router.callback_query(F.data == "back_to_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """
    Asosiy menyuga qaytish
    """
    from keyboars.user_kb import get_main_menu

    # Holatni tozalash
    await state.clear()

    # Xabarni o'chirish
    await callback.message.delete()

    # Asosiy menyu
    await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text="Asosiy menyu:",
        reply_markup=get_main_menu()
    )
    await callback.answer()