import sqlalchemy as sa
import sqlalchemy.orm as so
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from config.config import Base
from typing import Optional

followers = sa.Table(
    'followers',
    Base.metadata,
    sa.Column('follower_id', sa.Integer, sa.ForeignKey('users.id'), primary_key=True),
    sa.Column('followed_id', sa.Integer, sa.ForeignKey('users.id'), primary_key=True)
)

likes = sa.Table(
    'likes',
    Base.metadata,
    sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete="CASCADE"), primary_key=True),
    sa.Column('tweet_id', sa.Integer, sa.ForeignKey('tweets.id', ondelete="CASCADE"), primary_key=True)
)


class User(Base):
    __tablename__ = "users"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True, nullable=False)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True, nullable=False)
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    api_key: so.Mapped[str] = so.mapped_column(sa.String(256), nullable=False)

    last_seen: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now()
    )

    tweets: so.Mapped[list["Tweet"]] = so.relationship(
        "Tweet",
        back_populates='author',
        passive_deletes=True
    )
    liked_tweets: so.Mapped[list["Tweet"]] = so.relationship(
        "Tweet",
        secondary=likes,
        back_populates="liked_by"
    )

    following: so.Mapped[list["User"]] = so.relationship(
        "User",
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        back_populates='followers'
    )
    followers: so.Mapped[list["User"]] = so.relationship(
        "User",
        secondary=followers,
        primaryjoin=(followers.c.followed_id == id),
        secondaryjoin=(followers.c.follower_id == id),
        back_populates='following'
    )

    async def set_api_key(self, api_key: str):
        self.api_key = api_key

    async def update_last_seen(self):
        self.last_seen = datetime.now(timezone.utc)

    async def is_following(self, session: AsyncSession, user: "User") -> bool:
        query = sa.select(sa.exists().where(
            (followers.c.follower_id == self.id) & (followers.c.followed_id == user.id)
        ))
        result = await session.execute(query)
        return result.scalar()

    async def follow(self, session: AsyncSession, user: "User"):
        if not await self.is_following(session, user):
            await session.execute(
                followers.insert().values(follower_id=self.id, followed_id=user.id))
            await session.commit()

    async def unfollow(self, session: AsyncSession, user: "User"):
        await session.execute(
            followers.delete().where(
                (followers.c.follower_id == self.id) &
                (followers.c.followed_id == user.id)
            )
        )
        await session.commit()

    async def followers_count(self, session: AsyncSession) -> int:
        query = sa.select(sa.func.count()).where(followers.c.followed_id == self.id)
        result = await session.execute(query)
        return result.scalar()

    async def following_count(self, session: AsyncSession) -> int:
        query = sa.select(sa.func.count()).where(followers.c.follower_id == self.id)
        result = await session.execute(query)
        return result.scalar()

    async def like_tweet(self, session: AsyncSession, tweet: "Tweet") -> None:
        if tweet not in self.liked_tweets:
            await session.execute(
                likes.insert().values(user_id=self.id, tweet_id=tweet.id)
            )
            self.liked_tweets.append(tweet)
            tweet.liked_by.append(self)
            await session.commit()

    async def unlike_tweet(self, session: AsyncSession, tweet: "Tweet") -> None:
        if tweet in self.liked_tweets:
            await session.execute(
                likes.delete()
                .where((likes.c.user_id == self.id) & (likes.c.tweet_id == tweet.id))
            )
            self.liked_tweets.remove(tweet)
            tweet.liked_by.remove(self)
            await session.commit()

    def __repr__(self):
        return f"<User {self.username}>"


class Media(Base):
    __tablename__ = "media"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    image_link: so.Mapped[str] = so.mapped_column(sa.String(), nullable=False)
    tweet_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("tweets.id", ondelete="CASCADE"), index=True,
                                                nullable=True)

    def __repr__(self):
        return f"<Media {self.id}: {self.image_link}>"


class Tweet(Base):
    __tablename__ = "tweets"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    tweet_data: so.Mapped[Optional[str]] = so.mapped_column(sa.String(1000))
    timestamp: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now()
    )
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("users.id", ondelete="CASCADE"), index=True)
    author: so.Mapped[User] = so.relationship("User", back_populates="tweets")
    liked_by: so.Mapped[list[User]] = so.relationship("User", secondary=likes, back_populates="liked_tweets")
    tweet_media: so.Mapped[list[Media]] = so.relationship("Media", backref="tweet", passive_deletes=True)

    def __repr__(self):
        return f"<Tweet {self.id} by {self.user_id}>"
