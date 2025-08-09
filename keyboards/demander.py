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


def get_demander_categories_keyboard():
    """کیبورد انتخاب دسته‌بندی‌ها (سبک‌های کاری) برای جستجو"""
    kb = ReplyKeyboardBuilder()
    styles = [
        "👗 فشن / کت واک",
        "📢 تبلیغاتی / برندینگ",
        "🧕 مذهبی / پوشیده",
        "👶 کودک",
        "🏃 ورزشی",
        "🎨 هنری / خاص",
        "🌳 عکاسی فضای باز",
        "📸 عکاسی استودیویی",
    ]
    for style in styles:
        kb.button(text=f"✅ {style}")
    kb.button(text="✔️ تأیید و ادامه")
    kb.button(text="↩️ بازگشت")
    kb.adjust(2, 2, 2, 2, 1, 1)
    return kb.as_markup(resize_keyboard=True)


def get_demander_cooperation_types_keyboard():
    """کیبورد انتخاب نوع همکاری برای جستجو"""
    kb = ReplyKeyboardBuilder()
    kb.button(text="✅ حضوری")
    kb.button(text="✅ پروژه‌ای")
    kb.button(text="✅ پاره‌وقت")
    kb.button(text="🤷 مهم نیست")
    kb.button(text="✔️ تأیید و ادامه")
    kb.button(text="↩️ بازگشت")
    kb.adjust(3, 1, 1, 1)
    return kb.as_markup(resize_keyboard=True)


def get_demander_payment_types_keyboard():
    """کیبورد انتخاب انواع پرداخت مورد قبول"""
    kb = ReplyKeyboardBuilder()
    kb.button(text="✅ ساعتی")
    kb.button(text="✅ روزانه")
    kb.button(text="✅ به ازای هر لباس")
    kb.button(text="✅ بر اساس دسته‌بندی")
    kb.button(text="✅ همه مورد قبول است")
    kb.button(text="✔️ تأیید و ادامه")
    kb.button(text="↩️ بازگشت")
    kb.adjust(2, 2, 1, 1, 1)
    return kb.as_markup(resize_keyboard=True)


def get_doesnt_matter_keyboard():
    kb = ReplyKeyboardBuilder()
    kb.button(text="🤷 مهم نیست")
    kb.button(text="↩️ بازگشت")
    kb.adjust(1, 1)
    return kb.as_markup(resize_keyboard=True)
