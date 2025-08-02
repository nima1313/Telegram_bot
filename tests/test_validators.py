import pytest
from utils.validators import (
    validate_phone_number,
    validate_age,
    validate_height_weight,
    validate_username,
    parse_age_range
)

class TestValidators:
    """تست‌های validators"""
    
    def test_validate_phone_number(self):
        """تست اعتبارسنجی شماره تلفن"""
        # شماره‌های معتبر
        assert validate_phone_number("09123456789") == "09123456789"
        assert validate_phone_number("989123456789") == "09123456789"
        assert validate_phone_number("+989123456789") == "09123456789"
        assert validate_phone_number("0912 345 6789") == "09123456789"
        
        # شماره‌های نامعتبر
        assert validate_phone_number("123456789") is None
        assert validate_phone_number("091234567") is None
        assert validate_phone_number("09999999999") == "09999999999"
    
    def test_validate_age(self):
        """تست اعتبارسنجی سن"""
        assert validate_age("25") == 25
        assert validate_age("15") == 15
        assert validate_age("80") == 80
        
        assert validate_age("14") is None
        assert validate_age("81") is None
        assert validate_age("abc") is None
    
    def test_validate_height_weight(self):
        """تست اعتبارسنجی قد و وزن"""
        # قد
        assert validate_height_weight("170", is_height=True) == 170
        assert validate_height_weight("100", is_height=True) == 100
        assert validate_height_weight("250", is_height=True) == 250
        assert validate_height_weight("99", is_height=True) is None
        assert validate_height_weight("251", is_height=True) is None
        
        # وزن
        assert validate_height_weight("65", is_height=False) == 65
        assert validate_height_weight("30", is_height=False) == 30
        assert validate_height_weight("200", is_height=False) == 200
        assert validate_height_weight("29", is_height=False) is None
        assert validate_height_weight("201", is_height=False) is None
    
    def test_validate_username(self):
        """تست اعتبارسنجی یوزرنیم"""
        assert validate_username("john_doe") == True
        assert validate_username("user.name") == True
        assert validate_username("user123") == True
        
        assert validate_username("user name") == False
        assert validate_username("user@name") == False
        assert validate_username("") == False
        assert validate_username("a" * 31) == False
    
    def test_parse_age_range(self):
        """تست پارس محدوده سنی"""
        assert parse_age_range("18-30") == (18, 30)
        assert parse_age_range("25 - 35") == (25, 35)
        assert parse_age_range("20-40") == (20, 40)
        
        assert parse_age_range("30-18") is None
        assert parse_age_range("18") is None
        assert parse_age_range("abc-def") is None
