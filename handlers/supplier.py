import re
import logging
from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, FSInputFile, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
import json

def format_pricing_data(pricing_data: dict) -> str:
    if not pricing_data:
        return "اطلاعات قیمت‌گذاری موجود نیست"
    
    formatted_lines = []
    for style, prices in pricing_data.items():
        style_text = f"سبک {style}:"
        for price_type, amount in prices.items():
            style_text += f"\n  {price_type}: {amount} تومان"
        formatted_lines.append(style_text)
    
    return "\n".join(formatted_lines)

from database.models import User, Supplier, UserRole, Request, RequestStatus
from states.supplier import (
    SupplierRegistration, SupplierMenu, SupplierEditProfile, 
    SupplierSettings, PhotoEditState
)
from keyboards.reply import *
from keyboards.inline import get_request_action_keyboard
from utils.validators import validate_phone_number, validate_age, validate_height_weight
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

# Constants for price types
PRICE_TYPES = {
    "✅ ساعتی": "hourly",
    "✅ روزانه": "daily",
    "✅ به ازای هر لباس": "per_cloth",
    "✅ بر اساس دسته‌بندی": "category_based"
}

# Constants for price types
PRICE_TYPES = {
    "✅ ساعتی": "hourly",
    "✅ روزانه": "daily",
    "✅ به ازای هر لباس": "per_cloth",
    "✅ بر اساس دسته‌بندی": "category_based"
}

def get_finish_upload_keyboard():
    """کیبورد برای اتمام آپلود تصاویر"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ اتمام ارسال تصاویر")],
            [KeyboardButton(text="↩️ بازگشت")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_price_types_keyboard():
    """کیبورد برای انتخاب نوع قیمت‌گذاری"""
    keyboard = [
        [KeyboardButton(text="✅ ساعتی")],
        [KeyboardButton(text="✅ روزانه")],
        [KeyboardButton(text="✅ به ازای هر لباس")],
        [KeyboardButton(text="✅ بر اساس دسته‌بندی")],
        [KeyboardButton(text="✔️ تأیید و ادامه")],
        [KeyboardButton(text="↩️ بازگشت")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def validate_price_range(text: str) -> tuple[int, int] | None:
    """اعتبارسنجی محدوده قیمت (هزار تومان)"""
    try:
        # Remove any non-digit characters and split by any separator
        numbers = re.findall(r'\d+', text)
        if len(numbers) != 2:
            return None
        min_price = int(numbers[0])
        max_price = int(numbers[1])
        if min_price <= 0 or max_price <= 0 or min_price > max_price:
            return None
        return min_price, max_price
    except:
        return None
    return keyboard
from sqlalchemy.orm import selectinload

router = Router()

# A mapping from the button text to the database column name
EDITABLE_FIELDS = {
    "نام کامل": "full_name",
    "سن": "age",
    "شماره تماس": "phone_number",
    "اینستاگرام": "instagram_id",
    "قد": "height",
    "وزن": "weight",
    "رنگ مو": "hair_color",
    "رنگ چشم": "eye_color",
    "رنگ پوست": "skin_color",
    "سایز بالاتنه": "top_size",
    "سایز پایین‌تنه": "bottom_size",
    "ویژگی‌های خاص": "special_features",
    "محدوده قیمت": "price_range",
    "شهر": "city",
    "محدوده فعالیت": "area",
    "انواع همکاری": "cooperation_types",
    "سبک‌های کاری": "work_styles",
    "سابقه برند": "brand_experience",
    "توضیحات": "additional_notes",
    "مدیریت تصاویر": "portfolio_photos",
}
# ========== فرآیند ثبت‌نام تأمین‌کننده ==========

@router.message(SupplierRegistration.full_name)
async def process_full_name(message: Message, state: FSMContext):
    """پردازش نام و نام خانوادگی"""
    if message.text == "↩️ بازگشت":
        await state.clear()
        await message.answer("به منوی اصلی بازگشتید.", reply_markup=get_main_menu())
        return
    
    if len(message.text) < 3:
        await message.answer("لطفاً نام کامل خود را وارد کنید (حداقل ۳ حرف):")
        return
    
    await state.update_data(full_name=message.text)
    await message.answer(
        "🔸 جنسیت خود را انتخاب کنید:",
        reply_markup=get_gender_keyboard()
    )
    await state.set_state(SupplierRegistration.gender)

@router.message(SupplierRegistration.gender)
async def process_gender(message: Message, state: FSMContext):
    """پردازش جنسیت"""
    if message.text == "↩️ بازگشت":
        await message.answer(
            "🔸 نام و نام خانوادگی خود را وارد کنید:",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(SupplierRegistration.full_name)
        return
    
    if message.text not in ["👨 مرد", "👩 زن"]:
        await message.answer("لطفاً از گزینه‌های موجود انتخاب کنید:")
        return
    
    gender = "مرد" if message.text == "👨 مرد" else "زن"
    await state.update_data(gender=gender)
    await message.answer(
        "🔸 سن خود را به عدد وارد کنید:",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(SupplierRegistration.age)

@router.message(SupplierRegistration.age)
async def process_age(message: Message, state: FSMContext):
    """پردازش سن"""
    if message.text == "↩️ بازگشت":
        await message.answer(
            "🔸 جنسیت خود را انتخاب کنید:",
            reply_markup=get_gender_keyboard()
        )
        await state.set_state(SupplierRegistration.gender)
        return
    
    age = validate_age(message.text)
    if not age:
        await message.answer("لطفاً سن را به صورت عدد بین ۱۵ تا ۸۰ وارد کنید:")
        return
    
    await state.update_data(age=age)
    await message.answer(
        "🔸 شماره تماس خود را وارد کنید (ترجیحاً واتساپ):\n"
        "مثال: 09123456789",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(SupplierRegistration.phone_number)

@router.message(SupplierRegistration.phone_number)
async def process_phone_number(message: Message, state: FSMContext):
    """پردازش شماره تماس"""
    if message.text == "↩️ بازگشت":
        await message.answer(
            "🔸 سن خود را به عدد وارد کنید:",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(SupplierRegistration.age)
        return
    
    phone = validate_phone_number(message.text)
    if not phone:
        await message.answer(
            "شماره تماس نامعتبر است. لطفاً شماره را به صورت صحیح وارد کنید:\n"
            "مثال: 09123456789"
        )
        return
    
    await state.update_data(phone_number=phone)
    await message.answer(
        "🔸 آیدی اینستاگرام خود را وارد کنید (بدون @):\n"
        "برای رد کردن روی دکمه 'رد کردن' کلیک کنید.",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(SupplierRegistration.instagram_id)

@router.message(SupplierRegistration.instagram_id)
async def process_instagram_id(message: Message, state: FSMContext):
    """پردازش آیدی اینستاگرام"""
    if message.text == "↩️ بازگشت":
        await message.answer(
            "🔸 شماره تماس خود را وارد کنید:",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(SupplierRegistration.phone_number)
        return
    
    instagram_id = None if message.text == "⏭ رد کردن" else message.text.replace("@", "")
    await state.update_data(instagram_id=instagram_id)
    
    # Ask for portfolio photos
    await message.answer(
        "🖼 لطفاً نمونه کارهای خود را ارسال کنید.\n"
        "(لطفا آن ها را تک تک ارسال کنید)\n"
        "حداقل یک تصویر ارسال کنید.\n"
        "پس از اتمام ارسال تصاویر، روی دکمه 'اتمام ارسال تصاویر' کلیک کنید.",
        reply_markup=get_finish_upload_keyboard()
    )
    await state.update_data(portfolio_photos=[])
    await state.set_state(SupplierRegistration.portfolio_photos)

@router.message(SupplierRegistration.portfolio_photos)
async def process_portfolio_photos(message: Message, state: FSMContext):
    """پردازش تصاویر نمونه کار"""
    if message.text == "↩️ بازگشت":
        await message.answer(
            "🔸 آیدی اینستاگرام خود را وارد کنید:",
            reply_markup=get_skip_keyboard()
        )
        await state.set_state(SupplierRegistration.instagram_id)
        return
    
    if message.text == "✅ اتمام ارسال تصاویر":
        data = await state.get_data()
        if not data.get('portfolio_photos'):
            await message.answer("❌ لطفاً حداقل یک تصویر ارسال کنید.")
            return
        
        await message.answer(
            "حالا مشخصات ظاهری خود را وارد کنید.\n\n"
            "🔸 قد خود را به سانتی‌متر وارد کنید:\n"
            "مثال: 175",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(SupplierRegistration.height)
        return
    
    # اگر پیام حاوی عکس باشد
    if message.photo:
        data = await state.get_data()
        portfolio_photos = data.get('portfolio_photos', [])
        # ذخیره file_id عکس
        portfolio_photos.append(message.photo[-1].file_id)
        await state.update_data(portfolio_photos=portfolio_photos)
        await message.answer(
            f"✅ تصویر {len(portfolio_photos)} اضافه شد.\n"
            "می‌توانید تصویر دیگری ارسال کنید یا روی دکمه 'اتمام ارسال تصاویر' کلیک کنید."
        )
    else:
        await message.answer("❌ لطفاً یک تصویر ارسال کنید.")

@router.message(SupplierRegistration.height)
async def process_height(message: Message, state: FSMContext):
    """پردازش قد"""
    if message.text == "↩️ بازگشت":
        await message.answer(
            "🔸 آیدی اینستاگرام خود را وارد کنید:",
            reply_markup=get_skip_keyboard()
        )
        await state.set_state(SupplierRegistration.instagram_id)
        return
    
    height = validate_height_weight(message.text, is_height=True)
    if not height:
        await message.answer("لطفاً قد را به صورت عدد بین ۱۰۰ تا ۲۵۰ وارد کنید:")
        return
    
    await state.update_data(height=height)
    await message.answer(
        "🔸 وزن خود را به کیلوگرم وارد کنید:\n"
        "مثال: 65",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(SupplierRegistration.weight)

@router.message(SupplierRegistration.weight)
async def process_weight(message: Message, state: FSMContext):
    """پردازش وزن"""
    if message.text == "↩️ بازگشت":
        await message.answer(
            "🔸 قد خود را به سانتی‌متر وارد کنید:",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(SupplierRegistration.height)
        return
    
    weight = validate_height_weight(message.text, is_height=False)
    if not weight:
        await message.answer("لطفاً وزن را به صورت عدد بین ۳۰ تا ۲۰۰ وارد کنید:")
        return
    
    await state.update_data(weight=weight)
    await message.answer(
        "🔸 رنگ موی خود را وارد کنید:\n"
        "مثال: مشکی، قهوه‌ای، بلوند",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(SupplierRegistration.hair_color)

# ادامه فیلدهای ظاهری...
@router.message(SupplierRegistration.hair_color)
async def process_hair_color(message: Message, state: FSMContext):
    """پردازش رنگ مو"""
    if message.text == "↩️ بازگشت":
        await state.set_state(SupplierRegistration.weight)
        await message.answer("🔸 وزن خود را به کیلوگرم وارد کنید:")
        return
    
    await state.update_data(hair_color=message.text)
    await message.answer("🔸 رنگ چشم خود را وارد کنید:")
    await state.set_state(SupplierRegistration.eye_color)

@router.message(SupplierRegistration.eye_color)
async def process_eye_color(message: Message, state: FSMContext):
    """پردازش رنگ چشم"""
    if message.text == "↩️ بازگشت":
        await state.set_state(SupplierRegistration.hair_color)
        await message.answer("🔸 رنگ موی خود را وارد کنید:")
        return
    
    await state.update_data(eye_color=message.text)
    await message.answer("🔸 رنگ پوست خود را وارد کنید:")
    await state.set_state(SupplierRegistration.skin_color)

@router.message(SupplierRegistration.skin_color)
async def process_skin_color(message: Message, state: FSMContext):
    """پردازش رنگ پوست"""
    if message.text == "↩️ بازگشت":
        await state.set_state(SupplierRegistration.eye_color)
        await message.answer("🔸 رنگ چشم خود را وارد کنید:")
        return
    
    await state.update_data(skin_color=message.text)
    await message.answer("🔸 سایز لباس بالاتنه خود را وارد کنید (مثال: M یا 38):")
    await state.set_state(SupplierRegistration.top_size)

@router.message(SupplierRegistration.top_size)
async def process_top_size(message: Message, state: FSMContext):
    """پردازش سایز بالاتنه"""
    if message.text == "↩️ بازگشت":
        await state.set_state(SupplierRegistration.skin_color)
        await message.answer("🔸 رنگ پوست خود را وارد کنید:")
        return
    
    await state.update_data(top_size=message.text)
    await message.answer("🔸 سایز لباس پایین‌تنه خود را وارد کنید:")
    await state.set_state(SupplierRegistration.bottom_size)

@router.message(SupplierRegistration.bottom_size)
async def process_bottom_size(message: Message, state: FSMContext):
    """پردازش سایز پایین‌تنه"""
    if message.text == "↩️ بازگشت":
        await state.set_state(SupplierRegistration.top_size)
        await message.answer("🔸 سایز لباس بالاتنه خود را وارد کنید:")
        return
    
    await state.update_data(bottom_size=message.text)
    await message.answer(
        "🔸 ویژگی خاص ظاهری (تتو، خال، ریش و...) - اختیاری:\n"
        "برای رد کردن روی دکمه 'رد کردن' کلیک کنید.",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(SupplierRegistration.special_features)

@router.message(SupplierRegistration.special_features)
async def process_special_features(message: Message, state: FSMContext):
    """پردازش ویژگی‌های خاص"""
    if message.text == "↩️ بازگشت":
        await state.set_state(SupplierRegistration.bottom_size)
        await message.answer("🔸 سایز لباس پایین‌تنه خود را وارد کنید:")
        return
    
    special_features = None if message.text == "⏭ رد کردن" else message.text
    await state.update_data(special_features=special_features)
    await state.update_data(selected_work_styles=[])
    
    await message.answer(
        "🔸 سبک کاری مورد علاقه خود را انتخاب کنید (می‌توانید چند مورد انتخاب کنید):",
        reply_markup=get_work_styles_keyboard()
    )
    await state.set_state(SupplierRegistration.work_styles)

@router.message(SupplierRegistration.price_types)
async def process_price_types(message: Message, state: FSMContext):
    """پردازش انتخاب نوع قیمت‌گذاری"""
    data = await state.get_data()
    selected_types = data.get('selected_price_types', [])
    
    if message.text == "↩️ بازگشت":
        await state.set_state(SupplierRegistration.special_features)
        await message.answer(
            "🔸 ویژگی خاص ظاهری را وارد کنید:",
            reply_markup=get_skip_keyboard()
        )
        return
    
    if message.text == "✔️ تأیید و ادامه":
        if not selected_types:
            await message.answer("لطفاً حداقل یک نوع قیمت‌گذاری را انتخاب کنید.")
            return
        
        await state.update_data(pricing_data={})
        # Start with the first price type
        await process_next_price_type(message, state, selected_types[0])
        return
    
    if message.text in PRICE_TYPES:
        price_type = PRICE_TYPES[message.text]
        if price_type in selected_types:
            selected_types.remove(price_type)
            await message.answer(f"❌ {message.text.replace('✅ ', '')} از لیست حذف شد.")
        else:
            selected_types.append(price_type)
            await message.answer(f"✅ {message.text.replace('✅ ', '')} به لیست اضافه شد.")
        
        await state.update_data(selected_price_types=selected_types)
        
        # Show current selections
        if selected_types:
            current = "انتخاب‌های فعلی:\n" + "\n".join([f"✓ {k.replace('✅ ', '')}" for k, v in PRICE_TYPES.items() if v in selected_types])
            await message.answer(current)

async def process_next_price_type(message: Message, state: FSMContext, current_type: str):
    """پردازش قیمت برای نوع بعدی"""
    price_names = {
        "hourly": "ساعتی",
        "daily": "روزانه",
        "per_cloth": "به ازای هر لباس",
        "category_based": "دسته‌بندی"
    }
    
    await state.update_data(current_price_type=current_type)
    
    if current_type == "category_based":
        # Use already selected work styles
        data = await state.get_data()
        selected_styles = data.get('work_styles', [])
        if not selected_styles:
            await message.answer("❌ برای قیمت‌گذاری بر اساس دسته‌بندی، ابتدا باید سبک‌های کاری را انتخاب کرده باشید.")
            return
            
        await state.update_data(current_style=selected_styles[0])
        # Start getting prices for the first selected style
        await process_next_style_price(message, state, selected_styles[0])
    else:
        await message.answer(
            f"🔸 محدوده قیمت {price_names[current_type]} را وارد کنید (به هزار تومان):\n"
            "مثال: 100 تا 300\n"
            "(یعنی از 100 هزار تومان تا 300 هزار تومان)",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(SupplierRegistration.price_range)

@router.message(SupplierRegistration.price_range)
async def process_price_range(message: Message, state: FSMContext):
    """پردازش محدوده قیمت"""
    if message.text == "↩️ بازگشت":
        await state.set_state(SupplierRegistration.price_types)
        await message.answer(
            "🔸 نوع قیمت‌گذاری را انتخاب کنید:",
            reply_markup=get_price_types_keyboard()
        )
        return
    
    price_range = validate_price_range(message.text)
    if not price_range:
        await message.answer(
            "لطفاً محدوده قیمت را به صورت صحیح وارد کنید:\n"
            "مثال: 100 تا 300"
        )
        return
    
    data = await state.get_data()
    current_type = data.get('current_price_type')
    pricing_data = data.get('pricing_data', {})
    selected_types = data.get('selected_price_types', [])
    
    # Store the price range for current type
    pricing_data[current_type] = {"min": price_range[0], "max": price_range[1]}
    await state.update_data(pricing_data=pricing_data)
    
    # Find next price type to process
    current_index = selected_types.index(current_type)
    if current_index + 1 < len(selected_types):
        next_type = selected_types[current_index + 1]
        await process_next_price_type(message, state, next_type)
    else:
        # All price types processed, move to next step
        await message.answer(
            "🔸 شهر محل زندگی خود را وارد کنید:\n"
            "مثال: تهران",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(SupplierRegistration.city)

async def process_next_style_price(message: Message, state: FSMContext, current_style: str):
    """پردازش قیمت برای هر سبک"""
    style_names = {
        "fashion": "� فشن / کت واک",
        "advertising": "📢 تبلیغاتی / برندینگ",
        "religious": "🧕 مذهبی / پوشیده",
        "children": "👶 کودک",
        "sports": "🏃 ورزشی",
        "artistic": "🎨 هنری / خاص",
        "outdoor": "🌳 عکاسی فضای باز",
        "studio": "📸 عکاسی استودیویی"
    }
    
    await state.update_data(current_style=current_style)
    await message.answer(
        f"🔸 محدوده قیمت برای سبک {style_names[current_style]} را وارد کنید (به هزار تومان):\n"
        "مثال: 100 تا 300\n"
        "(یعنی از 100 هزار تومان تا 300 هزار تومان)",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(SupplierRegistration.style_price)

@router.message(SupplierRegistration.style_price)
async def process_style_price(message: Message, state: FSMContext):
    """پردازش قیمت هر سبک"""
    if message.text == "↩️ بازگشت":
        await state.set_state(SupplierRegistration.price_types)
        await message.answer(
            "🔸 نوع قیمت‌گذاری را انتخاب کنید:",
            reply_markup=get_price_types_keyboard()
        )
        return
    
    price_range = validate_price_range(message.text)
    if not price_range:
        await message.answer(
            "❌ فرمت قیمت نامعتبر است.\n"
            "لطفاً به این صورت وارد کنید: 100 تا 300\n"
            "(یعنی از 100 هزار تومان تا 300 هزار تومان)"
        )
        return
    
    data = await state.get_data()
    current_style = data.get('current_style')
    current_price_type = data.get('current_price_type')
    work_styles = data.get('work_styles', [])
    pricing_data = data.get('pricing_data', {})
    
    # Initialize pricing structure if needed
    if current_style not in pricing_data:
        pricing_data[current_style] = {}
    
    # Store the price range for current style and price type
    pricing_data[current_style][current_price_type] = {
        "min": price_range[0],
        "max": price_range[1]
    }
    await state.update_data(pricing_data=pricing_data)
    
    # Find next style to process
    current_index = work_styles.index(current_style)
    if current_index + 1 < len(work_styles):
        next_style = work_styles[current_index + 1]
        await process_next_style_price(message, state, next_style)
    else:
        # All styles processed for this price type, store in pricing_data
        pricing_data["category_based"] = {
            style: {"min": data.get("style_pricing", {}).get(style, {}).get("min", 0),
                   "max": data.get("style_pricing", {}).get(style, {}).get("max", 0)}
            for style in work_styles
        }
        await state.update_data(pricing_data=pricing_data)
        
        # Check if there are more price types to process
        selected_types = data.get('selected_price_types', [])
        current_type = data.get('current_price_type')
        current_type_index = selected_types.index(current_type)
        
        if current_type_index + 1 < len(selected_types):
            # Move to next price type
            next_type = selected_types[current_type_index + 1]
            await process_next_price_type(message, state, next_type)
        else:
            # All price types and styles processed, move to city input
            await message.answer(
                "🔸 شهر محل زندگی خود را وارد کنید:\n"
                "مثال: تهران",
                reply_markup=get_back_keyboard()
            )
            await state.set_state(SupplierRegistration.city)
        return
    
    price_range = validate_price_range(message.text)
    if not price_range:
        await message.answer(
            "لطفاً محدوده قیمت را به صورت صحیح وارد کنید:\n"
            "مثال: 100 تا 300"
        )
        return

@router.message(SupplierRegistration.city)
async def process_city(message: Message, state: FSMContext):
    """پردازش شهر"""
    if message.text == "↩️ بازگشت":
        await state.set_state(SupplierRegistration.price_range)
        await message.answer("🔸 محدوده قیمت همکاری خود را وارد کنید:")
        return
    
    await state.update_data(city=message.text)
    await message.answer(
        "🔸 محدوده فعالیت خود را وارد کنید:\n"
        "مثال: غرب تهران، کل تهران",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(SupplierRegistration.area)

@router.message(SupplierRegistration.area)
async def process_area(message: Message, state: FSMContext):
    """پردازش محدوده"""
    if message.text == "↩️ بازگشت":
        await state.set_state(SupplierRegistration.city)
        await message.answer("🔸 شهر محل زندگی خود را وارد کنید:")
        return
    
    await state.update_data(area=message.text)
    await state.update_data(selected_cooperation_types=[])
    
    await message.answer(
        "🔸 نوع همکاری مورد نظر خود را انتخاب کنید (می‌توانید چند مورد انتخاب کنید):\n\n"
        "روی گزینه‌های مورد نظر کلیک کنید و در انتها 'تأیید و ادامه' را بزنید.",
        reply_markup=get_cooperation_types_keyboard()
    )
    await state.set_state(SupplierRegistration.cooperation_types)

@router.message(SupplierRegistration.cooperation_types)
async def process_cooperation_types(message: Message, state: FSMContext):
    """پردازش نوع همکاری"""
    data = await state.get_data()
    selected_types = data.get('selected_cooperation_types', [])
    
    if message.text == "↩️ بازگشت":
        await state.set_state(SupplierRegistration.area)
        await message.answer("🔸 محدوده فعالیت خود را وارد کنید:")
        return
    
    if message.text == "✔️ تأیید و ادامه":
        if not selected_types:
            await message.answer("لطفاً حداقل یک نوع همکاری را انتخاب کنید.")
            return
        
        await state.update_data(cooperation_types=selected_types)
        
        # Move directly to brand experience after cooperation types
        await message.answer(
            "🔸 نام برندهایی که با آن‌ها همکاری داشته‌اید را وارد کنید:\n"
            "مثال: جین وست، آدیداس\n\n"
            "اگر سابقه همکاری ندارید، روی 'رد کردن' کلیک کنید.",
            reply_markup=get_skip_keyboard()
        )
        await state.set_state(SupplierRegistration.brand_experience)
        return
    
    # مدیریت انتخاب/لغو انتخاب
    cooperation_map = {
        "✅ حضوری": "in_person",
        "✅ پروژه‌ای": "project_based",
        "✅ پاره‌وقت": "part_time"
    }
    
    if message.text in cooperation_map:
        coop_type = cooperation_map[message.text]
        if coop_type in selected_types:
            selected_types.remove(coop_type)
        else:
            selected_types.append(coop_type)
        
        await state.update_data(selected_cooperation_types=selected_types)
        
        # نمایش وضعیت فعلی
        status_text = "انتخاب‌های فعلی:\n"
        for key, value in cooperation_map.items():
            if value in selected_types:
                status_text += f"✓ {key.replace('✅ ', '')}\n"
        status_text += "\n برای کنسل کردن انتخاب دوباره روی دکمه آن کلیک کنید."
        await message.answer(status_text)

@router.message(SupplierRegistration.work_styles)
async def process_work_styles(message: Message, state: FSMContext):
    """پردازش سبک کاری"""
    data = await state.get_data()
    selected_styles = data.get('selected_work_styles', [])
    
    if message.text == "↩️ بازگشت":
        await state.set_state(SupplierRegistration.cooperation_types)
        await message.answer(
            "🔸 نوع همکاری مورد نظر خود را انتخاب کنید:",
            reply_markup=get_cooperation_types_keyboard()
        )
        return
    
    if message.text == "✔️ تأیید و ادامه":
        if not selected_styles:
            await message.answer("لطفاً حداقل یک سبک کاری را انتخاب کنید.")
            return
        
        await state.update_data(work_styles=selected_styles)
        await state.update_data(selected_price_types=[])
        
        await message.answer(
            "حالا اطلاعات قیمت‌گذاری خود را وارد کنید.\n\n"
            "🔸 نحوه قیمت‌گذاری مورد نظر خود را انتخاب کنید (می‌توانید چند مورد انتخاب کنید):\n\n"
            "برای هر کدام از موارد انتخابی در مرحله بعد محدوده قیمت دریافت خواهد شد.",
            reply_markup=get_price_types_keyboard()
        )
        await state.set_state(SupplierRegistration.price_types)
        return
    
    # مدیریت انتخاب/لغو انتخاب
    style_map = {
        "✅ 👗 فشن / کت واک": "fashion",
        "✅ 📢 تبلیغاتی / برندینگ": "advertising",
        "✅ 🧕 مذهبی / پوشیده": "religious",
        "✅ 👶 کودک": "children",
        "✅ 🏃 ورزشی": "sports",
        "✅ 🎨 هنری / خاص": "artistic",
        "✅ 🌳 عکاسی فضای باز": "outdoor",
        "✅ 📸 عکاسی استودیویی": "studio"
    }
    
    if message.text in style_map:
        style = style_map[message.text]
        if style in selected_styles:
            selected_styles.remove(style)
        else:
            selected_styles.append(style)
        
        await state.update_data(selected_work_styles=selected_styles)
        
        # نمایش وضعیت فعلی
        status_text = "انتخاب‌های فعلی:\n"
        for key, value in style_map.items():
            if value in selected_styles:
                status_text += f"✓ {key.replace('✅ ', '')}\n"
        status_text += "\n برای کنسل کردن انتخاب دوباره روی دکمه آن کلیک کنید."

        
        await message.answer(status_text)

@router.message(SupplierRegistration.brand_experience)
async def process_brand_experience(message: Message, state: FSMContext):
    """پردازش سابقه همکاری با برندها"""
    if message.text == "↩️ بازگشت":
        await state.set_state(SupplierRegistration.work_styles)
        await message.answer(
            "🔸 سبک کاری مورد علاقه خود را انتخاب کنید:",
            reply_markup=get_work_styles_keyboard()
        )
        return
    
    brand_experience = None if message.text == "⏭ رد کردن" else message.text
    await state.update_data(brand_experience=brand_experience)
    
    await message.answer(
        "🔸 توضیحات تکمیلی (اختیاری):\n"
        "مثلاً: روزهای در دسترس، نوع همکاری‌هایی که نمی‌پذیرید و...\n\n"
        "اگر توضیحی ندارید، روی 'رد کردن' کلیک کنید.",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(SupplierRegistration.additional_notes)

async def show_confirmation_summary(message: types.Message, state: FSMContext):
    """Helper function to show the confirmation summary."""
    data = await state.get_data()
    summary = create_supplier_summary(data)
    
    portfolio_photos = data.get('portfolio_photos', [])
    
    if portfolio_photos:
        media_group = [types.InputMediaPhoto(media=photo_id) for photo_id in portfolio_photos]
        
        # Add caption to the first media element
        if media_group:
            media_group[0].caption = f"لطفاً اطلاعات خود را بررسی کنید:\n\n{summary}"

        try:
            await message.answer_media_group(media_group)
        except Exception as e:
            logging.error(f"Error sending media group for confirmation: {e}")
            # Fallback to sending text and photos separately
            await message.answer(f"لطفاً اطلاعات خود را بررسی کنید:\n\n{summary}")
            for photo_id in portfolio_photos:
                await message.answer_photo(photo_id)
    else:
        await message.answer(f"لطفاً اطلاعات خود را بررسی کنید:\n\n{summary}")

    await message.answer(
        "آیا اطلاعات فوق را تأیید می‌کنید؟",
        reply_markup=get_confirm_keyboard()
    )
    await state.set_state(SupplierRegistration.confirm)

@router.message(SupplierRegistration.additional_notes)
async def process_additional_notes(message: Message, state: FSMContext):
    """پردازش توضیحات اضافی و نمایش خلاصه"""
    if message.text == "↩️ بازگشت":
        await state.set_state(SupplierRegistration.brand_experience)
        await message.answer(
            "🔸 نام برندهایی که با آن‌ها همکاری داشته‌اید را وارد کنید:",
            reply_markup=get_skip_keyboard()
        )
        return
    
    additional_notes = None if message.text == "⏭ رد کردن" else message.text
    await state.update_data(additional_notes=additional_notes)
    
    await show_confirmation_summary(message, state)

@router.message(SupplierRegistration.confirm)
async def process_confirmation(message: Message, state: FSMContext, session: AsyncSession):
    """تأیید نهایی و ذخیره اطلاعات"""
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer(
            "ثبت‌نام لغو شد. برای شروع مجدد از /start استفاده کنید.",
            reply_markup=ReplyKeyboardRemove()
        )
        return
    
    if message.text == "🔄 ویرایش اطلاعات":
        await state.set_state(SupplierRegistration.editing_field)
        await message.answer(
            "کدام بخش از اطلاعات خود را می‌خواهید ویرایش کنید؟",
            reply_markup=get_edit_profile_keyboard()
        )
        return
    
    if message.text == "✅ تأیید نهایی":
        try:
            data = await state.get_data()
            
            user = await get_or_create_user(session, message.from_user, UserRole.SUPPLIER)
            user.role = UserRole.SUPPLIER
            
            # Check if a supplier profile already exists
            supplier = await session.scalar(
                select(Supplier).where(Supplier.user_id == user.id)
            )
            
            if supplier:
                # Update existing profile
                for key, value in data.items():
                    if hasattr(supplier, key):
                        setattr(supplier, key, value)
                supplier.price_range_min = extract_price_min(data['price_range'])
                supplier.price_range_max = extract_price_max(data['price_range'])
                supplier.price_unit = extract_price_unit(data['price_range'])
            else:
                # Create new profile
                supplier = Supplier(
                    user_id=user.id,
                    full_name=data['full_name'],
                    gender=data['gender'],
                    age=data['age'],
                    phone_number=data['phone_number'],
                    instagram_id=data.get('instagram_id'),
                    portfolio_photos=data.get('portfolio_photos', []),
                    height=data['height'],
                    weight=data['weight'],
                    hair_color=data['hair_color'],
                    eye_color=data['eye_color'],
                    skin_color=data['skin_color'],
                    top_size=data['top_size'],
                    bottom_size=data['bottom_size'],
                    special_features=data.get('special_features'),
                    price_range_min=extract_price_min(data['price_range']),
                    price_range_max=extract_price_max(data['price_range']),
                    price_unit=extract_price_unit(data['price_range']),
                    city=data['city'],
                    area=data['area'],
                    cooperation_types=data['cooperation_types'],
                    work_styles=data['work_styles'],
                    brand_experience=data.get('brand_experience'),
                    additional_notes=data.get('additional_notes')
                )
                session.add(supplier)

            await session.commit()
            
            await message.answer(
                "✅ ثبت‌نام شما با موفقیت انجام شد!\n\n"
                "اکنون می‌توانید از امکانات ربات استفاده کنید.",
                reply_markup=get_supplier_menu_keyboard()
            )
            await state.set_state(SupplierMenu.main_menu)
            
        except Exception as e:
            logging.exception("Error during supplier registration confirmation:")
            await message.answer(
                "❌ خطایی در ثبت اطلاعات رخ داد. لطفاً مجدداً تلاش کنید.",
                reply_markup=ReplyKeyboardRemove()
            )
            await state.clear()

# ========== Handlers for Editing During Registration ==========

@router.message(SupplierRegistration.editing_field)
async def registration_choose_field_to_edit(message: Message, state: FSMContext):
    """Choose which field to edit during registration confirmation."""
    if message.text == "↩️ بازگشت به منو":
        await show_confirmation_summary(message, state)
        return

    if message.text not in EDITABLE_FIELDS:
        await message.answer("لطفاً یک گزینه معتبر از کیبورد انتخاب کنید.")
        return

    field_to_edit = EDITABLE_FIELDS[message.text]
    await state.update_data(field_to_edit=field_to_edit, field_to_edit_fa=message.text)
    
    if field_to_edit == "portfolio_photos":
        await state.set_state(SupplierRegistration.managing_photos)
        data = await state.get_data()
        photos = data.get('portfolio_photos', [])
        
        if photos:
            await message.answer("تصاویر فعلی شما:")
            media = [InputMediaPhoto(media=photo_id) for photo_id in photos]
            await message.answer_media_group(media=media)
        
        await message.answer(
            f"شما در حال حاضر {len(photos)} تصویر دارید. چه کاری می‌خواهید انجام دهید?",
            reply_markup=get_photo_management_keyboard()
        )
        return

    await state.set_state(SupplierRegistration.entering_new_value)
    await message.answer(f"لطفاً مقدار جدید برای '{message.text}' را وارد کنید:", reply_markup=get_back_keyboard())

@router.message(SupplierRegistration.entering_new_value)
async def registration_enter_new_value(message: Message, state: FSMContext):
    """Enter the new value for the selected field during registration."""
    if message.text == "↩️ بازگشت":
        await state.set_state(SupplierRegistration.editing_field)
        await message.answer("از کدام بخش می‌خواهید ویرایش کنید؟", reply_markup=get_edit_profile_keyboard())
        return

    data = await state.get_data()
    field_to_edit = data.get("field_to_edit")
    new_value = message.text

    # --- Validation ---
    if field_to_edit == 'age':
        age = validate_age(new_value)
        if not age:
            await message.answer("سن نامعتبر است. لطفاً عدد بین ۱۵ تا ۸۰ وارد کنید.")
            return
        new_value = age
    elif field_to_edit == 'phone_number':
        phone = validate_phone_number(new_value)
        if not phone:
            await message.answer("شماره تماس نامعتبر است.")
            return
        new_value = phone
    
    await state.update_data({field_to_edit: new_value})
    
    await message.answer(f"✅ '{data.get('field_to_edit_fa')}' با موفقیت ویرایش شد.")
    await show_confirmation_summary(message, state)

# --- Photo Management During Registration ---

@router.message(SupplierRegistration.managing_photos)
async def registration_manage_photos(message: Message, state: FSMContext):
    """Handle photo management choices during registration."""
    if message.text == "↩️ بازگشت":
        await show_confirmation_summary(message, state)
        return

    if message.text == "➕ افزودن تصویر جدید":
        await state.set_state(SupplierRegistration.adding_photos)
        await message.answer(
            "🖼 تصاویر جدید خود را ارسال کنید. پس از اتمام روی دکمه 'اتمام ارسال تصاویر' کلیک کنید.",
            reply_markup=get_finish_upload_keyboard()
        )
    elif message.text == "❌ حذف تصاویر":
        data = await state.get_data()
        photos = data.get('portfolio_photos', [])
        if not photos:
            await message.answer("شما هیچ تصویری برای حذف ندارید!")
            return
        
        await state.set_state(SupplierRegistration.removing_photos)
        media = [InputMediaPhoto(media=photo_id, caption=f"تصویر شماره {i+1}") for i, photo_id in enumerate(photos)]
        await message.answer_media_group(media)
        await message.answer("کدام تصویر را می‌خواهید حذف کنید؟", reply_markup=create_photo_list_keyboard(photos))

@router.message(SupplierRegistration.adding_photos, F.photo)
async def registration_add_photo(message: Message, state: FSMContext):
    """Add a photo during registration editing."""
    data = await state.get_data()
    photos = data.get('portfolio_photos', [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(portfolio_photos=photos)
    await message.answer(f"✅ تصویر {len(photos)} اضافه شد.")

@router.message(SupplierRegistration.adding_photos, F.text == "✅ اتمام ارسال تصاویر")
async def registration_finish_adding_photos(message: Message, state: FSMContext):
    """Finish adding photos and return to summary."""
    await message.answer("✅ تصاویر شما به‌روز شد.")
    await show_confirmation_summary(message, state)

@router.message(SupplierRegistration.removing_photos)
async def registration_remove_photo(message: Message, state: FSMContext):
    """Remove a photo during registration editing."""
    data = await state.get_data()
    photos = data.get('portfolio_photos', [])

    if message.text == "✅ اتمام" or message.text == "↩️ بازگشت":
        await message.answer("✅ مدیریت تصاویر تمام شد.")
        await show_confirmation_summary(message, state)
        return

    if message.text.startswith("❌ حذف تصویر "):
        try:
            index_to_remove = int(message.text.split(" ")[-1]) - 1
            if 0 <= index_to_remove < len(photos):
                photos.pop(index_to_remove)
                await state.update_data(portfolio_photos=photos)
                await message.answer(f"تصویر شماره {index_to_remove + 1} حذف شد.", reply_markup=create_photo_list_keyboard(photos))
            else:
                await message.answer("شماره تصویر نامعتبر است.")
        except (ValueError, IndexError):
            await message.answer("دستور نامعتبر است.")
            
# ========== منوی تأمین‌کننده ==========

async def show_supplier_menu(message: Message, state: FSMContext, session: AsyncSession):
    """نمایش منوی اصلی تأمین‌کننده"""
    await message.answer(
        "🎭 منوی تأمین‌کننده\n\n"
        "از گزینه‌های زیر انتخاب کنید:",
        reply_markup=get_supplier_menu_keyboard()
    )
    await state.set_state(SupplierMenu.main_menu)

@router.message(F.text == "👤 مشاهده پروفایل", SupplierMenu.main_menu)
async def view_profile(message: Message, state: FSMContext, session: AsyncSession):
    """مشاهده پروفایل"""
    user = await get_user_by_telegram_id(session, str(message.from_user.id))
    if not user or not user.supplier_profile:
        await message.answer("پروفایل شما یافت نشد!")
        return
    
    supplier = user.supplier_profile
    profile_text = create_supplier_profile_text(supplier)

    if supplier.portfolio_photos:
        try:            
            # Create media group with all photos except the last one without captions
            media = [InputMediaPhoto(media=photo_id) for photo_id in supplier.portfolio_photos[:-1]]
            # Add the last photo with the caption
            media.append(InputMediaPhoto(media=supplier.portfolio_photos[-1], caption=profile_text))
            
            # Send all photos in a media group with the text as caption on last photo
            await message.answer_media_group(media=media)
        except Exception as e:
            logging.error(f"Error sending profile photos: {e}")
            # If media group fails, try sending photos individually
            for photo_id in supplier.portfolio_photos:
                try:
                    await message.answer_photo(photo_id)
                except Exception as photo_e:
                    logging.error(f"Error sending individual photo {photo_id}: {photo_e}")
    else:
        await message.answer(profile_text)

@router.message(F.text == "✏️ ویرایش پروفایل", SupplierMenu.main_menu)
async def edit_profile_start(message: Message, state: FSMContext):
    """شروع فرآیند ویرایش پروفایل"""
    await state.set_state(SupplierEditProfile.choosing_field)
    await message.answer(
        "کدام بخش از پروفایل خود را می‌خواهید ویرایش کنید?",
        reply_markup=get_edit_profile_keyboard()
    )

@router.message(SupplierEditProfile.choosing_field)
async def edit_profile_choose_field(message: Message, state: FSMContext, session: AsyncSession):
    """انتخاب فیلد برای ویرایش"""
    if message.text == "↩️ بازگشت به منو":
        await state.set_state(SupplierMenu.main_menu)
        await message.answer("به منوی تأمین‌کننده بازگشتید.", reply_markup=get_supplier_menu_keyboard())
        return

    if message.text not in EDITABLE_FIELDS:
        await message.answer("لطفاً یک گزینه معتبر از کیبورد انتخاب کنید.")
        return

    # Special handling for photo management
    if message.text == "مدیریت تصاویر":
        await state.set_state(PhotoEditState.choosing_action)
        user = await get_user_by_telegram_id(session, str(message.from_user.id))
        if not user or not user.supplier_profile:
            await message.answer("خطا: پروفایل شما یافت نشد!")
            await state.set_state(SupplierMenu.main_menu)
            await message.answer("به منوی تأمین‌کننده بازگشتید.", reply_markup=get_supplier_menu_keyboard())
            return

        photos = user.supplier_profile.portfolio_photos or []
        await state.update_data(current_photos=photos)

        # Show current photos
        if photos:
            await message.answer("تصاویر فعلی شما:")
            try:
                media = [InputMediaPhoto(media=photo_id) for photo_id in photos]
                await message.answer_media_group(media=media)
            except Exception as e:
                logging.error(f"Error sending media group in photo management: {e}")
                await message.answer("خطا در نمایش تصاویر.")
        
        await message.answer(
            f"شما در حال حاضر {len(photos)} تصویر دارید.\n"
            "چه کاری می‌خواهید انجام دهید؟",
            reply_markup=get_photo_management_keyboard()
        )
        return

    # For other fields
    field_to_edit = EDITABLE_FIELDS[message.text]
    await state.update_data(field_to_edit=field_to_edit, field_to_edit_fa=message.text)
    
    await state.set_state(SupplierEditProfile.entering_value)
    await message.answer(f"لطفاً مقدار جدید برای '{message.text}' را وارد کنید:", reply_markup=get_back_keyboard())

def get_photo_management_keyboard():
    """کیبورد برای مدیریت تصاویر"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ افزودن تصویر جدید")],
            [KeyboardButton(text="❌ حذف تصاویر")],
            [KeyboardButton(text="↩️ بازگشت")]
        ],
        resize_keyboard=True
    )

def create_photo_list_keyboard(photos):
    """ایجاد کیبورد برای لیست عکس‌ها"""
    keyboard = []
    for i, _ in enumerate(photos, 1):
        keyboard.append([KeyboardButton(text=f"❌ حذف تصویر {i}")])
    keyboard.append([KeyboardButton(text="✅ اتمام")])
    keyboard.append([KeyboardButton(text="↩️ بازگشت")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

@router.message(SupplierEditProfile.entering_value)
async def edit_profile_enter_value(message: Message, state: FSMContext, session: AsyncSession):
    """دریافت و ذخیره مقدار جدید برای فیلد"""
    if message.text == "↩️ بازگشت":
        await state.set_state(SupplierEditProfile.choosing_field)
        await message.answer("از کدام بخش می‌خواهید ویرایش کنید?", reply_markup=get_edit_profile_keyboard())
        return

    data = await state.get_data()
    field_to_edit = data.get("field_to_edit")
    field_to_edit_fa = data.get("field_to_edit_fa")

    new_value = message.text
    # Regular field validation
    if field_to_edit == 'age':
        age = validate_age(new_value)
        if not age:
            await message.answer("سن نامعتبر است. لطفاً عدد بین ۱۵ تا ۸۰ وارد کنید.")
            return
        new_value = age
    elif field_to_edit == 'phone_number':
        phone = validate_phone_number(new_value)
        if not phone:
            await message.answer("شماره تماس نامعتبر است.")
            return
        new_value = phone

    try:
        # Update the database
        user = await get_user_by_telegram_id(session, str(message.from_user.id))
        if user and user.supplier_profile:
            setattr(user.supplier_profile, field_to_edit, new_value)
            await session.commit()
            await message.answer(f"✅ '{field_to_edit_fa}' با موفقیت به '{new_value}' تغییر یافت.")
        else:
            await message.answer("خطا: پروفایل شما یافت نشد.")

        # Return to the edit menu
        await state.set_state(SupplierEditProfile.choosing_field)
        await message.answer("می‌توانید بخش دیگری را ویرایش کنید یا بازگردید.", reply_markup=get_edit_profile_keyboard())

    except Exception as e:
        logging.exception(f"Error updating field {field_to_edit}:")
        await message.answer("خطایی در به‌روزرسانی اطلاعات رخ داد.")


@router.message(F.text == "⚙️ تنظیمات", SupplierMenu.main_menu)
async def settings_start(message: Message, state: FSMContext, session: AsyncSession):
    """ورود به منوی تنظیمات"""
    user = await get_user_by_telegram_id(session, str(message.from_user.id))
    if not user:
        await message.answer("خطا: کاربر یافت نشد.")
        return

    await state.set_state(SupplierSettings.menu)
    status = "فعال ✅" if user.is_active else "غیرفعال ❌"
    await message.answer(
        f"⚙️ تنظیمات\n\n"
        f"وضعیت فعلی پروفایل شما: {status}\n\n"
        "در حالت غیرفعال، پروفایل شما در نتایج جستجو نمایش داده نخواهد شد.",
        reply_markup=get_settings_keyboard(user.is_active)
    )

@router.message(SupplierSettings.menu)
async def toggle_active_status(message: Message, state: FSMContext, session: AsyncSession):
    """تغییر وضعیت فعال/غیرفعال پروفایل"""
    user = await get_user_by_telegram_id(session, str(message.from_user.id))
    if not user:
        await message.answer("خطا: کاربر یافت نشد.")
        return

    if message.text == "↩️ بازگشت به منو":
        await state.set_state(SupplierMenu.main_menu)
        await message.answer("به منوی تأمین‌کننده بازگشتید.", reply_markup=get_supplier_menu_keyboard())
        return

    # Toggle the status
    new_status = not user.is_active
    user.is_active = new_status
    await session.commit()

    status_text = "فعال ✅" if new_status else "غیرفعال ❌"
    await message.answer(
        f"وضعیت پروفایل شما با موفقیت به {status_text} تغییر یافت.",
        reply_markup=get_settings_keyboard(new_status)
    )


@router.message(F.text == "🔙 بازگشت به منوی اصلی", SupplierMenu.main_menu)
async def back_to_main_menu(message: Message, state: FSMContext, session: AsyncSession):
    """بازگشت به منوی اصلی"""
    await state.clear()
    await message.answer("به منوی اصلی بازگشتید.", reply_markup=get_main_menu())
    # We need to re-import cmd_start to avoid circular imports
    from handlers.start import cmd_start
    await cmd_start(message, state, session)

@router.message(F.text == "📨 درخواست‌های جدید", SupplierMenu.main_menu)
async def view_new_requests(message: Message, state: FSMContext, session: AsyncSession):
    """مشاهده درخواست‌های جدید"""
    user = await get_user_by_telegram_id(session, str(message.from_user.id))
    if not user or not user.supplier_profile:
        await message.answer("پروفایل شما یافت نشد!")
        return
    
    # دریافت درخواست‌های در انتظار
    stmt = select(Request).where(
        Request.supplier_id == user.supplier_profile.id,
        Request.status == RequestStatus.PENDING
    ).order_by(Request.created_at.desc())
    
    result = await session.execute(stmt)
    requests = result.scalars().all()
    
    if not requests:
        await message.answer("🔔 شما درخواست جدیدی ندارید.")
        return
    
    await message.answer(f"📨 شما {len(requests)} درخواست جدید دارید:")
    
    for req in requests[:5]:  # نمایش 5 درخواست اخیر
        demander = req.demander
        text = f"""
🔸 درخواست از: {demander.full_name or 'بدون نام'}
🏢 شرکت: {demander.company_name or '-'}
📅 تاریخ: {req.created_at.strftime('%Y/%m/%d %H:%M')}
💬 پیام: {req.message or 'بدون پیام'}
"""
        await message.answer(
            text,
            reply_markup=get_request_action_keyboard(req.id)
        )

# ========== Callback Handlers ==========

@router.callback_query(F.data.startswith("accept_request:"))
async def accept_request(callback: CallbackQuery, session: AsyncSession):
    """پذیرفتن درخواست"""
    request_id = int(callback.data.split(":")[1])
    
    # دریافت درخواست
    stmt = select(Request).where(Request.id == request_id)
    result = await session.execute(stmt)
    request = result.scalar_one_or_none()
    
    if not request:
        await callback.answer("درخواست یافت نشد!", show_alert=True)
        return
    
    # به‌روزرسانی وضعیت
    request.status = RequestStatus.ACCEPTED
    request.updated_at = datetime.utcnow()
    await session.commit()
    
    # ارسال نوتیفیکیشن به درخواست‌کننده
    # (این بخش نیاز به پیاده‌سازی سیستم نوتیفیکیشن دارد)
    
    await callback.message.edit_text(
        callback.message.text + "\n\n✅ درخواست پذیرفته شد.",
        reply_markup=None
    )
    await callback.answer("درخواست پذیرفته شد!")

@router.callback_query(F.data.startswith("reject_request:"))
async def reject_request(callback: CallbackQuery, session: AsyncSession):
    """رد کردن درخواست"""
    request_id = int(callback.data.split(":")[1])
    
    # دریافت درخواست
    stmt = select(Request).where(Request.id == request_id)
    result = await session.execute(stmt)
    request = result.scalar_one_or_none()
    
    if not request:
        await callback.answer("درخواست یافت نشد!", show_alert=True)
        return
    
    # به‌روزرسانی وضعیت
    request.status = RequestStatus.REJECTED
    request.updated_at = datetime.utcnow()
    await session.commit()
    
    await callback.message.edit_text(
        callback.message.text + "\n\n❌ درخواست رد شد.",
        reply_markup=None
    )
    await callback.answer("درخواست رد شد!")

# ========== Photo Management Handlers ==========

@router.message(PhotoEditState.choosing_action)
async def photo_edit_action(message: Message, state: FSMContext, session: AsyncSession):
    """مدیریت عکس‌های پروفایل"""
    if message.text == "↩️ بازگشت":
        await state.set_state(SupplierEditProfile.choosing_field)
        await message.answer("از کدام بخش می‌خواهید ویرایش کنید?", reply_markup=get_edit_profile_keyboard())
        return

    if message.text == "➕ افزودن تصویر جدید":
        await state.set_state(PhotoEditState.adding_photos)
        await message.answer(
            "🖼 تصاویر جدید خود را ارسال کنید.\n"
            "پس از اتمام روی دکمه 'اتمام ارسال تصاویر' کلیک کنید.",
            reply_markup=get_finish_upload_keyboard()
        )
        return

    if message.text == "❌ حذف تصاویر":
        data = await state.get_data()
        photos = data.get('current_photos', [])
        if not photos:
            await message.answer("شما هیچ تصویری ندارید!")
            return

        # نمایش عکس‌های فعلی با شماره
        media = []
        for i, photo_id in enumerate(photos, 1):
            media.append(InputMediaPhoto(
                media=photo_id,
                caption=f"تصویر شماره {i}"
            ))
        await message.answer_media_group(media=media)

        await state.set_state(PhotoEditState.removing_photos)
        await message.answer(
            "برای حذف هر تصویر، شماره آن را انتخاب کنید:",
            reply_markup=create_photo_list_keyboard(photos)
        )
        return

@router.message(PhotoEditState.adding_photos)
async def add_photos(message: Message, state: FSMContext, session: AsyncSession):
    """افزودن عکس جدید"""
    if message.text == "↩️ بازگشت":
        await state.set_state(PhotoEditState.choosing_action)
        await message.answer(
            "چه کاری می‌خواهید انجام دهید؟",
            reply_markup=get_photo_management_keyboard()
        )
        return

    if message.text == "✅ اتمام ارسال تصاویر":
        data = await state.get_data()
        current_photos = data.get('current_photos', [])
        
        user = await get_user_by_telegram_id(session, str(message.from_user.id))
        if user and user.supplier_profile:
            user.supplier_profile.portfolio_photos = current_photos
            await session.commit()
            
            await message.answer("✅ تصاویر با موفقیت به‌روزرسانی شدند.")
            await state.set_state(SupplierEditProfile.choosing_field)
            await message.answer(
                "می‌توانید بخش دیگری را ویرایش کنید یا بازگردید.",
                reply_markup=get_edit_profile_keyboard()
            )
        return

    if message.photo:
        data = await state.get_data()
        current_photos = data.get('current_photos', [])
        current_photos.append(message.photo[-1].file_id)
        await state.update_data(current_photos=current_photos)
        await message.answer(
            f"✅ تصویر {len(current_photos)} اضافه شد.\n"
            "می‌توانید تصویر دیگری ارسال کنید یا روی دکمه 'اتمام ارسال تصاویر' کلیک کنید."
        )
    else:
        await message.answer("❌ لطفاً یک تصویر ارسال کنید.")

@router.message(PhotoEditState.removing_photos)
async def remove_photos(message: Message, state: FSMContext, session: AsyncSession):
    """حذف عکس"""
    if message.text == "↩️ بازگشت":
        await state.set_state(PhotoEditState.choosing_action)
        await message.answer(
            "چه کاری می‌خواهید انجام دهید؟",
            reply_markup=get_photo_management_keyboard()
        )
        return

    if message.text == "✅ اتمام":
        data = await state.get_data()
        current_photos = data.get('current_photos', [])
        
        user = await get_user_by_telegram_id(session, str(message.from_user.id))
        if user and user.supplier_profile:
            user.supplier_profile.portfolio_photos = current_photos
            await session.commit()
            
            await message.answer("✅ تصاویر با موفقیت به‌روزرسانی شدند.")
            await state.set_state(SupplierEditProfile.choosing_field)
            await message.answer(
                "می‌توانید بخش دیگری را ویرایش کنید یا بازگردید.",
                reply_markup=get_edit_profile_keyboard()
            )
        return

    if message.text.startswith("❌ حذف تصویر "):
        try:
            index = int(message.text.replace("❌ حذف تصویر ", "")) - 1
            data = await state.get_data()
            current_photos = data.get('current_photos', [])
            
            if 0 <= index < len(current_photos):
                deleted_photo = current_photos.pop(index)
                await state.update_data(current_photos=current_photos)
                
                # Show remaining photos
                if current_photos:
                    media = [InputMediaPhoto(media=photo_id) for photo_id in current_photos]
                    await message.answer_media_group(media=media)
                
                await message.answer(
                    f"✅ تصویر {index + 1} حذف شد.\n"
                    f"تعداد تصاویر باقی‌مانده: {len(current_photos)}",
                    reply_markup=create_photo_list_keyboard(current_photos)
                )
            else:
                await message.answer("❌ شماره تصویر نامعتبر است.")
        except ValueError:
            await message.answer("❌ لطفاً یک گزینه معتبر انتخاب کنید.")

# ========== Helper Functions ==========

from utils.users import get_or_create_user

async def get_user_by_telegram_id(session: AsyncSession, telegram_id: str) -> User:
    """دریافت کاربر با telegram_id"""
    stmt = select(User).options(selectinload(User.supplier_profile)).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

def create_supplier_summary(data: dict) -> str:
    """ایجاد خلاصه اطلاعات تأمین‌کننده"""
    coop_types_fa = {
        'in_person': 'حضوری',
        'project_based': 'پروژه‌ای',
        'part_time': 'پاره‌وقت'
    }
    
    work_styles_fa = {
        'fashion': 'فشن',
        'advertising': 'تبلیغاتی',
        'religious': 'مذهبی',
        'children': 'کودک',
        'sports': 'ورزشی',
        'artistic': 'هنری',
        'outdoor': 'فضای باز',
        'studio': 'استودیویی'
    }
    
    summary = f"""
👤 اطلاعات پایه:
نام: {data.get('full_name', '-')}
جنسیت: {data.get('gender', '-')}
سن: {data.get('age', '-')} سال
تلفن: {data.get('phone_number', '-')}
اینستاگرام: {data.get('instagram_id', '-')}
نمونه کار: {len(data.get('portfolio_photos', []))} تصویر

📏 مشخصات ظاهری:
قد: {data.get('height', '-')} سانتی‌متر
وزن: {data.get('weight', '-')} کیلوگرم
رنگ مو: {data.get('hair_color', '-')}
رنگ چشم: {data.get('eye_color', '-')}
رنگ پوست: {data.get('skin_color', '-')}
سایز بالاتنه: {data.get('top_size', '-')}
سایز پایین‌تنه: {data.get('bottom_size', '-')}
ویژگی خاص: {data.get('special_features', '-')}

💼 اطلاعات همکاری:
محدوده‌های قیمت:
{format_pricing_data(data.get('pricing_data', {}))}
شهر: {data.get('city', '-')}
محدوده: {data.get('area', '-')}
نوع همکاری: {', '.join([coop_types_fa.get(t, t) for t in data.get('cooperation_types', [])])}
سبک کاری: {', '.join([work_styles_fa.get(s, s) for s in data.get('work_styles', [])])}

📋 سابقه و توضیحات:
برندها: {data.get('brand_experience', '-')}
توضیحات: {data.get('additional_notes', '-')}
"""
    return summary

def create_supplier_profile_text(supplier: Supplier) -> str:
    """ایجاد متن پروفایل تأمین‌کننده"""
    coop_types_fa = {
        'in_person': 'حضوری',
        'project_based': 'پروژه‌ای',
        'part_time': 'پاره‌وقت'
    }
    
    work_styles_fa = {
        'fashion': 'فشن',
        'advertising': 'تبلیغاتی',
        'religious': 'مذهبی',
        'children': 'کودک',
        'sports': 'ورزشی',
        'artistic': 'هنری',
        'outdoor': 'فضای باز',
        'studio': 'استودیویی'
    }
    
    profile = f"""
🎭 پروفایل شما

👤 {supplier.full_name}
📱 {supplier.phone_number}
📍 {supplier.city} - {supplier.area}

💰 قیمت: {format_price_range(supplier)}
🤝 نوع همکاری: {', '.join([coop_types_fa.get(t, t) for t in supplier.cooperation_types])}
🎨 سبک: {', '.join([work_styles_fa.get(s, s) for s in supplier.work_styles])}

📊 مشخصات:
- {supplier.gender} - {supplier.age} ساله
- قد: {supplier.height} cm | وزن: {supplier.weight} kg
- موی {supplier.hair_color} | چشم {supplier.eye_color}
"""
    
    if supplier.instagram_id:
        profile += f"\n📷 @{supplier.instagram_id}"
    
    return profile

def extract_price_min(price_range: str) -> float:
    """استخراج حداقل قیمت از رشته"""
    # پیاده‌سازی ساده - باید بهبود یابد
    numbers = re.findall(r'\d+', price_range.replace(',', ''))
    return float(numbers[0]) * 1000 if numbers else 0

def extract_price_max(price_range: str) -> float:
    """استخراج حداکثر قیمت از رشته"""
    numbers = re.findall(r'\d+', price_range.replace(',', ''))
    return float(numbers[1]) * 1000 if len(numbers) > 1 else float(numbers[0]) * 1000 if numbers else 0

def extract_price_unit(price_range: str) -> str:
    """استخراج واحد قیمت"""
    if 'ساعت' in price_range:
        return 'hourly'
    elif 'روز' in price_range:
        return 'daily'
    return 'project'

def format_price_range(supplier: Supplier) -> str:
    """فرمت کردن محدوده قیمت"""
    unit_fa = {
        'hourly': 'ساعتی',
        'daily': 'روزی',
        'project': 'پروژه‌ای'
    }
    
    min_price = f"{supplier.price_range_min:,.0f}"
    max_price = f"{supplier.price_range_max:,.0f}"
    unit = unit_fa.get(supplier.price_unit, '')
    
    if supplier.price_range_min == supplier.price_range_max:
        return f"{unit} {min_price} تومان"
    else:
        return f"{unit} {min_price} تا {max_price} تومان"