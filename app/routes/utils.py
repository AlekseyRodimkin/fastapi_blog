from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app import models
from config.config import get_db
from config.logging_config import logger
from fastapi import Depends, HTTPException
import aiohttp
import aiofiles.os as aio_os
import os

app_logger = logger.bind(name="app")


async def get_current_user_or_none(api_key: str, db: AsyncSession = Depends(get_db)) -> models.User | None:
    """Get current user by api_key and update last seen timestamp.

       Args:
           api_key (str): API key from request headers
           db (AsyncSession): Database session dependency
       Returns:
           models.User: Authenticated user object if found by 'api_key'
           None: If user with provided API key doesn't exist
       Raises:
           HTTPException: 500 error if database operation fails
       """
    app_logger.debug(f"get_current_user(api_key={api_key})")

    result = await db.execute(select(models.User).where(models.User.api_key == api_key))
    current_user = result.scalars().first()

    if current_user:
        await current_user.update_last_seen()
        await db.commit()
        await db.refresh(current_user)
        app_logger.info(f"User authenticated: id={current_user.id}")
    else:
        app_logger.error("Invalid API key")
        raise HTTPException(status_code=403, detail={"result": False,
                                                     "error_type": 403,
                                                     "error_message": "Invalid API Key"})
    return current_user


async def check_unique_user(db: AsyncSession, username: str, email: str, api_key: str) -> bool | None:
    """Ensure username, email, and API key are unique."""
    app_logger.debug("check_unique_user_for_create_new()")
    result = await db.execute(
        select(models.User).where(
            (models.User.username == username) |
            (models.User.email == email) |
            (models.User.api_key == api_key)
        )
    )
    existing_user = result.scalars().first()

    if existing_user:
        return
    return True


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


async def get_file_shareable_link(file_path: str, ya_token: str) -> str | None:
    """Get a shareable link for a file on Yandex Disk."""
    url_publish = "https://cloud-api.yandex.net/v1/disk/resources/publish"
    url_meta = "https://cloud-api.yandex.net/v1/disk/resources"
    headers = {"Authorization": f"OAuth {ya_token}"}
    params = {"path": file_path}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.put(url_publish, headers=headers, params=params) as response:
                response.raise_for_status()
            async with session.get(url_meta, headers=headers, params=params) as response_meta:
                response_meta.raise_for_status()
                data = await response_meta.json()
                public_url = data.get("public_url")
                if public_url:
                    app_logger.info(f"Public link obtained: {public_url}")
                    return public_url
                app_logger.error("Failed to obtain public link")
                return None
    except aiohttp.ClientError as e:
        app_logger.exception("Error retrieving public link")
        return None


async def get_direct_link(public_url: str) -> str | None:
    """Convert a public Yandex Disk link to a direct download link."""
    return f"https://getfile.dokpub.com/yandex/get/{public_url}" if public_url else None


async def create_folder(folder_path: str) -> None:
    """Create a folder asynchronously."""
    try:
        if not await aio_os.path.exists(folder_path):
            await aio_os.makedirs(folder_path)
            app_logger.info(f"Folder created: {folder_path}")
    except Exception as e:
        app_logger.exception(f"Error creating folder: {folder_path}")


async def delete_folder_recursive(folder_path: str) -> None:
    """Recursively delete a folder and its contents asynchronously."""
    try:
        if await aio_os.path.exists(folder_path):
            for item in await aio_os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                if await aio_os.path.isdir(item_path):
                    await delete_folder_recursive(item_path)
                else:
                    await aio_os.remove(item_path)
            await aio_os.rmdir(folder_path)
            app_logger.info(f"Folder deleted: {folder_path}")
    except Exception as e:
        app_logger.exception(f"Error deleting folder: {folder_path}")
