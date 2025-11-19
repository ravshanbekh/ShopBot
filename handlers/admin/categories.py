"""
Admin kategoriya boshqaruvi
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import config
from keyboars.admin_kb import get_categories_admin_keyboard, get_category_manage_keyboard, get_admin_main_menu
from database.json_db import db
from middlewares.admin_check import AdminFilter

router = Router()
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


class AddCategory(StatesGroup):
    """Kategoriya qo'shish holati"""
    name = State()


class EditCategory(StatesGroup):
    """Kategoriyani tahrirlash holati"""
    old_name = State()
    new_name = State()


@router.message(F.text == "📂 Kategoriyalar")
async def categories_menu(message: Message):
    """Kategoriyalar menyusi"""
    categories = db.get_categories()

    text = f"""
📂 <b>KATEGORIYALAR BOSHQARUVI</b>

Jami kategoriyalar: {len(categories)}

Kategoriyani tanlang yoki yangi qo'shing:
    """

    await message.answer(
        text,
        reply_markup=get_categories_admin_keyboard(categories, action="manage")
    )


@router.callback_query(F.data == "admin_categories_menu")
async def categories_menu_callback(callback: CallbackQuery):
    """Kategoriyalar menyusiga qaytish"""
    categories = db.get_categories()

    text = f"""
📂 <b>KATEGORIYALAR BOSHQARUVI</b>

Jami kategoriyalar: {len(categories)}

Kategoriyani tanlang yoki yangi qo'shing:
    """

    await callback.message.edit_text(
        text,
        reply_markup=get_categories_admin_keyboard(categories, action="manage")
    )
    await callback.answer()


@router.callback_query(F.data == "admin_add_category")
async def start_add_category(callback: CallbackQuery, state: FSMContext):
    """Kategoriya qo'shishni boshlash"""
    await state.set_state(AddCategory.name)

    await callback.message.edit_text(
        "➕ <b>Yangi kategoriya qo'shish</b>\n\n"
        "Kategoriya nomini kiriting:\n\n"
        "Masalan: 🎮 O'yinchoqlar"
    )
    await callback.answer()


@router.message(AddCategory.name)
async def input_category_name(message: Message, state: FSMContext):
    """Kategoriya nomini kiritish"""
    category_name = message.text.strip()

    if len(category_name) < 2:
        await message.answer("❌ Kategoriya nomi kamida 2 ta belgidan iborat bo'lishi kerak:")
        return

    # Kategoriyani qo'shish
    success = db.add_category(category_name)

    if success:
        await message.answer(
            f"{config.MESSAGES['category_added']}\n\n"
            f"📂 {category_name}",
            reply_markup=get_admin_main_menu()
        )
    else:
        await message.answer(
            "❌ Bu kategoriya allaqachon mavjud!",
            reply_markup=get_admin_main_menu()
        )

    await state.clear()


@router.callback_query(F.data.startswith("admin_manage_category:"))
async def manage_category(callback: CallbackQuery):
    """Kategoriyani boshqarish"""
    category = callback.data.split(":", 1)[1]

    # Kategoriyada nechta tovar borligini aniqlash
    products = db.get_products_by_category(category)
    products_count = len(products)

    text = f"""
📂 <b>{category}</b>

📦 Tovarlar soni: {products_count}

Quyidagi amallarni bajarish mumkin:
    """

    await callback.message.edit_text(
        text,
        reply_markup=get_category_manage_keyboard(category)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_edit_category:"))
async def start_edit_category(callback: CallbackQuery, state: FSMContext):
    """Kategoriya nomini o'zgartirishni boshlash"""
    category = callback.data.split(":", 1)[1]

    await state.set_state(EditCategory.new_name)
    await state.update_data(old_name=category)

    await callback.message.edit_text(
        f"✏️ <b>Kategoriya nomini o'zgartirish</b>\n\n"
        f"Eski nom: {category}\n\n"
        "Yangi nomni kiriting:"
    )
    await callback.answer()


@router.message(EditCategory.new_name)
async def input_new_category_name(message: Message, state: FSMContext):
    """Yangi kategoriya nomini kiritish"""
    new_name = message.text.strip()

    if len(new_name) < 2:
        await message.answer("❌ Kategoriya nomi kamida 2 ta belgidan iborat bo'lishi kerak:")
        return

    data = await state.get_data()
    old_name = data['old_name']

    # Kategoriyani yangilash
    success = db.update_category(old_name, new_name)

    if success:
        await message.answer(
            f"✅ Kategoriya o'zgartirildi!\n\n"
            f"Eski: {old_name}\n"
            f"Yangi: {new_name}",
            reply_markup=get_admin_main_menu()
        )
    else:
        await message.answer(
            "❌ Xatolik yuz berdi!",
            reply_markup=get_admin_main_menu()
        )

    await state.clear()


@router.callback_query(F.data.startswith("admin_confirm_delete_category:"))
async def confirm_delete_category(callback: CallbackQuery):
    """Kategoriyani o'chirishni tasdiqlash"""
    category = callback.data.split(":", 1)[1]

    # Kategoriyada nechta tovar borligini aniqlash
    products = db.get_products_by_category(category)
    products_count = len(products)

    # O'chirish
    success = db.delete_category(category)

    if success:
        warning = f"\n\n⚠️ {products_count} ta tovar ham o'chirildi!" if products_count > 0 else ""
        await callback.message.edit_text(
            f"{config.MESSAGES['category_deleted']}\n\n"
            f"📂 {category}{warning}"
        )
        await callback.answer("🗑 O'chirildi", show_alert=True)

        # Kategoriyalar menyusiga qaytish
        categories = db.get_categories()
        await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            text=f"📂 Jami kategoriyalar: {len(categories)}",
            reply_markup=get_categories_admin_keyboard(categories, action="manage")
        )
    else:
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)