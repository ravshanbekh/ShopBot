"""
Avtomatik post qilish scheduler - To'liq versiya
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import config
from database.json_db import db
import logging

logger = logging.getLogger(__name__)


async def post_random_products(bot: Bot):
    """
    Random tovarlarni kanalga va guruhga post qilish
    Bu funksiya schedulerdan avtomatik chaqiriladi
    """
    try:
        logger.info(f"[{datetime.now()}] Avtomatik post boshlandi...")

        # Random tovarlarni olish
        products = db.get_random_products(count=config.DAILY_POSTS_COUNT)

        if not products:
            logger.warning(f"[{datetime.now()}] Tovarlar topilmadi!")
            return

        logger.info(f"[{datetime.now()}] {len(products)} ta tovar tanlandi")

        # Bot username olish
        bot_info = await bot.get_me()
        bot_username = bot_info.username

        # Har bir tovarni post qilish
        for idx, product in enumerate(products, 1):
            try:
                # Tovar haqida caption tayyorlash
                caption = f"""
🛍 <b>{product['name']}</b>

📂 <b>Kategoriya:</b> {product['category']}
💰 <b>Narx:</b> {product['price']:,.0f} so'm
"""

                if product.get('size'):
                    caption += f"📏 <b>O'lcham/Rang:</b> {product['size']}\n"

                if product.get('description'):
                    caption += f"\n📝 <b>Tavsif:</b>\n{product['description']}\n"

                caption += f"\n✅ Buyurtma berish uchun botga o'ting: @{bot_username}"

                # Inline klaviatura yaratish - DEEP LINK
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="🛒 Buyurtma berish",
                        url=f"https://t.me/{bot_username}?start=order_{product['id']}"
                    )]
                ])

                # Kanalga yuborish
                if config.CHANNEL_ID:
                    try:
                        if product.get('photo_id'):
                            await bot.send_photo(
                                chat_id=config.CHANNEL_ID,
                                photo=product['photo_id'],
                                caption=caption,
                                reply_markup=keyboard
                            )
                        else:
                            await bot.send_message(
                                chat_id=config.CHANNEL_ID,
                                text=caption,
                                reply_markup=keyboard
                            )

                        logger.info(f"[{datetime.now()}] ✅ Tovar #{idx} kanalga yuborildi: {product['name']}")

                    except Exception as e:
                        logger.error(f"[{datetime.now()}] ❌ Kanalga yuborishda xatolik: {e}")

                # Guruhga yuborish
                if hasattr(config, 'GROUP_ID') and config.GROUP_ID and config.GROUP_ID != config.CHANNEL_ID:
                    try:
                        if product.get('photo_id'):
                            await bot.send_photo(
                                chat_id=config.GROUP_ID,
                                photo=product['photo_id'],
                                caption=caption,
                                reply_markup=keyboard
                            )
                        else:
                            await bot.send_message(
                                chat_id=config.GROUP_ID,
                                text=caption,
                                reply_markup=keyboard
                            )

                        logger.info(f"[{datetime.now()}] ✅ Tovar #{idx} guruhga yuborildi: {product['name']}")

                    except Exception as e:
                        logger.error(f"[{datetime.now()}] ❌ Guruhga yuborishda xatolik: {e}")

            except Exception as e:
                logger.error(f"[{datetime.now()}] ❌ Tovar post qilishda xatolik: {e}")

        logger.info(f"[{datetime.now()}] ✅ Avtomatik post muvaffaqiyatli yakunlandi! {len(products)} ta tovar yuborildi")

    except Exception as e:
        logger.error(f"[{datetime.now()}] ❌ Scheduler xatolik: {e}")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """
    Schedulerni sozlash va ishga tushirish

    Args:
        bot: Aiogram Bot obyekti

    Returns:
        AsyncIOScheduler: Sozlangan scheduler
    """
    # Scheduler yaratish
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")

    logger.info("=" * 50)
    logger.info("📅 SCHEDULER SOZLANMOQDA...")
    logger.info("=" * 50)

    # Har bir vaqt uchun task qo'shish
    for time_str in config.AUTO_POST_TIMES:
        try:
            # Vaqtni ajratish
            hour, minute = map(int, time_str.split(':'))

            # Schedulerga qo'shish
            scheduler.add_job(
                post_random_products,
                trigger=CronTrigger(hour=hour, minute=minute, timezone="Asia/Tashkent"),
                args=[bot],
                id=f"auto_post_{time_str.replace(':', '_')}",
                replace_existing=True,
                name=f"Avtomatik post - {time_str}"
            )

            logger.info(f"✅ Scheduler qo'shildi: {time_str} (har kuni)")

        except Exception as e:
            logger.error(f"❌ Scheduler qo'shishda xatolik ({time_str}): {e}")

    logger.info("=" * 50)
    logger.info(f"📊 Jami {len(config.AUTO_POST_TIMES)} ta avtomatik post sozlandi")
    logger.info(f"📦 Har bir post: {config.DAILY_POSTS_COUNT} ta random tovar")
    logger.info("=" * 50)

    return scheduler