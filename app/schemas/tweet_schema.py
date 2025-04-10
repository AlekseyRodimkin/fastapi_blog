from typing import List, Optional

from pydantic import BaseModel


class TweetCreate(BaseModel):
    tweet_data: Optional[str]
    media_ids: Optional[list[int]]


class TweetCreateResponse(BaseModel):
    result: bool
    tweet_id: int


class Like(BaseModel):
    user_id: int
    name: str


class Author(BaseModel):
    id: int
    name: str


class TweetResponse(BaseModel):
    id: int
    content: str
    attachments: List[str]
    author: Author
    likes: List[Like]


class TweetListResponse(BaseModel):
    result: bool
    tweets: List[TweetResponse]
