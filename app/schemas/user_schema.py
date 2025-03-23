from pydantic import BaseModel, ConfigDict, field_serializer
from typing import Optional
from datetime import datetime, timezone


class BaseUser(BaseModel):
    username: str
    email: str
    telegram: Optional[str] = None
    about_me: Optional[str] = None
    password_hash: Optional[str] = None


class UserIn(BaseUser):
    ...


class UserOut(BaseUser):
    id: int
    last_seen: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('last_seen')
    def serialize_last_seen(self, last_seen: datetime, _info):
        return last_seen.astimezone(timezone.utc).isoformat()
