from celery import group
from fastapi import APIRouter, Depends, HTTPException, Header, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from config.logging_config import logger
from config.config import get_db, YANDEX_DISK_APP_FOLDER_PATH
from app.models import Media, Tweet
from app.schemas import tweet_schema
from app.services.utils import get_current_user_or_none
from app.services.yandex import celery_task_delete_media
from typing import Dict

tweets_router = APIRouter(prefix="/api/tweets", tags=["Tweets"])
app_logger = logger.bind(name="app")


@tweets_router.post("/", status_code=201, response_model=tweet_schema.TweetCreateResponse)
async def create_new_tweet(
        tweet_in: tweet_schema.TweetCreate = Body(...),
        db: AsyncSession = Depends(get_db),
        api_key: str = Header(..., convert_underscores=False)) -> Dict[str, bool | int]:
    """Create new tweet func"""
    app_logger.info(f"POST/api/tweets")

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
                raise HTTPException(
                    status_code=400,
                    detail={"result": False,
                            "error_type": 400,
                            "error_message": f"Media not found: {missing}"}
                )

            await new_tweet.set_tweet_media(db=db, media=media_list)

        await db.commit()
        app_logger.info(f"Tweet {new_tweet.id} created successfully by user {current_user.id}")

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
    app_logger.info(f"DELETE/api/tweets/{tweet_id}")

    try:
        current_user = await get_current_user_or_none(api_key, db)

        # File deletion
        medias_result = await db.execute(
            select(Media)
            .join(Tweet)
            .where(Media.tweet_id == tweet_id)
            .where(Tweet.user_id == current_user.id)
        )
        media_files = medias_result.scalars().all()

        file_paths = [f"{YANDEX_DISK_APP_FOLDER_PATH[5:]}/{media.file_name}" for media in media_files]

        if file_paths:
            app_logger.debug(f"Triggering Celery tasks for files deletion: {file_paths}")
            task_group = group(celery_task_delete_media.s(file_path) for file_path in file_paths)
            task_group.apply_async()

        # Tweet deletion
        tweet_result = await db.execute(
            select(Tweet)
            .where(Tweet.id == tweet_id)
            .where(Tweet.user_id == current_user.id)
        )
        tweet = tweet_result.scalars().first()

        if not tweet:
            raise HTTPException(status_code=404, detail={"result": False,
                                                         "error_type": 404,
                                                         "error_message": f"Tweet not found: {tweet_id}"})

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


@tweets_router.post("/{tweet_id}/likes", status_code=201, response_model=dict)
async def like_tweet_by_id(
        tweet_id: int,
        db: AsyncSession = Depends(get_db),
        api_key: str = Header(..., convert_underscores=False)) -> Dict[str, bool | int]:
    """Like tweet by id func"""
    app_logger.info(f"POST/api/tweets/{tweet_id}/like")

    try:
        current_user = await get_current_user_or_none(api_key, db)

        tweet_result = await db.execute(
            select(Tweet)
            .where(Tweet.id == tweet_id)
            .where(Tweet.user_id == current_user.id)
        )
        tweet = tweet_result.scalars().first()
        if not tweet:
            raise HTTPException(status_code=404, detail={"result": False,
                                                         "error_type": 404,
                                                         "error_message": f"Tweet not found: {tweet_id}"})

        await current_user.like_tweet(session=db, tweet=tweet)
        app_logger.info(f"Tweet {tweet.id} liked successfully by user {current_user.id}")
        return {"result": True}

    except HTTPException as http_ex:
        app_logger.error(f"Error HTTP: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        app_logger.error(f"Database error: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail={"result": False,
                                                     "error_type": 500,
                                                     "error_message": "Failed to like tweet"})


@tweets_router.delete("/{tweet_id}/likes", status_code=200, response_model=dict)
async def delete_like_tweet_by_id(
        tweet_id: int,
        db: AsyncSession = Depends(get_db),
        api_key: str = Header(..., convert_underscores=False)) -> Dict[str, bool | int]:
    """Delete like tweet by id func"""
    app_logger.info(f"DELETE/api/tweets/{tweet_id}/like")

    try:
        current_user = await get_current_user_or_none(api_key, db)

        tweet_result = await db.execute(
            select(Tweet)
            .where(Tweet.id == tweet_id)
            .where(Tweet.user_id == current_user.id)
        )
        tweet = tweet_result.scalars().first()
        if not tweet:
            raise HTTPException(status_code=404, detail={"result": False,
                                                         "error_type": 404,
                                                         "error_message": f"Tweet not found: {tweet_id}"})

        await current_user.unlike_tweet(session=db, tweet=tweet)
        app_logger.info(f"Tweet {tweet.id} like delete successfully by user {current_user.id}")
        return {"result": True}

    except HTTPException as http_ex:
        app_logger.error(f"Error HTTP: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        app_logger.error(f"Database error: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail={"result": False,
                                                     "error_type": 500,
                                                     "error_message": "Failed to like tweet"})
