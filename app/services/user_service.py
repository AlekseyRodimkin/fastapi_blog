from typing import Sequence

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models import User
from config.config import get_db
from config.logging_config import logger

app_logger = logger.bind(name="app")


async def user_by_api_key(
    api_key: str, db: AsyncSession = Depends(get_db), _with=None
) -> User | None:
    """Get user by api_key and update last seen timestamp."""
    if _with == "followers":
        user_result = await db.execute(
            select(User).where(User.api_key == api_key).options(selectinload(User.followers))
        )
    elif _with == "following":
        user_result = await db.execute(
            select(User).where(User.api_key == api_key).options(selectinload(User.following))
        )
    elif _with == "all":
        user_result = await db.execute(
            select(User)
            .where(User.api_key == api_key)
            .options(selectinload(User.following), selectinload(User.followers))
        )
    else:
        user_result = await db.execute(select(User).where(User.api_key == api_key))
    current_user = user_result.scalars().first()
    if current_user:
        await current_user.update_last_seen()
        await db.flush()
        await db.commit()
        await db.refresh(current_user)
        app_logger.info(f"User authenticated: id={current_user.id}")
    else:
        app_logger.error("Invalid API key")
        raise HTTPException(
            status_code=403,
            detail={
                "result": False,
                "error_type": 403,
                "error_message": "Invalid API Key",
            },
        )
    return current_user


async def user_by_id(user_id: int, db: AsyncSession = Depends(get_db), _with=None) -> User | None:
    if _with == "followers":
        user_result = await db.execute(
            select(User).where(User.id == user_id).options(selectinload(User.followers))
        )
    elif _with == "following":
        user_result = await db.execute(
            select(User).where(User.id == user_id).options(selectinload(User.following))
        )
    elif _with == "all":
        user_result = await db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.following), selectinload(User.followers))
        )
    else:
        user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalars().first()
    if not user:
        app_logger.error(f"User id={user_id} not found")
        raise HTTPException(
            status_code=404,
            detail={
                "result": False,
                "error_type": 404,
                "error_message": f"User id={user_id} not found",
            },
        )
    return user


async def check_unique_user(
    db: AsyncSession, username: str, email: str, api_key: str
) -> bool | None:
    """Ensure username, email, and API key are unique."""
    app_logger.debug("check_unique_user()")
    result = await db.execute(
        select(User).where(
            (User.username == username) | (User.email == email) | (User.api_key == api_key)
        )
    )
    existing_user = result.scalars().first()
    if existing_user:
        return
    return True


async def get_users(db: AsyncSession, limit: int, offset: int) -> Sequence[User]:
    users_result = await db.execute(
        select(User).order_by(User.id.desc()).offset(offset).limit(limit)
    )
    return users_result.scalars().all()
