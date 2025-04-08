from config.logging_config import logger
import aiofiles.os as aio_os
import os

app_logger = logger.bind(name="app")


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
