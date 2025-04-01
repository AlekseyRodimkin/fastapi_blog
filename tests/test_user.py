from .conftest import test_data, assert_and_log
from config.logging_config import logger

tests_logger = logger.bind(name="tests")

old_user = test_data["users"]["created"]
new_user = test_data["users"]["new"]


def test_create_user(test_client):
    """New user creation test"""
    tests_logger.debug("test_create_user()")

    # correct user
    response = test_client.post("/api/users", headers=new_user["headers"], json=new_user["data"])
    assert_and_log(function_name="test_create_user",
                   condition=response.status_code == 201,
                   error_message=f"{response.status_code} != 201")

    response_create_user = response.json()

    assert_and_log(function_name="test_create_user",
                   condition=response_create_user["username"] == new_user["data"]["username"],
                   error_message="response_create_user['username'] != new_user['data']['username']")

    assert_and_log(function_name="test_create_user",
                   condition=response_create_user["email"] == new_user["data"]["email"],
                   error_message="response_create_user['email'] != new_user['data']['email']")

    # already registered
    response = test_client.post("/api/users", headers=new_user["headers"], json=new_user["data"])
    assert_and_log(function_name="test_create_user",
                   condition=response.status_code == 400,
                   error_message=f"{response.status_code} != 400")

    response_create_user = response.json()

    correct_error = {"detail": {
        "result": False,
        "error_type": 400,
        "error_message": "Name/email/api_key already registered"}
    }

    assert_and_log(function_name="test_create_user",
                   condition=response_create_user == correct_error,
                   error_message="response_create_user != correct_error")


def test_get_user_by_id(added_test_user, test_client):
    """Getting test user by ID"""
    tests_logger.debug("test_get_user_by_id()")

    # existing id
    response = test_client.get(f"/api/users/{added_test_user.id}")
    assert_and_log(function_name="test_get_user_by_id",
                   condition=response.status_code == 200,
                   error_message="{response.status_code} != 200")

    response_get_user_by_id = response.json()

    assert_and_log(function_name="test_get_user_by_id",
                   condition=response_get_user_by_id["result"] == "true",
                   error_message="response_get_user_by_id['result'] == 'true'")

    assert_and_log(function_name="test_get_user_by_id",
                   condition="username" in response_get_user_by_id["user"],
                   error_message="username not in response_get_user_by_id['user']")

    # not existing id
    response = test_client.get(f"/api/users/2")
    assert_and_log(function_name="test_get_user_by_id",
                   condition=response.status_code == 404,
                   error_message="{response.status_code} != 404")


def test_get_users(added_test_user, test_client):
    """Getting all users test"""
    tests_logger.debug("test_get_users()")

    response = test_client.get("/api/users", headers=old_user["headers"])
    assert_and_log(function_name="test_get_users",
                   condition=response.status_code == 200,
                   error_message=f"{response.status_code} != 200")

    response_get_users = response.json()

    assert_and_log(function_name="test_get_users",
                   condition=response_get_users[0]["id"] == added_test_user.id,
                   error_message="response_get_users[0]['id'] != add_test_user.id ")

    # invalid api_key
    correct_error = {"detail": {
        "result": False,
        "error_type": 403,
        "error_message": "Invalid API Key"}
    }
    response = test_client.get("/api/users", headers={"api_key": "Who I am"})
    assert_and_log(function_name="test_get_users",
                   condition=response.status_code == 403,
                   error_message=f"{response.status_code} != 403")

    response_get_users = response.json()

    assert_and_log(function_name="test_get_users",
                   condition=response_get_users == correct_error,
                   error_message="response_create_user != correct_error")


def test_get_me(added_test_user, test_client):
    """Getting test current user"""
    tests_logger.debug("test_get_me()")

    response = test_client.get(f"/api/users/me", headers=old_user["headers"])
    assert_and_log(function_name="test_get_me",
                   condition=response.status_code == 200,
                   error_message="{response.status_code} != 200")

    response_get_me = response.json()

    assert_and_log(function_name="test_get_me",
                   condition=response_get_me["result"] == "true",
                   error_message="response_get_me['result'] == 'true'")

    assert_and_log(function_name="test_get_me",
                   condition=response_get_me["user"]["username"] == old_user["username"],
                   error_message="response_get_me['user']['username'] == old_user['username']")

    response = test_client.get(f"/api/users/me", headers={"api_key": "Who I am"})
    assert_and_log(function_name="test_get_me",
                   condition=response.status_code == 403,
                   error_message="{response.status_code} != 403")


def test_follow_unfollow(added_test_user, test_client):
    """Subscription and unsubscribing test"""
    tests_logger.debug("test_follow_unfollow()")

    # create user
    response = test_client.post("/api/users", headers=new_user["headers"], json=new_user["data"])
    assert_and_log(function_name="test_follow_unfollow",
                   condition=response.status_code == 201, error_message=f"{response.status_code} != 201")

    # invalid id
    response = test_client.post("/api/users/3/follow", headers=old_user["headers"])
    assert_and_log(function_name="test_follow_unfollow",
                   condition=response.status_code == 404, error_message=f"{response.status_code} != 404")

    # correct follow
    response = test_client.post("/api/users/2/follow", headers=old_user["headers"])
    assert_and_log(function_name="test_follow_unfollow",
                   condition=response.status_code == 201, error_message=f"{response.status_code} != 201")

    # invalid id
    response = test_client.delete("/api/users/3/unfollow", headers=old_user["headers"])
    assert_and_log(function_name="test_follow_unfollow",
                   condition=response.status_code == 404, error_message=f"{response.status_code} != 404")

    # correct unfollow
    response = test_client.delete("/api/users/2/unfollow", headers=old_user["headers"])
    assert_and_log(function_name="test_follow_unfollow",
                   condition=response.status_code == 200, error_message=f"{response.status_code} != 200")
