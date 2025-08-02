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
    full_name = State()
    company_name = State()
    phone_number = State()
