import re
import logging
from aiogram import Router, F, types
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from database.models import User, Supplier, UserRole, Request, RequestStatus
from states.supplier import SupplierRegistration, SupplierMenu, SupplierEditProfile, PhotoEditState, SupplierSettings
from keyboards.reply import *
from keyboards.inline import get_request_action_keyboard
from utils.validators import validate_phone_number, validate_age, validate_height_weight
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from sqlalchemy.orm import selectinload
from utils.users import get_or_create_user

router = Router()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def show_supplier_menu(message: Message, state: FSMContext, session: AsyncSession):
    """نمایش منوی اصلی تأمین‌کننده"""
    await message.answer(
        "🎭 منوی تأمین‌کننده\n\n"
        "از گزینه‌های زیر انتخاب کنید:",
        reply_markup=get_supplier_menu_keyboard()
    )
    await state.set_state(SupplierMenu.main_menu)

EDITABLE_FIELDS = {
    "نام کامل": "full_name", "سن": "age", "شماره تماس": "phone_number", "اینستاگرام": "instagram_id",
    "قد": "height", "وزن": "weight", "رنگ مو": "hair_color", "رنگ چشم": "eye_color", "رنگ پوست": "skin_color",
    "سایز بالاتنه": "top_size", "سایز پایین‌تنه": "bottom_size", "ویژگی‌های خاص": "special_features",
    "محدوده قیمت": "price_range", "شهر": "city", "محدوده فعالیت": "area",
    "انواع همکاری": "cooperation_types", "سبک‌های کاری": "work_styles",
    "سابقه برند": "brand_experience", "توضیحات": "additional_notes", "مدیریت تصاویر": "portfolio_photos",
}

# ========== Registration Process ========== 

@router.message(SupplierRegistration.full_name)
async def process_full_name(message: Message, state: FSMContext):
    if message.text == "↩️ بازگشت":
        await state.clear()
        await message.answer("به منوی اصلی بازگشتید.", reply_markup=get_main_menu())
        return
    if len(message.text) < 3:
        await message.answer("لطفاً نام کامل خود را وارد کنید (حداقل ۳ حرف):")
        return
    await state.update_data(full_name=message.text)
    await message.answer("🔸 جنسیت خود را انتخاب کنید:", reply_markup=get_gender_keyboard())
    await state.set_state(SupplierRegistration.gender)

# ... (Other registration steps remain the same, so they are omitted for brevity) ...

@router.message(SupplierRegistration.additional_notes)
async def process_additional_notes(message: Message, state: FSMContext):
    if message.text == "↩️ بازگشت":
        await state.set_state(SupplierRegistration.brand_experience)
        await message.answer("🔸 نام برندهایی که با آن‌ها همکاری داشته‌اید را وارد کنید:", reply_markup=get_skip_keyboard())
        return
    
    additional_notes = None if message.text == "⏭ رد کردن" else message.text
    await state.update_data(additional_notes=additional_notes)
    await show_confirmation_summary(message, state)
    await state.set_state(SupplierRegistration.confirm)

async def show_confirmation_summary(message: types.Message, state: FSMContext):
    data = await state.get_data()
    summary = create_supplier_summary(data)
    photos = data.get('portfolio_photos', [])
    
    if photos:
        media_group = [types.InputMediaPhoto(media=photo_id) for photo_id in photos]
        if media_group:
            media_group[0].caption = f"لطفاً اطلاعات خود را بررسی کنید:\n\n{summary}"
        try:
            await message.answer_media_group(media_group)
        except Exception as e:
            logger.error(f"Error sending media group for confirmation: {e}")
            await message.answer(f"لطفاً اطلاعات خود را بررسی کنید:\n\n{summary}")
            for photo_id in photos:
                await message.answer_photo(photo_id)
    else:
        await message.answer(f"لطفاً اطلاعات خود را بررسی کنید:\n\n{summary}")

    await message.answer("آیا اطلاعات فوق را تأیید می‌کنید؟", reply_markup=get_confirm_keyboard())

@router.message(SupplierRegistration.confirm)
async def process_confirmation(message: Message, state: FSMContext, session: AsyncSession):
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer("ثبت‌نام لغو شد.", reply_markup=ReplyKeyboardRemove())
        return
    
    if message.text == "🔄 ویرایش اطلاعات":
        await state.set_state(SupplierRegistration.editing_field)
        await message.answer("کدام بخش را می‌خواهید ویرایش کنید؟", reply_markup=get_edit_profile_keyboard())
        return
    
    if message.text == "✅ تأیید نهایی":
        try:
            data = await state.get_data()
            user = await get_or_create_user(session, message.from_user, UserRole.SUPPLIER)
            
            price_min, price_max, price_unit = extract_price_details(data.get('price_range', ''))
            
            supplier_data = {
                'full_name': data['full_name'], 'gender': data['gender'], 'age': data['age'],
                'phone_number': data['phone_number'], 'instagram_id': data.get('instagram_id'),
                'portfolio_photos': data.get('portfolio_photos', []), 'height': data['height'],
                'weight': data['weight'], 'hair_color': data['hair_color'], 'eye_color': data['eye_color'],
                'skin_color': data['skin_color'], 'top_size': data['top_size'], 'bottom_size': data['bottom_size'],
                'special_features': data.get('special_features'), 'price_range_min': price_min,
                'price_range_max': price_max, 'price_unit': price_unit, 'city': data['city'], 'area': data['area'],
                'cooperation_types': data.get('cooperation_types', []), 'work_styles': data.get('work_styles', []),
                'brand_experience': data.get('brand_experience'), 'additional_notes': data.get('additional_notes')
            }

            result = await session.execute(select(Supplier).filter_by(user_id=user.id))
            supplier = result.scalar_one_or_none()

            if supplier:
                for key, value in supplier_data.items():
                    setattr(supplier, key, value)
            else:
                supplier = Supplier(user_id=user.id, **supplier_data)
                session.add(supplier)
            
            await session.commit()
            await message.answer("✅ ثبت‌نام شما با موفقیت انجام شد!", reply_markup=get_supplier_menu_keyboard())
            await state.set_state(SupplierMenu.main_menu)
            
        except Exception as e:
            logger.exception("Error during supplier registration confirmation:")
            await message.answer("❌ خطایی در ثبت اطلاعات رخ داد. لطفاً مجدداً تلاش کنید.", reply_markup=ReplyKeyboardRemove())
            await state.clear()

# ========== Supplier Menu ========== 

@router.message(F.text == "👤 مشاهده پروفایل", StateFilter(SupplierMenu.main_menu))
async def view_profile(message: Message, session: AsyncSession):
    user = await get_user_by_telegram_id(session, str(message.from_user.id))
    if not user or not user.supplier_profile:
        await message.answer("پروفایل شما یافت نشد!")
        return
    
    supplier = user.supplier_profile
    profile_text = create_supplier_profile_text(supplier)
    
    if supplier.portfolio_photos:
        try:
            media = [InputMediaPhoto(media=photo_id) for photo_id in supplier.portfolio_photos]
            if media:
                media[0].caption = profile_text
            await message.answer_media_group(media=media)
        except Exception as e:
            logger.error(f"Error sending profile photos: {e}")
            await message.answer(profile_text) # Fallback
    else:
        await message.answer(profile_text)

# ... (Other menu handlers remain the same) ...

# ========== Helper Functions ========== 

async def get_user_by_telegram_id(session: AsyncSession, telegram_id: str) -> User | None:
    stmt = select(User).options(selectinload(User.supplier_profile)).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

def create_supplier_summary(data: dict) -> str:
    coop_types_fa = {'in_person': 'حضوری', 'project_based': 'پروژه‌ای', 'part_time': 'پاره‌وقت'}
    work_styles_fa = {
        'fashion': 'فشن', 'advertising': 'تبلیغاتی', 'religious': 'مذهبی', 'children': 'کودک',
        'sports': 'ورزشی', 'artistic': 'هنری', 'outdoor': 'فضای باز', 'studio': 'استودیویی'
    }
    
    summary = f"👤 **اطلاعات پایه:**\n"
    summary += f"نام: {data.get('full_name', '-')}\n"
    summary += f"جنسیت: {data.get('gender', '-')}\n"
    summary += f"سن: {data.get('age', '-')} سال\n"
    summary += f"تلفن: {data.get('phone_number', '-')}\n"
    summary += f"اینستاگرام: @{data.get('instagram_id', '-')}\n"
    summary += f"نمونه کار: {len(data.get('portfolio_photos', []))} تصویر\n\n"

    summary += f"📏 **مشخصات ظاهری:**\n"
    summary += f"قد: {data.get('height', '-')} سانتی‌متر\n"
    summary += f"وزن: {data.get('weight', '-')} کیلوگرم\n"
    summary += f"ویژگی خاص: {data.get('special_features', '-')}\n\n"

    summary += f"💼 **اطلاعات همکاری:**\n"
    summary += f"محدوده قیمت: {data.get('price_range', 'توافقی')}\n"
    summary += f"شهر: {data.get('city', '-')}\n"
    summary += f"نوع همکاری: {', '.join([coop_types_fa.get(t, t) for t in data.get('cooperation_types', [])])}\n"
    summary += f"سبک کاری: {', '.join([work_styles_fa.get(s, s) for s in data.get('work_styles', [])])}\n\n"
    
    summary += f"📋 **سابقه و توضیحات:**\n"
    summary += f"برندها: {data.get('brand_experience', '-')}\n"
    summary += f"توضیحات: {data.get('additional_notes', '-')}"
    
    return summary

def create_supplier_profile_text(supplier: Supplier) -> str:
    coop_types_fa = {'in_person': 'حضوری', 'project_based': 'پروژه‌ای', 'part_time': 'پاره‌وقت'}
    work_styles_fa = {
        'fashion': 'فشن', 'advertising': 'تبلیغاتی', 'religious': 'مذهبی', 'children': 'کودک',
        'sports': 'ورزشی', 'artistic': 'هنری', 'outdoor': 'فضای باز', 'studio': 'استودیویی'
    }
    
    profile = f"🎭 **پروفایل شما**\n\n"
    profile += f"👤 {supplier.full_name}\n"
    profile += f"📱 {supplier.phone_number}\n"
    profile += f"📍 {supplier.city} - {supplier.area}\n"
    if supplier.instagram_id:
        profile += f"📷 @{supplier.instagram_id}\n"
    
    profile += f"\n💰 **قیمت:** {format_price_range(supplier)}\n"
    profile += f"🤝 **نوع همکاری:** {', '.join([coop_types_fa.get(t, t) for t in supplier.cooperation_types or []])}\n"
    profile += f"🎨 **سبک:** {', '.join([work_styles_fa.get(s, s) for s in supplier.work_styles or []])}\n"
    
    profile += f"\n📊 **مشخصات:**\n"
    profile += f"- {supplier.gender} - {supplier.age} ساله\n"
    profile += f"- قد: {supplier.height} cm | وزن: {supplier.weight} kg\n"
    profile += f"- موی {supplier.hair_color} | چشم {supplier.eye_color}\n"
    
    return profile

def extract_price_details(price_range_str: str) -> (float | None, float | None, str | None):
    if not price_range_str or 'توافقی' in price_range_str:
        return None, None, 'project'

    numbers = [int(n) * 1000 for n in re.findall(r'\d+', price_range_str)]
    min_price = numbers[0] if numbers else None
    max_price = numbers[1] if len(numbers) > 1 else min_price
    
    unit = 'project'
    if 'ساعت' in price_range_str: unit = 'hourly'
    elif 'روز' in price_range_str: unit = 'daily'
        
    return min_price, max_price, unit

def format_price_range(supplier: Supplier) -> str:
    if not supplier.price_range_min:
        return "توافقی"
        
    unit_fa = {'hourly': 'ساعتی', 'daily': 'روزی', 'project': 'پروژه‌ای'}
    unit = unit_fa.get(supplier.price_unit, '')
    
    min_price = f"{supplier.price_range_min:,.0f}"
    max_price = f"{supplier.price_range_max:,.0f}"
    
    if supplier.price_range_min == supplier.price_range_max:
        return f"{unit} {min_price} تومان"
    else:
        return f"{unit} {min_price} تا {max_price} تومان"

# The rest of the file (edit handlers, etc.) is omitted for brevity as it remains unchanged.
# A placeholder comment indicates that the rest of the original file content should follow.
# ... (rest of the original file content for supplier.py)
