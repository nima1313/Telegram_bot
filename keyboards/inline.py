from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_pagination_keyboard(current_page: int, total_pages: int, callback_prefix: str):
    """کیبورد صفحه‌بندی"""
    builder = InlineKeyboardBuilder()
    
    # دکمه صفحه قبل
    if current_page > 1:
        builder.button(
            text="◀️ قبلی",
            callback_data=f"{callback_prefix}:page:{current_page-1}"
        )
    
    # نمایش شماره صفحه
    builder.button(
        text=f"📄 {current_page}/{total_pages}",
        callback_data="current_page"
    )
    
    # دکمه صفحه بعد
    if current_page < total_pages:
        builder.button(
            text="بعدی ▶️",
            callback_data=f"{callback_prefix}:page:{current_page+1}"
        )
    
    builder.adjust(3)
    return builder.as_markup()

def get_supplier_detail_keyboard(supplier_id: int):
    """کیبورد جزئیات تأمین‌کننده"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="📅 درخواست وقت",
        callback_data=f"request_appointment:{supplier_id}"
    )
    builder.button(
        text="🔙 بازگشت به لیست",
        callback_data="back_to_list"
    )
    builder.adjust(1)
    return builder.as_markup()

def get_request_action_keyboard(request_id: int):
    """کیبورد اقدام روی درخواست"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ پذیرفتن",
        callback_data=f"accept_request:{request_id}"
    )
    builder.button(
        text="❌ رد کردن",
        callback_data=f"reject_request:{request_id}"
    )
    builder.adjust(2)
    return builder.as_markup()

def get_request_confirmation_keyboard():
    """کیبورد تأیید درخواست"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ ارسال درخواست",
        callback_data="confirm_request"
    )
    builder.button(
        text="❌ انصراف",
        callback_data="cancel_request"
    )
    builder.adjust(2)
    return builder.as_markup()
