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

def get_search_result_keyboard(current_index: int, total_results: int, supplier_id: int):
    """کیبورد نتایج جست‌وجو با قابلیت ناوبری و ارسال درخواست"""
    builder = InlineKeyboardBuilder()
    
    # Navigation buttons
    nav_buttons = []
    if current_index > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="◀️ قبلی",
            callback_data=f"search_nav:prev:{current_index}"
        ))
    
    if current_index < total_results - 1:
        nav_buttons.append(InlineKeyboardButton(
            text="بعدی ▶️",
            callback_data=f"search_nav:next:{current_index}"
        ))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    # Send request button
    builder.button(
        text="📩 ارسال درخواست",
        callback_data=f"send_request:{supplier_id}"
    )
    
    # Back to menu button
    builder.button(
        text="🔙 بازگشت به منو",
        callback_data="back_to_demander_menu"
    )
    
    builder.adjust(len(nav_buttons) if nav_buttons else 1, 1, 1)
    return builder.as_markup()

def get_request_message_keyboard(supplier_id: int):
    """کیبورد برای نوشتن پیام درخواست"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="❌ انصراف",
        callback_data="cancel_send_request"
    )
    return builder.as_markup()


def get_request_status_keyboard(current_index: int, total_requests: int):
    """کیبورد وضعیت درخواست‌ها با ناوبری و بازگشت"""
    builder = InlineKeyboardBuilder()

    nav_buttons = []
    if current_index > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="◀️ قبلی",
            callback_data=f"req_status_nav:prev:{current_index}"
        ))
    if current_index < total_requests - 1:
        nav_buttons.append(InlineKeyboardButton(
            text="بعدی ▶️",
            callback_data=f"req_status_nav:next:{current_index}"
        ))
    if nav_buttons:
        builder.row(*nav_buttons)

    builder.button(
        text="🔙 بازگشت به منو",
        callback_data="back_to_demander_menu_from_status"
    )

    builder.adjust(len(nav_buttons) if nav_buttons else 1, 1)
    return builder.as_markup()


def get_supplier_requests_keyboard(current_index: int, total_requests: int, request_id: int, is_pending: bool):
    """کیبورد برای مرور درخواست‌های دریافتی تأمین‌کننده با ناوبری و اقدام"""
    builder = InlineKeyboardBuilder()

    # Navigation
    nav_buttons = []
    if current_index > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="◀️ قبلی",
            callback_data=f"sup_req_nav:prev:{current_index}"
        ))
    if current_index < total_requests - 1:
        nav_buttons.append(InlineKeyboardButton(
            text="بعدی ▶️",
            callback_data=f"sup_req_nav:next:{current_index}"
        ))
    if nav_buttons:
        builder.row(*nav_buttons)

    # Actions for pending only
    if is_pending:
        builder.button(text="✅ پذیرش", callback_data=f"sup_req_accept:{request_id}")
        builder.button(text="❌ رد", callback_data=f"sup_req_reject:{request_id}")

    # Back
    builder.button(text="🔙 بازگشت به منو", callback_data="back_to_supplier_menu_from_reqs")

    if is_pending and nav_buttons:
        builder.adjust(len(nav_buttons), 2, 1)
    elif is_pending:
        builder.adjust(2, 1)
    elif nav_buttons:
        builder.adjust(len(nav_buttons), 1)
    else:
        builder.adjust(1)

    return builder.as_markup()
