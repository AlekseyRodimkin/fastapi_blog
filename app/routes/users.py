from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app import models
from app.schemas import user_schema
from config.config import get_db

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.post("/", response_model=user_schema.UserOut)
async def create_new_user(user: user_schema.UserIn, db: AsyncSession = Depends(get_db)) -> models.User:
    """Create new user func"""
    new_user = models.User(**user.model_dump())

    async with db.begin():
        db.add(new_user)

    await db.refresh(new_user)
    return new_user


@router.get("/", response_model=List[user_schema.UserOut])
async def get_user_by_id(db: AsyncSession = Depends(get_db)) -> List[models.User]:
    """Get user by id func"""
    async with db.begin():
        result = await db.execute(select(models.User))
        users = result.scalars().all()
    return users



@router.get("/{user_id}", response_model=user_schema.UserOut)
async def get_user_by_id(user_id: int, db: AsyncSession = Depends(get_db)) -> models.User:
    """Get user by id func"""
    async with db.begin():
        result = await db.execute(
            select(models.User).where(models.User.id == user_id)
        )
        user = result.scalars().first()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

    return user

# @router.get("/me", response_model=schemas.UserOut)
# async def get_authorized_user(db: AsyncSession = Depends(get_db)) -> models.User:
#     """Get authorized user func"""
#     async with db.begin():
#         result = await db.execute(select(User).where(  # todo)
#             user=result.scalars().first()
#
#         if user is None:
#             raise HTTPException(status_code=404, detail="The user was not found")
#
#         return user


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
