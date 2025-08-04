from aiogram.fsm.state import State, StatesGroup

class DemanderSearch(StatesGroup):
    city = State()
    gender = State()
    age_range = State()
    work_styles = State()
    price_range = State()
    special_features = State()

    # نمایش نتایج
    viewing_results = State()
    viewing_supplier = State()
    writing_message = State()

class DemanderRegistration(StatesGroup):
    """حالت‌های ثبت‌نام درخواست‌کننده"""
    full_name = State()
    company_name = State()
    address = State()
    gender = State()
    phone_number = State()
    instagram_id = State()
    additional_notes = State()

    # Confirmation & editing
    confirm = State()
    editing_field = State()

class DemanderMenu(StatesGroup):
    """منوی اصلی درخواست‌کننده"""
    main_menu = State()

class DemanderEditProfile(StatesGroup):
    """فرآیند ویرایش پروفایل درخواست‌کننده"""
    choosing_field = State()
    entering_value = State()
