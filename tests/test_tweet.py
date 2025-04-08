from .conftest import test_data, assert_and_log
from config.logging_config import logger
import os

tests_logger = logger.bind(name="tests")

old_user = test_data["users"]["created"]
new_user = test_data["users"]["new"]
old_tweet = test_data["tweets"]["created"]
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

    # load the media
    for name in file_names:
        with open(name, "rb") as f:
            response_create_media = test_client.post(
                "/api/medias",
                headers=old_user["headers"],
                files={"file": ("test_image.jpg", f, "image/jpeg")}
            )

        assert_and_log(
            function_name="test_create_tweet",
            condition=response_create_media.status_code == 201,
            error_message=f"{response_create_media.status_code} != 201"
        )

        response_create_media = response_create_media.json()
        assert_and_log(
            function_name="test_create_tweet",
            condition="result" in response_create_media and "media_id" in response_create_media,
            error_message="`result` and `media_id` not in response_data"
        )

    # create correct post
    response_create_tweet = test_client.post("/api/tweets", headers=old_user["headers"], json=new_tweet)
    assert_and_log(function_name="test_create_tweet",
                   condition=response_create_tweet.status_code == 201,
                   error_message=f"{response_create_tweet.status_code} != 201")

    # get post for check attachments
    response_get_tweet = test_client.get("/api/tweets/1", headers=old_user["headers"])
    assert_and_log(function_name="test_create_tweet",
                   condition=response_get_tweet.status_code == 200,
                   error_message=f"{response_get_tweet.status_code} != 200")

    # check attachments
    response_get_tweet = response_get_tweet.json()
    assert_and_log(function_name="test_create_tweet",
                   condition=response_get_tweet.get("attachments", []),
                   error_message=f"response_get_tweet['attachments'] is empty")

    # create post with empty data
    response_create_tweet = test_client.post("/api/tweets", headers=old_user["headers"], json={})
    assert_and_log(function_name="test_create_tweet",
                   condition=response_create_tweet.status_code == 422,
                   error_message=f"{response_create_tweet.status_code} != 422")

    # check error
    response_create_tweet = response_create_tweet.json()
    assert_and_log(function_name="test_create_tweet",
                   condition=response_create_tweet["detail"][0]["msg"] == "Field required",
                   error_message=f"{response_create_tweet['detail'][0]['msg']} != 'Field required'")
    assert_and_log(function_name="test_create_tweet",
                   condition=response_create_tweet["detail"][0]["msg"] == "Field required",
                   error_message=f"{response_create_tweet['detail'][1]['msg']} != 'Field required'")

    # create post with not existing media ids
    response_create_tweet = test_client.post("/api/tweets",
                                             headers=old_user["headers"],
                                             json={
                                                 "tweet_data": "Congratulations! You’ve earned chromosome",
                                                 "media_ids": [47]
                                             })
    assert_and_log(function_name="test_create_tweet",
                   condition=response_create_tweet.status_code == 400,
                   error_message=f"{response_create_tweet.status_code} != 400")

    # check error
    response_create_tweet = response_create_tweet.json()
    assert_and_log(function_name="test_create_tweet",
                   condition=response_create_tweet["detail"]["error_message"] == "Media not found: {47}",
                   error_message=f"{response_create_tweet['detail']['error_message']} != 'Media not found: {47}'")


def test_get_test_by_id(added_test_user, added_test_post, test_client):
    """Tweet getting post"""
    tests_logger.debug("test_get_test_by_id()")

    # correct id
    response_get = test_client.get(
        f"/api/tweets/1",
        headers=old_user["headers"]
    )

    assert_and_log(
        function_name="test_get_test_by_id",
        condition=response_get.status_code == 200,
        error_message=f"{response_get.status_code} != 200"
    )
    response_get = response_get.json()

    assert_and_log(
        function_name="test_get_test_by_id",
        condition=response_get["id"] == 1,
        error_message=f"{response_get['id']} != 1"
    )

    # invalid id
    response_get = test_client.get(
        f"/api/tweets/2",
        headers=old_user["headers"]
    )

    assert_and_log(
        function_name="test_get_test_by_id",
        condition=response_get.status_code == 404,
        error_message=f"{response_get.status_code} != 404"
    )
    response_get = response_get.json()

    assert_and_log(
        function_name="test_get_test_by_id",
        condition=response_get["detail"]["error_message"] == "Tweet id=2 not found",
        error_message=f"{response_get['detail']['error_message']} != 'Tweet id=2 not found'"
    )

    # id: str
    response_get = test_client.get(
        f"/api/tweets/who_am_i",
        headers=old_user["headers"]
    )

    assert_and_log(
        function_name="test_get_test_by_id",
        condition=response_get.status_code == 422,
        error_message=f"{response_get.status_code} != 422"
    )
    response_get = response_get.json()

    assert_and_log(
        function_name="test_get_test_by_id",
        condition=response_get["detail"][0][
                      "msg"] == "Input should be a valid integer, unable to parse string as an integer",
        error_message=f"Error msg not in response"
    )


def test_delete_tweet_by_id(added_test_user, added_test_post, test_client):
    """Tweet removal test"""
    tests_logger.debug("test_delete_tweet_by_id()")

    response_delete = test_client.delete(
        f"/api/tweets/1",
        headers=old_user["headers"]
    )
    assert_and_log(
        function_name="test_delete_tweet_by_id",
        condition=response_delete.status_code == 200,
        error_message=f"{response_delete.status_code} != 200"
    )

    # invalid id
    response = test_client.delete(
        f"/api/tweets/1",
        headers=old_user["headers"]
    )

    assert_and_log(
        function_name="test_delete_tweet_by_id",
        condition=response.status_code == 404,
        error_message=f"{response.status_code} != 404"
    )

    # id: str
    response = test_client.delete(
        f"/api/tweets/tweet_id",
        headers=old_user["headers"]
    )

    assert_and_log(
        function_name="test_delete_tweet_by_id",
        condition=response.status_code == 422,
        error_message=f"{response.status_code} != 422"
    )

    response_delete = response.json()

    assert_and_log(
        function_name="test_delete_tweet_by_id",
        condition=response_delete["detail"][0][
                      "msg"] == "Input should be a valid integer, unable to parse string as an integer",
        error_message=f"Error message is not exist"
    )


def test_get_tweets(added_test_user, added_test_post, added_second_test_user, test_client):
    """Tweet getting tweets"""
    tests_logger.debug("test_get_tweets()")

    # follow
    response_follow = test_client.post("/api/users/1/follow", headers=new_user["headers"])
    assert_and_log(function_name="test_get_tweets",
                   condition=response_follow.status_code == 201, error_message=f"{response_follow.status_code} != 201")

    # get tweets
    response = test_client.get(
        f"/api/tweets",
        headers=new_user["headers"]
    )
    assert_and_log(
        function_name="test_get_tweets",
        condition=response.status_code == 200,
        error_message=f"{response.status_code} != 200"
    )

    response_tweets = response.json()

    assert_and_log(
        function_name="test_get_tweets",
        condition=response_tweets["tweets"][0]["content"] == old_tweet["tweet_data"],
        error_message=f"Created tweet not found"
    )


def test_like_tweet(added_test_user, added_test_post, added_second_test_user, test_client):
    """Test like tweet"""
    tests_logger.debug("test_like_tweet()")

    # invalid id
    response_like = test_client.post(
        f"/api/tweets/2/likes",
        headers=old_user["headers"]
    )
    assert_and_log(
        function_name="test_like_tweet",
        condition=response_like.status_code == 404,
        error_message=f"{response_like.status_code} != 404"
    )
    response_like = response_like.json()

    assert_and_log(
        function_name="test_like_tweet",
        condition=response_like["detail"]["error_message"] == "Tweet id=2 not found",
        error_message=f"{response_like['detail']['error_message']} != 'Tweet id=2 not found'"
    )

    # like
    response = test_client.post(
        f"/api/tweets/1/likes",
        headers=old_user["headers"]
    )
    assert_and_log(
        function_name="test_like_tweet",
        condition=response.status_code == 201,
        error_message=f"{response.status_code} != 201"
    )

    # check like
    response_get = test_client.get(
        f"/api/tweets/1",
        headers=old_user["headers"]
    )

    assert_and_log(
        function_name="test_like_tweet",
        condition=response_get.status_code == 200,
        error_message=f"{response_get.status_code} != 200"
    )
    response_get = response_get.json()

    assert_and_log(
        function_name="test_like_tweet",
        condition=response_get["likes"][0]["name"] == old_user["username"],
        error_message=f"{response_get['likes'][0]['name']} != {old_user['username']}"
    )


def test_unlike_tweet(added_test_user, added_test_post, added_second_test_user, test_client):
    """Test unlike tweet"""
    tests_logger.debug("test_unlike_tweet()")

    # invalid id
    response_like = test_client.delete(
        f"/api/tweets/2/likes",
        headers=old_user["headers"]
    )
    assert_and_log(
        function_name="test_unlike_tweet",
        condition=response_like.status_code == 404,
        error_message=f"{response_like.status_code} != 404"
    )
    response_like = response_like.json()

    assert_and_log(
        function_name="test_unlike_tweet",
        condition=response_like["detail"]["error_message"] == "Tweet id=2 not found",
        error_message=f"{response_like['detail']['error_message']} != 'Tweet id=2 not found'"
    )

    # like
    response = test_client.post(
        f"/api/tweets/1/likes",
        headers=old_user["headers"]
    )
    assert_and_log(
        function_name="test_unlike_tweet",
        condition=response.status_code == 201,
        error_message=f"{response.status_code} != 201"
    )

    # check like
    response_get = test_client.get(
        f"/api/tweets/1",
        headers=old_user["headers"]
    )

    assert_and_log(
        function_name="test_unlike_tweet",
        condition=response_get.status_code == 200,
        error_message=f"{response_get.status_code} != 200"
    )
    response_get = response_get.json()

    assert_and_log(
        function_name="test_unlike_tweet",
        condition=response_get["likes"][0]["name"] == old_user["username"],
        error_message=f"{response_get['likes'][0]['name']} != {old_user['username']}"
    )

    # unlike
    response = test_client.delete(
        f"/api/tweets/1/likes",
        headers=old_user["headers"]
    )
    assert_and_log(
        function_name="test_unlike_tweet",
        condition=response.status_code == 200,
        error_message=f"{response.status_code} != 200"
    )

    # check like
    response_get = test_client.get(
        f"/api/tweets/1",
        headers=old_user["headers"]
    )

    assert_and_log(
        function_name="test_unlike_tweet",
        condition=response_get.status_code == 200,
        error_message=f"{response_get.status_code} != 200"
    )
    response_get = response_get.json()

    assert_and_log(
        function_name="test_unlike_tweet",
        condition=response_get["likes"] == [],
        error_message=f"{response_get['likes']} != []"
    )