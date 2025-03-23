from .conftest import test_data, assert_and_log
from config.logging_config import logger

tests_logger = logger.bind(name="tests")

old_user = test_data["users"]["created"]
new_user = test_data["users"]["new"]


def test_create_user(test_client):
    """New user creation test"""
    tests_logger.debug("test_create_user()")

    response = test_client.post("/api/users", headers=new_user["headers"], json=new_user["data"])

    assert_and_log(condition=response.status_code == 201, error_message=f"{response.status_code} != 201")

    response_create_user = response.json()

    assert_and_log(condition=response_create_user["username"] == new_user["data"]["username"],
                   error_message="response_create_user['username'] != new_user['data']['username']")

    assert_and_log(condition=response_create_user["email"] == new_user["data"]["email"],
                   error_message="response_create_user['email'] != new_user['data']['email']")


def test_get_user_by_id(add_test_user, test_client):
    """Getting test user by ID"""
    tests_logger.debug("test_get_user_by_id()")

    response = test_client.get(f"/api/users/{add_test_user.id}")

    assert_and_log(condition=response.status_code == 200, error_message="{response.status_code} != 200")

    response_get_user_by_id = response.json()

    assert_and_log(condition=response_get_user_by_id["username"] == old_user["username"],
                   error_message="response_get_user_by_id['username'] != old_user['username']")

    assert_and_log(condition=response.json()["email"] == old_user["email"],
                   error_message="response_get_user_by_id['email'] != old_user['email'] ")


def test_get_users(add_test_user, test_client):
    """Getting all users test"""
    tests_logger.debug("test_get_users()")

    response = test_client.get("/api/users", headers=old_user["headers"])

    assert_and_log(condition=response.status_code == 200, error_message=f"{response.status_code} != 200")

    response_get_users = response.json()

    assert_and_log(condition=response_get_users[0]["id"] == add_test_user.id,
                   error_message="response_get_users[0]['id'] != add_test_user.id ")
