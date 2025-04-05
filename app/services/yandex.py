import asyncio
import os
from config.logging_config import logger
import aiohttp
from config.config import YANDEX_DISK_TOKEN, celery_app
import requests
import time

app_logger = logger.bind(name="app")


async def upload_file_to_disk(dir_path: str, file_name: str, disk_folder_path: str, ya_token: str) -> bool:
    """Upload a file to Yandex Disk."""
    url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
    headers = {"Authorization": f"OAuth {ya_token}"}
    params = {"path": f"{disk_folder_path}/{file_name}", "overwrite": "true"}

    try:
        app_logger.info("Requesting upload URL from Yandex Disk")
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                upload_url = data.get("href")
                if not upload_url:
                    app_logger.error("Failed to obtain upload URL")
                    return False

        path = os.path.join(dir_path, file_name)
        if not os.path.isfile(path):
            app_logger.error(f"File not found: {path}")
            return False

        app_logger.info("Uploading file to Yandex Disk")
        async with aiohttp.ClientSession() as session:

            async with session.put(upload_url, data=open(path, "rb")) as upload_response:
                upload_response.raise_for_status()
                if upload_response.status == 201:
                    app_logger.info("File uploaded successfully")
                    return True

                app_logger.error("File upload failed")
                return False

    except aiohttp.ClientError as e:
        app_logger.exception("Error during file upload to Yandex Disk")
        return False


async def get_file_shareable_link(
        file_path: str,
        ya_token: str,
        max_retries: int = 3,
        retry_delay: float = 1.0
) -> str | None:
    """Get a shareable link for a file on Yandex Disk with retry logic."""
    publish_url = "https://cloud-api.yandex.net/v1/disk/resources/publish"
    meta_url = "https://cloud-api.yandex.net/v1/disk/resources"
    headers = {"Authorization": f"OAuth {ya_token}"}
    params = {"path": file_path}

    async with aiohttp.ClientSession() as session:
        for attempt in range(1, max_retries + 1):
            try:
                async with session.put(publish_url, headers=headers, params=params) as pub_response:
                    pub_response.raise_for_status()

                async with session.get(meta_url, headers=headers, params=params) as meta_response:
                    meta_response.raise_for_status()
                    data = await meta_response.json()
                    public_url = data.get("public_url")

                    if public_url:
                        app_logger.info(f"Public link obtained after {attempt} attempts: {public_url}")
                        return public_url

                if attempt < max_retries:
                    await asyncio.sleep(retry_delay)

            except aiohttp.ClientError as e:
                app_logger.warning(f"Attempt {attempt} failed: {str(e)}")
                if attempt == max_retries:
                    app_logger.error("All attempts to get public link failed")
                    return None
                await asyncio.sleep(retry_delay)

    return None


async def get_direct_link(public_url: str) -> str | None:
    """Convert a public Yandex Disk link to a direct download link."""
    return f"https://getfile.dokpub.com/yandex/get/{public_url}" if public_url else None


@celery_app.task(bind=True, max_retries=3)
def celery_task_delete_media(self, file_path):
    try:
        delete_from_yadisk(YANDEX_DISK_TOKEN, file_path)
        return {'status': 'success', 'file_path': file_path}
    except Exception as e:
        self.retry(exc=e, countdown=60)


def delete_from_yadisk(ya_token: str, file_disk_path: str, retries: int = 3):
    """Sync function of deleting file from Y.disk"""
    app_logger.debug(f"delete_from_yadisk(file_disk_path={file_disk_path})")

    url = "https://cloud-api.yandex.net/v1/disk/resources"
    headers = {"Authorization": f"OAuth {ya_token}"}
    params = {"path": file_disk_path, "permanently": "true"}

    for attempt in range(1, retries + 1):
        try:
            response = requests.delete(url, headers=headers, params=params)

            if response.status_code == 204:
                app_logger.info(f"Successfully deleted: {file_disk_path}")
                return

            elif response.status_code in {429, 500, 502, 503, 504}:
                app_logger.warning(f"Attempt {attempt}/{retries} failed: {response.status_code}. Retrying...")
                time.sleep(2 ** attempt)

            else:
                error_text = response.text
                raise Exception(f"Yandex.Disk API error ({response.status_code}): {error_text}")

        except requests.exceptions.RequestException as e:
            app_logger.warning(f"Attempt {attempt}/{retries} failed with exception: {str(e)}")
            if attempt == retries:
                raise
            time.sleep(2 ** attempt)
