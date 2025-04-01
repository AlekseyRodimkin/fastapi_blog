"""Create tables

Revision ID: 63557c0efae2
Revises: 
Create Date: 2025-04-01 18:41:10.797579

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '63557c0efae2'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('users',
                    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
                    sa.Column('username', sa.VARCHAR(length=64), autoincrement=False, nullable=False),
                    sa.Column('email', sa.VARCHAR(length=120), autoincrement=False, nullable=False),
                    sa.Column('about_me', sa.VARCHAR(length=140), autoincrement=False, nullable=True),
                    sa.Column('api_key', sa.VARCHAR(length=256), autoincrement=False, nullable=False),
                    sa.Column('last_seen', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'),
                              autoincrement=False, nullable=False),
                    sa.PrimaryKeyConstraint('id', name='users_pkey')
                    )
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    op.create_table('tweets',
                    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
                    sa.Column('tweet_data', sa.VARCHAR(length=1000), autoincrement=False, nullable=True),
                    sa.Column('timestamp', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'),
                              autoincrement=False, nullable=False),
                    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='tweets_user_id_fkey', ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id', name='tweets_pkey')
                    )
    op.create_index('ix_tweets_user_id', 'tweets', ['user_id'], unique=False)

    op.create_table('media',
                    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
                    sa.Column('image_link', sa.VARCHAR(), autoincrement=False, nullable=False),
                    sa.Column('tweet_id', sa.INTEGER(), autoincrement=False, nullable=True),
                    sa.ForeignKeyConstraint(['tweet_id'], ['tweets.id'], name='media_tweet_id_fkey',
                                            ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id', name='media_pkey')
                    )
    op.create_index('ix_media_tweet_id', 'media', ['tweet_id'], unique=False)

    op.create_table('likes',
                    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False),
                    sa.Column('tweet_id', sa.INTEGER(), autoincrement=False, nullable=False),
                    sa.ForeignKeyConstraint(['tweet_id'], ['tweets.id'], name='likes_tweet_id_fkey',
                                            ondelete='CASCADE'),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='likes_user_id_fkey', ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('user_id', 'tweet_id', name='likes_pkey')
                    )

    op.create_table('followers',
                    sa.Column('follower_id', sa.INTEGER(), autoincrement=False, nullable=False),
                    sa.Column('followed_id', sa.INTEGER(), autoincrement=False, nullable=False),
                    sa.ForeignKeyConstraint(['followed_id'], ['users.id'], name='followers_followed_id_fkey'),
                    sa.ForeignKeyConstraint(['follower_id'], ['users.id'], name='followers_follower_id_fkey'),
                    sa.PrimaryKeyConstraint('follower_id', 'followed_id', name='followers_pkey')
                    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_table('users')
    op.drop_index('ix_tweets_user_id', table_name='tweets')
    op.drop_table('tweets')
    op.drop_table('followers')
    op.drop_index('ix_media_tweet_id', table_name='media')
    op.drop_table('media')
    op.drop_table('likes')
