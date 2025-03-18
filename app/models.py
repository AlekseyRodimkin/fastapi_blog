from sqlalchemy import Column, String, Integer
from config.config import Base


class User(Base):
    """Model of User"""

    __tablename__ = "Users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
