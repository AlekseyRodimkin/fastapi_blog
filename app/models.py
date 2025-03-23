import sqlalchemy as sa
import sqlalchemy.orm as so
from datetime import datetime, timezone
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from config.config import Base
from typing import Optional

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# Subscriber table
followers = sa.Table(
    'followers',
    Base.metadata,
    sa.Column('follower_id', sa.Integer, sa.ForeignKey('users.id'), primary_key=True),
    sa.Column('followed_id', sa.Integer, sa.ForeignKey('users.id'), primary_key=True)
)


class User(Base):
    """User model"""
    __tablename__ = "users"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True, nullable=False)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True, nullable=False)
    telegram: so.Mapped[Optional[str]] = so.mapped_column(sa.String(120), index=True, nullable=True)
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140), nullable=True)
    api_key: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256), nullable=False)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256), nullable=True)

    last_seen: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now()
    )

    posts: so.WriteOnlyMapped['Post'] = so.relationship("Post", back_populates='author', passive_deletes=True)
    following: so.WriteOnlyMapped['User'] = so.relationship(
        "User",
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        back_populates='followers',
        passive_deletes=True
    )
    followers: so.WriteOnlyMapped['User'] = so.relationship(
        "User",
        secondary=followers,
        primaryjoin=(followers.c.followed_id == id),
        secondaryjoin=(followers.c.follower_id == id),
        back_populates='following',
        passive_deletes=True
    )

    def set_password(self, password: str):
        """Password setting function"""
        self.password_hash = generate_password_hash(password)

    def set_api_key(self, api_key: str):
        """Api key setting function"""
        self.api_key = api_key

    def set_last_seen(self):
        """Updates Last_seen for the current time"""
        self.last_seen = datetime.now()

    async def is_following(self, session: AsyncSession, user: "User") -> bool:
        """Subscription check"""
        query = sa.select(followers).where(
            (followers.c.follower_id == self.id) & (followers.c.followed_id == user.id)
        )
        result = await session.execute(query)
        return result.scalar() is not None

    async def follow(self, session: AsyncSession, user: "User"):
        """Subscription"""
        if not await self.is_following(session, user):
            session.add(followers.insert().values(follower_id=self.id, followed_id=user.id))
            await session.commit()

    async def unfollow(self, session: AsyncSession, user: "User"):
        """Unsubscribe"""
        if await self.is_following(session, user):
            query = followers.delete().where(
                (followers.c.follower_id == self.id) & (followers.c.followed_id == user.id)
            )
            await session.execute(query)
            await session.commit()

    async def followers_count(self, session: AsyncSession) -> int:
        """The number of subscribers"""
        query = sa.select(sa.func.count()).select_from(
            followers.select().where(followers.c.followed_id == self.id).subquery()
        )
        result = await session.execute(query)
        return result.scalar()

    async def following_count(self, session: AsyncSession) -> int:
        """The number of subscriptions"""
        query = sa.select(sa.func.count()).select_from(
            followers.select().where(followers.c.follower_id == self.id).subquery()
        )
        result = await session.execute(query)
        return result.scalar()


class Media(Base):
    """Media model"""
    __tablename__ = "media"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    image_link: so.Mapped[str] = so.mapped_column(sa.String(), nullable=False)
    post_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("posts.id"), nullable=True)

    def __repr__(self):
        return f"<Media {self.image_link}>"


class Post(Base):
    """Post model"""
    __tablename__ = "posts"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now()
    )
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("users.id"), index=True)
    author: so.Mapped[User] = so.relationship("User", back_populates="posts")
    media: so.Mapped[list["Media"]] = so.relationship("Media", backref="post")

    def __repr__(self):
        return f"<Post {self.body}>"
