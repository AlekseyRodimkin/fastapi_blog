from typing import Sequence

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models import Tweet, User
from config.config import get_db
from config.logging_config import logger

app_logger = logger.bind(name="app")


async def tweet_by_id(
    tweet_id: int, db: AsyncSession = Depends(get_db), user_id=None
) -> User | None:
    if user_id:
        tweet_result = await db.execute(
            select(Tweet).where(Tweet.id == tweet_id).where(Tweet.user_id == user_id)
        )
    else:
        tweet_result = await db.execute(select(Tweet).where(Tweet.id == tweet_id))
    tweet = tweet_result.scalars().first()
    if not tweet:
        app_logger.error(f"Tweet id={tweet_id} not found")
        raise HTTPException(
            status_code=404,
            detail={
                "result": False,
                "error_type": 404,
                "error_message": f"Tweet id={tweet_id} not found",
            },
        )
    return tweet


async def tweet_by_id_with_details(db: AsyncSession, tweet_id: int) -> Tweet:
    tweet_result = await db.execute(
        select(Tweet)
        .where(Tweet.id == tweet_id)
        .options(
            selectinload(Tweet.tweet_media),
            selectinload(Tweet.liked_by),
            selectinload(Tweet.author),
        )
        .order_by(Tweet.timestamp.desc())
    )
    tweet = tweet_result.scalars().first()
    if not tweet:
        app_logger.error(f"Tweet id={tweet_id} not found")
        raise HTTPException(
            status_code=404,
            detail={
                "result": False,
                "error_type": 404,
                "error_message": f"Tweet id={tweet_id} not found",
            },
        )
    return tweet


async def tweets_by_user_ids(
    db: AsyncSession, user_ids: list[int], limit: int, offset: int
) -> Sequence[Tweet]:
    result = await db.execute(
        select(Tweet)
        .where(Tweet.user_id.in_(user_ids))
        .options(
            selectinload(Tweet.tweet_media),
            selectinload(Tweet.liked_by),
            selectinload(Tweet.author),
        )
        .order_by(Tweet.timestamp.desc())
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()
