import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, User as TelegramUser

from handlers.start import cmd_start, select_supplier_role
from handlers.demander import _parse_notes_for_search, _validate_notes_input
from states.supplier import SupplierRegistration

@pytest.mark.asyncio
async def test_cmd_start_new_user():
    """تست دستور start برای کاربر جدید"""
    # Mock objects
    message = AsyncMock(spec=Message)
    message.from_user = MagicMock(spec=TelegramUser)
    message.from_user.id = 123456789
    message.from_user.full_name = "Test User"
    
    state = AsyncMock(spec=FSMContext)
    session = AsyncMock()
    
    # Mock database query
    session.execute.return_value.scalar_one_or_none.return_value = None
    
    # Call handler
    await cmd_start(message, state, session)
    
    # Assertions
    state.clear.assert_called_once()
    message.answer.assert_called_once()
    assert "خوش آمدید" in message.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_select_supplier_role_new():
    """تست انتخاب نقش تأمین‌کننده برای کاربر جدید"""
    # Mock objects
    message = AsyncMock(spec=Message)
    message.from_user = MagicMock(spec=TelegramUser)
    message.from_user.id = 123456789
    message.text = "🎭 تأمین‌کننده"
    
    state = AsyncMock(spec=FSMContext)
    session = AsyncMock()
    
    # Mock database query
    session.execute.return_value.scalar_one_or_none.return_value = None
    
    # Call handler
    await select_supplier_role(message, state, session)
    
    # Assertions
    message.answer.assert_called_once()
    assert "نام و نام خانوادگی" in message.answer.call_args[0][0]
    state.set_state.assert_called_with(SupplierRegistration.full_name)


def test_parse_notes_for_search():
    """تست تابع پارس کردن یادداشت‌ها برای جست‌جو"""
    
    # Test normal case with multiple terms
    result = _parse_notes_for_search("بلند - موی بور - خوشگل")
    assert result == ["بلند", "موی بور", "خوشگل"]
    
    # Test single term
    result = _parse_notes_for_search("بلند")
    assert result == ["بلند"]
    
    # Test with extra spaces
    result = _parse_notes_for_search("  بلند  -  موی بور  -  خوشگل  ")
    assert result == ["بلند", "موی بور", "خوشگل"]
    
    # Test empty string
    result = _parse_notes_for_search("")
    assert result == []
    
    # Test None
    result = _parse_notes_for_search(None)
    assert result == []
    
    # Test only spaces and dashes
    result = _parse_notes_for_search("  -  -  ")
    assert result == []
    
    # Test with empty terms between dashes
    result = _parse_notes_for_search("بلند - - موی بور")
    assert result == ["بلند", "موی بور"]


def test_validate_notes_input():
    """تست تابع اعتبارسنجی ورودی یادداشت‌ها"""
    
    # Test valid inputs
    is_valid, msg = _validate_notes_input("بلند - موی بور - خوشگل")
    assert is_valid is True
    assert msg == ""
    
    # Test empty input (should be valid)
    is_valid, msg = _validate_notes_input("")
    assert is_valid is True
    assert msg == ""
    
    # Test None input (should be valid)
    is_valid, msg = _validate_notes_input(None)
    assert is_valid is True
    assert msg == ""
    
    # Test single term
    is_valid, msg = _validate_notes_input("بلند")
    assert is_valid is True
    assert msg == ""
    
    # Test too long input
    long_text = "a" * 501
    is_valid, msg = _validate_notes_input(long_text)
    assert is_valid is False
    assert "طولانی" in msg
    
    # Test too many terms
    many_terms = " - ".join(["term"] * 11)
    is_valid, msg = _validate_notes_input(many_terms)
    assert is_valid is False
    assert "تعداد عبارات" in msg
    
    # Test term too long
    is_valid, msg = _validate_notes_input("a" * 51)
    assert is_valid is False
    assert "طولانی" in msg
    
    # Test term too short
    is_valid, msg = _validate_notes_input("a")
    assert is_valid is False
    assert "کوتاه" in msg
    
    # Test mixed valid and invalid terms
    is_valid, msg = _validate_notes_input("بلند - a")
    assert is_valid is False
    assert "کوتاه" in msg
