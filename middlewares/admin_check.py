"""
Admin tekshirish middleware va filtri - To'liq versiya
"""

from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery, TelegramObject
import config
import logging

logger = logging.getLogger(__name__)


class AdminFilter(Filter):
    """
    Admin ekanligini tekshiruvchi filtr
    Bu filtrni handlerga qo'llash orqali faqat adminlar uchun ishlashini ta'minlash mumkin

    Foydalanish:
        router.message.filter(AdminFilter())

        @router.message(Command("admin"))
        async def admin_panel(message: Message):
            # Faqat adminlar bu handlerga kiradi
            pass
    """

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        """
        Foydalanuvchi admin ekanligini tekshirish

        Args:
            event: Message yoki CallbackQuery

        Returns:
            bool: Admin bo'lsa True, aks holda False
        """
        if not event.from_user:
            return False

        user_id = event.from_user.id
        is_admin = user_id in config.ADMINS

        if not is_admin and isinstance(event, Message):
            # Agar admin bo'lmasa va message bo'lsa, ogohlantirish
            logger.warning(
                f"⚠️ Admin emas foydalanuvchi admin buyrug'ini ishlatishga urinmoqda: "
                f"user_id={user_id}, username=@{event.from_user.username}"
            )

        return is_admin


class AdminCheckMiddleware(BaseMiddleware):
    """
    Admin huquqlarini tekshiruvchi middleware
    Bu middleware har bir xabar yoki callback uchun ishlaydi
    va data ga is_admin flag qo'shadi

    Foydalanish:
        dp.message.middleware(AdminCheckMiddleware())
        dp.callback_query.middleware(AdminCheckMiddleware())

        @router.message()
        async def some_handler(message: Message, is_admin: bool):
            if is_admin:
                await message.answer("Siz adminsiz!")
            else:
                await message.answer("Siz oddiy foydalanuvchisiz")
    """

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        """
        Middleware asosiy funksiyasi

        Args:
            handler: Keyingi handler
            event: Telegram event (Message, CallbackQuery, etc.)
            data: Handler uchun ma'lumotlar

        Returns:
            Any: Handler natijasi
        """
        # User ID ni olish va admin ekanligini tekshirish
        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id
            username = event.from_user.username or "username_yo'q"
            first_name = event.from_user.first_name or ""

            # Admin ekanligini aniqlash
            is_admin = user_id in config.ADMINS

            # Data ga qo'shish
            data['is_admin'] = is_admin
            data['user_id'] = user_id
            data['username'] = username

            # Logging
            event_type = "Message" if isinstance(event, Message) else "Callback"
            admin_status = "👨‍💼 Admin" if is_admin else "👤 User"

            if isinstance(event, Message) and event.text:
                logger.debug(
                    f"{admin_status} | {event_type} | "
                    f"user_id={user_id} | @{username} | "
                    f"text='{event.text[:50]}...'"
                )
            elif isinstance(event, CallbackQuery):
                logger.debug(
                    f"{admin_status} | {event_type} | "
                    f"user_id={user_id} | @{username} | "
                    f"data='{event.data}'"
                )

        # Keyingi handlerga o'tish
        return await handler(event, data)


def is_admin(user_id: int) -> bool:
    """
    Utility funksiya - foydalanuvchi admin ekanligini tekshirish

    Args:
        user_id: Telegram user ID

    Returns:
        bool: Admin bo'lsa True

    Example:
        if is_admin(message.from_user.id):
            await message.answer("Siz adminsiz!")
    """
    return user_id in config.ADMINS


async def check_admin_access(event: Message | CallbackQuery) -> bool:
    """
    Async funksiya - admin dostupini tekshirish va xabar yuborish

    Args:
        event: Message yoki CallbackQuery

    Returns:
        bool: Admin bo'lsa True

    Example:
        if not await check_admin_access(message):
            return
        # Admin kodi davom etadi
    """
    user_id = event.from_user.id

    if user_id not in config.ADMINS:
        if isinstance(event, Message):
            await event.answer(
                "⚠️ Bu buyruq faqat adminlar uchun!\n\n"
                "Agar admin bo'lishni istasangiz, bot egasi bilan bog'laning."
            )
        else:  # CallbackQuery
            await event.answer(
                "⚠️ Bu funksiya faqat adminlar uchun!",
                show_alert=True
            )
        return False

    return True