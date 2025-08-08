from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_main_menu():
    """منوی اصلی انتخاب نقش"""
    kb = ReplyKeyboardBuilder()
    kb.button(text="🎭 تأمین‌کننده")
    kb.button(text="🔍 درخواست‌کننده")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

def get_gender_keyboard():
    """کیبورد انتخاب جنسیت"""
    kb = ReplyKeyboardBuilder()
    kb.button(text="👨 مرد")
    kb.button(text="👩 زن")
    kb.button(text="↩️ بازگشت")
    kb.adjust(2, 1)
    return kb.as_markup(resize_keyboard=True)

def get_cooperation_types_keyboard():
    """کیبورد انتخاب نوع همکاری"""
    kb = ReplyKeyboardBuilder()
    kb.button(text="✅ حضوری")
    kb.button(text="✅ پروژه‌ای")
    kb.button(text="✅ پاره‌وقت")
    kb.button(text="✔️ تأیید و ادامه")
    kb.button(text="↩️ بازگشت")
    kb.adjust(3, 1, 1)
    return kb.as_markup(resize_keyboard=True)

def get_work_styles_keyboard():
    """کیبورد انتخاب سبک کاری"""
    kb = ReplyKeyboardBuilder()
    styles = [
        "👗 فشن / کت واک",
        "📢 تبلیغاتی / برندینگ",
        "🧕 مذهبی / پوشیده",
        "👶 کودک",
        "🏃 ورزشی",
        "🎨 هنری / خاص",
        "🌳 عکاسی فضای باز",
        "📸 عکاسی استودیویی"
    ]
    for style in styles:
        kb.button(text=f"✅ {style}")
    kb.button(text="✔️ تأیید و ادامه")
    kb.button(text="↩️ بازگشت")
    kb.adjust(2, 2, 2, 2, 1, 1)
    return kb.as_markup(resize_keyboard=True)

def get_skip_keyboard():
    """کیبورد برای رد کردن فیلد اختیاری"""
    kb = ReplyKeyboardBuilder()
    kb.button(text="⏭ رد کردن")
    kb.button(text="↩️ بازگشت")
    kb.adjust(1, 1)
    return kb.as_markup(resize_keyboard=True)

def get_confirm_keyboard():
    """کیبورد تأیید نهایی"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="✅ تأیید نهایی"),
                KeyboardButton(text="❌ انصراف")
            ],
            [KeyboardButton(text="🔄 ویرایش اطلاعات")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_supplier_menu_keyboard():
    """منوی تأمین‌کننده"""
    kb = ReplyKeyboardBuilder()
    kb.button(text="👤 مشاهده پروفایل")
    kb.button(text="✏️ ویرایش پروفایل")
    kb.button(text="📨 درخواست‌های جدید")
    kb.button(text="⚙️ تنظیمات")
    kb.button(text="🔙 بازگشت به منوی اصلی")
    kb.adjust(2, 2, 1)
    return kb.as_markup(resize_keyboard=True)

def get_edit_profile_keyboard():
    """کیبورد انتخاب فیلد برای ویرایش پروفایل"""
    kb = ReplyKeyboardBuilder()
    fields = [
        "نام کامل", "سن", "شماره تماس", "اینستاگرام",
        "قد", "وزن", "رنگ مو", "رنگ چشم", "رنگ پوست",
        "سایز بالاتنه", "سایز پایین‌تنه", "ویژگی‌های خاص",
        "قیمت‌گذاری", "شهر", "محدوده فعالیت",
        "انواع همکاری", "سبک‌های کاری", "سابقه برند", "توضیحات",
        "مدیریت تصاویر"
    ]
    for field in fields:
        kb.button(text=field)
    kb.button(text="↩️ بازگشت به منو")
    kb.adjust(2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1)
    return kb.as_markup(resize_keyboard=True)

def get_settings_keyboard(is_active: bool):
    """کیبورد منوی تنظیمات"""
    kb = ReplyKeyboardBuilder()
    if is_active:
        kb.button(text="🔴 غیرفعال کردن پروفایل")
    else:
        kb.button(text="🟢 فعال کردن پروفایل")
    kb.button(text="↩️ بازگشت به منو")
    kb.adjust(1, 1)
    return kb.as_markup(resize_keyboard=True)



def get_back_keyboard():
    """کیبورد بازگشت"""
    kb = ReplyKeyboardBuilder()
    kb.button(text="↩️ بازگشت")
    return kb.as_markup(resize_keyboard=True)

def get_demander_search_gender_keyboard():
    """کیبورد انتخاب جنسیت برای جستجو"""
    kb = ReplyKeyboardBuilder()
    kb.button(text="👨 مرد")
    kb.button(text="👩 زن")
    kb.button(text="🤷 مهم نیست")
    kb.button(text="↩️ بازگشت")
    kb.adjust(2, 1, 1)
    return kb.as_markup(resize_keyboard=True)

def get_price_range_keyboard():
    """کیبورد محدوده قیمت"""
    kb = ReplyKeyboardBuilder()
    kb.button(text="💰 زیر ۵۰۰ هزار تومان")
    kb.button(text="💰 ۵۰۰ هزار - ۱ میلیون")
    kb.button(text="💰 ۱ - ۲ میلیون")
    kb.button(text="💰 بالای ۲ میلیون")
    kb.button(text="🤷 مهم نیست")
    kb.button(text="↩️ بازگشت")
    kb.adjust(2, 2, 1, 1)
    return kb.as_markup(resize_keyboard=True)
