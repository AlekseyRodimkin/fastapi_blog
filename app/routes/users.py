from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Any, Dict
from app import models
from app.schemas import user_schema
from app.routes.utils import get_current_user_or_none
from config.config import get_db
from config.logging_config import logger
from .utils import check_unique_user

users_router = APIRouter(prefix="/api/users", tags=["Users"])
app_logger = logger.bind(name="app")


@users_router.post("/", status_code=201, response_model=user_schema.UserOut)
async def create_user(
        user_data: user_schema.UserIn,
        db: AsyncSession = Depends(get_db),
        api_key: str = Header(..., convert_underscores=False)) -> user_schema.UserOut:
    """Function of the registration of a new user"""
    app_logger.info(f"POST/api/users (api_key={api_key})")

    try:
        if not await check_unique_user(db, user_data.username, user_data.email, api_key):
            raise HTTPException(status_code=400, detail={"result": False,
                                                         "error_type": 400,
                                                         "error_message": f"Name/email/api_key already registered"})
        new_user = models.User(**user_data.model_dump())
        await new_user.set_api_key(api_key=api_key)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

    except HTTPException as http_ex:
        app_logger.error(f"Error HTTP: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        app_logger.error(f"Database error: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail={"result": False,
                                                     "error_type": 500,
                                                     "error_message": "Failed to create user"})

    app_logger.info(f"User created successfully (user_id={new_user.id})")
    return new_user


@users_router.get("/me", status_code=200, response_model=dict)
async def get_authorized_user(db: AsyncSession = Depends(get_db),
                              api_key: str = Header(..., convert_underscores=False)) -> Dict[str, str | Dict[str, Any]]:
    """The function of obtaining an authorized user"""
    app_logger.info(f"GET/api/users/me (api_key={api_key})")

    try:
        result = await db.execute(
            select(models.User)
            .where(models.User.api_key == api_key)
            .options(selectinload(models.User.followers), selectinload(models.User.following))
        )
        user = result.scalars().first()

        if not user:
            app_logger.error(f"403(Invalid API Key)")
            raise HTTPException(status_code=403, detail={"result": False,
                                                         "error_type": 403,
                                                         "error_message": "Invalid API Key"})

        return {
            "result": "true",
            "user": user_schema.UserWithRelations.model_validate(user).model_dump()
        }

    except HTTPException as http_ex:
        app_logger.error(f"Error HTTP: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        app_logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail={"result": False,
                                                     "error_type": 500,
                                                     "error_message": "Failed to get current user"})


@users_router.get("/{user_id}", status_code=200, response_model=dict)
async def get_user_by_id(user_id: int, db: AsyncSession = Depends(get_db)) -> Dict[str, str | Dict[str, Any]]:
    """The function of obtaining a user by ID"""
    app_logger.info(f"GET/api/users/{user_id}")

    try:
        result = await db.execute(
            select(models.User)
            .where(models.User.id == user_id)
            .options(selectinload(models.User.followers), selectinload(models.User.following))
        )
        user = result.scalars().first()

        if user is None:
            raise HTTPException(status_code=404, detail={"result": False,
                                                         "error_type": 404,
                                                         "error_message": "User not found"})

        return {
            "result": "true",
            "user": user_schema.UserWithRelations.model_validate(user).model_dump()
        }

    except HTTPException as http_ex:
        app_logger.error(f"Error HTTP: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        app_logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail={"result": False,
                                                     "error_type": 500,
                                                     "error_message": "Failed to get user"})


@users_router.get("/", status_code=200, response_model=List[user_schema.UserOut])
async def get_all_users(
        db: AsyncSession = Depends(get_db),
        api_key: str = Header(..., convert_underscores=False)
) -> List[models.User]:
    """The function of obtaining all users"""
    app_logger.info(f"GET/api/users (api_key={api_key})")

    try:
        await get_current_user_or_none(api_key, db)
        result = await db.execute(select(models.User))
        return result.scalars().all()

    except HTTPException as http_ex:
        app_logger.error(f"Error HTTP: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        app_logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail={"result": False,
                                                     "error_type": 500,
                                                     "error_message": "Failed to get all users"})


@users_router.post("/{user_id}/follow", status_code=201)
async def follow(
        user_id: int,
        db: AsyncSession = Depends(get_db),
        api_key: str = Header(..., convert_underscores=False)) -> Dict[str, bool]:
    """Follow func"""
    app_logger.info(f"POST/api/users/{user_id}/follow (api_key={api_key})")

    try:
        existing_user = await get_current_user_or_none(api_key, db)

        if existing_user.id == user_id:
            raise HTTPException(status_code=400, detail={"result": False,
                                                         "error_type": 400,
                                                         "error_message": "Invalid user_id"})
        result = await db.execute(
            select(models.User).where(models.User.id == user_id)
        )
        user = result.scalars().first()

        if user is None:
            raise HTTPException(status_code=404, detail={"result": False,
                                                         "error_type": 404,
                                                         "error_message": "User not found"})

        await existing_user.follow(db, user)

    except HTTPException as http_ex:
        app_logger.error(f"Error HTTP: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        app_logger.error(f"Database error: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail={"result": False,
                                                     "error_type": 500,
                                                     "error_message": "Failed to create follow"})

    app_logger.info(f"User follow successfully")
    return {"result": True}


@users_router.delete("/{user_id}/unfollow", status_code=200)
async def unfollow(
        user_id: int,
        db: AsyncSession = Depends(get_db),
        api_key: str = Header(..., convert_underscores=False)) -> Dict[str, bool]:
    """Unfollow func"""
    app_logger.info(f"DELETE/api/users/{user_id}/unfollow (api_key={api_key})")

    try:
        existing_user = await get_current_user_or_none(api_key, db)

        if existing_user.id == user_id:
            raise HTTPException(status_code=400, detail={"result": False,
                                                         "error_type": 400,
                                                         "error_message": "Invalid user_id"})
        result = await db.execute(
            select(models.User).where(models.User.id == user_id)
        )
        user = result.scalars().first()

        if user is None:
            raise HTTPException(status_code=404, detail={"result": False,
                                                         "error_type": 404,
                                                         "error_message": "User not found"})
        await existing_user.unfollow(db, user)

    except HTTPException as http_ex:
        app_logger.error(f"Error HTTP: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        app_logger.error(f"Database error: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail={"result": False,
                                                     "error_type": 500,
                                                     "error_message": "Failed to create unfollow"})
    app_logger.info(f"User unfollow successfully")
    return {"result": True}
