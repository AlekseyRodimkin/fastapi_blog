from .conftest import test_data, assert_and_log
from config.logging_config import logger

tests_logger = logger.bind(name="tests")

old_user = test_data["users"]["created"]
new_tweet = test_data["tweets"]["new"]


def test_create_tweet(added_test_user, test_client):
    """New tweet creation test"""
    tests_logger.debug("test_create_tweet()")

    response = test_client.post("/api/tweets", headers=old_user["headers"], json=new_tweet)
    assert_and_log(function_name="test_create_tweet",
                   condition=response.status_code == 201,
                   error_message=f"{response.status_code} != 201")


def test_delete_tweet_by_id(added_test_user, test_client):
    """Tweet removal test"""
    tests_logger.debug("test_delete_tweet_by_id()")

    response = test_client.post("/api/tweets", headers=old_user["headers"], json=new_tweet)
    assert_and_log(function_name="test_create_tweet",
                   condition=response.status_code == 201,
                   error_message=f"{response.status_code} != 201")

    response = test_client.delete("/api/tweets/1", headers=old_user["headers"])
    assert_and_log(function_name="test_delete_tweet_by_id",
                   condition=response.status_code == 200,
                   error_message=f"{response.status_code} != 200")

    # test cascade...
