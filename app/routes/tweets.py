from celery import group
from fastapi import APIRouter, Depends, HTTPException, Header, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app import logger, get_db, YANDEX_DISK_APP_FOLDER_PATH, Tweet, TweetCreate, TweetCreateResponse, TweetListResponse, \
    Like, TweetResponse, Author, celery_task_delete_media, tweet_by_id, tweets_by_user_ids, tweet_by_id_with_details, \
    exception_handler, user_by_api_key, get_media_by_ids, get_media_by_user_id_tweet_id

tweets_router = APIRouter(prefix="/api/tweets", tags=["Tweets"])
app_logger = logger.bind(name="app")


@tweets_router.post("/", status_code=201, response_model=TweetCreateResponse)
@exception_handler()
async def create_new_tweet(
        tweet_in: TweetCreate = Body(...),
        db: AsyncSession = Depends(get_db),
        api_key: str = Header(..., convert_underscores=False)):
    """Create new tweet func"""
    app_logger.info(f"POST/api/tweets")

    current_user = await user_by_api_key(api_key=api_key, db=db)
    if not tweet_in.tweet_data and not tweet_in.media_ids:
        raise HTTPException(
            status_code=400,
            detail={"result": False,
                    "error_type": 400,
                    "error_message": "Tweet text or media required"}
        )
    new_tweet = Tweet(tweet_data=tweet_in.tweet_data, user_id=current_user.id)
    db.add(new_tweet)
    await db.flush()

    if tweet_in.media_ids:
        media_list = await get_media_by_ids(db=db, ids=tweet_in.media_ids)
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


@tweets_router.get("/", status_code=200, response_model=TweetListResponse)
@exception_handler()
async def get_tweets(
        db: AsyncSession = Depends(get_db),
        api_key: str = Header(..., convert_underscores=False),
        limit: int = Query(10, ge=1, le=30),
        offset: int = Query(0, ge=0)):
    """Get tweets func"""
    app_logger.info(f"GET/api/tweets")

    current_user = await user_by_api_key(api_key=api_key, db=db, _with="following")
    followed_ids = [u.id for u in current_user.following]
    if not followed_ids:
        return TweetListResponse(result=True, tweets=[])

    tweets = await tweets_by_user_ids(db, followed_ids, limit, offset)
    tweets_data = []
    for tweet in tweets:
        attachments = [media.image_link for media in tweet.tweet_media]
        likes_data = [
            Like(user_id=user.id, name=user.username)
            for user in tweet.liked_by
        ]
        tweets_data.append(
            TweetResponse(
                id=tweet.id,
                content=tweet.tweet_data or "",
                attachments=attachments,
                author=Author(id=tweet.author.id, name=tweet.author.username),
                likes=likes_data
            )
        )
    return TweetListResponse(result=True, tweets=tweets_data)


@tweets_router.get("/{tweet_id}", status_code=200, response_model=TweetResponse)
@exception_handler()
async def get_tweet_by_id(
        tweet_id: int,
        db: AsyncSession = Depends(get_db),
        api_key: str = Header(..., convert_underscores=False)):
    """Get tweet by id func"""
    app_logger.info(f"GET/api/tweets")

    await user_by_api_key(api_key=api_key, db=db)
    tweet = await tweet_by_id_with_details(db=db, tweet_id=tweet_id)
    attachments = [media.image_link for media in tweet.tweet_media]
    likes_data = [
        Like(user_id=user.id, name=user.username)
        for user in tweet.liked_by
    ]
    return TweetResponse(
        id=tweet.id,
        content=tweet.tweet_data or "",
        attachments=attachments,
        author=Author(id=tweet.author.id, name=tweet.author.username),
        likes=likes_data
    )


@tweets_router.delete("/{tweet_id}", status_code=200)
@exception_handler()
async def delete_tweet_by_id(
        tweet_id: int,
        db: AsyncSession = Depends(get_db),
        api_key: str = Header(..., convert_underscores=False)):
    """Delete tweet by id func"""
    app_logger.info(f"DELETE/api/tweets/{tweet_id}")

    current_user = await user_by_api_key(api_key, db)
    # File deletion
    media_files = await get_media_by_user_id_tweet_id(db=db, user_id=current_user.id, tweet_id=tweet_id)
    file_paths = [f"{YANDEX_DISK_APP_FOLDER_PATH[5:]}/{media.file_name}" for media in media_files]

    if file_paths:
        app_logger.debug(f"Triggering Celery tasks for files deletion: {file_paths}")
        task_group = group(celery_task_delete_media.s(file_path) for file_path in file_paths)
        task_group.apply_async()

    # Tweet deletion
    tweet = await tweet_by_id(tweet_id=tweet_id, db=db, user_id=current_user.id)
    await db.delete(tweet)
    await db.commit()

    app_logger.info(f"Tweet {tweet_id} deleted successfully by user {current_user.id}")
    return {"result": True}


@tweets_router.post("/{tweet_id}/likes", status_code=201, response_model=dict)
@exception_handler()
async def like_tweet_by_id(
        tweet_id: int,
        db: AsyncSession = Depends(get_db),
        api_key: str = Header(..., convert_underscores=False)):
    """Like tweet by id func"""
    app_logger.info(f"POST/api/tweets/{tweet_id}/like")

    current_user = await user_by_api_key(api_key, db)
    tweet = await tweet_by_id(tweet_id=tweet_id, db=db)
    await current_user.like_tweet(session=db, tweet=tweet)
    app_logger.info(f"Tweet {tweet.id} liked successfully by user {current_user.id}")
    return {"result": True}


@tweets_router.delete("/{tweet_id}/likes", status_code=200, response_model=dict)
@exception_handler()
async def delete_like_tweet_by_id(
        tweet_id: int,
        db: AsyncSession = Depends(get_db),
        api_key: str = Header(..., convert_underscores=False)):
    """Delete like tweet by id func"""
    app_logger.info(f"DELETE/api/tweets/{tweet_id}/like")

    current_user = await user_by_api_key(api_key, db)
    tweet = await tweet_by_id(tweet_id=tweet_id, db=db)
    await current_user.unlike_tweet(session=db, tweet=tweet)
    app_logger.info(f"Tweet {tweet.id} like delete successfully by user {current_user.id}")
    return {"result": True}
