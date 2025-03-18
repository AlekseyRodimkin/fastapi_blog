# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select
#
# from app import models, schemas
# from config.config import get_db
#
# router = APIRouter(prefix="/api/tweets", tags=["Tweets"])
#
#
# @router.get("/", response_model=schemas.PostOut)
# async def get_all_posts(db: AsyncSession = Depends(get_db)):
#     """Get all posts func"""
#     async with db.begin():
#         pass  # todo
#
#
# @router.post("/", response_model=PostOut)
# async def create_new_post(db: AsyncSession = Depends(get_db)):
#     """Create new post func"""
#     async with db.begin():
#         pass  # todo
#
#
# @router.get("/{post_id}", response_model=PostOut)
# async def get_post_by_id(post_id: int, db: AsyncSession = Depends(get_db)):
#     """Get post by id func"""
#     async with db.begin():
#         result = await db.execute(select(Post).where(Post.id == post_id))
#         post = result.scalars().first()
#
#         if post is None:
#             raise HTTPException(status_code=404, detail="The user was not found")
#
#         return post
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
