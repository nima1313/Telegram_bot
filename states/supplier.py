from aiogram.fsm.state import State, StatesGroup

class SupplierRegistration(StatesGroup):
    # اطلاعات پایه
    full_name = State()
    gender = State()
    age = State()
    phone_number = State()
    instagram_id = State()
    portfolio_photos = State()
    
    # مشخصات ظاهری
    height = State()
    weight = State()
    hair_color = State()
    eye_color = State()
    skin_color = State()
    top_size = State()
    bottom_size = State()
    special_features = State()
    
    # اطلاعات همکاری
    price_range = State()
    city = State()
    area = State()
    cooperation_types = State()
    work_styles = State()
    
    # سابقه و توضیحات
    brand_experience = State()
    additional_notes = State()
    
    # تأیید نهایی
    confirm = State()
    
    # States for editing during registration
    editing_field = State()
    entering_new_value = State()
    managing_photos = State()
    adding_photos = State()
    removing_photos = State()

class SupplierRegistrationEdit(StatesGroup):
    choosing_field = State()
    entering_value = State()

class SupplierMenu(StatesGroup):
    main_menu = State()
    
class SupplierEditProfile(StatesGroup):
    choosing_field = State()
    entering_value = State()

class SupplierSettings(StatesGroup):
    menu = State()

class PhotoEditState(StatesGroup):
    choosing_action = State()
    adding_photos = State()
    removing_photos = State()


