"""
Admin panel asosiy handlerlari
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import config
from keyboars.admin_kb import get_admin_main_menu, get_orders_list_keyboard, get_order_status_keyboard
from keyboars.user_kb import get_main_menu
from database.json_db import db
from middlewares.admin_check import AdminFilter

router = Router()
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


@router.message(Command("admin"))
async def admin_panel(message: Message, state: FSMContext):
    """Admin panelga kirish"""
    await state.clear()
    await message.answer(
        f"{config.MESSAGES['admin_panel']}\n\n"
        "Quyidagi funksiyalardan foydalaning:",
        reply_markup=get_admin_main_menu()
    )


@router.message(F.text == "👤 Foydalanuvchi rejimi")
async def user_mode(message: Message, state: FSMContext):
    """Foydalanuvchi rejimiga qaytish"""
    await state.clear()
    await message.answer(
        "👤 Foydalanuvchi rejimiga qaytdingiz",
        reply_markup=get_main_menu()
    )


@router.message(F.text == "📊 Statistika")
async def show_statistics(message: Message):
    """Statistika ko'rsatish"""
    products = db.get_all_products()
    available_products = db.get_available_products()
    orders = db.get_all_orders()
    users_count = db.get_users_count()
    categories = db.get_categories()

    # Statuslar bo'yicha buyurtmalar
    new_orders = len([o for o in orders if o['status'] == 'yangi'])
    confirmed_orders = len([o for o in orders if o['status'] == 'tasdiqlandi'])
    delivering_orders = len([o for o in orders if o['status'] == 'yetkazilmoqda'])
    delivered_orders = len([o for o in orders if o['status'] == 'yetkazildi'])
    cancelled_orders = len([o for o in orders if o['status'] == 'bekor'])

    stats_text = f"""
📊 <b>STATISTIKA</b>

📦 <b>Tovarlar:</b>
• Jami: {len(products)}
• Mavjud: {len(available_products)}
• Mavjud emas: {len(products) - len(available_products)}

📂 <b>Kategoriyalar:</b> {len(categories)}

🛒 <b>Buyurtmalar:</b>
• Jami: {len(orders)}
• 🆕 Yangi: {new_orders}
• ✅ Tasdiqlangan: {confirmed_orders}
• 🚚 Yetkazilmoqda: {delivering_orders}
• ✔️ Yetkazilgan: {delivered_orders}
• ❌ Bekor qilingan: {cancelled_orders}

👥 <b>Foydalanuvchilar:</b> {users_count}
    """

    await message.answer(stats_text)


@router.message(F.text == "📦 Buyurtmalar")
async def show_orders(message: Message):
    """Buyurtmalar ro'yxatini ko'rsatish"""
    orders = db.get_all_orders()

    if not orders:
        await message.answer("📭 Buyurtmalar yo'q")
        return

    await message.answer(
        f"📦 Jami buyurtmalar: {len(orders)}\n\n"
        "Buyurtmani tanlang:",
        reply_markup=get_orders_list_keyboard(orders)
    )


@router.callback_query(F.data.startswith("admin_order:"))
async def show_order_detail(callback: CallbackQuery):
    """Buyurtma tafsilotlari"""
    order_id = int(callback.data.split(":")[1])
    order = db.get_order(order_id)

    if not order:
        await callback.answer("❌ Buyurtma topilmadi", show_alert=True)
        return

    product = db.get_product(order['product_id'])
    total_price = product['price'] * order['quantity']

    status_emoji = {
        'yangi': '🆕',
        'tasdiqlandi': '✅',
        'yetkazilmoqda': '🚚',
        'yetkazildi': '✔️',
        'bekor': '❌'
    }.get(order['status'], '❓')

    order_text = f"""
{status_emoji} <b>BUYURTMA TAFSILOTLARI</b>

📋 <b>Raqami:</b> {order['order_number']}
📅 <b>Sana:</b> {order['created_at']}
📊 <b>Status:</b> {order['status'].capitalize()}

📦 <b>Tovar:</b> {product['name']}
💰 <b>Narxi:</b> {product['price']:,.0f} so'm
🔢 <b>Miqdor:</b> {order['quantity']}
💵 <b>Jami:</b> {total_price:,.0f} so'm

👤 <b>Mijoz:</b> {order['customer_name']}
📱 <b>Telefon:</b> {order['phone']}
📍 <b>Manzil:</b> {order['address']}

🆔 <b>User ID:</b> {order['user_id']}
👤 <b>Username:</b> @{order['username']}
    """

    if product.get('photo_id'):
        try:
            await callback.message.delete()
            await callback.bot.send_photo(
                chat_id=callback.message.chat.id,
                photo=product['photo_id'],
                caption=order_text,
                reply_markup=get_order_status_keyboard(order_id)
            )
        except Exception:
            await callback.message.edit_text(
                order_text,
                reply_markup=get_order_status_keyboard(order_id)
            )
    else:
        await callback.message.edit_text(
            order_text,
            reply_markup=get_order_status_keyboard(order_id)
        )

    await callback.answer()


@router.callback_query(F.data.startswith("admin_order_status:"))
async def change_order_status(callback: CallbackQuery):
    """Buyurtma statusini o'zgartirish"""
    parts = callback.data.split(":")
    order_id = int(parts[1])
    new_status = parts[2]

    db.update_order_status(order_id, new_status)

    order = db.get_order(order_id)

    # Mijozga xabar yuborish
    status_messages = {
        'tasdiqlandi': '✅ Buyurtmangiz tasdiqlandi! Tez orada yetkazib beriladi.',
        'yetkazilmoqda': '🚚 Buyurtmangiz yetkazib berilmoqda!',
        'yetkazildi': '✔️ Buyurtmangiz muvaffaqiyatli yetkazib berildi! Xaridingiz uchun rahmat!',
        'bekor': '❌ Buyurtmangiz bekor qilindi. Murojaat uchun rahmat!'
    }

    try:
        await callback.bot.send_message(
            chat_id=order['user_id'],
            text=f"📦 Buyurtma: <code>{order['order_number']}</code>\n\n" +
                 status_messages.get(new_status, f"Status o'zgartirildi: {new_status}")
        )
    except Exception as e:
        print(f"Mijozga xabar yuborishda xatolik: {e}")

    await callback.answer(f"✅ Status o'zgartirildi: {new_status}", show_alert=True)

    # Buyurtma tafsilotlarini qayta ko'rsatish
    await show_order_detail(callback)


@router.callback_query(F.data == "admin_orders")
async def back_to_orders(callback: CallbackQuery):
    """Buyurtmalar ro'yxatiga qaytish"""
    orders = db.get_all_orders()

    await callback.message.delete()
    await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text=f"📦 Jami buyurtmalar: {len(orders)}\n\nBuyurtmani tanlang:",
        reply_markup=get_orders_list_keyboard(orders)
    )
    await callback.answer()


@router.callback_query(F.data == "admin_cancel")
async def admin_cancel(callback: CallbackQuery, state: FSMContext):
    """Admin amalini bekor qilish"""
    await state.clear()
    await callback.message.delete()
    await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text="❌ Bekor qilindi",
        reply_markup=get_admin_main_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_menu")
async def back_to_admin_menu(callback: CallbackQuery, state: FSMContext):
    """Admin menyuga qaytish"""
    await state.clear()
    await callback.message.delete()
    await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text=config.MESSAGES['admin_panel'],
        reply_markup=get_admin_main_menu()
    )
    await callback.answer()