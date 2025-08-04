from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_demander_menu_keyboard():
    """منوی اصلی درخواست‌کننده"""
    kb = ReplyKeyboardBuilder()
    kb.button(text="👤 مشاهده پروفایل")
    kb.button(text="✏️ ویرایش پروفایل")
    kb.button(text="🔍 جست‌جوی تأمین‌کننده")
    kb.button(text="📄 وضعیت درخواست‌ها")
    kb.button(text="🔙 بازگشت به منوی اصلی")
    kb.adjust(2, 2, 1)
    return kb.as_markup(resize_keyboard=True)


def get_demander_edit_profile_keyboard():
    """کیبورد انتخاب فیلد برای ویرایش پروفایل درخواست‌کننده"""
    kb = ReplyKeyboardBuilder()
    fields = [
        "نام کامل",
        "نام شرکت",
        "آدرس",
        "جنسیت",
        "شماره تماس",
        "اینستاگرام",
        "توضیحات",
    ]
    for field in fields:
        kb.button(text=field)
    kb.button(text="↩️ بازگشت به منو")
    kb.adjust(2, 2, 2, 1)
    return kb.as_markup(resize_keyboard=True)
