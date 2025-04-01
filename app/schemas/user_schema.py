from pydantic import BaseModel, ConfigDict, field_serializer, field_validator
from typing import Optional
from datetime import datetime, timezone


class BaseUser(BaseModel):
    username: str
    email: str
    about_me: Optional[str] = None


class UserIn(BaseUser):
    ...


class UserOut(BaseUser):
    id: int
    last_seen: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('last_seen')
    def serialize_last_seen(self, last_seen: datetime, _info):
        return last_seen.astimezone(timezone.utc).isoformat()


class FollowerOut(BaseModel):
    id: int
    username: str


class UserWithRelations(UserOut):
    followers: list[FollowerOut] = []
    following: list[FollowerOut] = []

    @field_validator('followers', 'following', mode='before')
    def convert_user_objects(cls, v):
        return [
            {"id": user.id, "username": user.username}
            for user in v
        ]

    model_config = ConfigDict(from_attributes=True)
