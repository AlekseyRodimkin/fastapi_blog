from .conftest import test_data, assert_and_log
from config.logging_config import logger
import os

tests_logger = logger.bind(name="tests")

old_user = test_data["users"]["created"]
new_tweet = test_data["tweets"]["new"]


def test_create_tweet(added_test_user, test_client):
    """
    New tweet creation test
    Perhaps after the test it is necessary to remove the media from Ya.disk
    """
    tests_logger.debug("test_create_tweet()")

    test_dir_path = os.path.join(os.path.dirname(__file__), "test_files")
    file_names = [
        os.path.join(test_dir_path, file_name)
        for file_name in os.listdir(test_dir_path)
        if os.path.isfile(os.path.join(test_dir_path, file_name))
    ]

    for name in file_names:
        with open(name, "rb") as f:
            response = test_client.post(
                "/api/medias",
                headers=old_user["headers"],
                files={"file": ("test_image.jpg", f, "image/jpeg")}
            )

        assert_and_log(
            function_name="test_media_load",
            condition=response.status_code == 201,
            error_message=f"response.status_code != 201"
        )

        response_data = response.json()
        assert_and_log(
            function_name="test_media_load",
            condition="result" in response_data and "media_id" in response_data,
            error_message="`result` and `media_id` not in response_data"
        )

    response = test_client.post("/api/tweets", headers=old_user["headers"], json=new_tweet)
    assert_and_log(function_name="test_create_tweet",
                   condition=response.status_code == 201,
                   error_message=f"{response.status_code} != 201")


def test_delete_tweet_by_id(added_test_user, added_test_post, test_client):
    """Tweet removal test"""
    tests_logger.debug("test_delete_tweet_by_id()")

    response = test_client.delete(
        f"/api/tweets/{added_test_post.id}",
        headers=old_user["headers"]
    )

    assert_and_log(
        function_name="test_delete_tweet_by_id",
        condition=response.status_code == 200,
        error_message=f"{response.status_code} != 200"
    )

    # test cascade...
