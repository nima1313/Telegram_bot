from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, cast, String
from typing import List
import math
import logging

from database.models import User, Demander, Supplier, UserRole, Request, RequestStatus
from states.demander import DemanderRegistration, DemanderSearch
from keyboards.reply import *
from keyboards.inline import *
from utils.users import get_or_create_user

router = Router()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        
        user = await get_or_create_user(session, message.from_user, UserRole.DEMANDER)
        
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
        
        await show_search_menu(message, state)
        
    except Exception as e:
        logger.exception("Error during demander registration:")
        await message.answer(
            "❌ خطایی در ثبت اطلاعات رخ داد. لطفاً مجدداً تلاش کنید.",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()

# ========== جستجوی تأمین‌کنندگان ========== 

async def show_search_menu(message: Message, state: FSMContext, session: AsyncSession = None):
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
    
    age_range = None
    if message.text != "⏭ رد کردن":
        try:
            if '-' in message.text:
                min_age, max_age = map(int, message.text.split('-'))
                age_range = (min_age, max_age)
            else:
                await message.answer("لطفاً محدوده سنی را به صورت صحیح وارد کنید (مثال: 25-35):")
                return
        except ValueError:
            await message.answer("فرمت نامعتبر. لطفاً محدوده سنی را به صورت صحیح وارد کنید:")
            return
    
    await state.update_data(search_age_range=age_range, selected_search_styles=[])
    
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
        await message.answer("محدوده سنی مورد نظر را وارد کنید:", reply_markup=get_skip_keyboard())
        await state.set_state(DemanderSearch.age_range)
        return
    
    if message.text == "✔️ تأیید و ادامه":
        await state.update_data(search_work_styles=selected_styles)
        await message.answer("🔸 محدوده قیمت مورد نظر برای پروژه را انتخاب کنید:", reply_markup=get_price_range_keyboard())
        await state.set_state(DemanderSearch.price_range)
        return
    
    style_map = {
        "✅ 👗 فشن / کت واک": "fashion", "✅ 📢 تبلیغاتی / برندینگ": "advertising",
        "✅ 🧕 مذهبی / پوشیده": "religious", "✅ 👶 کودک": "children",
        "✅ 🏃 ورزشی": "sports", "✅ 🎨 هنری / خاص": "artistic",
        "✅ 🌳 عکاسی فضای باز": "outdoor", "✅ 📸 عکاسی استودیویی": "studio"
    }
    
    if message.text in style_map:
        style = style_map[message.text]
        if style in selected_styles:
            selected_styles.remove(style)
        else:
            selected_styles.append(style)
        
        await state.update_data(selected_search_styles=selected_styles)
        
        status_text = "انتخاب‌های فعلی:\n" + "\n".join([f"✓ {k.replace('✅ ', '')}" for k, v in style_map.items() if v in selected_styles])
        await message.answer(status_text if selected_styles else "هیچ سبکی انتخاب نشده است.")

@router.message(DemanderSearch.price_range)
async def process_search_price_range(message: Message, state: FSMContext):
    """پردازش محدوده قیمت برای جستجو"""
    if message.text == "↩️ بازگشت":
        await message.answer("سبک کاری مورد نظر را انتخاب کنید:", reply_markup=get_work_styles_keyboard())
        await state.set_state(DemanderSearch.work_styles)
        return
    
    price_map = {
        "💰 زیر ۵۰۰ هزار تومان": (0, 500000), "💰 ۵۰۰ هزار - ۱ میلیون": (500000, 1000000),
        "💰 ۱ - ۲ میلیون": (1000000, 2000000), "💰 بالای ۲ میلیون": (2000000, float('inf')),
        "🤷 مهم نیست": None
    }
    
    if message.text not in price_map:
        await message.answer("لطفاً از گزینه‌های موجود انتخاب کنید:")
        return
    
    await state.update_data(search_price_range=price_map[message.text])
    await message.answer(
        "🔸 ویژگی ظاهری خاص (اختیاری):\nمثال: چشم رنگی، مو بلوند، بدون تتو\n\n" 
        "برای رد کردن روی 'رد کردن' کلیک کنید.",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(DemanderSearch.special_features)

@router.message(DemanderSearch.special_features)
async def process_search_special_features(message: Message, state: FSMContext, session: AsyncSession):
    """پردازش ویژگی‌های خاص و شروع جستجو"""
    if message.text == "↩️ بازگشت":
        await message.answer("محدوده قیمت مورد نظر را انتخاب کنید:", reply_markup=get_price_range_keyboard())
        await state.set_state(DemanderSearch.price_range)
        return
    
    special_features = None if message.text == "⏭ رد کردن" else message.text
    await state.update_data(search_special_features=special_features)
    
    await message.answer("🔎 در حال جستجو...", reply_markup=ReplyKeyboardRemove())
    
    try:
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
        
        await state.update_data(
            search_results=[s.id for s in suppliers],
            current_page=1,
            total_pages=math.ceil(len(suppliers) / 5)
        )
        
        await show_search_results(message, state, 1, session)
        await state.set_state(DemanderSearch.viewing_results)

    except Exception as e:
        logger.error(f"Error during supplier search: {e}")
        await message.answer(
            "❌ خطایی در هنگام جستجو رخ داد. لطفاً دوباره تلاش کنید.",
            reply_markup=get_main_menu()
        )
        await state.clear()

async def show_search_results(message: Message, state: FSMContext, page: int, session: AsyncSession):
    """نمایش نتایج جستجو با صفحه‌بندی"""
    data = await state.get_data()
    supplier_ids = data.get('search_results', [])
    total_pages = data.get('total_pages', 1)
    
    start_idx = (page - 1) * 5
    end_idx = start_idx + 5
    page_supplier_ids = supplier_ids[start_idx:end_idx]
    
    if not page_supplier_ids:
        await message.answer("هیچ نتیجه‌ای برای نمایش در این صفحه وجود ندارد.")
        return
        
    stmt = select(Supplier).where(Supplier.id.in_(page_supplier_ids)).order_by(Supplier.id)
    result = await session.execute(stmt)
    suppliers = result.scalars().all()
    
    supplier_map = {s.id: s for s in suppliers}
    ordered_suppliers = [supplier_map[id] for id in page_supplier_ids if id in supplier_map]
    
    text = f"📋 نتایج جستجو (صفحه {page} از {total_pages}):\n\n"
    builder = InlineKeyboardBuilder()
    
    for i, supplier in enumerate(ordered_suppliers, start=start_idx + 1):
        text += f"{i}. {format_supplier_summary(supplier)}\n\n"
        builder.button(text=f"👁 مشاهده {i}", callback_data=f"view_supplier:{supplier.id}")
    
    builder.adjust(3)
    
    pagination_builder = InlineKeyboardBuilder()
    if page > 1:
        pagination_builder.button(text="◀️ قبلی", callback_data=f"search_page:{page-1}")
    pagination_builder.button(text=f"📄 {page}/{total_pages}", callback_data="current_page")
    if page < total_pages:
        pagination_builder.button(text="بعدی ▶️", callback_data=f"search_page:{page+1}")
    
    builder.attach(pagination_builder)
    builder.row(InlineKeyboardButton(text="🔙 جستجوی جدید", callback_data="new_search"))
    
    try:
        if isinstance(message, CallbackQuery):
            await message.message.edit_text(text, reply_markup=builder.as_markup())
        elif hasattr(message, 'edit_text'):
            await message.edit_text(text, reply_markup=builder.as_markup())
        else:
            await message.answer(text, reply_markup=builder.as_markup())
    except Exception as e:
        # If editing fails, send as new message
        await message.answer(text, reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("search_page:"))
async def handle_search_pagination(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """هندل کردن صفحه‌بندی نتایج"""
    try:
        page = int(callback.data.split(":")[1])
        await state.update_data(current_page=page)
        try:
            await show_search_results(callback.message, state, page, session)
        except Exception as e:
            # If editing fails, send a new message
            await callback.message.answer("🔄 بارگذاری نتایج جدید...")
            await show_search_results(callback.message, state, page, session)
        await callback.answer()
    except Exception as e:
        await callback.answer("❌ خطا در بارگذاری صفحه")

@router.callback_query(F.data.startswith("view_supplier:"))
async def view_supplier_details(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """نمایش جزئیات تأمین‌کننده"""
    supplier_id = int(callback.data.split(":")[1])
    
    result = await session.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    
    if not supplier:
        await callback.answer("تأمین‌کننده یافت نشد!", show_alert=True)
        return
    
    await state.update_data(selected_supplier_id=supplier_id)
    await callback.message.edit_text(
        format_supplier_details(supplier),
        reply_markup=get_supplier_detail_keyboard(supplier_id)
    )
    await state.set_state(DemanderSearch.viewing_supplier)
    await callback.answer()

@router.callback_query(F.data == "back_to_list")
async def back_to_search_results(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """بازگشت به لیست نتایج"""
    data = await state.get_data()
    await show_search_results(callback.message, state, data.get('current_page', 1), session)
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
    preview_text = f"📋 پیش‌نمایش درخواست شما:\n\n📝 پیام:\n{message.text}\n\nآیا می‌خواهید این درخواست را ارسال کنید؟"
    await message.answer(preview_text, reply_markup=get_request_confirmation_keyboard())
    await state.update_data(appointment_message=message.text)

@router.callback_query(F.data == "confirm_request")
async def confirm_appointment_request(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """تأیید و ارسال درخواست وقت"""
    data = await state.get_data()
    
    result = await session.execute(select(User).where(User.telegram_id == str(callback.from_user.id)))
    user = result.scalar_one_or_none()
    
    if not user or not user.demander_profile:
        await callback.answer("خطا: پروفایل شما یافت نشد!", show_alert=True)
        return
    
    request = Request(
        demander_id=user.demander_profile.id,
        supplier_id=data['appointment_supplier_id'],
        message=data['appointment_message'],
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
    await callback.answer("درخواست ارسال شد!")

@router.callback_query(F.data == "cancel_request")
async def cancel_appointment_request(callback: CallbackQuery, state: FSMContext):
    """لغو درخواست وقت"""
    data = await state.get_data()
    await callback.message.edit_text(
        "درخواست لغو شد.",
        reply_markup=get_supplier_detail_keyboard(data.get('selected_supplier_id'))
    )
    await state.set_state(DemanderSearch.viewing_supplier)
    await callback.answer()

@router.callback_query(F.data == "new_search")
async def start_new_search(callback: CallbackQuery, state: FSMContext):
    """شروع جستجوی جدید"""
    await state.clear()
    await callback.message.delete()
    await show_search_menu(callback.message, state)
    await callback.answer()

# ========== Helper Functions ========== 

async def search_suppliers(session: AsyncSession, search_criteria: dict) -> List[Supplier]:
    """جستجوی تأمین‌کنندگان بر اساس فیلترها"""
    query = select(Supplier).where(Supplier.user.has(is_active=True))
    
    if city := search_criteria.get('search_city'):
        query = query.where(Supplier.city.ilike(f"%{city}%"))
    
    if gender := search_criteria.get('search_gender'):
        query = query.where(Supplier.gender == gender)
    
    if age_range := search_criteria.get('search_age_range'):
        query = query.where(Supplier.age.between(age_range[0], age_range[1]))
    
    if price_range := search_criteria.get('search_price_range'):
        min_price, max_price = price_range
        query = query.where(and_(Supplier.price_range_min <= max_price, Supplier.price_range_max >= min_price))
    
    if styles := search_criteria.get('search_work_styles'):
        from sqlalchemy.dialects.postgresql import JSONB
        from sqlalchemy import cast, func
        style_conditions = []
        for style in styles:
            # Cast work_styles to JSONB and use PostgreSQL's @> operator
            style_conditions.append(
                cast(Supplier.work_styles, JSONB).contains([style])
            )
        if style_conditions:
            query = query.where(or_(*style_conditions))
    
    if features := search_criteria.get('search_special_features'):
        feature_clauses = [col.ilike(f"%{features}%") for col in [Supplier.special_features, Supplier.hair_color, Supplier.eye_color]]
        query = query.where(or_(*feature_clauses))
    
    result = await session.execute(query)
    return result.scalars().all()

def format_supplier_summary(supplier: Supplier) -> str:
    """فرمت خلاصه اطلاعات تأمین‌کننده برای نمایش در لیست"""
    styles_fa = {
        'fashion': '👗 فشن', 'advertising': '📢 تبلیغاتی', 'religious': '🧕 مذهبی',
        'children': '👶 کودک', 'sports': '🏃 ورزشی', 'artistic': '🎨 هنری',
        'outdoor': '🌳 فضای باز', 'studio': '📸 استودیو'
    }
    display_styles = [styles_fa.get(s, s) for s in (supplier.work_styles or [])[:2]]
    if supplier.work_styles and len(supplier.work_styles) > 2:
        display_styles.append('...')
    
    return f"👤 {supplier.full_name}\n📍 {supplier.city}\n💰 {format_price_short(supplier)}\n🎨 {' | '.join(display_styles)}"

def format_supplier_details(supplier: Supplier) -> str:
    """فرمت جزئیات کامل تأمین‌کننده"""
    coop_types_fa = {'in_person': 'حضوری', 'project_based': 'پروژه‌ای', 'part_time': 'پاره‌وقت'}
    work_styles_fa = {
        'fashion': 'فشن / کت واک', 'advertising': 'تبلیغاتی / برندینگ', 'religious': 'مذهبی / پوشیده',
        'children': 'کودک', 'sports': 'ورزشی', 'artistic': 'هنری / خاص',
        'outdoor': 'عکاسی فضای باز', 'studio': 'عکاسی استودیویی'
    }
    
    details = f"🎭 **اطلاعات کامل تأمین‌کننده**\n\n"
    details += f"👤 **نام:** {supplier.full_name}\n"
    details += f"📱 **تماس:** {supplier.phone_number}\n"
    details += f"📍 **موقعیت:** {supplier.city} - {supplier.area}\n"
    if supplier.instagram_id:
        details += f"📷 **اینستاگرام:** @{supplier.instagram_id}\n"
    
    details += f"\n📊 **مشخصات:**\n"
    details += f"- **جنسیت:** {supplier.gender}\n"
    details += f"- **سن:** {supplier.age} سال\n"
    details += f"- **قد:** {supplier.height} سانتی‌متر\n"
    details += f"- **وزن:** {supplier.weight} کیلوگرم\n"
    details += f"- **رنگ مو:** {supplier.hair_color}\n"
    details += f"- **رنگ چشم:** {supplier.eye_color}\n"
    details += f"- **رنگ پوست:** {supplier.skin_color}\n"
    details += f"- **سایز بالاتنه:** {supplier.top_size}\n"
    details += f"- **سایز پایین‌تنه:** {supplier.bottom_size}\n"
    if supplier.special_features:
        details += f"- **ویژگی خاص:** {supplier.special_features}\n"
        
    details += f"\n💼 **اطلاعات همکاری:**\n"
    details += f"- **قیمت:** {format_price_range(supplier)}\n"
    details += f"- **نوع همکاری:** {', '.join([coop_types_fa.get(t, t) for t in supplier.cooperation_types or []])}\n"
    details += f"- **سبک کاری:** {', '.join([work_styles_fa.get(s, s) for s in supplier.work_styles or []])}\n"
    
    if supplier.brand_experience:
        details += f"\n🏢 **سابقه همکاری:** {supplier.brand_experience}\n"
    if supplier.additional_notes:
        details += f"\n📝 **توضیحات:** {supplier.additional_notes}\n"
        
    return details

def format_price_short(supplier: Supplier) -> str:
    """فرمت کوتاه قیمت برای نمایش در لیست"""
    unit_fa = {'hourly': 'ساعتی', 'daily': 'روزی', 'project': 'پروژه‌ای'}
    unit = unit_fa.get(supplier.price_unit, '')
    min_p, max_p = supplier.price_range_min, supplier.price_range_max
    
    if not min_p or not max_p: return "توافقی"
    
    if min_p == max_p:
        return f"{unit} {min_p/1000:,.0f}K"
    return f"{unit} {min_p/1000:,.0f}-{max_p/1000:,.0f}K"

def format_price_range(supplier: Supplier) -> str:
    """فرمت کامل محدوده قیمت"""
    unit_fa = {'hourly': 'ساعتی', 'daily': 'روزی', 'project': 'پروژه‌ای'}
    unit = unit_fa.get(supplier.price_unit, '')
    min_p, max_p = supplier.price_range_min, supplier.price_range_max

    if not min_p or not max_p: return "توافقی"

    if min_p == max_p:
        return f"{unit} {min_p:,.0f} تومان"
    return f"{unit} {min_p:,.0f} تا {max_p:,.0f} تومان"