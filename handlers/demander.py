import logging
import os
from aiogram import Router, F, types
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery, FSInputFile, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import User, Demander, UserRole, Supplier, Request, RequestStatus
from database.connection import get_session
from states.demander import (
    DemanderRegistration, DemanderMenu, DemanderEditProfile, DemanderSearch
)
from keyboards.reply import (
    get_demander_search_gender_keyboard,
    get_back_keyboard,
    get_skip_keyboard,
    get_confirm_keyboard,
    get_main_menu,
    get_price_range_keyboard,
)
from keyboards.demander import (
    get_demander_menu_keyboard,
    get_demander_edit_profile_keyboard,
    get_demander_categories_keyboard,
    get_demander_cooperation_types_keyboard,
    get_demander_payment_types_keyboard,
    get_doesnt_matter_keyboard,
)
from keyboards.inline import (
    get_search_result_keyboard,
    get_request_message_keyboard,
    get_request_action_keyboard,
)
from utils.validators import validate_phone_number
from utils.users import get_or_create_user

router = Router()

# Mapping from Persian field names to database column names
EDITABLE_FIELDS = {
    "نام کامل": "full_name",
    "نام شرکت": "company_name", 
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
            await message.answer("🔸 نام شرکت/گروه خود را وارد کنید (اختیاری):", reply_markup=get_back_keyboard())
            await state.set_state(DemanderRegistration.company_name)
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

# ======================= Advanced Demander Search =========================

STYLE_MAP = {
    "✅ 👗 فشن / کت واک": "fashion",
    "✅ 📢 تبلیغاتی / برندینگ": "advertising",
    "✅ 🧕 مذهبی / پوشیده": "religious",
    "✅ 👶 کودک": "children",
    "✅ 🏃 ورزشی": "sports",
    "✅ 🎨 هنری / خاص": "artistic",
    "✅ 🌳 عکاسی فضای باز": "outdoor",
    "✅ 📸 عکاسی استودیویی": "studio",
}

COOP_MAP = {
    "✅ حضوری": "in_person",
    "✅ پروژه‌ای": "project_based",
    "✅ پاره‌وقت": "part_time",
}


def _parse_min_max(text: str) -> tuple | None:
    import re
    nums = [int(n) for n in re.findall(r"\d+", text)]
    if not nums:
        return None
    if len(nums) == 1:
        return (None, nums[0])
    return (nums[0], nums[1])


@router.message(F.text == "🔍 جست‌جوی تأمین‌کننده", DemanderMenu.main_menu)
async def start_advanced_search(message: Message, state: FSMContext):
    await state.update_data(
        search={
            "categories": [],
            "gender": None,
            "cooperation_types": [],
            "payment_types": [],
            "price_filters": {},  # price_hourly/daily/per_cloth -> {gte,lte}
            "category_price_filters": {},  # style -> {gte,lte}
            "city": None,
            "height": None,  # {gte,lte}
            "hair_color": None,
            "skin_color": None,
            "notes": None,
        }
    )
    await message.answer(
        "لطفاً دسته‌بندی‌ها (سبک‌ها) را انتخاب کنید. می‌توانید چند مورد را انتخاب کنید و سپس 'تأیید و ادامه' را بزنید.",
        reply_markup=get_demander_categories_keyboard(),
    )
    await state.set_state(DemanderSearch.categories)


@router.message(DemanderSearch.categories)
async def pick_categories(message: Message, state: FSMContext):
    data = await state.get_data()
    search = data.get("search", {})
    selected = set(search.get("categories", []))

    if message.text == "↩️ بازگشت":
        await state.set_state(DemanderMenu.main_menu)
        await message.answer("به منوی درخواست‌کننده بازگشتید.", reply_markup=get_demander_menu_keyboard())
        return

    if message.text == "✔️ تأیید و ادامه":
        if not selected:
            await message.answer("لطفاً حداقل یک دسته‌بندی را انتخاب کنید.")
            return
        await state.update_data(search={**search, "categories": list(selected)})
        await message.answer("جنسیت مورد نظر را انتخاب کنید:", reply_markup=get_demander_search_gender_keyboard())
        await state.set_state(DemanderSearch.gender)
        return

    if message.text in STYLE_MAP:
        style = STYLE_MAP[message.text]
        if style in selected:
            selected.remove(style)
            await message.answer("❌ از انتخاب‌ها حذف شد.")
        else:
            selected.add(style)
            await message.answer("✅ اضافه شد.")
        await state.update_data(search={**search, "categories": list(selected)})
        return

    await message.answer("لطفاً از گزینه‌های موجود استفاده کنید.")


@router.message(DemanderSearch.gender)
async def pick_gender(message: Message, state: FSMContext):
    if message.text == "↩️ بازگشت":
        await message.answer(
            "لطفاً دسته‌بندی‌ها را انتخاب کنید.",
            reply_markup=get_demander_categories_keyboard(),
        )
        await state.set_state(DemanderSearch.categories)
        return

    if message.text not in ["👨 مرد", "👩 زن", "🤷 مهم نیست"]:
        await message.answer("لطفاً یکی از گزینه‌ها را انتخاب کنید.")
        return

    gender = None
    if message.text == "👨 مرد":
        gender = "مرد"
    elif message.text == "👩 زن":
        gender = "زن"
    # If "مهم نیست", gender remains None
    data = await state.get_data()
    search = data.get("search", {})
    await state.update_data(search={**search, "gender": gender})

    await message.answer(
        "نوع همکاری قابل قبول را انتخاب کنید (می‌توانید چند مورد انتخاب کنید) یا 'مهم نیست' را بزنید.",
        reply_markup=get_demander_cooperation_types_keyboard(),
    )
    await state.set_state(DemanderSearch.cooperation_types)


@router.message(DemanderSearch.cooperation_types)
async def pick_cooperation_types(message: Message, state: FSMContext):
    data = await state.get_data()
    search = data.get("search", {})
    selected = set(search.get("cooperation_types", []))

    if message.text == "↩️ بازگشت":
        await message.answer("جنسیت را انتخاب کنید:", reply_markup=get_demander_search_gender_keyboard())
        await state.set_state(DemanderSearch.gender)
        return

    if message.text == "🤷 مهم نیست":
        await state.update_data(search={**search, "cooperation_types": []})
        # move on
        await message.answer(
            "کدام نوع پرداخت‌ها قابل قبول هستند؟ (می‌توانید چند مورد انتخاب کنید)",
            reply_markup=get_demander_payment_types_keyboard(),
        )
        await state.set_state(DemanderSearch.payment_types)
        return

    if message.text == "✔️ تأیید و ادامه":
        await state.update_data(search={**search, "cooperation_types": list(selected)})
        await message.answer(
            "کدام نوع پرداخت‌ها قابل قبول هستند؟ (می‌توانید چند مورد انتخاب کنید)",
            reply_markup=get_demander_payment_types_keyboard(),
        )
        await state.set_state(DemanderSearch.payment_types)
        return

    if message.text in COOP_MAP:
        coop = COOP_MAP[message.text]
        if coop in selected:
            selected.remove(coop)
            await message.answer("❌ از انتخاب‌ها حذف شد.")
        else:
            selected.add(coop)
            await message.answer("✅ اضافه شد.")
        await state.update_data(search={**search, "cooperation_types": list(selected)})
        return

    await message.answer("لطفاً از گزینه‌های موجود استفاده کنید.")


PRICE_TYPE_MAP = {
    "✅ ساعتی": "price_hourly",
    "✅ روزانه": "price_daily",
    "✅ به ازای هر لباس": "price_per_cloth",
    "✅ بر اساس دسته‌بندی": "category_based",
}


@router.message(DemanderSearch.payment_types)
async def pick_payment_types(message: Message, state: FSMContext):
    data = await state.get_data()
    search = data.get("search", {})
    selected = list(search.get("payment_types", []))

    if message.text == "↩️ بازگشت":
        await message.answer(
            "نوع همکاری قابل قبول را انتخاب کنید.",
            reply_markup=get_demander_cooperation_types_keyboard(),
        )
        await state.set_state(DemanderSearch.cooperation_types)
        return

    if message.text == "✅ همه مورد قبول است":
        selected = ["price_hourly", "price_daily", "price_per_cloth", "category_based"]
        await state.update_data(search={**search, "payment_types": selected})
        # proceed to price ranges per selected
        await _ask_next_price_range(message, state)
        return

    if message.text == "✔️ تأیید و ادامه":
        if not selected:
            await message.answer("لطفاً حداقل یک نوع پرداخت را انتخاب کنید یا 'همه مورد قبول است' را بزنید.")
            return
        await state.update_data(search={**search, "payment_types": selected})
        await _ask_next_price_range(message, state)
        return

    if message.text in PRICE_TYPE_MAP:
        p = PRICE_TYPE_MAP[message.text]
        if p in selected:
            selected.remove(p)
            await message.answer("❌ از انتخاب‌ها حذف شد.")
        else:
            selected.append(p)
            await message.answer("✅ اضافه شد.")
        await state.update_data(search={**search, "payment_types": selected})
        return

    await message.answer("لطفاً از گزینه‌های موجود استفاده کنید.")


async def _ask_next_price_range(message: Message, state: FSMContext):
    data = await state.get_data()
    search = data.get("search", {})
    payment_types = search.get("payment_types", [])
    price_filters = search.get("price_filters", {})
    # find next non-category payment needing range
    for p in ["price_daily", "price_hourly", "price_per_cloth"]:
        if p in payment_types and p not in price_filters:
            name = {"price_daily": "روزانه", "price_hourly": "ساعتی", "price_per_cloth": "به ازای هر لباس"}[p]
            await message.answer(
                f"محدوده قیمت {name} قابل قبول را وارد کنید (به هزار تومان، مانند 300-800) یا 'مهم نیست'.",
                reply_markup=get_doesnt_matter_keyboard(),
            )
            await state.update_data(search={**search, "_current_price_key": p})
            await state.set_state(DemanderSearch.price_range_type)
            return

    # handle category-based if selected
    if "category_based" in payment_types:
        # ask per selected category
        categories = search.get("categories", [])
        cat_filters = search.get("category_price_filters", {})
        for c in categories:
            if c not in cat_filters:
                await message.answer(
                    f"محدوده قیمت برای سبک '{c}' را وارد کنید (هزار تومان، مثل 200-600) یا 'مهم نیست'.",
                    reply_markup=get_doesnt_matter_keyboard(),
                )
                await state.update_data(search={**search, "_current_category": c})
                await state.set_state(DemanderSearch.category_price_range)
                return

    # otherwise proceed to city
    await message.answer("شهر مورد نظر شما چیست؟ (می‌توانید تقریبی بنویسید) یا 'مهم نیست'", reply_markup=get_doesnt_matter_keyboard())
    await state.set_state(DemanderSearch.city)


@router.message(DemanderSearch.price_range_type)
async def enter_price_range_type(message: Message, state: FSMContext):
    data = await state.get_data()
    search = data.get("search", {})
    current_key = search.get("_current_price_key")
    if not current_key:
        await _ask_next_price_range(message, state)
        return

    if message.text == "↩️ بازگشت":
        await message.answer(
            "کدام نوع پرداخت‌ها قابل قبول هستند؟",
            reply_markup=get_demander_payment_types_keyboard(),
        )
        await state.set_state(DemanderSearch.payment_types)
        return

    if message.text == "🤷 مهم نیست":
        # mark this price type as processed with no constraints
        pf = {**search.get("price_filters", {})}
        pf[current_key] = {}
        await state.update_data(search={**search, "price_filters": pf, "_current_price_key": None})
        await _ask_next_price_range(message, state)
        return

    rng = _parse_min_max(message.text)
    if not rng:
        await message.answer("لطفاً یک محدوده معتبر وارد کنید، مثل 300-800 یا 'مهم نیست'.")
        return
    gte, lte = rng
    pf = {**search.get("price_filters", {})}
    pf[current_key] = {k: v for k, v in {"gte": gte, "lte": lte}.items() if v is not None}
    await state.update_data(search={**search, "price_filters": pf, "_current_price_key": None})
    await _ask_next_price_range(message, state)


@router.message(DemanderSearch.category_price_range)
async def enter_category_price_range(message: Message, state: FSMContext):
    data = await state.get_data()
    search = data.get("search", {})
    current_category = search.get("_current_category")
    if not current_category:
        await _ask_next_price_range(message, state)
        return

    if message.text == "↩️ بازگشت":
        await message.answer(
            "کدام نوع پرداخت‌ها قابل قبول هستند؟",
            reply_markup=get_demander_payment_types_keyboard(),
        )
        await state.set_state(DemanderSearch.payment_types)
        return

    if message.text == "🤷 مهم نیست":
        cpf = {**search.get("category_price_filters", {})}
        cpf[current_category] = {}
        await state.update_data(search={**search, "category_price_filters": cpf, "_current_category": None})
        await _ask_next_price_range(message, state)
        return

    rng = _parse_min_max(message.text)
    if not rng:
        await message.answer("لطفاً یک محدوده معتبر وارد کنید، مثل 200-600 یا 'مهم نیست'.")
        return
    gte, lte = rng
    cpf = {**search.get("category_price_filters", {})}
    cpf[current_category] = {k: v for k, v in {"gte": gte, "lte": lte}.items() if v is not None}
    await state.update_data(search={**search, "category_price_filters": cpf, "_current_category": None})
    await _ask_next_price_range(message, state)


@router.message(DemanderSearch.city)
async def enter_city(message: Message, state: FSMContext):
    if message.text == "↩️ بازگشت":
        await _ask_next_price_range(message, state)
        return
    city = None if message.text == "🤷 مهم نیست" else message.text.strip()
    data = await state.get_data()
    search = data.get("search", {})
    await state.update_data(search={**search, "city": city})
    await message.answer("محدوده قد مورد نظر (سانتی‌متر) را وارد کنید، مانند 165-185، یا 'مهم نیست'.", reply_markup=get_doesnt_matter_keyboard())
    await state.set_state(DemanderSearch.height_range)


@router.message(DemanderSearch.height_range)
async def enter_height_range(message: Message, state: FSMContext):
    if message.text == "↩️ بازگشت":
        await message.answer("شهر مورد نظر شما چیست؟", reply_markup=get_doesnt_matter_keyboard())
        await state.set_state(DemanderSearch.city)
        return
    data = await state.get_data()
    search = data.get("search", {})
    if message.text == "🤷 مهم نیست":
        await state.update_data(search={**search, "height": None})
    else:
        rng = _parse_min_max(message.text)
        if not rng:
            await message.answer("فرمت محدوده معتبر نیست. مثال: 165-185 یا 'مهم نیست'.")
            return
        gte, lte = rng
        await state.update_data(search={**search, "height": {k: v for k, v in {"gte": gte, "lte": lte}.items() if v is not None}})

    await message.answer("رنگ مو (برای اولویت‌بندی، اختیاری) را وارد کنید یا 'مهم نیست'.", reply_markup=get_doesnt_matter_keyboard())
    await state.set_state(DemanderSearch.hair_color)


@router.message(DemanderSearch.hair_color)
async def enter_hair_color(message: Message, state: FSMContext):
    if message.text == "↩️ بازگشت":
        await message.answer("محدوده قد را وارد کنید.", reply_markup=get_doesnt_matter_keyboard())
        await state.set_state(DemanderSearch.height_range)
        return
    hair = None if message.text == "🤷 مهم نیست" else message.text.strip()
    data = await state.get_data()
    search = data.get("search", {})
    await state.update_data(search={**search, "hair_color": hair})
    await message.answer("رنگ پوست (برای اولویت‌بندی، اختیاری) را وارد کنید یا 'مهم نیست'.", reply_markup=get_doesnt_matter_keyboard())
    await state.set_state(DemanderSearch.skin_color)


@router.message(DemanderSearch.skin_color)
async def enter_skin_color(message: Message, state: FSMContext):
    if message.text == "↩️ بازگشت":
        await message.answer("رنگ مو را وارد کنید.", reply_markup=get_doesnt_matter_keyboard())
        await state.set_state(DemanderSearch.hair_color)
        return
    skin = None if message.text == "🤷 مهم نیست" else message.text.strip()
    data = await state.get_data()
    search = data.get("search", {})
    await state.update_data(search={**search, "skin_color": skin})
    await message.answer("توضیحات اضافی (اختیاری) را وارد کنید یا 'مهم نیست'.")
    await state.set_state(DemanderSearch.notes)


@router.message(DemanderSearch.notes)
async def enter_notes_and_search(message: Message, state: FSMContext, session: AsyncSession):
    if message.text == "↩️ بازگشت":
        await message.answer("رنگ پوست را وارد کنید.", reply_markup=get_doesnt_matter_keyboard())
        await state.set_state(DemanderSearch.skin_color)
        return

    notes = None if message.text == "🤷 مهم نیست" else message.text.strip()
    data = await state.get_data()
    search = data.get("search", {})
    search = {**search, "notes": notes}
    await state.update_data(search=search)

    # Build ES query
    filters: list[dict] = []
    should: list[dict] = []
    min_should: int | None = None

    # Exact filters first (fast)
    if search.get("gender"):
        filters.append({"term": {"gender": search["gender"]}})

    if search.get("cooperation_types"):
        filters.append({"terms": {"cooperation_types": search["cooperation_types"]}})

    # Categories: require at least one match via terms filter, and boost by more matches via should
    categories = search.get("categories") or []
    if categories:
        filters.append({"terms": {"work_styles": categories}})
        for c in categories:
            should.append({"term": {"work_styles": {"value": c, "boost": 2.0}}})

    # Price types: use should so any acceptable price can match
    price_filters = search.get("price_filters") or {}
    price_should = []
    for field_key, rng in price_filters.items():
        if rng:
            price_should.append({"range": {field_key: rng}})
    # Note: category-based prices are not flattened in the index yet; reserved for future
    if price_should:
        should.extend(price_should)
        # ensure at least one price condition matches if any were provided
        min_should = (min_should or 0) + 1

    # City fuzzy boosting
    if search.get("city"):
        should.append({
            "match": {
                "city": {
                    "query": search["city"],
                    "fuzziness": "AUTO",
                    "boost": 1.5,
                }
            }
        })

    # Height filter
    if search.get("height"):
        filters.append({"range": {"height": search["height"]}})

    # Hair/Skin color boosting
    if search.get("hair_color"):
        should.append({
            "match": {
                "hair_color": {
                    "query": search["hair_color"],
                    "fuzziness": "AUTO",
                    "boost": 1.2,
                }
            }
        })
    if search.get("skin_color"):
        should.append({
            "match": {
                "skin_color": {
                    "query": search["skin_color"],
                    "fuzziness": "AUTO",
                    "boost": 1.2,
                }
            }
        })

    # Notes boosting through search_text
    query = None
    if search.get("notes"):
        query = search["notes"]

    # Execute ES search with robust error handling
    from search.suppliers_index import search_suppliers as es_search

    try:
        res = await es_search(
            query=query,
            filter_clauses=filters or None,
            from_=0,
            size=10,
            should=should or None,
            min_should_match=min_should,
            sort=None,
        )
        hits = res.get("hits", {}).get("hits", [])
        # Log ES hit IDs (no _source by design)
        try:
            es_ids = [h.get("_id") for h in hits]
            logging.info(f"ES hit IDs: {es_ids}")
        except Exception as log_err:
            logging.warning(f"Failed to log ES hits: {log_err}")
        # Filter out inactive suppliers based on DB (User.is_active == True)
        try:
            supplier_ids: list[int] = []
            for h in hits:
                sid = h.get("_id") if isinstance(h, dict) else None
                if sid is not None:
                    try:
                        supplier_ids.append(int(str(sid)))
                    except (ValueError, TypeError):
                        continue
            if supplier_ids:
                from sqlalchemy import select
                active_stmt = select(Supplier.id).join(User, Supplier.user_id == User.id).where(
                    Supplier.id.in_(supplier_ids),
                    User.is_active.is_(True)
                )
                result = await session.execute(active_stmt)
                active_ids = set(int(r) for r in result.scalars().all())
                # Preserve original order
                hits = [h for h in hits if int(str(h.get("_id"))) in active_ids]
        except Exception:
            logging.exception("Failed to filter inactive suppliers from ES results")
    except Exception:
        logging.exception("Elasticsearch search failed, falling back to DB search")
        # Fallback to database search
        hits = await _fallback_search_suppliers(session=session, search=search)
        # hits here are already source-like dicts

    if not hits:
        await state.set_state(DemanderMenu.main_menu)
        await message.answer("نتیجه‌ای یافت نشد.", reply_markup=get_demander_menu_keyboard())
        return

    # Store search results in state for navigation
    await state.update_data(search_results=hits, current_result_index=0)
    await state.set_state(DemanderSearch.viewing_results)
    # Remove reply keyboard so only inline navigation/back buttons are available
    await message.answer("🔎 نتایج جست‌وجو", reply_markup=ReplyKeyboardRemove())
    
    # Show the first result
    await show_search_result(message, state, 0)

@router.message(F.text == "📄 وضعیت درخواست‌ها", DemanderMenu.main_menu)
async def view_request_status(message: Message, state: FSMContext, session: AsyncSession):
    """مشاهده وضعیت درخواست‌ها"""
    # Get demander info
    user = await get_user_by_telegram_id(session, str(message.from_user.id))
    if not user or not user.demander_profile:
        await message.answer("خطا در دریافت اطلاعات کاربری.")
        return
    
    demander = user.demander_profile
    
    # Get requests with supplier info
    from sqlalchemy.orm import selectinload
    requests_stmt = select(Request).options(
        selectinload(Request.supplier)
    ).where(Request.demander_id == demander.id).order_by(Request.created_at.desc())
    
    result = await session.execute(requests_stmt)
    requests = result.scalars().all()
    
    if not requests:
        await message.answer("شما هنوز هیچ درخواستی ارسال نکرده‌اید.")
        return
    
    # Format request list
    status_text = "📄 **وضعیت درخواست‌های شما:**\n\n"
    
    for i, req in enumerate(requests, 1):
        status_emoji = {
            RequestStatus.PENDING: "⏳",
            RequestStatus.ACCEPTED: "✅", 
            RequestStatus.REJECTED: "❌"
        }.get(req.status, "❓")
        
        status_name = {
            RequestStatus.PENDING: "در انتظار پاسخ",
            RequestStatus.ACCEPTED: "پذیرفته شده",
            RequestStatus.REJECTED: "رد شده"
        }.get(req.status, "نامشخص")
        
        # Format date
        created_date = req.created_at.strftime("%Y/%m/%d %H:%M")
        
        status_text += f"""**{i}.** {status_emoji} **{status_name}**
👤 تأمین‌کننده: {req.supplier.full_name}
📅 تاریخ ارسال: {created_date}
📝 پیام: {req.message[:50]}{'...' if len(req.message) > 50 else ''}

"""
    
    status_text += "💡 برای مشاهده جزئیات بیشتر و ارسال درخواست جدید، از منوی جست‌وجو استفاده کنید."
    
    await message.answer(status_text, parse_mode="Markdown")

@router.message(F.text == "🔙 بازگشت به منوی اصلی", DemanderMenu.main_menu)
async def back_to_main_menu(message: Message, state: FSMContext):
    """بازگشت به منوی اصلی"""
    await state.clear()
    await message.answer("به منوی اصلی بازگشتید.", reply_markup=get_main_menu())

# ======================= Search Result Handlers ===============================

async def show_search_result(message: Message, state: FSMContext, result_index: int):
    """Show a single search result with navigation buttons"""
    data = await state.get_data()
    results = data.get("search_results", [])
    
    if not results or result_index >= len(results):
        await message.answer("خطا در نمایش نتایج.")
        await state.set_state(DemanderMenu.main_menu)
        return
    
    result = results[result_index]
    # Get supplier ID from search results
    # When ES _source is disabled, hits contain only metadata including "_id"
    supplier_id = None
    if isinstance(result, dict):
        supplier_id = result.get("_id") or result.get("id")
    
    # Get complete supplier data from PostgreSQL using the ID
    try:
        logging.info(f"Resolved supplier_id from ES hit: {supplier_id} (type={type(supplier_id).__name__})")
        supplier_id_int = int(str(supplier_id))
        from sqlalchemy.orm import selectinload
        async for session in get_session():
            stmt = select(Supplier).options(selectinload(Supplier.user)).where(Supplier.id == supplier_id_int)
            supplier_result = await session.execute(stmt)
            supplier = supplier_result.scalar_one_or_none()
            
            if not supplier:
                await message.answer("خطا در بارگذاری اطلاعات تأمین‌کننده.")
                return
            
            # Convert supplier object to dict for the display function
            supplier_data = {
                "full_name": supplier.full_name,
                "gender": supplier.gender,
                "age": supplier.age,
                "phone_number": supplier.phone_number,
                "instagram_id": supplier.instagram_id,
                "height": supplier.height,
                "weight": supplier.weight,
                "hair_color": supplier.hair_color,
                "eye_color": supplier.eye_color,
                "skin_color": supplier.skin_color,
                "top_size": supplier.top_size,
                "bottom_size": supplier.bottom_size,
                "special_features": supplier.special_features,
                "pricing_data": supplier.pricing_data,
                "city": supplier.city,
                "area": supplier.area,
                "cooperation_types": supplier.cooperation_types,
                "work_styles": supplier.work_styles,
                "brand_experience": supplier.brand_experience,
                "additional_notes": supplier.additional_notes,
                "portfolio_photos": supplier.portfolio_photos,
            }
            # Log DB supplier payload
            try:
                logging.info(f"DB supplier fetched for id={supplier_id_int}: {supplier_data}")
            except Exception as log_err:
                logging.warning(f"Failed to log DB supplier: {log_err}")
            break
    except (ValueError, TypeError) as e:
        logging.error(f"Error converting supplier_id to int: {e}")
        await message.answer("خطا در شناسایی تأمین‌کننده.")
        return
    except Exception as e:
        logging.error(f"Error fetching supplier data: {e}")
        await message.answer("خطا در بارگذاری اطلاعات تأمین‌کننده.")
        return
    
    # Create detailed profile text
    profile_text = create_supplier_detail_text(supplier_data, result_index, len(results))
    
    # Get keyboard for navigation and actions
    keyboard = get_search_result_keyboard(result_index, len(results), int(str(supplier_id)))
    
    # Send profile picture if available
    portfolio_photos = supplier_data.get("portfolio_photos", [])
    if portfolio_photos:
        # Send all photos in a single media group (up to 10 as per Telegram limits)
        try:
            photos = portfolio_photos[:10]
            media = []
            for i, photo in enumerate(photos):
                # Build media item; support both Telegram file IDs and local paths
                media_obj = None
                if os.path.exists(photo):
                    media_obj = InputMediaPhoto(media=FSInputFile(photo))
                else:
                    media_obj = InputMediaPhoto(media=photo)
                # Put caption on the last item
                if i == len(photos) - 1:
                    media_obj.caption = profile_text
                media.append(media_obj)
            await message.answer_media_group(media=media)
            # Send keyboard in a follow-up message (sendMediaGroup cannot attach reply_markup)
            await message.answer("گزینه‌ها:", reply_markup=keyboard)
            return
        except Exception as e:
            logging.error(f"Failed to send media group: {e}")
            # Fallback to text-only below
    
    # Send text-only message if no photo or photo failed
    await message.answer(
        profile_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("search_nav:"), DemanderSearch.viewing_results)
async def handle_search_navigation(callback: CallbackQuery, state: FSMContext):
    """Handle search result navigation"""
    data = await state.get_data()
    results = data.get("search_results", [])
    current_index = data.get("current_result_index", 0)
    
    action = callback.data.split(":")[1]
    if action == "prev" and current_index > 0:
        new_index = current_index - 1
    elif action == "next" and current_index < len(results) - 1:
        new_index = current_index + 1
    else:
        await callback.answer("عملیات نامعتبر")
        return
    
    await state.update_data(current_result_index=new_index)
    
    # Delete the current message and send new one
    await callback.message.delete()
    await show_search_result(callback.message, state, new_index)
    await callback.answer()

@router.callback_query(F.data.startswith("send_request:"), DemanderSearch.viewing_results)
async def handle_send_request(callback: CallbackQuery, state: FSMContext):
    """Handle send request button"""
    supplier_id = callback.data.split(":")[1]
    await state.update_data(selected_supplier_id=supplier_id)
    await state.set_state(DemanderSearch.writing_request_message)
    
    await callback.message.edit_text(
        "📝 لطفاً پیام درخواست خود را بنویسید:\n\n"
        "💡 در پیام خود می‌توانید:\n"
        "• نوع پروژه یا کار مورد نظر را شرح دهید\n"
        "• زمان و مکان کار را مشخص کنید\n" 
        "• سایر توضیحات مهم را اضافه کنید",
        reply_markup=get_request_message_keyboard(supplier_id)
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_demander_menu", DemanderSearch.viewing_results)
async def handle_back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Handle back to menu button"""
    await state.set_state(DemanderMenu.main_menu)
    await callback.message.edit_text(
        "بازگشت به منوی درخواست‌کننده",
        reply_markup=None
    )
    await callback.message.answer(
        "به منوی درخواست‌کننده بازگشتید.",
        reply_markup=get_demander_menu_keyboard()
    )
    await callback.answer()

@router.message(DemanderSearch.writing_request_message)
async def process_request_message(message: Message, state: FSMContext, session: AsyncSession):
    """Process the request message and send to supplier"""
    data = await state.get_data()
    supplier_id = data.get("selected_supplier_id")
    
    if not supplier_id:
        await message.answer("خطا در ارسال درخواست. لطفاً دوباره تلاش کنید.")
        await state.set_state(DemanderMenu.main_menu)
        return
    
    try:
        supplier_id = int(supplier_id)
    except (ValueError, TypeError):
        await message.answer("خطا در شناسایی تأمین‌کننده. لطفاً دوباره تلاش کنید.")
        await state.set_state(DemanderMenu.main_menu)
        return
    
    # Get demander info
    user = await get_user_by_telegram_id(session, str(message.from_user.id))
    if not user or not user.demander_profile:
        await message.answer("خطا در دریافت اطلاعات کاربری.")
        await state.set_state(DemanderMenu.main_menu)
        return
    
    demander = user.demander_profile
    
    # Get supplier info
    supplier_stmt = select(Supplier).where(Supplier.id == int(supplier_id))
    supplier_result = await session.execute(supplier_stmt)
    supplier = supplier_result.scalar_one_or_none()
    
    if not supplier:
        await message.answer("تأمین‌کننده مورد نظر یافت نشد.")
        await state.set_state(DemanderMenu.main_menu)
        return
    
    # Create request
    new_request = Request(
        demander_id=demander.id,
        supplier_id=supplier.id,
        message=message.text,
        demander_phone=demander.phone_number,
        status=RequestStatus.PENDING
    )
    
    session.add(new_request)
    await session.commit()
    
    # Send notification to supplier
    try:
        supplier_user_stmt = select(User).where(User.id == supplier.user_id)
        supplier_user_result = await session.execute(supplier_user_stmt)
        supplier_user = supplier_user_result.scalar_one_or_none()
        
        if supplier_user:
            notification_text = f"""
🔔 **درخواست جدید دریافت شد!**

👤 **از:** {demander.full_name}
🏢 **شرکت:** {demander.company_name or '-'}

📝 **پیام درخواست:**
{message.text}

لطفاً درخواست را بررسی کرده و پاسخ دهید.
"""
            
            keyboard = get_request_action_keyboard(new_request.id)
            await message.bot.send_message(
                chat_id=supplier_user.telegram_id,
                text=notification_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
    except Exception as e:
        logging.error(f"Failed to send notification to supplier: {e}")
    
    # Inform the demander and return to viewing the current result options (do not go to the menu)
    await message.answer(
        "✅ درخواست شما با موفقیت ارسال شد!\n\n"
        "تأمین‌کننده اطلاع‌رسانی شده و به محض پاسخ، به شما اطلاع داده خواهد شد."
    )
    await state.set_state(DemanderSearch.viewing_results)
    data = await state.get_data()
    current_index = data.get("current_result_index", 0)
    await show_search_result(message, state, current_index)

@router.callback_query(F.data == "cancel_send_request", DemanderSearch.writing_request_message)
async def cancel_send_request(callback: CallbackQuery, state: FSMContext):
    """Cancel sending request and return to search results"""
    await state.set_state(DemanderSearch.viewing_results)
    data = await state.get_data()
    current_index = data.get("current_result_index", 0)
    
    await callback.message.delete()
    await show_search_result(callback.message, state, current_index)
    await callback.answer("انصراف از ارسال درخواست")

# ======================= Helper Functions ===============================

async def _fallback_search_suppliers(session: AsyncSession, search: dict) -> list[dict]:
    """Lightweight fallback query using the database if Elastic is unavailable.
    It applies a subset of filters for a best-effort result.
    """
    stmt = select(Supplier)
    # Only active users' suppliers
    from database.models import User as _User
    stmt = stmt.where(Supplier.user.has(_User.is_active.is_(True)))
    # gender filter
    if search.get("gender"):
        stmt = stmt.where(Supplier.gender == search["gender"]) 
    # cooperation_types any-match (simple contains check)
    if search.get("cooperation_types"):
        from sqlalchemy import or_
        ors = []
        for ct in search["cooperation_types"]:
            ors.append(Supplier.cooperation_types.contains([ct]))
        if ors:
            stmt = stmt.where(or_(*ors))
    # height range
    if isinstance(search.get("height"), dict):
        hr = search["height"]
        if "gte" in hr:
            stmt = stmt.where(Supplier.height >= hr["gte"]) 
        if "lte" in hr:
            stmt = stmt.where(Supplier.height <= hr["lte"]) 
    # city contains
    if search.get("city"):
        stmt = stmt.where(Supplier.city.ilike(f"%{search['city']}%"))

    result = await session.execute(stmt)
    rows = result.scalars().all()
    output: list[dict] = []
    for s in rows:
        output.append({
            "full_name": s.full_name,
            "city": s.city,
            "work_styles": s.work_styles or [],
            "price_daily": (s.pricing_data or {}).get("daily"),
        })
    return output

def create_demander_summary(data: dict) -> str:
    summary = f"""
👤 اطلاعات پایه:
نام: {data.get('full_name', '-')}
شرکت/گروه: {data.get('company_name', '-')}
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
📱 شماره تماس: {demander.phone_number}
"""
    if demander.instagram_id:
        profile += f"📷 اینستاگرام: @{demander.instagram_id}\n"
    
    if demander.additional_notes:
        profile += f"\n📋 توضیحات:\n{demander.additional_notes}"
    
    return profile


def create_supplier_detail_text(supplier_data: dict, current_index: int, total_results: int) -> str:
    """Create detailed supplier profile text without phone number"""
    
    def format_price_data(pricing_data):
        """Format pricing information"""
        if not pricing_data:
            return "قیمت: توافقی"
        
        price_parts = []
        if pricing_data.get("hourly"):
            price_parts.append(f"ساعتی: {int(pricing_data['hourly'])*1000:,.0f} تومان")
        if pricing_data.get("daily"):
            price_parts.append(f"روزانه: {int(pricing_data['daily'])*1000:,.0f} تومان")
        if pricing_data.get("per_cloth"):
            price_parts.append(f"هر لباس: {int(pricing_data['per_cloth'])*1000:,.0f} تومان")
        
        if pricing_data.get("category_based"):
            category_prices = []
            for cat, price in pricing_data["category_based"].items():
                cat_name = {
                    "fashion": "فشن",
                    "advertising": "تبلیغاتی", 
                    "religious": "مذهبی",
                    "children": "کودک",
                    "sports": "ورزشی",
                    "artistic": "هنری",
                    "outdoor": "فضای باز",
                    "studio": "استودیویی"
                }.get(cat, cat)
                category_prices.append(f"{cat_name}: {int(price)*1000:,.0f} تومان")
            if category_prices:
                price_parts.append("قیمت بر اساس دسته‌بندی:\n" + "\n".join(category_prices))
        
        return "\n".join(price_parts) if price_parts else "قیمت: توافقی"
    
    def format_work_styles(styles):
        """Format work styles"""
        if not styles:
            return "-"
        style_names = []
        for style in styles:
            style_name = {
                "fashion": "فشن",
                "advertising": "تبلیغاتی",
                "religious": "مذهبی", 
                "children": "کودک",
                "sports": "ورزشی",
                "artistic": "هنری",
                "outdoor": "فضای باز",
                "studio": "استودیو"
            }.get(style, style)
            style_names.append(style_name)
        return ", ".join(style_names)
    
    def format_cooperation_types(types):
        """Format cooperation types"""
        if not types:
            return "-"
        type_names = []
        for ctype in types:
            type_name = {
                "in_person": "حضوری",
                "project_based": "پروژه‌ای", 
                "part_time": "پاره وقت"
            }.get(ctype, ctype)
            type_names.append(type_name)
        return ", ".join(type_names)

    profile = f"""👤 **{supplier_data.get('full_name', 'بدون نام')}**

🔍 **اطلاعات پایه:**
👤 جنسیت: {supplier_data.get('gender', '-')}
🎂 سن: {supplier_data.get('age', '-')} سال
📏 قد: {supplier_data.get('height', '-')} سانتی‌متر
⚖️ وزن: {supplier_data.get('weight', '-')} کیلوگرم
📍 شهر: {supplier_data.get('city', '-')}
🏘️ منطقه: {supplier_data.get('area', '-')}

🎨 **مشخصات ظاهری:**
💇 رنگ مو: {supplier_data.get('hair_color', '-')}
👁️ رنگ چشم: {supplier_data.get('eye_color', '-')}
🌟 رنگ پوست: {supplier_data.get('skin_color', '-')}
👕 سایز بالا تنه: {supplier_data.get('top_size', '-')}
👖 سایز پایین تنه: {supplier_data.get('bottom_size', '-')}

💼 **اطلاعات همکاری:**
🎭 سبک‌های کاری: {format_work_styles(supplier_data.get('work_styles'))}
🤝 نوع همکاری: {format_cooperation_types(supplier_data.get('cooperation_types'))}

💰 **قیمت‌گذاری:**
{format_price_data(supplier_data.get('pricing_data'))}

📸 **اینستاگرام:** {"@" + supplier_data.get('instagram_id') if supplier_data.get('instagram_id') else '-'}
"""

    if supplier_data.get('special_features'):
        profile += f"\n✨ **ویژگی‌های خاص:** {supplier_data['special_features']}"
    
    if supplier_data.get('brand_experience'):
        profile += f"\n🏆 **سابقه کار:** {supplier_data['brand_experience']}"
    
    if supplier_data.get('additional_notes'):
        profile += f"\n📝 **توضیحات تکمیلی:** {supplier_data['additional_notes']}"
    
    # Add result counter
    profile += f"\n\n📊 نتیجه {current_index + 1} از {total_results}"
    
    return profile


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: str) -> User:
    from sqlalchemy.orm import selectinload
    stmt = select(User).options(selectinload(User.demander_profile)).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

# ========== Fallback: Recover demander main menu state after restarts ==========

@router.message(F.text.in_({
    "👤 مشاهده پروفایل",
    "✏️ ویرایش پروفایل",
    "📄 وضعیت درخواست‌ها",
    "🔍 جست‌جوی تأمین‌کننده",
    "🔙 بازگشت به منوی اصلی",
}))
async def demander_main_menu_fallback(message: Message, state: FSMContext, session: AsyncSession):
    """Allow demander main menu actions to work even if FSM state was lost (e.g., after container restart)."""
    # Verify the user is a demander
    user = await get_user_by_telegram_id(session, str(message.from_user.id))
    if not user or user.role != UserRole.DEMANDER:
        return

    # Restore expected menu state
    await state.set_state(DemanderMenu.main_menu)

    # Dispatch to the appropriate handler
    text = message.text
    if text == "👤 مشاهده پروفایل":
        await view_profile(message, state, session)
    elif text == "✏️ ویرایش پروفایل":
        await edit_profile_start(message, state)
    elif text == "📄 وضعیت درخواست‌ها":
        await view_request_status(message, state, session)
    elif text == "🔍 جست‌روی تأمین‌کننده" or text == "🔍 جست‌جوی تأمین‌کننده":
        await start_advanced_search(message, state)
    elif text == "🔙 بازگشت به منوی اصلی":
        await back_to_main_menu(message, state)
