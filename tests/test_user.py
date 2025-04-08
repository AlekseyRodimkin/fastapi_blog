from .conftest import test_data, assert_and_log
from config.logging_config import logger

tests_logger = logger.bind(name="tests")

old_user = test_data["users"]["created"]
new_user = test_data["users"]["new"]


def test_create_user(test_client):
    """New user creation test"""
    tests_logger.debug("test_create_user()")

    headers = {"api_key": "I`m a key"}
    body = {"username": "u", "email": "e"}

    # correct user
    response = test_client.post("/api/users", headers=headers, json=body)
    assert_and_log(function_name="test_create_user",
                   condition=response.status_code == 201,
                   error_message=f"{response.status_code} != 201")

    response_create_user = response.json()

    # already registered
    response = test_client.post("/api/users", headers=headers, json=body)
    assert_and_log(function_name="test_create_user",
                   condition=response.status_code == 400,
                   error_message=f"{response.status_code} != 400")

    response_create_user = response.json()

    correct_error = {"detail": {
        "result": False,
        "error_type": 400,
        "error_message": "Already registered"}
    }

    assert_and_log(function_name="test_create_user",
                   condition=response_create_user == correct_error,
                   error_message=f"{response_create_user} != correct_error")

    # empty fields
    response = test_client.post("/api/users", headers={"api_key": "im a key"}, json={})
    assert_and_log(function_name="test_create_user",
                   condition=response.status_code == 422,
                   error_message=f"{response.status_code} != 422")

    response_create_user = response.json()

    assert_and_log(
        function_name="test_create_user",
        condition=any(
            error.get("msg") == "Field required"
            for error in response_create_user.get("detail", [])
        ),
        error_message=f"Expected 'Field required' error, got: {response_create_user}"
    )


def test_get_user_by_id(added_test_user, test_client):
    """Getting test user by ID"""
    tests_logger.debug("test_get_user_by_id()")

    # existing id
    response = test_client.get(f"/api/users/{added_test_user.id}")
    assert_and_log(function_name="test_get_user_by_id",
                   condition=response.status_code == 200,
                   error_message=f"{response.status_code} != 200")

    response_get_user_by_id = response.json()

    assert_and_log(function_name="test_get_user_by_id",
                   condition=response_get_user_by_id["result"] == True,
                   error_message=f"{response_get_user_by_id['result']} != True")

    assert_and_log(function_name="test_get_user_by_id",
                   condition=response_get_user_by_id["user"]["username"] == old_user["username"],
                   error_message=f"{response_get_user_by_id["user"]["username"]} != {old_user['username']}")

    # not existing id
    response = test_client.get(f"/api/users/2")
    assert_and_log(function_name="test_get_user_by_id",
                   condition=response.status_code == 404,
                   error_message=f"{response.status_code} != 404")

    response_get_user_by_id = response.json()

    assert_and_log(function_name="test_get_user_by_id",
                   condition=response_get_user_by_id["detail"]["error_message"] == "User id=2 not found",
                   error_message=f"{response_get_user_by_id['detail']['error_message']} != 'User id=2 not found'")

    # user_id = str
    response = test_client.get(f"/api/users/user_id")
    assert_and_log(function_name="test_create_user",
                   condition=response.status_code == 422,
                   error_message=f"{response.status_code} != 422")

    response_create_user = response.json()

    assert_and_log(
        function_name="test_create_user",
        condition=any(
            error.get("msg") == "Input should be a valid integer, unable to parse string as an integer"
            for error in response_create_user.get("detail", [])
        ),
        error_message=f"Expected 'Field required' error, got: {response_create_user}"
    )


def test_get_users(added_test_user, test_client):
    """Getting all users test"""
    tests_logger.debug("test_get_users()")

    response = test_client.get("/api/users", headers=old_user["headers"])
    assert_and_log(function_name="test_get_users",
                   condition=response.status_code == 200,
                   error_message=f"{response.status_code} != 200")

    response_get_users = response.json()

    assert_and_log(function_name="test_get_users",
                   condition=response_get_users["users"][0]["username"] == old_user["username"],
                   error_message=f"{response_get_users['users'][0]['username']} != {old_user['username']}")

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
                   error_message=f"{response.status_code} != 200")

    response_get_me = response.json()

    assert_and_log(function_name="test_get_me",
                   condition=response_get_me["result"] == True,
                   error_message=f"{response_get_me['result']} != True")

    assert_and_log(function_name="test_get_me",
                   condition=response_get_me["user"]["username"] == old_user["username"],
                   error_message=f"{response_get_me['user']['username']} != {old_user['username']}")

    response = test_client.get(f"/api/users/me", headers={"api_key": "Who I am"})
    assert_and_log(function_name="test_get_me",
                   condition=response.status_code == 403,
                   error_message=f"{response.status_code} != 403")


def test_follow(added_test_user, added_second_test_user, test_client):
    """Subscription test"""
    tests_logger.debug("test_follow()")

    # invalid id
    response_follow = test_client.post("/api/users/3/follow", headers=old_user["headers"])
    assert_and_log(function_name="test_follow",
                   condition=response_follow.status_code == 404, error_message=f"{response_follow.status_code} != 404")
    # id: str
    response_follow = test_client.post("/api/users/user_id/follow")
    assert_and_log(function_name="test_follow",
                   condition=response_follow.status_code == 422,
                   error_message=f"{response_follow.status_code} != 422")

    response_follow = response_follow.json()

    assert_and_log(function_name="test_follow",
                   condition=response_follow["detail"][0][
                                 "msg"] == "Input should be a valid integer, unable to parse string as an integer",
                   error_message=f"Error not exist in {response_follow}")

    # correct follow
    response_follow = test_client.post("/api/users/2/follow", headers=old_user["headers"])
    assert_and_log(function_name="test_follow",
                   condition=response_follow.status_code == 201, error_message=f"{response_follow.status_code} != 201")

    # check follow
    response_get_user = test_client.get("/api/users/2")
    assert_and_log(function_name="test_follow",
                   condition=response_get_user.status_code == 200,
                   error_message=f"{response_get_user.status_code} != 200")

    response_get_user = response_get_user.json()

    assert_and_log(function_name="test_follow",
                   condition=response_get_user["user"]["followers"][0]["username"] == old_user["username"],
                   error_message=f"{response_get_user['user']['followers'][0]['username']} != {old_user['username']}")


def test_unfollow(added_test_user, added_second_test_user, test_client):
    """Unsubscribing test"""
    tests_logger.debug("test_unfollow()")

    # invalid id
    response_unfollow = test_client.delete("/api/users/3/unfollow", headers=old_user["headers"])
    assert_and_log(function_name="test_unfollow",
                   condition=response_unfollow.status_code == 404,
                   error_message=f"{response_unfollow.status_code} != 404")
    # id: str
    response_unfollow = test_client.delete("/api/users/user_id/unfollow")
    assert_and_log(function_name="test_unfollow",
                   condition=response_unfollow.status_code == 422,
                   error_message=f"{response_unfollow.status_code} != 422")

    response_unfollow = response_unfollow.json()

    assert_and_log(function_name="test_unfollow",
                   condition=response_unfollow["detail"][0][
                                 "msg"] == "Input should be a valid integer, unable to parse string as an integer",
                   error_message=f"Error not exist in {response_unfollow}")

    # follow
    response_follow = test_client.post("/api/users/2/follow", headers=old_user["headers"])
    assert_and_log(function_name="test_unfollow",
                   condition=response_follow.status_code == 201, error_message=f"{response_follow.status_code} != 201")

    # unfollow
    response_unfollow = test_client.delete("/api/users/2/unfollow", headers=old_user["headers"])
    assert_and_log(function_name="test_unfollow",
                   condition=response_unfollow.status_code == 200,
                   error_message=f"{response_unfollow.status_code} != 200")

    # check unfollow
    response_get_user = test_client.get("/api/users/2")
    assert_and_log(function_name="test_unfollow",
                   condition=response_get_user.status_code == 200,
                   error_message=f"{response_get_user.status_code} != 200")

    response_get_user = response_get_user.json()

    assert_and_log(function_name="test_unfollow",
                   condition=response_get_user["user"]["followers"] == [],
                   error_message=f"{response_get_user['user']['followers']} != []")
