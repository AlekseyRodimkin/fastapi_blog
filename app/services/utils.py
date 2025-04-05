from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import User
from config.config import get_db
from config.logging_config import logger
from fastapi import Depends, HTTPException
import aiofiles.os as aio_os
import os

app_logger = logger.bind(name="app")


async def get_current_user_or_none(api_key: str, db: AsyncSession = Depends(get_db)) -> User | None:
    """Get current user by api_key and update last seen timestamp."""
    result = await db.execute(select(User).where(User.api_key == api_key))
    current_user = result.scalars().first()

    if current_user:
        await current_user.update_last_seen()
        await db.flush()
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
    app_logger.debug("check_unique_user()")
    result = await db.execute(
        select(User).where(
            (User.username == username) |
            (User.email == email) |
            (User.api_key == api_key)
        )
    )
    existing_user = result.scalars().first()

    if existing_user:
        return
    return True


async def create_folder(folder_path: str) -> None:
    """Create a folder asynchronously."""
    try:
        if not await aio_os.path.exists(folder_path):
            await aio_os.makedirs(folder_path)
            app_logger.info(f"Folder created: {folder_path}")
    except Exception as e:
        app_logger.exception(f"Error creating folder: {folder_path}")
        raise Exception(f"Error creating folder: {folder_path}")


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
        raise Exception(f"Error deleting folder: {folder_path}")
