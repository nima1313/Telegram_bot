from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import User, UserRole

async def get_or_create_user(session: AsyncSession, telegram_user, role: UserRole) -> User:
    """دریافت یا ایجاد کاربر"""
    stmt = select(User).where(User.telegram_id == str(telegram_user.id))
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            telegram_id=str(telegram_user.id),
            username=telegram_user.username,
            role=role
        )
        session.add(user)
        await session.flush()
    
    return user
