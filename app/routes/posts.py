from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from config.logging_config import logger
from app import models
from app.schemas import post_schema
from config.config import get_db
from .utils import get_current_user
from typing import List

router = APIRouter(prefix="/api/tweets", tags=["Tweets"])
app_logger = logger.bind(name="app")


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=post_schema.PostCreatedOut)
async def create_new_post(
        post_data: post_schema.PostIn,
        db: AsyncSession = Depends(get_db),
        api_key: str = Header(..., convert_underscores=False)) -> post_schema.PostCreatedOut:
    """Create new post func"""
    app_logger.info(f"POST/api/tweets (api_key={api_key})")

    existing_user = await get_current_user(api_key, db)
    if not existing_user:
        app_logger.error(f"403(Invalid API Key)")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API Key")
    try:
        new_post = models.Post(
            **post_data.model_dump(),
            user_id=existing_user.id,
        )
        db.add(new_post)
        await db.commit()
        await db.refresh(new_post)

    except Exception as e:
        app_logger.error(f"Database error: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create post")

    app_logger.info(f"Post created successfully (post_id={new_post.id})")
    return new_post


@router.get("/{post_id}", status_code=status.HTTP_200_OK, response_model=post_schema.PostOut)
async def get_post_by_id(post_id: int,
                         db: AsyncSession = Depends(get_db),
                         api_key: str = Header(..., convert_underscores=False)) -> models.Post:
    """Get post by id func"""
    app_logger.info(f"GET/api/tweets/{post_id}")

    existing_user = await get_current_user(api_key, db)
    if not existing_user:
        app_logger.error(f"403(Invalid API Key)")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API Key")

    try:
        result = await db.execute(select(models.Post).where(models.Post.id == post_id))
        post = result.scalars().first()

        if post is None:
            app_logger.error(f"404(Post not found)")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

        return post

    except Exception as e:
        app_logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get post")


@router.get("/", status_code=status.HTTP_200_OK, response_model=List[post_schema.PostOut])
async def get_all_posts(
        db: AsyncSession = Depends(get_db),
        api_key: str = Header(..., convert_underscores=False)
) -> List[models.User]:
    """The function of obtaining all posts"""
    app_logger.info(f"GET/api/tweets (api_key={api_key})")

    existing_user = await get_current_user(api_key, db)
    if not existing_user:
        app_logger.error(f"403(Invalid API Key)")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API Key")
    try:
        result = await db.execute(select(models.Post))
        return result.scalars().all()

    except Exception as e:
        app_logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to all posts")

#
#
# @router.delete()"/{post_id}", response_model=..)
# async def delete_post(db: AsyncSession = Depends(get_db)):
#     """Delete post func"""
#     async with db.begin():
#         pass  # todo
#
#
# @router.post()"/{post_id}/likes", response_model=...)
# async def ...(db: AsyncSession = Depends(get_db)):
#     """""
#     async with db.begin():
#         pass  # todo
#
#
# @router.delete()"/{post_id}/likes", response_model=...)
# async def ...(db: AsyncSession = Depends(get_db)):
#     """"""
#     async with db.begin():
#         pass  # todo
