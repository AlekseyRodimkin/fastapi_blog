from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.future import select
from app import models
from app.schemas import user_schema
from config.config import get_db
from config.logging_config import logger
from app.routes.utils import get_current_user
from .utils import check_unique_user

router = APIRouter(prefix="/api/users", tags=["Users"])
app_logger = logger.bind(name="app")


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=user_schema.UserOut)
async def create_user(
        user_data: user_schema.UserIn,
        db: AsyncSession = Depends(get_db),
        api_key: str = Header(..., convert_underscores=False)) -> user_schema.UserOut:
    """Function of the registration of a new user"""
    app_logger.info(f"POST/api/users (api_key={api_key})")

    await check_unique_user(db, user_data.username, user_data.email, api_key)

    new_user = models.User(**user_data.model_dump())
    new_user.set_api_key(api_key=api_key)

    try:
        new_user = models.User(**user_data.model_dump())
        new_user.set_api_key(api_key=api_key)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
    except Exception as e:
        app_logger.error(f"Database error: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user")

    app_logger.info(f"User created successfully (user_id={new_user.id})")
    return new_user


@router.get("/me", status_code=status.HTTP_200_OK, response_model=user_schema.UserOut)
async def get_authorized_user(db: AsyncSession = Depends(get_db),
                              api_key: str = Header(..., convert_underscores=False)) -> models.User:
    """The function of obtaining an authorized user"""
    app_logger.info(f"GET/api/users/me (api_key={api_key})")

    existing_user = await get_current_user(api_key, db)
    if not existing_user:
        app_logger.error(f"403(Invalid API Key)")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API Key")

    try:
        user = await get_current_user(api_key, db)

        if user is None:
            app_logger.error(f"403(The user was not found. Invalid API Key)")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The user was not found. Invalid API Key")

        return user

    except Exception as e:
        app_logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get current user")


@router.get("/{user_id}", status_code=status.HTTP_200_OK, response_model=user_schema.UserOut)
async def get_user_by_id(user_id: int, db: AsyncSession = Depends(get_db)) -> models.User:
    """The function of obtaining a user by ID"""
    app_logger.info(f"GET/api/users/{user_id}")

    try:
        result = await db.execute(
            select(models.User).where(models.User.id == user_id)
        )
        user = result.scalars().first()

        if user is None:
            app_logger.error(f"404(User not found)")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        return user

    except Exception as e:
        app_logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get user")


@router.get("/", status_code=status.HTTP_200_OK, response_model=List[user_schema.UserOut])
async def get_all_users(
        db: AsyncSession = Depends(get_db),
        api_key: str = Header(..., convert_underscores=False)
) -> List[models.User]:
    """The function of obtaining all users"""
    app_logger.info(f"GET/api/users (api_key={api_key})")

    existing_user = await get_current_user(api_key, db)
    if not existing_user:
        app_logger.error(f"403(Invalid API Key)")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API Key")

    try:
        result = await db.execute(select(models.User))
        return result.scalars().all()

    except Exception as e:
        app_logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get all users")

# @router.post("/{user_id}/follow", response_model=...)
# async def follow(db: AsyncSession = Depends(get_db)):
#     """Follow func"""
#     async with db.begin():
#         pass  # todo
#
#
# @router.delete("/{user_id}/follow", response_model=...)
# async def unfollow(db: AsyncSession = Depends(get_db)):
#     """Unfollow func"""
#     async with db.begin():
#         pass  # todo
