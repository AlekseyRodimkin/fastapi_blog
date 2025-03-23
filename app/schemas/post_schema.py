from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class BasePost(BaseModel):
    body: Optional[str] = None


class PostIn(BasePost):
    ...


class PostOut(BasePost):
    id: int
    timestamp: datetime


class PostCreatedOut(BaseModel):
    id: int
