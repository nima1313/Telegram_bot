import re
from typing import Optional

def validate_phone_number(phone: str) -> Optional[str]:
    """اعتبارسنجی شماره تلفن"""
    # حذف کاراکترهای اضافی
    phone = re.sub(r'\D', '', phone)
    
    # بررسی فرمت شماره ایران
    if re.match(r'^09\d{9}$', phone):
        return phone
    elif re.match(r'^989\d{9}$', phone):
        return '0' + phone[2:]
    elif re.match(r'^\+989\d{9}$', phone):
        return '0' + phone[3:]
    
    return None

def validate_age(age_str: str) -> Optional[int]:
    """اعتبارسنجی سن"""
    try:
        age = int(age_str)
        if 15 <= age <= 80:
            return age
    except ValueError:
        pass
    return None

def validate_height_weight(value_str: str, is_height: bool = True) -> Optional[int]:
    """اعتبارسنجی قد و وزن"""
    try:
        value = int(value_str)
        if is_height:
            if 100 <= value <= 250:
                return value
        else:
            if 30 <= value <= 200:
                return value
    except ValueError:
        pass
    return None

def validate_clothing_size(value_str: str) -> Optional[int]:
    """اعتبارسنجی سایز لباس به صورت عددی (مثلاً 34 تا 60)

    حروفی مانند S/M/L/XL پشتیبانی نمی‌شود زیرا نوع داده عددی شده است.
    """
    try:
        value = int(re.findall(r"\d+", value_str)[0]) if re.findall(r"\d+", value_str) else None
        if value is None:
            return None
        # معقول برای سایزهای عددی لباس (اروپایی/ایرانی)
        if 20 <= value <= 80:
            return value
    except Exception:
        pass
    return None

def validate_price(price_str: str) -> Optional[int]:
    """اعتبارسنجی قیمت تکی (به هزار تومان)

    ورودی می‌تواند شامل متن و عدد باشد. اولین عدد استخراج و بازگردانده می‌شود.
    مثال معتبر: "250" یا "250 هزار". مقدار باید > 0 باشد.
    """
    try:
        numbers = re.findall(r"\d+", price_str)
        if not numbers:
            return None
        price = int(numbers[0])
        if price <= 0:
            return None
        return price
    except Exception:
        return None

def validate_username(username: str) -> bool:
    """اعتبارسنجی یوزرنیم اینستاگرام"""
    # یوزرنیم معتبر: حروف، اعداد، نقطه و آندرلاین
    pattern = r'^[a-zA-Z0-9._]{1,30}$'
    return bool(re.match(pattern, username))

def parse_age_range(age_range_str: str) -> Optional[tuple]:
    """پارس کردن محدوده سنی"""
    try:
        # Extract first two numbers regardless of separator and normalize order
        nums = [int(x) for x in re.findall(r"\d+", age_range_str)]
        if len(nums) < 2:
            return None
        a, b = nums[0], nums[1]
        lo, hi = (a, b) if a <= b else (b, a)
        if 0 < lo <= hi <= 100:
            return (lo, hi)
    except Exception:
        pass
    return None

def extract_numbers(text: str) -> list:
    """استخراج اعداد از متن"""
    return [int(x) for x in re.findall(r'\d+', text)]

def format_phone_number(phone: str) -> str:
    """فرمت کردن شماره تلفن برای نمایش"""
    if len(phone) == 11 and phone.startswith('09'):
        return f"{phone[:4]} {phone[4:7]} {phone[7:]}"
    return phone
