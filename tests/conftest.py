from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config.config import Base, get_db
from app.app import app
from loguru import logger
import pytest_asyncio

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
            "email": "test1@example.com"
        },
        "new": {
            "headers": {"api_key": "key2"},
            "data": {"username": "test_user_2", "email": "test2@example.com"}
        },
    },
    "tweets": {
        "new": {
            "tweet_data": "Test data1",
            "media_ids": []
        }
    }

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
        old_user = test_data["users"]["created"]
        test_user = User(
            username=old_user["username"],
            email=old_user["email"],
            api_key=old_user["headers"]["api_key"],
        )
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)
        yield test_user


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
