import logging
from aiogram import Router, F, types
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import User, Demander, UserRole, Supplier
from states.demander import (
    DemanderRegistration, DemanderMenu, DemanderEditProfile, DemanderSearch
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
    get_demander_categories_keyboard,
    get_demander_cooperation_types_keyboard,
    get_demander_payment_types_keyboard,
    get_doesnt_matter_keyboard,
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
        await message.answer("جنسیت مورد نظر را انتخاب کنید:", reply_markup=get_gender_keyboard())
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

    if message.text not in ["👨 مرد", "👩 زن"]:
        await message.answer("لطفاً یکی از گزینه‌ها را انتخاب کنید.")
        return

    gender = "مرد" if message.text == "👨 مرد" else "زن"
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
        await message.answer("جنسیت را انتخاب کنید:", reply_markup=get_gender_keyboard())
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
    # Convert filters list into dict for helper
    filter_dict = {}
    for f in filters:
        if "term" in f:
            key, value = next(iter(f["term"].items()))
            filter_dict[key] = value
        elif "terms" in f:
            key, value = next(iter(f["terms"].items()))
            filter_dict[key] = value
        elif "range" in f:
            key, value = next(iter(f["range"].items()))
            filter_dict[key] = value

    try:
        res = await es_search(
            query=query,
            filters=filter_dict or None,
            from_=0,
            size=10,
            should=should or None,
            min_should_match=min_should,
            sort=None,
        )
        hits = res.get("hits", {}).get("hits", [])
    except Exception:
        logging.warning("Elasticsearch search failed (service unavailable or timeout), falling back to DB search")
        # Fallback to database search
        hits = await _fallback_search_suppliers(session=session, search=search)
        # hits here are already source-like dicts
        if not hits:
            await message.answer("نتیجه‌ای یافت نشد.")
            await state.set_state(DemanderMenu.main_menu)
            return

        text_lines = ["نتایج پیشنهادی:"]
        for i, src in enumerate(hits[:10], 1):
            name = src.get("full_name", "بدون نام")
            city = src.get("city") or "-"
            styles = src.get("work_styles") or []
            price_daily = src.get("price_daily")
            price_display = f"روزانه: {int(price_daily)*1000:,.0f} تومان" if isinstance(price_daily, (int, float)) else "قیمت: توافقی/نامشخص"
            text_lines.append(f"{i}. {name} - {city} - {price_display}\nسبک‌ها: {', '.join(styles) if styles else '-'}")

        await message.answer("\n\n".join(text_lines))
        await state.set_state(DemanderMenu.main_menu)
        return

    hits = res.get("hits", {}).get("hits", [])
    if not hits:
        await message.answer("نتیجه‌ای یافت نشد.")
        await state.set_state(DemanderMenu.main_menu)
        return

    # Show results without phone numbers
    text_lines = ["نتایج پیشنهادی:"]
    for i, h in enumerate(hits[:10], 1):
        src = h.get("_source", {})
        name = src.get("full_name", "بدون نام")
        city = src.get("city") or "-"
        styles = src.get("work_styles") or []
        price_daily = src.get("price_daily")
        price_display = f"روزانه: {int(price_daily)*1000:,.0f} تومان" if isinstance(price_daily, (int, float)) else "قیمت: توافقی/نامشخص"
        text_lines.append(f"{i}. {name} - {city} - {price_display}\nسبک‌ها: {', '.join(styles) if styles else '-'}")

    await message.answer("\n\n".join(text_lines))
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

async def _fallback_search_suppliers(session: AsyncSession, search: dict) -> list[dict]:
    """Lightweight fallback query using the database if Elastic is unavailable.
    It applies a subset of filters for a best-effort result.
    """
    stmt = select(Supplier)
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
