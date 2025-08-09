from aiogram.fsm.state import State, StatesGroup

class DemanderSearch(StatesGroup):
    categories = State()
    gender = State()
    cooperation_types = State()
    payment_types = State()
    price_range_type = State()
    category_price_range = State()
    city = State()
    height_range = State()
    hair_color = State()
    skin_color = State()
    notes = State()

    # نمایش نتایج
    viewing_results = State()
    viewing_supplier = State()
    writing_request_message = State()

class DemanderRegistration(StatesGroup):
    """حالت‌های ثبت‌نام درخواست‌کننده"""
    full_name = State()
    company_name = State()
    phone_number = State()
    instagram_id = State()
    additional_notes = State()

    # Confirmation & editing
    confirm = State()
    editing_field = State()

class DemanderMenu(StatesGroup):
    """منوی اصلی درخواست‌کننده"""
    main_menu = State()
    searching = State()

class DemanderEditProfile(StatesGroup):
    """فرآیند ویرایش پروفایل درخواست‌کننده"""
    choosing_field = State()
    entering_value = State()
