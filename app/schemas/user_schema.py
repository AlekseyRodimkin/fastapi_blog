from pydantic import BaseModel
from typing import List, Optional


class BaseUser(BaseModel):
    username: str
    email: str
    about_me: Optional[str] = None


class UserCreateResponse(BaseModel):
    result: bool
    id: int


class Other(BaseModel):
    id: int
    username: str


class UserWithRelations(BaseModel):
    id: int
    username: str
    followers: List[Other]
    following: List[Other]


class UserResponse(BaseModel):
    result: bool
    user: UserWithRelations


class UserFull(BaseUser):
    id: int


class UserListResponse(BaseModel):
    result: bool
    users: List[UserFull]
