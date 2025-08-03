from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime

from database.models import User, Supplier, Demander, Request, RequestStatus
from keyboards.reply import get_main_menu_keyboard
from keyboards.inline import get_profile_actions_keyboard, get_request_detail_keyboard
from states.common import ProfileEdit
from utils.validators import validate_phone_number
import logging

logger = logging.getLogger(__name__)
router = Router()

# دستورات عمومی
@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext, session: AsyncSession):
    """بازگشت به منوی اصلی"""
    await state.clear()
    
    # بررسی نقش کاربر
    user_result = await session.execute(
        select(User).where(User.telegram_id == str(message.from_user.id))
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        await message.answer(
            "لطفاً ابتدا با دستور /start شروع کنید.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    keyboard = None
    if user.role == 'supplier':
        from keyboards.reply import get_supplier_menu_keyboard
        keyboard = get_supplier_menu_keyboard()
        text = "📋 منوی تأمین‌کننده"
    elif user.role == 'demander':
        from keyboards.reply import get_demander_menu_keyboard
        keyboard = get_demander_menu_keyboard()
        text = "📋 منوی درخواست‌کننده"
    else:
        keyboard = get_main_menu_keyboard()
        text = "منوی اصلی"
    
    await message.answer(text, reply_markup=keyboard)

@router.message(Command("help"))
async def cmd_help(message: Message):
    """راهنمای استفاده از ربات"""
    help_text = """
📚 راهنمای استفاده از ربات

🎭 برای تأمین‌کنندگان:
- ثبت‌نام و تکمیل پروفایل
- مشاهده درخواست‌های دریافتی
- پذیرش یا رد درخواست‌ها
- ویرایش اطلاعات پروفایل

👤 برای درخواست‌کنندگان:
- جستجوی تأمین‌کنندگان
- فیلتر بر اساس شهر، جنسیت، سن و...
- ارسال درخواست وقت
- مشاهده وضعیت درخواست‌ها

دستورات مفید:
/start - شروع مجدد
/menu - بازگشت به منو
/profile - مشاهده پروفایل
/help - این راهنما

برای پشتیبانی: @support
"""
    await message.answer(help_text)

@router.message(Command("profile"))
async def cmd_profile(message: Message, session: AsyncSession):
    """مشاهده پروفایل کاربر"""
    # دریافت اطلاعات کاربر
    user_result = await session.execute(
        select(User).where(User.telegram_id == str(message.from_user.id))
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        await message.answer("شما هنوز ثبت‌نام نکرده‌اید! از /start شروع کنید.")
        return
    
    profile_text = f"👤 پروفایل شما\n\n"
    
    if user.role == 'supplier':
        supplier_result = await session.execute(
            select(Supplier).where(Supplier.user_id == user.id)
        )
        supplier = supplier_result.scalar_one_or_none()
        
        if supplier:
            profile_text += f"""
🎭 نقش: تأمین‌کننده
📱 شماره: {supplier.phone_number}
👤 نام: {supplier.full_name}
📍 شهر: {supplier.city}
💰 قیمت: {format_price_for_profile(supplier)}
📅 تاریخ ثبت‌نام: {supplier.created_at.strftime('%Y/%m/%d')}
"""
            if supplier.instagram_id:
                profile_text += f"📷 اینستاگرام: @{supplier.instagram_id}\n"
                
    elif user.role == 'demander':
        demander_result = await session.execute(
            select(Demander).where(Demander.user_id == user.id)
        )
        demander = demander_result.scalar_one_or_none()
        
        if demander:
            profile_text += f"""
👤 نقش: درخواست‌کننده
📱 شماره: {demander.phone_number}
👤 نام: {demander.full_name}
🏢 شرکت: {demander.company_name or '-'}
📅 تاریخ ثبت‌نام: {demander.created_at.strftime('%Y/%m/%d')}
"""
    
    await message.answer(
        profile_text,
        reply_markup=get_profile_actions_keyboard(user.role)
    )

def format_price_for_profile(supplier):
    """فرمت قیمت برای نمایش در پروفایل"""
    if not supplier.pricing_data:
        return "توافقی"

    # Try to find a daily or hourly price to show
    price_info = None
    unit = ""
    if 'daily' in supplier.pricing_data and isinstance(supplier.pricing_data.get('daily'), dict):
        price_info = supplier.pricing_data['daily']
        unit = "روزی"
    elif 'hourly' in supplier.pricing_data and isinstance(supplier.pricing_data.get('hourly'), dict):
        price_info = supplier.pricing_data['hourly']
        unit = "ساعتی"
    
    if not price_info:
        # If no daily/hourly, find the first available price
        for p_type, p_info in supplier.pricing_data.items():
            if p_type != 'category_based' and isinstance(p_info, dict):
                price_info = p_info
                unit = {'per_cloth': 'هر لباس'}.get(p_type, 'توافقی')
                break

    if not price_info:
        return "توافقی"

    min_price = price_info.get('min', 0) * 1000
    max_price = price_info.get('max', 0) * 1000

    if min_price == max_price:
        return f"{unit} {min_price:,.0f} تومان"
    else:
        return f"{unit} {min_price:,.0f} تا {max_price:,.0f} تومان"

# مدیریت درخواست‌ها
@router.message(F.text == "📥 درخواست‌های من")
async def my_requests(message: Message, session: AsyncSession):
    """نمایش درخواست‌های کاربر"""
    user_result = await session.execute(
        select(User).where(User.telegram_id == str(message.from_user.id))
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        await message.answer("لطفاً ابتدا ثبت‌نام کنید.")
        return
    
    # بر اساس نقش کاربر
    if user.role == 'supplier':
        await show_supplier_requests(message, user, session)
    elif user.role == 'demander':
        await show_demander_requests(message, user, session)

async def show_supplier_requests(message: Message, user: User, session: AsyncSession):
    """نمایش درخواست‌های دریافتی برای تأمین‌کننده"""
    # دریافت supplier
    supplier_result = await session.execute(
        select(Supplier).where(Supplier.user_id == user.id)
    )
    supplier = supplier_result.scalar_one_or_none()
    
    if not supplier:
        await message.answer("پروفایل تأمین‌کننده یافت نشد!")
        return
    
    # دریافت درخواست‌های pending
    requests_result = await session.execute(
        select(Request)
        .where(Request.supplier_id == supplier.id)
        .where(Request.status == RequestStatus.PENDING)
        .order_by(Request.created_at.desc())
    )
    requests = requests_result.scalars().all()
    
    if not requests:
        await message.answer("📭 شما درخواست جدیدی ندارید.")
        return
    
    text = f"📥 درخواست‌های دریافتی ({len(requests)} مورد):\n\n"
    
    for i, req in enumerate(requests, 1):
        text += f"{i}. از: {req.demander.full_name}\n"
        text += f"   زمان: {req.created_at.strftime('%Y/%m/%d %H:%M')}\n"
        text += f"   وضعیت: در انتظار پاسخ\n\n"
    
    await message.answer(text)
    
    # نمایش جزئیات هر درخواست
    for req in requests[:5]:  # حداکثر 5 درخواست اخیر
        await message.answer(
            f"👤 {req.demander.full_name}\n"
            f"💬 {req.message[:200]}{'...' if len(req.message) > 200 else ''}",
            reply_markup=get_request_detail_keyboard(req.id)
        )

async def show_demander_requests(message: Message, user: User, session: AsyncSession):
    """نمایش درخواست‌های ارسالی برای درخواست‌کننده"""
    # دریافت demander
    demander_result = await session.execute(
        select(Demander).where(Demander.user_id == user.id)
    )
    demander = demander_result.scalar_one_or_none()
    
    if not demander:
        await message.answer("پروفایل درخواست‌کننده یافت نشد!")
        return
    
    # دریافت درخواست‌های ارسالی
    requests_result = await session.execute(
        select(Request)
        .where(Request.demander_id == demander.id)
        .order_by(Request.created_at.desc())
        .limit(10)
    )
    requests = requests_result.scalars().all()
    
    if not requests:
        await message.answer("📭 شما هنوز درخواستی ارسال نکرده‌اید.")
        return
    
    text = "📤 درخواست‌های ارسالی:\n\n"
    
    status_emoji = {
        RequestStatus.PENDING: "⏳",
        RequestStatus.ACCEPTED: "✅",
        RequestStatus.REJECTED: "❌"
    }
    
    status_text = {
        RequestStatus.PENDING: "در انتظار",
        RequestStatus.ACCEPTED: "پذیرفته شده",
        RequestStatus.REJECTED: "رد شده"
    }
    
    for req in requests:
        text += f"{status_emoji.get(req.status, '❓')} به: {req.supplier.full_name}\n"
        text += f"   زمان: {req.created_at.strftime('%Y/%m/%d %H:%M')}\n"
        text += f"   وضعیت: {status_text.get(req.status, 'نامشخص')}\n"
        
        if req.status == RequestStatus.ACCEPTED and req.response_message:
            text += f"   پیام: {req.response_message[:50]}...\n"
        
        text += "\n"
    
    await message.answer(text)

# Callback handlers
@router.callback_query(F.data == "edit_profile")
async def edit_profile_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """شروع فرآیند ویرایش پروفایل"""
    await callback.answer()
    
    user_result = await session.execute(
        select(User).where(User.telegram_id == str(callback.from_user.id))
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        await callback.message.answer("خطا در دریافت اطلاعات کاربر!")
        return
    
    if user.role == 'supplier':
        # منوی ویرایش برای تأمین‌کننده
        text = """
🛠 کدام بخش را می‌خواهید ویرایش کنید؟

1️⃣ اطلاعات پایه (نام، شماره)
2️⃣ مشخصات ظاهری
3️⃣ اطلاعات همکاری
4️⃣ سبک کاری
5️⃣ توضیحات

برای انصراف: /cancel
"""
    else:
        # منوی ویرایش برای درخواست‌کننده
        text = """
🛠 کدام بخش را می‌خواهید ویرایش کنید؟

1️⃣ نام و نام خانوادگی
2️⃣ شماره تماس
3️⃣ نام شرکت

برای انصراف: /cancel
"""
    
    await callback.message.answer(text)
    await state.set_state(ProfileEdit.selecting_field)

@router.message(StateFilter(ProfileEdit.selecting_field))
async def select_field_to_edit(message: Message, state: FSMContext, session: AsyncSession):
    """انتخاب فیلد برای ویرایش"""
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ ویرایش لغو شد.", reply_markup=get_main_menu_keyboard())
        return
    
    choice = message.text.strip()
    
    # ذخیره انتخاب
    await state.update_data(edit_choice=choice)
    
    # بر اساس انتخاب، درخواست مقدار جدید
    if choice == "1":
        await message.answer("نام و نام خانوادگی جدید را وارد کنید:")
        await state.set_state(ProfileEdit.editing_name)
    elif choice == "2":
        await message.answer("شماره تماس جدید را وارد کنید:")
        await state.set_state(ProfileEdit.editing_phone)
    # و الی آخر...

@router.callback_query(F.data == "delete_profile")
async def delete_profile_callback(callback: CallbackQuery, session: AsyncSession):
    """حذف پروفایل - نیاز به تأیید"""
    await callback.answer("این قابلیت فعلاً در دسترس نیست.", show_alert=True)

# مدیریت لغو عملیات
@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """لغو هر عملیات در حال انجام"""
    current_state = await state.get_state()
    
    if current_state is None:
        await message.answer("عملیاتی برای لغو وجود ندارد.")
        return
    
    await state.clear()
    await message.answer(
        "❌ عملیات لغو شد.",
        reply_markup=get_main_menu_keyboard()
    )

# Error handler
@router.message()
async def handle_unknown_message(message: Message):
    """مدیریت پیام‌های ناشناخته"""
    await message.answer(
        "❓ دستور نامعتبر!\n"
        "از منو استفاده کنید یا /help را امتحان کنید."
    )
