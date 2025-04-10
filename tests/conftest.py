import pytest_asyncio
from app.app import app
from config.config import Base, get_db
from fastapi.testclient import TestClient
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

tests_logger = logger.bind(name="tests")

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=True,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

test_data = {
    "users": {
        "created": {
            "headers": {"api_key": "key1"},
            "username": "test_user_1",
            "email": "test1@example.com",
        },
        "new": {
            "headers": {"api_key": "key2"},
            "username": "test_user_2",
            "email": "test2@example.com",
        },
    },
    "tweets": {
        "created": {"tweet_data": "Test body 1", "media_ids": []},
        "new": {"tweet_data": "Test body 2", "media_ids": [1, 2, 3]},
    },
}


def assert_and_log(function_name: str, condition, error_message: str):
    """Checks condition and logs the error if it is not fulfilled"""
    try:
        assert condition
    except AssertionError:
        tests_logger.error(f"{function_name}() -> {error_message}")
        raise


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Fixture for creating and deleting tables in front of each test."""
    tests_logger.debug("db_session()")
    async with test_engine.begin() as conn:
        tests_logger.debug("Create tables ...")
        await conn.run_sync(Base.metadata.create_all)
        tests_logger.debug("Tables created")

        async with AsyncSession(test_engine) as session:
            yield session

        tests_logger.debug("Delete tables ...")
        await conn.run_sync(Base.metadata.drop_all)
        tests_logger.debug("Tables deleted")


@pytest_asyncio.fixture(scope="function")
async def added_test_user(db_session):
    """Fixture for adding a test user before each test."""
    tests_logger.debug("add_test_user()")

    from app.models import User

    async with db_session as session:
        created_user = test_data["users"]["created"]
        test_user = User(
            username=created_user["username"],
            email=created_user["email"],
            api_key=created_user["headers"]["api_key"],
        )
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)
        yield test_user


@pytest_asyncio.fixture(scope="function")
async def added_second_test_user(db_session):
    """Fixture for adding a second test user before each test."""
    tests_logger.debug("added_second_test_user()")

    from app.models import User

    async with db_session as session:
        user = test_data["users"]["new"]
        second_test_user = User(
            username=user["username"],
            email=user["email"],
            api_key=user["headers"]["api_key"],
        )
        session.add(second_test_user)
        await session.commit()
        await session.refresh(second_test_user)
        yield second_test_user


@pytest_asyncio.fixture(scope="function")
async def added_test_post(db_session, added_test_user):
    """Fixture for adding a test post before each test."""
    tests_logger.debug("added_test_post()")

    from app.models import Tweet

    created_post = test_data["tweets"]["created"]

    test_post = Tweet(tweet_data=created_post["tweet_data"], user_id=added_test_user.id)
    db_session.add(test_post)
    await db_session.flush()
    await db_session.refresh(test_post)

    yield test_post


@pytest_asyncio.fixture(scope="function")
def test_client(db_session):
    """Fixture for a test client."""

    async def override_get_db():
        """Change the dependence of Get_DB for tests."""
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client
