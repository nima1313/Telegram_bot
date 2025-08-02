from aiogram.fsm.state import State, StatesGroup

class ProfileEdit(StatesGroup):
    """حالت‌های ویرایش پروفایل"""
    selecting_field = State()
    editing_name = State()
    editing_phone = State()
    editing_company = State()
    editing_city = State()
    editing_area = State()
    editing_instagram = State()
    editing_portfolio = State()
    editing_appearance = State()
    editing_price = State()
    editing_work_styles = State()
    editing_cooperation = State()
    editing_brand = State()
    editing_notes = State()
    confirming_changes = State()

class RequestManagement(StatesGroup):
    """حالت‌های مدیریت درخواست‌ها"""
    viewing_request = State()
    writing_response = State()
    confirming_action = State()

class AdminStates(StatesGroup):
    """حالت‌های پنل ادمین"""
    admin_menu = State()
    user_management = State()
    viewing_user = State()
    broadcast_message = State()
    statistics_view = State()

class SearchAnalytics(StatesGroup):
    """حالت‌های آنالیز جستجو"""
    viewing_history = State()
    exporting_data = State()
