import logging
from aiogram import Router, F, types
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import User, Demander, UserRole
from states.demander import (
    DemanderRegistration, DemanderMenu, DemanderEditProfile
)
from keyboards.reply import (
    get_gender_keyboard,
    get_back_keyboard,
    get_skip_keyboard,
    get_confirm_keyboard,
    get_main_menu,
    get_price_range_keyboard,
)
from keyboards.demander import (
    get_demander_menu_keyboard,
    get_demander_edit_profile_keyboard,
)
from utils.validators import validate_phone_number
from utils.users import get_or_create_user

router = Router()

# Mapping from Persian field names to database column names
EDITABLE_FIELDS = {
    "نام کامل": "full_name",
    "نام شرکت": "company_name", 
    "آدرس": "address",
    "جنسیت": "gender",
    "شماره تماس": "phone_number",
    "اینستاگرام": "instagram_id",
    "توضیحات": "additional_notes",
}

# ========================= Registration Flow ============================

@router.message(F.text == "🔍 درخواست‌کننده")
async def demander_role_selected(message: Message, state: FSMContext):
    """Entry point after user selects the demander role from main menu"""
    await message.answer(
        "🔸 نام و نام خانوادگی خود را وارد کنید:",
        reply_markup=get_back_keyboard(),
    )
    await state.set_state(DemanderRegistration.full_name)


@router.message(DemanderRegistration.full_name)
async def process_full_name(message: Message, state: FSMContext):
    """پردازش نام و نام خانوادگی"""
    data = await state.get_data()
    is_editing = data.get('editing', False)
    
    if message.text == "↩️ بازگشت":
        if is_editing:
            await state.update_data(editing=False)
            await state.set_state(DemanderRegistration.editing_field)
            await message.answer("کدام بخش از اطلاعات خود را می‌خواهید ویرایش کنید؟", reply_markup=get_demander_edit_profile_keyboard())
        else:
            await state.clear()
            await message.answer("به منوی اصلی بازگشتید.", reply_markup=get_main_menu())
        return

    if len(message.text) < 3:
        await message.answer("❌ لطفاً نام کامل معتبر وارد کنید (حداقل ۳ حرف).")
        return

    await state.update_data(full_name=message.text)
    
    if is_editing:
        await state.update_data(editing=False)
        await message.answer(f"✅ نام کامل شما به '{message.text}' تغییر یافت.")
        await state.set_state(DemanderRegistration.editing_field)
        await message.answer("کدام بخش دیگری را می‌خواهید ویرایش کنید؟", reply_markup=get_demander_edit_profile_keyboard())
    else:
        await message.answer(
            "🔸 نام شرکت/گروه خود را وارد کنید (اختیاری):\nدر صورت نداشتن روی 'رد کردن' بزنید.",
            reply_markup=get_skip_keyboard(),
        )
        await state.set_state(DemanderRegistration.company_name)


@router.message(DemanderRegistration.company_name)
async def process_company_name(message: Message, state: FSMContext):
    """پردازش نام شرکت"""
    data = await state.get_data()
    is_editing = data.get('editing', False)
    
    if message.text == "↩️ بازگشت":
        if is_editing:
            await state.update_data(editing=False)
            await state.set_state(DemanderRegistration.editing_field)
            await message.answer("کدام بخش از اطلاعات خود را می‌خواهید ویرایش کنید؟", reply_markup=get_demander_edit_profile_keyboard())
        else:
            await message.answer("🔸 نام و نام خانوادگی خود را وارد کنید:", reply_markup=get_back_keyboard())
            await state.set_state(DemanderRegistration.full_name)
        return

    company = None if message.text == "⏭ رد کردن" else message.text.strip()
    await state.update_data(company_name=company)
    
    if is_editing:
        await state.update_data(editing=False)
        display_value = company if company else "حذف شد"
        await message.answer(f"✅ نام شرکت شما به '{display_value}' تغییر یافت.")
        await state.set_state(DemanderRegistration.editing_field)
        await message.answer("کدام بخش دیگری را می‌خواهید ویرایش کنید؟", reply_markup=get_demander_edit_profile_keyboard())
    else:
        await message.answer(
            "🔸 آدرس خود را وارد کنید:",
            reply_markup=get_back_keyboard(),
        )
        await state.set_state(DemanderRegistration.address)


@router.message(DemanderRegistration.address)
async def process_address(message: Message, state: FSMContext):
    """پردازش آدرس"""
    data = await state.get_data()
    is_editing = data.get('editing', False)
    
    if message.text == "↩️ بازگشت":
        if is_editing:
            await state.update_data(editing=False)
            await state.set_state(DemanderRegistration.editing_field)
            await message.answer("کدام بخش از اطلاعات خود را می‌خواهید ویرایش کنید؟", reply_markup=get_demander_edit_profile_keyboard())
        else:
            await message.answer(
                "🔸 نام شرکت/گروه خود را وارد کنید (اختیاری):", reply_markup=get_skip_keyboard()
            )
            await state.set_state(DemanderRegistration.company_name)
        return

    address = message.text.strip()
    if len(address) < 3:
        await message.answer("❌ لطفاً آدرس معتبر وارد کنید.")
        return

    await state.update_data(address=address)
    
    if is_editing:
        await state.update_data(editing=False)
        await message.answer(f"✅ آدرس شما به '{address}' تغییر یافت.")
        await state.set_state(DemanderRegistration.editing_field)
        await message.answer("کدام بخش دیگری را می‌خواهید ویرایش کنید؟", reply_markup=get_demander_edit_profile_keyboard())
    else:
        await message.answer("🔸 جنسیت خود را انتخاب کنید:", reply_markup=get_gender_keyboard())
        await state.set_state(DemanderRegistration.gender)


@router.message(DemanderRegistration.gender)
async def process_gender(message: Message, state: FSMContext):
    """پردازش جنسیت"""
    data = await state.get_data()
    is_editing = data.get('editing', False)
    
    if message.text == "↩️ بازگشت":
        if is_editing:
            await state.update_data(editing=False)
            await state.set_state(DemanderRegistration.editing_field)
            await message.answer("کدام بخش از اطلاعات خود را می‌خواهید ویرایش کنید؟", reply_markup=get_demander_edit_profile_keyboard())
        else:
            await message.answer("🔸 آدرس خود را وارد کنید:", reply_markup=get_back_keyboard())
            await state.set_state(DemanderRegistration.address)
        return

    if message.text not in ["👨 مرد", "👩 زن"]:
        await message.answer("❌ لطفاً از گزینه‌های موجود انتخاب کنید.")
        return

    gender = "مرد" if message.text == "👨 مرد" else "زن"
    await state.update_data(gender=gender)
    
    if is_editing:
        await state.update_data(editing=False)
        await message.answer(f"✅ جنسیت شما به '{gender}' تغییر یافت.")
        await state.set_state(DemanderRegistration.editing_field)
        await message.answer("کدام بخش دیگری را می‌خواهید ویرایش کنید؟", reply_markup=get_demander_edit_profile_keyboard())
    else:
        await message.answer(
            "🔸 شماره تماس خود را وارد کنید:\nمثال: 09123456789",
            reply_markup=get_back_keyboard(),
        )
        await state.set_state(DemanderRegistration.phone_number)


@router.message(DemanderRegistration.phone_number)
async def process_phone_number(message: Message, state: FSMContext):
    """پردازش شماره تماس"""
    data = await state.get_data()
    is_editing = data.get('editing', False)
    
    if message.text == "↩️ بازگشت":
        if is_editing:
            await state.update_data(editing=False)
            await state.set_state(DemanderRegistration.editing_field)
            await message.answer("کدام بخش از اطلاعات خود را می‌خواهید ویرایش کنید؟", reply_markup=get_demander_edit_profile_keyboard())
        else:
            await message.answer("🔸 جنسیت خود را انتخاب کنید:", reply_markup=get_gender_keyboard())
            await state.set_state(DemanderRegistration.gender)
        return

    phone = validate_phone_number(message.text)
    if not phone:
        await message.answer("❌ شماره تماس نامعتبر است. مجدداً تلاش کنید.")
        return

    await state.update_data(phone_number=phone)
    
    if is_editing:
        await state.update_data(editing=False)
        await message.answer(f"✅ شماره تماس شما به '{phone}' تغییر یافت.")
        await state.set_state(DemanderRegistration.editing_field)
        await message.answer("کدام بخش دیگری را می‌خواهید ویرایش کنید؟", reply_markup=get_demander_edit_profile_keyboard())
    else:
        await message.answer(
            "🔸 لینک یا آیدی اینستاگرام خود را وارد کنید (اختیاری):",
            reply_markup=get_skip_keyboard(),
        )
        await state.set_state(DemanderRegistration.instagram_id)


@router.message(DemanderRegistration.instagram_id)
async def process_instagram(message: Message, state: FSMContext):
    """پردازش آیدی اینستاگرام"""
    data = await state.get_data()
    is_editing = data.get('editing', False)
    
    if message.text == "↩️ بازگشت":
        if is_editing:
            await state.update_data(editing=False)
            await state.set_state(DemanderRegistration.editing_field)
            await message.answer("کدام بخش از اطلاعات خود را می‌خواهید ویرایش کنید؟", reply_markup=get_demander_edit_profile_keyboard())
        else:
            await message.answer("🔸 شماره تماس خود را وارد کنید:", reply_markup=get_back_keyboard())
            await state.set_state(DemanderRegistration.phone_number)
        return

    instagram = None if message.text == "⏭ رد کردن" else message.text.strip().replace("@", "")
    await state.update_data(instagram_id=instagram)
    
    if is_editing:
        await state.update_data(editing=False)
        display_value = instagram if instagram else "حذف شد"
        await message.answer(f"✅ آیدی اینستاگرام شما به '{display_value}' تغییر یافت.")
        await state.set_state(DemanderRegistration.editing_field)
        await message.answer("کدام بخش دیگری را می‌خواهید ویرایش کنید؟", reply_markup=get_demander_edit_profile_keyboard())
    else:
        await message.answer(
            "🔸 توضیحات تکمیلی (اختیاری):",
            reply_markup=get_skip_keyboard(),
        )
        await state.set_state(DemanderRegistration.additional_notes)


@router.message(DemanderRegistration.additional_notes)
async def process_additional_notes(message: Message, state: FSMContext):
    """پردازش توضیحات اضافی"""
    data = await state.get_data()
    is_editing = data.get('editing', False)
    
    if message.text == "↩️ بازگشت":
        if is_editing:
            await state.update_data(editing=False)
            await state.set_state(DemanderRegistration.editing_field)
            await message.answer("کدام بخش از اطلاعات خود را می‌خواهید ویرایش کنید؟", reply_markup=get_demander_edit_profile_keyboard())
        else:
            await message.answer(
                "🔸 لینک یا آیدی اینستاگرام خود را وارد کنید:", reply_markup=get_skip_keyboard()
            )
            await state.set_state(DemanderRegistration.instagram_id)
        return

    notes = None if message.text == "⏭ رد کردن" else message.text.strip()
    await state.update_data(additional_notes=notes)
    
    if is_editing:
        await state.update_data(editing=False)
        display_value = notes if notes else "حذف شد"
        await message.answer(f"✅ توضیحات شما به '{display_value}' تغییر یافت.")
        await state.set_state(DemanderRegistration.editing_field)
        await message.answer("کدام بخش دیگری را می‌خواهید ویرایش کنید؟", reply_markup=get_demander_edit_profile_keyboard())
    else:
        await show_confirmation_summary(message, state)


async def show_confirmation_summary(message: types.Message, state: FSMContext):
    data = await state.get_data()
    summary = create_demander_summary(data)

    await message.answer(
        f"لطفاً اطلاعات خود را بررسی کنید:\n\n{summary}",
        reply_markup=get_confirm_keyboard(),
    )
    await state.set_state(DemanderRegistration.confirm)


@router.message(DemanderRegistration.confirm)
async def process_confirmation(message: Message, state: FSMContext, session: AsyncSession):
    if message.text == "❌ انصراف":
        await state.clear()
        await message.answer("ثبت‌نام لغو شد.", reply_markup=ReplyKeyboardRemove())
        return

    if message.text == "🔄 ویرایش اطلاعات":
        await message.answer(
            "کدام بخش را می‌خواهید ویرایش کنید؟",
            reply_markup=get_demander_edit_profile_keyboard(),
        )
        await state.set_state(DemanderRegistration.editing_field)
        return

    if message.text == "✅ تأیید نهایی":
        try:
            data = await state.get_data()
            user = await get_or_create_user(session, message.from_user, UserRole.DEMANDER)
            user.role = UserRole.DEMANDER

            # Check existing profile
            demander = await session.scalar(
                select(Demander).where(Demander.user_id == user.id)
            )

            if demander:
                # Update
                update_fields = [
                    "full_name",
                    "company_name",
                    "address",
                    "gender",
                    "phone_number",
                    "instagram_id",
                    "additional_notes",
                ]
                for f in update_fields:
                    if f in data and hasattr(demander, f):
                        setattr(demander, f, data.get(f))
            else:
                demander = Demander(
                    user_id=user.id,
                    full_name=data["full_name"],
                    company_name=data.get("company_name"),
                    address=data["address"],
                    gender=data["gender"],
                    phone_number=data["phone_number"],
                    instagram_id=data.get("instagram_id"),
                    additional_notes=data.get("additional_notes"),
                )
                session.add(demander)

            await session.commit()

            await message.answer(
                "✅ ثبت‌نام شما با موفقیت انجام شد!",
                reply_markup=get_demander_menu_keyboard(),
            )
            await state.set_state(DemanderMenu.main_menu)

        except Exception as e:
            logging.exception("Error during demander registration:")
            await message.answer("❌ خطا در ثبت اطلاعات رخ داد.", reply_markup=ReplyKeyboardRemove())
            await state.clear()

# ========== Handlers for Editing During Registration ==========

@router.message(DemanderRegistration.editing_field)
async def registration_choose_field_to_edit(message: Message, state: FSMContext):
    """Choose which field to edit during registration confirmation."""
    if message.text == "↩️ بازگشت به منو":
        await show_confirmation_summary(message, state)
        return

    if message.text not in EDITABLE_FIELDS:
        await message.answer("لطفاً یک گزینه معتبر از کیبورد انتخاب کنید.")
        return

    field_to_edit = EDITABLE_FIELDS[message.text]
    await state.update_data(field_to_edit=field_to_edit, field_to_edit_fa=message.text, editing=True)
    
    # Redirect to appropriate registration state based on field
    if field_to_edit == "full_name":
        await message.answer("🔸 نام و نام خانوادگی جدید خود را وارد کنید:", reply_markup=get_back_keyboard())
        await state.set_state(DemanderRegistration.full_name)
    elif field_to_edit == "company_name":
        await message.answer("🔸 نام شرکت/گروه جدید خود را وارد کنید:", reply_markup=get_skip_keyboard())
        await state.set_state(DemanderRegistration.company_name)
    elif field_to_edit == "address":
        await message.answer("🔸 آدرس جدید خود را وارد کنید:", reply_markup=get_back_keyboard())
        await state.set_state(DemanderRegistration.address)
    elif field_to_edit == "gender":
        await message.answer("🔸 جنسیت جدید خود را انتخاب کنید:", reply_markup=get_gender_keyboard())
        await state.set_state(DemanderRegistration.gender)
    elif field_to_edit == "phone_number":
        await message.answer("🔸 شماره تماس جدید خود را وارد کنید:", reply_markup=get_back_keyboard())
        await state.set_state(DemanderRegistration.phone_number)
    elif field_to_edit == "instagram_id":
        await message.answer("🔸 آیدی اینستاگرام جدید خود را وارد کنید:", reply_markup=get_skip_keyboard())
        await state.set_state(DemanderRegistration.instagram_id)
    elif field_to_edit == "additional_notes":
        await message.answer("🔸 توضیحات جدید خود را وارد کنید:", reply_markup=get_skip_keyboard())
        await state.set_state(DemanderRegistration.additional_notes)
    else:
        await message.answer("این فیلد قابل ویرایش نیست.")

# ======================= Demander Menu Handlers =========================

@router.message(F.text == "👤 مشاهده پروفایل", DemanderMenu.main_menu)
async def view_profile(message: Message, state: FSMContext, session: AsyncSession):
    # Query with eager loading of demander_profile
    from sqlalchemy.orm import selectinload
    stmt = select(User).options(selectinload(User.demander_profile)).where(User.telegram_id == str(message.from_user.id))
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not user.demander_profile:
        await message.answer("پروفایل شما یافت نشد!")
        return

    profile_text = create_demander_profile_text(user.demander_profile)
    await message.answer(profile_text)


@router.message(F.text == "✏️ ویرایش پروفایل", DemanderMenu.main_menu)
async def edit_profile_start(message: Message, state: FSMContext):
    await state.set_state(DemanderEditProfile.choosing_field)
    await message.answer(
        "کدام بخش پروفایل را می‌خواهید ویرایش کنید؟",
        reply_markup=get_demander_edit_profile_keyboard(),
    )

@router.message(DemanderEditProfile.choosing_field)
async def edit_profile_choose_field(message: Message, state: FSMContext, session: AsyncSession):
    """انتخاب فیلد برای ویرایش"""
    if message.text == "↩️ بازگشت به منو":
        await state.set_state(DemanderMenu.main_menu)
        await message.answer("به منوی درخواست‌کننده بازگشتید.", reply_markup=get_demander_menu_keyboard())
        return

    if message.text not in EDITABLE_FIELDS:
        await message.answer("لطفاً یک گزینه معتبر از کیبورد انتخاب کنید.")
        return

    # For other fields
    field_to_edit = EDITABLE_FIELDS[message.text]
    await state.update_data(field_to_edit=field_to_edit, field_to_edit_fa=message.text)
    
    await state.set_state(DemanderEditProfile.entering_value)
    await message.answer(f"لطفاً مقدار جدید برای '{message.text}' را وارد کنید:", reply_markup=get_back_keyboard())

@router.message(DemanderEditProfile.entering_value)
async def edit_profile_enter_value(message: Message, state: FSMContext, session: AsyncSession):
    """دریافت و ذخیره مقدار جدید برای فیلد"""
    if message.text == "↩️ بازگشت":
        await state.set_state(DemanderEditProfile.choosing_field)
        await message.answer("از کدام بخش می‌خواهید ویرایش کنید?", reply_markup=get_demander_edit_profile_keyboard())
        return

    data = await state.get_data()
    field_to_edit = data.get("field_to_edit")
    field_to_edit_fa = data.get("field_to_edit_fa")

    new_value = message.text
    # Regular field validation
    if field_to_edit == 'phone_number':
        phone = validate_phone_number(new_value)
        if not phone:
            await message.answer("شماره تماس نامعتبر است.")
            return
        new_value = phone

    try:
        # Update the database
        user = await get_user_by_telegram_id(session, str(message.from_user.id))
        if user and user.demander_profile:
            setattr(user.demander_profile, field_to_edit, new_value)
            await session.commit()
            await message.answer(f"✅ '{field_to_edit_fa}' با موفقیت به '{new_value}' تغییر یافت.")
        else:
            await message.answer("خطا: پروفایل شما یافت نشد.")

        # Return to the edit menu
        await state.set_state(DemanderEditProfile.choosing_field)
        await message.answer("می‌توانید بخش دیگری را ویرایش کنید یا بازگردید.", reply_markup=get_demander_edit_profile_keyboard())

    except Exception as e:
        logging.exception(f"Error updating field {field_to_edit}:")
        await message.answer("خطایی در به‌روزرسانی اطلاعات رخ داد.")

# ======================= Menu Button Handlers (Placeholder) ==============

@router.message(F.text == "🔍 جست‌جوی تأمین‌کننده", DemanderMenu.main_menu)
async def search_suppliers(message: Message, state: FSMContext):
    """جست‌جوی تأمین‌کننده با فیلتر قیمت ساده"""
    await state.update_data(search_filters={})
    await message.answer(
        "🔎 یک بازه قیمت انتخاب کنید (بر اساس قیمت روزانه، به هزار تومان):",
        reply_markup=get_price_range_keyboard(),
    )
    await state.set_state(DemanderMenu.searching)

@router.message(DemanderMenu.searching)
async def handle_search_filters(message: Message, state: FSMContext):
    data = await state.get_data()
    filters = data.get("search_filters", {})

    if message.text == "↩️ بازگشت":
        await state.set_state(DemanderMenu.main_menu)
        await message.answer("به منو برگشتید.")
        return

    ranges_map = {
        "💰 زیر ۵۰۰ هزار تومان": {"lte": 500},
        "💰 ۵۰۰ هزار - ۱ میلیون": {"gte": 500, "lte": 1000},
        "💰 ۱ - ۲ میلیون": {"gte": 1000, "lte": 2000},
        "💰 بالای ۲ میلیون": {"gte": 2000},
        "🤷 مهم نیست": None,
    }
    price_range = ranges_map.get(message.text)
    if message.text not in ranges_map:
        await message.answer("لطفاً یک گزینه معتبر انتخاب کنید.", reply_markup=get_price_range_keyboard())
        return

    # We'll filter on ES field price_daily
    if price_range is not None:
        filters["price_daily"] = price_range

    await state.update_data(search_filters=filters)

    # Execute ES search
    from search.suppliers_index import search_suppliers as es_search
    res = await es_search(query=None, filters=filters, from_=0, size=5)
    hits = res.get("hits", {}).get("hits", [])
    if not hits:
        await message.answer("نتیجه‌ای یافت نشد.")
        await state.set_state(DemanderMenu.main_menu)
        return

    text = "نتایج:"
    for i, h in enumerate(hits, 1):
        src = h.get("_source", {})
        name = src.get("full_name", "بدون نام")
        city = src.get("city", "-")
        price = src.get("price_daily")
        price_text = f"{int(price)*1000:,.0f} تومان" if isinstance(price, (int, float)) else "توافقی"
        text += f"\n{i}. {name} - {city} - روزانه: {price_text}"

    await message.answer(text)
    await state.set_state(DemanderMenu.main_menu)

@router.message(F.text == "📄 وضعیت درخواست‌ها", DemanderMenu.main_menu)
async def view_request_status(message: Message, state: FSMContext):
    """مشاهده وضعیت درخواست‌ها - نسخه آتی"""
    await message.answer("📄 قابلیت مشاهده وضعیت درخواست‌ها به زودی اضافه خواهد شد.")

@router.message(F.text == "🔙 بازگشت به منوی اصلی", DemanderMenu.main_menu)
async def back_to_main_menu(message: Message, state: FSMContext):
    """بازگشت به منوی اصلی"""
    await state.clear()
    await message.answer("به منوی اصلی بازگشتید.", reply_markup=get_main_menu())

# ======================= Helper Functions ===============================

def create_demander_summary(data: dict) -> str:
    summary = f"""
👤 اطلاعات پایه:
نام: {data.get('full_name', '-')}
شرکت/گروه: {data.get('company_name', '-')}
آدرس: {data.get('address', '-')}
جنسیت: {data.get('gender', '-')}
تلفن: {data.get('phone_number', '-')}
اینستاگرام: {data.get('instagram_id', '-')}

📝 توضیحات:
{data.get('additional_notes', '-')}
"""
    return summary


def create_demander_profile_text(demander: Demander) -> str:
    profile = f"""
👤 **پروفایل درخواست‌کننده**

📝 نام کامل: {demander.full_name}
🏢 نام شرکت/گروه: {demander.company_name or '-'}
📍 آدرس: {demander.address}
👤 جنسیت: {demander.gender}
📱 شماره تماس: {demander.phone_number}
"""
    if demander.instagram_id:
        profile += f"📷 اینستاگرام: @{demander.instagram_id}\n"
    
    if demander.additional_notes:
        profile += f"\n📋 توضیحات:\n{demander.additional_notes}"
    
    return profile


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: str) -> User:
    from sqlalchemy.orm import selectinload
    stmt = select(User).options(selectinload(User.demander_profile)).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
