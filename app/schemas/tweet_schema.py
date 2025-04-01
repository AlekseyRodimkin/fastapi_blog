from pydantic import BaseModel, Field
from typing import Optional


class TweetCreate(BaseModel):
    tweet_data: Optional[str] = Field(None, max_length=1000, example="X is cool")
    media_ids: Optional[list[int]]


class TweetCreateResponse(BaseModel):
    result: bool
    tweet_id: int
