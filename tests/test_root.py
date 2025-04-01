import pytest
from sqlalchemy import text
from config.logging_config import logger
from .conftest import assert_and_log

tests_logger = logger.bind(name="tests")


def test_root_route(test_client):
    tests_logger.debug("test_root_route()")

    response = test_client.get("/api/healthchecker")

    assert_and_log(function_name="test_root_route",
                   condition=response.status_code == 200,
                   error_message=f"Error: {response.status_code} != 200")

    assert_and_log(function_name="test_root_route",
                   condition=response.json() == {"message": "The API is LIVE!!"},
                   error_message=f"Error: {response.json()} != {{'message': 'The API is LIVE!!'}}")


@pytest.mark.asyncio
async def test_tables_created(db_session):
    """Test creation of tables"""
    tests_logger.debug("test_tables_created()")

    async with db_session as session:
        result = await session.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        tables = result.scalars().all()

        assert_and_log(function_name="test_tables_created", condition="users" in tables, error_message="Table 'users' not created")
        assert_and_log(function_name="test_tables_created", condition="tweets" in tables, error_message="Table 'tweets' not created")
