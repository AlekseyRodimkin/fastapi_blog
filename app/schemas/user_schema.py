from pydantic import BaseModel


class BaseUser(BaseModel):
    name: str


class UserIn(BaseUser): ...


class UserOut(BaseUser):
    id: int
    name: str

    class Config:
        from_attributes = True
