from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Tweet, Media
from config.logging_config import logger
from typing import Sequence

app_logger = logger.bind(name="app")


async def get_media_by_ids(db: AsyncSession, ids: list[int]) -> Sequence[Tweet]:
    result = await db.execute(
        select(Media)
        .where(Media.id.in_(ids))
        .where(Media.tweet_id.is_(None))
    )
    return result.scalars().all()


async def get_media_by_user_id_tweet_id(db: AsyncSession, user_id, tweet_id: int) -> Sequence[Media]:
    medias_result = await db.execute(
        select(Media)
        .join(Tweet)
        .where(Media.tweet_id == tweet_id)
        .where(Tweet.user_id == user_id)
    )
    return medias_result.scalars().all()
