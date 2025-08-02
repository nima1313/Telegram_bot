import asyncio
import logging
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import redis.asyncio as redis

from config.settings import settings
from middlewares.database import DatabaseMiddleware
from handlers import start, supplier, demander
from database.models import Base
from database.connection import engine

# تنظیم لاگینگ
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def on_startup(bot: Bot):
    """عملیات هنگام شروع ربات"""
    # ایجاد جداول دیتابیس
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Bot started successfully!")

async def on_shutdown(bot: Bot):
    """عملیات هنگام خاموش شدن ربات"""
    logger.info("Bot shutting down...")

async def main():
    """تابع اصلی برای راه‌اندازی ربات"""
    # ایجاد bot و dispatcher
    bot = Bot(token=settings.bot_token)
    
    # تنظیم storage برای FSM
    redis_client = await redis.from_url(settings.redis_url)
    storage = RedisStorage(redis=redis_client)
    
    dp = Dispatcher(storage=storage)
    
    # اضافه کردن middleware
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    
    # اضافه کردن routers
    dp.include_router(start.router)
    dp.include_router(supplier.router)
    dp.include_router(demander.router)
    
    # تنظیم startup و shutdown
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # شروع polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
