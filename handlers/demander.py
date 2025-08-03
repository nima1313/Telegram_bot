from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List
import math
import logging

from database.models import User, Demander, Supplier, UserRole, Request, RequestStatus
from states.demander import DemanderRegistration, DemanderSearch
from keyboards.reply import *
from keyboards.inline import *
from utils.users import get_or_create_user

router = Router()

# ========== ثبت‌نام درخواست‌کننده ==========

@router.message(DemanderRegistration.full_name)
async def process_demander_name(message: Message, state: FSMContext):
    """پردازش نام درخواست‌کننده"""
    if message.text == "↩️ بازگشت":
        await state.clear()
        await message.answer("به منوی اصلی بازگشتید.", reply_markup=get_main_menu())
        return
    
    if len(message.text) < 3:
        await message.answer("لطفاً نام کامل خود را وارد کنید (حداقل ۳ حرف):")
        return
    
    await state.update_data(full_name=message.text)
    await message.answer(
        "🔸 نام شرکت یا برند خود را وارد کنید (اختیاری):\n"
        "برای رد کردن روی 'رد کردن' کلیک کنید.",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(DemanderRegistration.company_name)

@router.message(DemanderRegistration.company_name)
async def process_company_name(message: Message, state: FSMContext):
    """پردازش نام شرکت"""
    if message.text == "↩️ بازگشت":
        await message.answer(
            "🔸 نام و نام خانوادگی خود را وارد کنید:",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(DemanderRegistration.full_name)
        return
    
    company_name = None if message.text == "⏭ رد کردن" else message.text
    await state.update_data(company_name=company_name)
    
    await message.answer(
        "🔸 شماره تماس خود را وارد کنید:\n"
        "مثال: 09123456789",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(DemanderRegistration.phone_number)

@router.message(DemanderRegistration.phone_number)
async def process_demander_phone(message: Message, state: FSMContext, session: AsyncSession):
    """پردازش شماره تماس و تکمیل ثبت‌نام"""
    if message.text == "↩️ بازگشت":
        await message.answer(
            "🔸 نام شرکت یا برند خود را وارد کنید:",
            reply_markup=get_skip_keyboard()
        )
        await state.set_state(DemanderRegistration.company_name)
        return
    
    from utils.validators import validate_phone_number
    phone = validate_phone_number(message.text)
    if not phone:
        await message.answer(
            "شماره تماس نامعتبر است. لطفاً شماره را به صورت صحیح وارد کنید:\n"
            "مثال: 09123456789"
        )
        return
    
    try:
        data = await state.get_data()
        
        # ایجاد یا به‌روزرسانی کاربر
        user = await get_or_create_user(session, message.from_user, UserRole.DEMANDER)
        user.role = UserRole.DEMANDER
        
        # ایجاد پروفایل درخواست‌کننده
        demander = Demander(
            user_id=user.id,
            full_name=data['full_name'],
            company_name=data.get('company_name'),
            phone_number=phone
        )
        
        session.add(demander)
        await session.commit()
        
        await message.answer(
            "✅ ثبت‌نام شما با موفقیت انجام شد!\n\n"
            "اکنون می‌توانید جستجوی خود را شروع کنید.",
            reply_markup=ReplyKeyboardRemove()
        )
        
        # نمایش منوی جستجو
        await show_search_menu(message, state, session)
        
    except Exception as e:
        logging.exception("Error during demander registration:")
        await message.answer(
            "❌ خطایی در ثبت اطلاعات رخ داد. لطفاً مجدداً تلاش کنید.",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()

# ========== جستجوی تأمین‌کنندگان ==========

async def show_search_menu(message: Message, state: FSMContext, session: AsyncSession):
    """نمایش منوی جستجو"""
    await message.answer(
        "🔍 جستجوی تأمین‌کننده\n\n"
        "برای شروع جستجو، ابتدا شهر مورد نظر خود را وارد کنید:\n"
        "مثال: تهران، کرج، اصفهان",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(DemanderSearch.city)

@router.message(DemanderSearch.city)
async def process_search_city(message: Message, state: FSMContext):
    """پردازش شهر برای جستجو"""
    if message.text == "↩️ بازگشت":
        await state.clear()
        await message.answer("به منوی اصلی بازگشتید.", reply_markup=get_main_menu())
        return
    
    await state.update_data(search_city=message.text)
    await message.answer(
        "🔸 جنسیت تأمین‌کننده مورد نظر را انتخاب کنید:",
        reply_markup=get_demander_search_gender_keyboard()
    )
    await state.set_state(DemanderSearch.gender)

@router.message(DemanderSearch.gender)
async def process_search_gender(message: Message, state: FSMContext):
    """پردازش جنسیت برای جستجو"""
    if message.text == "↩️ بازگشت":
        await message.answer(
            "شهر مورد نظر خود را وارد کنید:",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(DemanderSearch.city)
        return
    
    gender_map = {
        "👨 مرد": "مرد",
        "👩 زن": "زن",
        "🤷 مهم نیست": None
    }
    
    if message.text not in gender_map:
        await message.answer("لطفاً از گزینه‌های موجود انتخاب کنید:")
        return
    
    await state.update_data(search_gender=gender_map[message.text])
    await message.answer(
        "🔸 محدوده سنی مورد نظر را وارد کنید:\n"
        "مثال: 18-30 یا 25-35\n"
        "برای رد کردن این فیلتر، 'رد کردن' را بزنید.",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(DemanderSearch.age_range)

@router.message(DemanderSearch.age_range)
async def process_search_age_range(message: Message, state: FSMContext):
    """پردازش محدوده سنی برای جستجو"""
    if message.text == "↩️ بازگشت":
        await message.answer(
            "جنسیت تأمین‌کننده مورد نظر را انتخاب کنید:",
            reply_markup=get_demander_search_gender_keyboard()
        )
        await state.set_state(DemanderSearch.gender)
        return
    
    if message.text == "⏭ رد کردن":
        age_range = None
    else:
        # پارس محدوده سنی
        try:
            if '-' in message.text:
                min_age, max_age = message.text.split('-')
                age_range = (int(min_age.strip()), int(max_age.strip()))
            else:
                await message.answer("لطفاً محدوده سنی را به صورت صحیح وارد کنید (مثال: 25-35):")
                return
        except:
            await message.answer("فرمت نامعتبر. لطفاً محدوده سنی را به صورت صحیح وارد کنید:")
            return
    
    await state.update_data(search_age_range=age_range)
    await state.update_data(selected_search_styles=[])
    
    await message.answer(
        "🔸 سبک کاری مورد نظر را انتخاب کنید (می‌توانید چند مورد انتخاب کنید):",
        reply_markup=get_work_styles_keyboard()
    )
    await state.set_state(DemanderSearch.work_styles)

@router.message(DemanderSearch.work_styles)
async def process_search_work_styles(message: Message, state: FSMContext):
    """پردازش سبک کاری برای جستجو"""
    data = await state.get_data()
    selected_styles = data.get('selected_search_styles', [])
    
    if message.text == "↩️ بازگشت":
        await message.answer(
            "محدوده سنی مورد نظر را وارد کنید:",
            reply_markup=get_skip_keyboard()
        )
        await state.set_state(DemanderSearch.age_range)
        return
    
    if message.text == "✔️ تأیید و ادامه":
        await state.update_data(search_work_styles=selected_styles)
        await message.answer(
            "🔸 محدوده قیمت مورد نظر برای پروژه را انتخاب کنید:",
            reply_markup=get_price_range_keyboard()
        )
        await state.set_state(DemanderSearch.price_range)
        return
    
    # مدیریت انتخاب سبک‌ها (مشابه supplier)
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
        
        await state.update_data(selected_search_styles=selected_styles)
        
        # نمایش وضعیت
        if selected_styles:
            status_text = "انتخاب‌های فعلی:\n"
            for key, value in style_map.items():
                if value in selected_styles:
                    status_text += f"✓ {key.replace('✅ ', '')}\n"
            status_text += "\n برای کنسل کردن انتخاب دوباره روی دکمه آن کلیک کنید."

            await message.answer(status_text)

@router.message(DemanderSearch.price_range)
async def process_search_price_range(message: Message, state: FSMContext):
    """پردازش محدوده قیمت برای جستجو"""
    if message.text == "↩️ بازگشت":
        await message.answer(
            "سبک کاری مورد نظر را انتخاب کنید:",
            reply_markup=get_work_styles_keyboard()
        )
        await state.set_state(DemanderSearch.work_styles)
        return
    
    price_map = {
        "💰 زیر ۵۰۰ هزار تومان": (0, 500000),
        "💰 ۵۰۰ هزار - ۱ میلیون": (500000, 1000000),
        "💰 ۱ - ۲ میلیون": (1000000, 2000000),
        "💰 بالای ۲ میلیون": (2000000, float('inf')),
        "🤷 مهم نیست": None
    }
    
    if message.text not in price_map:
        await message.answer("لطفاً از گزینه‌های موجود انتخاب کنید:")
        return
    
    await state.update_data(search_price_range=price_map[message.text])
    await message.answer(
        "🔸 ویژگی ظاهری خاص (اختیاری):\n"
        "مثال: چشم رنگی، مو بلوند، بدون تتو\n\n"
        "برای رد کردن روی 'رد کردن' کلیک کنید.",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(DemanderSearch.special_features)

@router.message(DemanderSearch.special_features)
async def process_search_special_features(message: Message, state: FSMContext, session: AsyncSession):
    """پردازش ویژگی‌های خاص و شروع جستجو"""
    if message.text == "↩️ بازگشت":
        await message.answer(
            "محدوده قیمت مورد نظر را انتخاب کنید:",
            reply_markup=get_price_range_keyboard()
        )
        await state.set_state(DemanderSearch.price_range)
        return
    
    special_features = None if message.text == "⏭ رد کردن" else message.text
    await state.update_data(search_special_features=special_features)
    
    # انجام جستجو
    await message.answer(
        "🔎 در حال جستجو...",
        reply_markup=ReplyKeyboardRemove()
    )
    
    data = await state.get_data()
    suppliers = await search_suppliers(session, data)
    
    if not suppliers:
        await message.answer(
            "متأسفانه تأمین‌کننده‌ای با مشخصات مورد نظر شما یافت نشد.\n\n"
            "می‌توانید با تغییر فیلترها مجدداً جستجو کنید.",
            reply_markup=get_main_menu()
        )
        await state.clear()
        return
    
    # ذخیره نتایج در state
    await state.update_data(
        search_results=suppliers,
        current_page=1,
        total_pages=math.ceil(len(suppliers) / 5)  # 5 نتیجه در هر صفحه
    )
    
    await show_search_results(message, state, 1)
    await state.set_state(DemanderSearch.viewing_results)

# ========== نمایش نتایج جستجو ==========

async def show_search_results(message: Message, state: FSMContext, page: int):
    """نمایش نتایج جستجو با صفحه‌بندی"""
    data = await state.get_data()
    suppliers = data.get('search_results', [])
    total_pages = data.get('total_pages', 1)
    
    # محاسبه ایندکس‌ها
    start_idx = (page - 1) * 5
    end_idx = min(start_idx + 5, len(suppliers))
    
    text = f"📋 نتایج جستجو (صفحه {page} از {total_pages}):\n\n"
    
    # ایجاد inline keyboard برای نتایج
    builder = InlineKeyboardBuilder()
    
    for i, supplier in enumerate(suppliers[start_idx:end_idx], start=start_idx+1):
        # نمایش خلاصه اطلاعات
        text += f"{i}. {format_supplier_summary(supplier)}\n\n"
        
        # دکمه مشاهده جزئیات
        builder.button(
            text=f"👁 مشاهده {i}",
            callback_data=f"view_supplier:{supplier.id}"
        )
    
    # تنظیم layout دکمه‌ها
    builder.adjust(3)  # 3 دکمه در هر ردیف
    
    # اضافه کردن دکمه‌های صفحه‌بندی
    pagination_builder = InlineKeyboardBuilder()
    if page > 1:
        pagination_builder.button(
            text="◀️ قبلی",
            callback_data=f"search_page:{page-1}"
        )
    
    pagination_builder.button(
        text=f"📄 {page}/{total_pages}",
        callback_data="current_page"
    )
    
    if page < total_pages:
        pagination_builder.button(
            text="بعدی ▶️",
            callback_data=f"search_page:{page+1}"
        )
    
    # ترکیب keyboards
    builder.attach(pagination_builder)
    
    # دکمه بازگشت
    builder.row(
        InlineKeyboardButton(
            text="🔙 جستجوی جدید",
            callback_data="new_search"
        )
    )
    
    if hasattr(message, 'edit_text'):
        await message.edit_text(text, reply_markup=builder.as_markup())
    else:
        await message.answer(text, reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("search_page:"))
async def handle_search_pagination(callback: CallbackQuery, state: FSMContext):
    """هندل کردن صفحه‌بندی نتایج"""
    page = int(callback.data.split(":")[1])
    await state.update_data(current_page=page)
    await show_search_results(callback.message, state, page)
    await callback.answer()

@router.callback_query(F.data.startswith("view_supplier:"))
async def view_supplier_details(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """نمایش جزئیات تأمین‌کننده"""
    supplier_id = int(callback.data.split(":")[1])
    
    # دریافت اطلاعات کامل تأمین‌کننده
    stmt = select(Supplier).where(Supplier.id == supplier_id)
    result = await session.execute(stmt)
    supplier = result.scalar_one_or_none()
    
    if not supplier:
        await callback.answer("تأمین‌کننده یافت نشد!", show_alert=True)
        return
    
    # ایجاد متن جزئیات
    detail_text = format_supplier_details(supplier)
    
    # ذخیره supplier_id در state برای درخواست وقت
    await state.update_data(selected_supplier_id=supplier_id)
    
    await callback.message.edit_text(
        detail_text,
        reply_markup=get_supplier_detail_keyboard(supplier_id)
    )
    await state.set_state(DemanderSearch.viewing_supplier)
    await callback.answer()

@router.callback_query(F.data == "back_to_list")
async def back_to_search_results(callback: CallbackQuery, state: FSMContext):
    """بازگشت به لیست نتایج"""
    data = await state.get_data()
    current_page = data.get('current_page', 1)
    await show_search_results(callback.message, state, current_page)
    await state.set_state(DemanderSearch.viewing_results)
    await callback.answer()

@router.callback_query(F.data.startswith("request_appointment:"))
async def request_appointment(callback: CallbackQuery, state: FSMContext):
    """درخواست وقت از تأمین‌کننده"""
    supplier_id = int(callback.data.split(":")[1])
    
    await callback.message.edit_text(
        "📝 لطفاً پیام خود را برای تأمین‌کننده بنویسید:\n\n"
        "می‌توانید جزئیات پروژه، زمان و مکان مورد نظر را ذکر کنید.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="❌ انصراف", callback_data="cancel_request")
        ]])
    )
    
    await state.update_data(appointment_supplier_id=supplier_id)
    await state.set_state(DemanderSearch.writing_message)
    await callback.answer()

@router.message(DemanderSearch.writing_message)
async def process_appointment_message(message: Message, state: FSMContext, session: AsyncSession):
    """پردازش پیام درخواست وقت"""
    data = await state.get_data()
    supplier_id = data.get('appointment_supplier_id')
    
    # دریافت demander
    stmt = select(User).where(User.telegram_id == str(message.from_user.id))
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not user.demander_profile:
        await message.answer("خطا: پروفایل شما یافت نشد!")
        return
    
    # نمایش پیش‌نمایش
    preview_text = f"""
📋 پیش‌نمایش درخواست شما:

📝 پیام:
{message.text}

آیا می‌خواهید این درخواست را ارسال کنید؟
"""
    
    await message.answer(
        preview_text,
        reply_markup=get_request_confirmation_keyboard()
    )
    
    await state.update_data(appointment_message=message.text)

@router.callback_query(F.data == "confirm_request")
async def confirm_appointment_request(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """تأیید و ارسال درخواست وقت"""
    data = await state.get_data()
    supplier_id = data.get('appointment_supplier_id')
    appointment_message = data.get('appointment_message')
    
    # دریافت demander
    stmt = select(User).where(User.telegram_id == str(callback.from_user.id))
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not user.demander_profile:
        await callback.answer("خطا: پروفایل شما یافت نشد!", show_alert=True)
        return
    
    # ایجاد درخواست
    request = Request(
        demander_id=user.demander_profile.id,
        supplier_id=supplier_id,
        message=appointment_message,
        status=RequestStatus.PENDING
    )
    
    session.add(request)
    await session.commit()
    
    await callback.message.edit_text(
        "✅ درخواست شما با موفقیت ارسال شد!\n\n"
        "پس از بررسی توسط تأمین‌کننده، نتیجه به شما اطلاع داده خواهد شد.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔙 بازگشت به نتایج", callback_data="back_to_list")
        ]])
    )
    
    # ارسال نوتیفیکیشن به تأمین‌کننده
    # (نیاز به پیاده‌سازی سیستم نوتیفیکیشن)
    
    await callback.answer("درخواست ارسال شد!")

@router.callback_query(F.data == "cancel_request")
async def cancel_appointment_request(callback: CallbackQuery, state: FSMContext):
    """لغو درخواست وقت"""
    data = await state.get_data()
    supplier_id = data.get('appointment_supplier_id', data.get('selected_supplier_id'))
    
    await callback.message.edit_text(
        "درخواست لغو شد.",
        reply_markup=get_supplier_detail_keyboard(supplier_id)
    )
    await state.set_state(DemanderSearch.viewing_supplier)
    await callback.answer()

@router.callback_query(F.data == "new_search")
async def start_new_search(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """شروع جستجوی جدید"""
    await state.clear()
    await callback.message.delete()
    await show_search_menu(callback.message, state, session)
    await callback.answer()

# ========== Helper Functions ==========

async def search_suppliers(session: AsyncSession, search_criteria: dict) -> List[Supplier]:
    """جستجوی تأمین‌کنندگان بر اساس فیلترها"""
    query = select(Supplier)

    # فیلتر شهر
    if search_criteria.get('search_city'):
        query = query.where(Supplier.city.ilike(f"%{search_criteria['search_city']}%"))

    # فیلتر جنسیت
    if search_criteria.get('search_gender'):
        query = query.where(Supplier.gender == search_criteria['search_gender'])

    # فیلتر محدوده سنی
    if search_criteria.get('search_age_range'):
        min_age, max_age = search_criteria['search_age_range']
        query = query.where(and_(
            Supplier.age >= min_age,
            Supplier.age <= max_age
        ))

    # فیلتر سبک کاری
    if search_criteria.get('search_work_styles'):
        # برای هر سبک انتخاب شده، چک می‌کنیم که در لیست سبک‌های تأمین‌کننده باشد
        style_conditions = []
        for style in search_criteria['search_work_styles']:
            style_conditions.append(Supplier.work_styles.contains([style]))
        if style_conditions:
            query = query.where(or_(*style_conditions))

    # فیلتر ویژگی خاص
    if search_criteria.get('search_special_features'):
        features = search_criteria['search_special_features']
        query = query.where(or_(
            Supplier.special_features.ilike(f"%{features}%"),
            Supplier.hair_color.ilike(f"%{features}%"),
            Supplier.eye_color.ilike(f"%{features}%")
        ))

    # اجرای کوئری
    result = await session.execute(query)
    suppliers = result.scalars().all()

    # فیلتر قیمت در پایتون
    if search_criteria.get('search_price_range'):
        min_price, max_price = search_criteria['search_price_range']
        filtered_suppliers = []
        for supplier in suppliers:
            if not supplier.pricing_data:
                continue

            is_match = False
            for price_type, price_info in supplier.pricing_data.items():
                if price_type == 'category_based':
                    if isinstance(price_info, dict):
                        for category, category_price_info in price_info.items():
                            if isinstance(category_price_info, dict):
                                db_min = category_price_info.get('min', 0) * 1000
                                db_max = category_price_info.get('max', 0) * 1000
                                if db_min <= max_price and db_max >= min_price:
                                    is_match = True
                                    break
                elif isinstance(price_info, dict):
                    db_min = price_info.get('min', 0) * 1000
                    db_max = price_info.get('max', 0) * 1000
                    if db_min <= max_price and db_max >= min_price:
                        is_match = True
                        break
                if is_match:
                    break
            
            if is_match:
                filtered_suppliers.append(supplier)
        
        suppliers = filtered_suppliers

    return suppliers

def format_supplier_summary(supplier: Supplier) -> str:
    """فرمت خلاصه اطلاعات تأمین‌کننده برای نمایش در لیست"""
    styles_fa = {
        'fashion': '👗 فشن',
        'advertising': '📢 تبلیغاتی',
        'religious': '🧕 مذهبی',
        'children': '👶 کودک',
        'sports': '🏃 ورزشی',
        'artistic': '🎨 هنری',
        'outdoor': '🌳 فضای باز',
        'studio': '📸 استودیو'
    }
    
    # انتخاب 2 سبک اول برای نمایش
    display_styles = [styles_fa.get(s, s) for s in supplier.work_styles[:2]]
    if len(supplier.work_styles) > 2:
        display_styles.append('...')
    
    return f"""👤 {supplier.full_name}
📍 {supplier.city}
💰 {format_price_short(supplier)}
🎨 {' | '.join(display_styles)}"""

def format_supplier_details(supplier: Supplier) -> str:
    """فرمت جزئیات کامل تأمین‌کننده"""
    coop_types_fa = {
        'in_person': 'حضوری',
        'project_based': 'پروژه‌ای',
        'part_time': 'پاره‌وقت'
    }
    
    work_styles_fa = {
        'fashion': 'فشن / کت واک',
        'advertising': 'تبلیغاتی / برندینگ',
        'religious': 'مذهبی / پوشیده',
        'children': 'کودک',
        'sports': 'ورزشی',
        'artistic': 'هنری / خاص',
        'outdoor': 'عکاسی فضای باز',
        'studio': 'عکاسی استودیویی'
    }
    
    details = f"""
🎭 اطلاعات امل تأمین‌کننده

👤 نام: {supplier.full_name}
� تماس: {supplier.phone_number}
� موقعیت: {supplier.city} - {supplier.area}
"""
    
    if supplier.instagram_id:
        details += f"📷 اینستاگرا: @{supplier.instagram_id}\n"
    
    details += f"""
� مشخصات:
-جنسیت: {supplier.gender}
- سن: {supplier.age} سال
- قد: {supplier.height} سانتی‌متر
- وزن: {supplier.weight} کیلوگرم
- رنگ مو: {supplier.hair_color}
- رنگ چشم: {supplier.eye_color}
- رنگ پوست: {supplier.skin_color}
- سایز بالاتنه: {supplier.top_size}
- سایز پایین‌تنه: {supplier.bottom_size}
"""
    
    if supplier.special_features:
        details += f"• ویژگی خاص: {supplier.special_features}\n"
    
    details += f"""
💼 طلاعات همکاری:
- قیمت: {format_price_range(supplier)}
- نوع همکاری: {', '.join([coop_types_fa.get(t, t) for t in supplier.cooperation_types])}
- سبک کاری: {', '.join([work_styles_fa.get(s, s) for s in supplier.work_styles])}
"""
    
    if supplier.brand_experience:
        details += f"\n🏢 ابقه همکاری: {supplier.brand_experience}\n"
    
    if supplier.additional_notes:
        details += f"\n📝 توضیحات {supplier.additional_notes}\n"
    
    return details

def format_price_short(supplier: Supplier) -> str:
    """فرمت کوتاه قیمت برای نمایش در لیست"""
    if not supplier.pricing_data:
        return "قیمت نامشخص"

    price_to_show = None
    unit_to_show = ""

    unit_fa = {
        'hourly': 'ساعتی',
        'daily': 'روزی',
        'per_cloth': 'هر لباس'
    }

    if 'daily' in supplier.pricing_data and isinstance(supplier.pricing_data['daily'], dict):
        price_to_show = supplier.pricing_data['daily']
        unit_to_show = unit_fa['daily']
    else:
        for p_type, p_info in supplier.pricing_data.items():
            if p_type != 'category_based' and isinstance(p_info, dict):
                price_to_show = p_info
                unit_to_show = unit_fa.get(p_type, p_type)
                break
    
    if not price_to_show:
        return "قیمت توافقی"

    min_p = price_to_show.get('min', 0)
    max_p = price_to_show.get('max', 0)

    if min_p == max_p:
        return f"{unit_to_show} {min_p}K"
    else:
        return f"{unit_to_show} {min_p}-{max_p}K"

def format_price_range(supplier: Supplier) -> str:
    """فرمت کامل محدوده قیمت"""
    if not supplier.pricing_data:
        return "اطلاعات قیمت‌گذاری موجود نیست"

    formatted_lines = []
    price_types_fa = {
        "hourly": "ساعتی",
        "daily": "روزانه",
        "per_cloth": "به ازای هر لباس"
    }
    
    for price_type, data in supplier.pricing_data.items():
        if price_type == "category_based":
            if isinstance(data, dict) and data:
                formatted_lines.append("قیمت‌گذاری بر اساس سبک:")
                for style, price in data.items():
                    style_price = f"  - سبک {style}: "
                    if isinstance(price, dict) and "min" in price and "max" in price:
                        min_p = price['min'] * 1000
                        max_p = price['max'] * 1000
                        style_price += f"{min_p:,.0f} تا {max_p:,.0f} تومان"
                    formatted_lines.append(style_price)
        else:
            if price_type in price_types_fa and isinstance(data, dict):
                price_line = f"{price_types_fa[price_type]}: "
                if "min" in data and "max" in data:
                    min_p = data['min'] * 1000
                    max_p = data['max'] * 1000
                    price_line += f"{min_p:,.0f} تا {max_p:,.0f} تومان"
                formatted_lines.append(price_line)

    return "\n".join(formatted_lines) if formatted_lines else "قیمت توافقی"

