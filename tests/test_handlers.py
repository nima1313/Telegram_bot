import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, User as TelegramUser

from handlers.start import cmd_start, select_supplier_role
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
