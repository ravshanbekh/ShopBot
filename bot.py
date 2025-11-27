"""
Telegram Shop Bot - Asosiy fayl
"""

import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

import config
from handlers.user import start, catalog, order
from handlers.admin import panel, products, categories, broadcast
from middlewares.admin_check import AdminCheckMiddleware
from utils.schedular import setup_scheduler

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    """Bot ishga tushganda"""
    logger.info("Bot ishga tushmoqda...")

    # Adminga xabar
    for admin_id in config.ADMINS:
        try:
            await bot.send_message(
                admin_id,
                "🤖 <b>Bot ishga tushdi!</b>\n\n"
                "✅ Barcha funksiyalar faol"
            )
        except Exception as e:
            logger.error(f"Adminga xabar yuborishda xatolik: {e}")

    logger.info("Bot muvaffaqiyatli ishga tushdi!")


async def on_shutdown(bot: Bot):
    """Bot to'xtaganda"""
    logger.info("Bot to'xtatilmoqda...")

    # Adminga xabar
    for admin_id in config.ADMINS:
        try:
            await bot.send_message(
                admin_id,
                "🤖 <b>Bot to'xtatildi</b>"
            )
        except Exception as e:
            logger.error(f"Adminga xabar yuborishda xatolik: {e}")

    logger.info("Bot to'xtatildi")


async def main():
    """Asosiy funksiya"""
    # Bot va Dispatcher yaratish
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Middlewares qo'shish
    dp.message.middleware(AdminCheckMiddleware())
    dp.callback_query.middleware(AdminCheckMiddleware())

    # Routerlarni ro'yxatdan o'tkazish
    # User handlerlar
    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(order.router)

    # Admin handlerlar
    dp.include_router(panel.router)
    dp.include_router(products.router)
    dp.include_router(categories.router)
    dp.include_router(broadcast.router)

    # Startup va shutdown handlerlar
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Scheduler ishga tushirish
    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("Scheduler ishga tushdi")

    # Polling rejimida ishga tushirish
    try:
        logger.info("Polling boshlandi...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot to'xtatildi (KeyboardInterrupt)")
    except Exception as e:
        logger.error(f"Bot ishida xatolik: {e}")