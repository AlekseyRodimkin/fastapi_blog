"""Create tables

Revision ID: 6749ab498aba
Revises: 96d5dc030ee8
Create Date: 2025-03-23 13:57:02.033261

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6749ab498aba'
down_revision: Union[str, None] = '96d5dc030ee8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('users',
                    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('users_id_seq'::regclass)"),
                              autoincrement=True, nullable=False),
                    sa.Column('username', sa.VARCHAR(length=64), autoincrement=False, nullable=False),
                    sa.Column('email', sa.VARCHAR(length=120), autoincrement=False, nullable=False),
                    sa.Column('telegram', sa.VARCHAR(length=120), autoincrement=False, nullable=True),
                    sa.Column('about_me', sa.VARCHAR(length=140), autoincrement=False, nullable=True),
                    sa.Column('api_key', sa.VARCHAR(length=256), autoincrement=False, nullable=False),
                    sa.Column('password_hash', sa.VARCHAR(length=256), autoincrement=False, nullable=True),
                    sa.Column('last_seen', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'),
                              autoincrement=False, nullable=False),
                    sa.PrimaryKeyConstraint('id', name='users_pkey'),
                    postgresql_ignore_search_path=False
                    )
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_telegram', 'users', ['telegram'], unique=False)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    op.create_table('posts',
                    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('posts_id_seq'::regclass)"),
                              autoincrement=True, nullable=False),
                    sa.Column('body', sa.VARCHAR(length=140), autoincrement=False, nullable=False),
                    sa.Column('timestamp', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'),
                              autoincrement=False, nullable=False),
                    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='posts_user_id_fkey'),
                    sa.PrimaryKeyConstraint('id', name='posts_pkey'),
                    postgresql_ignore_search_path=False
                    )
    op.create_index('ix_posts_user_id', 'posts', ['user_id'], unique=False)

    op.create_table('followers',
                    sa.Column('follower_id', sa.INTEGER(), autoincrement=False, nullable=False),
                    sa.Column('followed_id', sa.INTEGER(), autoincrement=False, nullable=False),
                    sa.ForeignKeyConstraint(['followed_id'], ['users.id'], name='followers_followed_id_fkey'),
                    sa.ForeignKeyConstraint(['follower_id'], ['users.id'], name='followers_follower_id_fkey'),
                    sa.PrimaryKeyConstraint('follower_id', 'followed_id', name='followers_pkey')
                    )

    op.create_table('media',
                    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
                    sa.Column('image_link', sa.VARCHAR(), autoincrement=False, nullable=False),
                    sa.Column('post_id', sa.INTEGER(), autoincrement=False, nullable=True),
                    sa.ForeignKeyConstraint(['post_id'], ['posts.id'], name='media_post_id_fkey'),
                    sa.PrimaryKeyConstraint('id', name='media_pkey')
                    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_telegram', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_index('ix_posts_user_id', table_name='posts')

    op.execute("DROP TABLE media CASCADE")
    op.execute("DROP TABLE followers CASCADE")
    op.execute("DROP TABLE posts CASCADE")
    op.execute("DROP TABLE users CASCADE")
