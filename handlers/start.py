from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.models import User, UserRole
from keyboards.reply import get_main_menu, get_back_keyboard
from states.supplier import SupplierRegistration
from states.demander import DemanderRegistration

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession):
    """هندلر دستور /start"""
    await state.clear()
    
    # بررسی کاربر در دیتابیس
    stmt = select(User).where(User.telegram_id == str(message.from_user.id))
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user:
        # کاربر قبلاً ثبت‌نام کرده
        if user.role == UserRole.SUPPLIER:
            await message.answer(
                f"سلام {message.from_user.full_name} عزیز! 👋\n"
                "شما قبلاً به عنوان تأمین‌کننده ثبت‌نام کرده‌اید.\n"
                "از منوی زیر گزینه مورد نظر را انتخاب کنید:",
                reply_markup=get_main_menu()
            )
        else:
            await message.answer(
                f"سلام {message.from_user.full_name} عزیز! 👋\n"
                "شما قبلاً به عنوان درخواست‌کننده ثبت‌نام کرده‌اید.\n"
                "از منوی زیر گزینه مورد نظر را انتخاب کنید:",
                reply_markup=get_main_menu()
            )
    else:
        # کاربر جدید
        await message.answer(
            f"سلام {message.from_user.full_name} عزیز! 👋\n\n"
            "به ربات مدیریت مدل‌ها و عکاسان خوش آمدید.\n\n"
            "لطفاً نقش خود را انتخاب کنید:\n"
            "🎭 تأمین‌کننده: اگر مدل یا عکاس هستید\n"
            "🔍 درخواست‌کننده: اگر به دنبال مدل یا عکاس هستید",
            reply_markup=get_main_menu()
        )

@router.message(F.text == "🎭 تأمین‌کننده")
async def select_supplier_role(message: Message, state: FSMContext, session: AsyncSession):
    """انتخاب نقش تأمین‌کننده"""
    # بررسی وجود کاربر
    stmt = select(User).options(selectinload(User.supplier_profile)).where(User.telegram_id == str(message.from_user.id))
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user and user.supplier_profile:
        # کاربر قبلاً پروفایل تأمین‌کننده دارد
        from handlers.supplier import show_supplier_menu
        await show_supplier_menu(message, state, session)
    else:
        # شروع فرآیند ثبت‌نام
        await message.answer(
            "عالی! برای ثبت‌نام به عنوان تأمین‌کننده، لطفاً اطلاعات خود را وارد کنید.\n\n"
            "🔸 نام و نام خانوادگی خود را وارد کنید:",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(SupplierRegistration.full_name)

@router.message(F.text == "🔍 درخواست‌کننده")
async def select_demander_role(message: Message, state: FSMContext, session: AsyncSession):
    """انتخاب نقش درخواست‌کننده"""
    # بررسی وجود کاربر
    stmt = select(User).options(selectinload(User.demander_profile)).where(User.telegram_id == str(message.from_user.id))
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user and user.demander_profile:
        # کاربر قبلاً پروفایل درخواست‌کننده دارد - به منوی درخواست‌کننده هدایت کنیم
        from keyboards.demander import get_demander_menu_keyboard
        from states.demander import DemanderMenu
        await message.answer(
            "سلام! به ربات خوش آمدید.\n"
            "شما قبلاً به عنوان درخواست‌کننده ثبت‌نام کرده‌اید.",
            reply_markup=get_demander_menu_keyboard()
        )
        await state.set_state(DemanderMenu.main_menu)
    else:
        # شروع فرآیند ثبت‌نام
        await message.answer(
            "عالی! برای ثبت‌نام به عنوان درخواست‌کننده، لطفاً اطلاعات خود را وارد کنید.\n\n"
            "🔸 نام و نام خانوادگی خود را وارد کنید:",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(DemanderRegistration.full_name)
