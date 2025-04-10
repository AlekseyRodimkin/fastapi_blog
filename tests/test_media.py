import os

from config.logging_config import logger

from .conftest import assert_and_log, test_data

tests_logger = logger.bind(name="tests")

old_user = test_data["users"]["created"]
img = "img.jpeg"


def test_media_load(added_test_user, test_client):
    """
    Test media upload endpoint
    Perhaps after the test it is necessary to remove the media from Ya.disk
    """
    tests_logger.debug("test_media_load()")

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
                files={"file": ("test_image.jpg", f, "image/jpeg")},
            )

        assert_and_log(
            function_name="test_media_load",
            condition=response.status_code == 201,
            error_message=f"{response.status_code} != 201",
        )

        response_data = response.json()
        assert_and_log(
            function_name="test_media_load",
            condition="result" in response_data and "media_id" in response_data,
            error_message="`result` and `media_id` not in response_data",
        )
