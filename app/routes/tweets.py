from fastapi import APIRouter, Depends, HTTPException, Header, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from config.logging_config import logger
from config.config import get_db
from app.models import Media, User, Tweet
from app.schemas import tweet_schema
from .utils import get_current_user_or_none
from typing import Dict

tweets_router = APIRouter(prefix="/api/tweets", tags=["Tweets"])
app_logger = logger.bind(name="app")


@tweets_router.post("/", status_code=201, response_model=tweet_schema.TweetCreateResponse)
async def create_new_tweet(
        tweet_in: tweet_schema.TweetCreate = Body(...),
        db: AsyncSession = Depends(get_db),
        api_key: str = Header(..., convert_underscores=False)) -> Dict[str, bool | int]:
    """Create new tweet func"""
    app_logger.info(f"POST/api/tweets (api_key={api_key})")

    try:
        current_user = await get_current_user_or_none(api_key, db)

        if not tweet_in.tweet_data and not tweet_in.media_ids:
            raise HTTPException(
                status_code=400,
                detail={"result": False,
                        "error_type": 400,
                        "error_message": "Tweet text or media required"}
            )

        new_tweet = Tweet(
            tweet_data=tweet_in.tweet_data,
            user_id=current_user.id
        )
        db.add(new_tweet)
        await db.flush()

        if tweet_in.media_ids:
            result = await db.execute(
                select(Media)
                .where(Media.id.in_(tweet_in.media_ids))
                .where(Media.tweet_id.is_(None))
            )
            media_list = result.scalars().all()

            found_ids = {m.id for m in media_list}
            if len(found_ids) != len(tweet_in.media_ids):
                missing = set(tweet_in.media_ids) - found_ids
                await db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail={"result": False,
                            "error_type": 400,
                            "error_message": f"Media not found: {missing}"}
                )

            new_tweet.tweet_media = media_list

        await db.commit()
        app_logger.info(f"Tweet created successfully (tweet_id={new_tweet.id})")

        return {"result": True, "tweet_id": new_tweet.id}

    except HTTPException as http_ex:
        app_logger.error(f"Error HTTP: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        app_logger.error(f"Database error: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail={"result": False,
                                                     "error_type": 500,
                                                     "error_message": "Failed to create new tweet"})


@tweets_router.delete("/{tweet_id}", status_code=200)
async def delete_tweet_by_id(
        tweet_id: int,
        db: AsyncSession = Depends(get_db),
        api_key: str = Header(..., convert_underscores=False)) -> Dict[str, bool | int]:
    """Delete tweet by id func"""
    app_logger.info(f"DELETE/api/tweets/{tweet_id} (api_key={api_key})")

    try:
        current_user = await get_current_user_or_none(api_key, db)

        result = await db.execute(
            select(Tweet)
            .where(Tweet.id == tweet_id)
            .where(Tweet.user_id == current_user.id)
        )
        tweet = result.scalars().first()

        if not tweet:
            raise HTTPException(
                status_code=404,
                detail={"result": False,
                        "error_type": 404,
                        "error_message": "Tweet not found"}
            )

        await db.delete(tweet)
        await db.commit()

        app_logger.info(f"Tweet {tweet_id} deleted successfully by user {current_user.id}")
        return {"result": True}

    except HTTPException as http_ex:
        app_logger.error(f"Error HTTP: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        app_logger.error(f"Database error: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail={"result": False,
                                                     "error_type": 500,
                                                     "error_message": "Failed to create new tweet"})
