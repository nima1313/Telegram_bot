from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import User, Supplier, Demander, Request
from keyboards.inline import get_request_action_keyboard
import logging

logger = logging.getLogger(__name__)

async def notify_supplier_new_request(
    bot: Bot, 
    session: AsyncSession, 
    request: Request
):
    """ارسال نوتیفیکیشن به تأمین‌کننده برای درخواست جدید"""
    try:
        # دریافت اطلاعات تأمین‌کننده
        supplier = request.supplier
        user = supplier.user
        
        if not user.telegram_id:
            logger.warning(f"No telegram_id for supplier {supplier.id}")
            return
        
        # دریافت اطلاعات درخواست‌کننده
        demander = request.demander
        
        text = f"""
🔔 درخواست جدید

👤 از طرف: {demanderfull_name}
🏢 رکت: {demander.company_name or '-'}
📱 تمس: {demander.phone_number}

💬 یام:
{request.message}

📅 زمان: {reques.created_at.strftime('%Y/%m/%d %H:%M')}
"""
        
        await bot.send_message(
            chat_id=user.telegram_id,
            text=text,
            reply_markup=get_request_action_keyboard(request.id)
        )
        
    except Exception as e:
        logger.error(f"Error sending notification to supplier: {e}")

async def notify_demander_request_accepted(
    bot: Bot,
    session: AsyncSession,
    request: Request
):
    """ارسال نوتیفیکیشن به درخواست‌کننده برای پذیرش درخواست"""
    try:
        demander = request.demander
        user = demander.user
        supplier = request.supplier
        
        if not user.telegram_id:
            logger.warning(f"No telegram_id for demander {demander.id}")
            return
        
        text = f"""
✅ درخواست شما پذیرفته شد!

� تأمین‌کننده: {supplier.full_name}
📱 شماره ماس: {supplier.phone_number}
📍 مقعیت: {supplier.city} - {supplier.area}

برای هماهنگی جزئیات با ایشان تماس بگیرید.
"""
        
        if supplier.instagram_id:
            text += f"\n📷اینستاگرام: @{supplier.instagram_id}"
        
        if request.response_message:
            text += f"\n\n💬 پیا تأمین‌کننده:\n{request.response_message}"
        
        await bot.send_message(
            chat_id=user.telegram_id,
            text=text
        )
        
    except Exception as e:
        logger.error(f"Error sending notification to demander: {e}")

async def notify_demander_request_rejected(
    bot: Bot,
    session: AsyncSession,
    request: Request
):
    """ارسال نوتیفیکیشن به درخواست‌کننده برای رد درخواست"""
    try:
        demander = request.demander
        user = demander.user
        supplier = request.supplier
        
        if not user.telegram_id:
            logger.warning(f"No telegram_id for demander {demander.id}")
            return
        
        text = f"""
❌ متأسفانه درخواست شما رد شد.

🎭 تأین‌کننده: {supplier.full_name}

می‌توانید تأمین‌کننده دیگری را جستجو کنید.
"""
        
        if request.response_message:
            text += f"\n\n� پیام تأمین‌کننده:\n{request.response_message}"
        
        await bot.send_message(
            chat_id=user.telegram_id,
            text=text
        )
        
    except Exception as e:
        logger.error(f"Error sending notification to demander: {e}")

async def send_reminder(
    bot: Bot,
    chat_id: str,
    text: str,
    reply_markup: InlineKeyboardMarkup = None
):
    """ارسال یادآوری عمومی"""
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error sending reminder to {chat_id}: {e}")
