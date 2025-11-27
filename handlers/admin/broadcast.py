"""
Admin - Barcha foydalanuvchilarga xabar yuborish
"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio

from keyboars.admin_kb import get_admin_main_menu
from database.json_db import db
from middlewares.admin_check import AdminFilter

router = Router()
router.message.filter(AdminFilter())


class BroadcastState(StatesGroup):
    """Xabar yuborish holati"""
    waiting_for_message = State()


@router.message(F.text == "✉️ Xabar yuborish")
async def start_broadcast(message: Message, state: FSMContext):
    """Xabar yuborishni boshlash"""
    await state.set_state(BroadcastState.waiting_for_message)

    users_count = db.get_users_count()

    await message.answer(
        f"📢 <b>Xabar yuborish</b>\n\n"
        f"👥 Foydalanuvchilar: {users_count}\n\n"
        "Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yuboring:\n\n"
        "• Matn\n"
        "• Rasm + matn\n"
        "• Video\n"
        "• va boshqalar\n\n"
        "❌ Bekor qilish: /cancel"
    )


@router.message(BroadcastState.waiting_for_message, F.text == "/cancel")
async def cancel_broadcast(message: Message, state: FSMContext):
    """Bekor qilish"""
    await state.clear()
    await message.answer(
        "❌ Xabar yuborish bekor qilindi",
        reply_markup=get_admin_main_menu()
    )


@router.message(BroadcastState.waiting_for_message)
async def process_broadcast(message: Message, state: FSMContext):
    """Xabarni barcha userlarga yuborish"""
    users = db.get_all_users()

    if not users:
        await message.answer("❌ Foydalanuvchilar yo'q")
        await state.clear()
        return

    # Yuborish jarayonini boshlash
    status_msg = await message.answer(
        f"📤 Xabar yuborilmoqda...\n\n"
        f"Jami: {len(users)}\n"
        f"Yuborildi: 0\n"
        f"Xatolik: 0"
    )

    success_count = 0
    error_count = 0

    for i, user in enumerate(users):
        try:
            # Xabarni nusxalash (copy_to)
            await message.copy_to(user['user_id'])
            success_count += 1

            # Har 10 ta foydalanuvchidan keyin statusni yangilash
            if (i + 1) % 10 == 0 or (i + 1) == len(users):
                try:
                    await status_msg.edit_text(
                        f"📤 Xabar yuborilmoqda...\n\n"
                        f"Jami: {len(users)}\n"
                        f"Yuborildi: {success_count}\n"
                        f"Xatolik: {error_count}\n"
                        f"Jarayon: {((i+1)/len(users)*100):.1f}%"
                    )
                except:
                    pass

            # Telegram limitlarini hurmat qilish
            await asyncio.sleep(0.05)  # 50ms kutish

        except Exception as e:
            error_count += 1
            print(f"Xabar yuborishda xatolik ({user['user_id']}): {e}")

    # Yakuniy natija
    await state.clear()

    try:
        await status_msg.edit_text(
            f"✅ <b>Xabar yuborish yakunlandi!</b>\n\n"
            f"📊 Natijalar:\n"
            f"• Jami foydalanuvchilar: {len(users)}\n"
            f"• ✅ Muvaffaqiyatli: {success_count}\n"
            f"• ❌ Xatolik: {error_count}"
        )
    except:
        pass

    await message.answer(
        "Asosiy menyu:",
        reply_markup=get_admin_main_menu()
    )