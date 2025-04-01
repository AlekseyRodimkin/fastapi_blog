from fastapi import APIRouter, HTTPException, status, File, UploadFile, Depends, Header
from config.logging_config import logger
from config.config import YANDEX_DISK_TOKEN, YANDEX_DISK_APP_FOLDER_PATH
from .utils import (
    upload_file_to_disk, get_file_shareable_link, get_direct_link,
    delete_folder_recursive, create_folder, get_current_user_or_none
)
import os
import uuid
import aiofiles
from app import models
from config.config import get_db
from sqlalchemy.ext.asyncio import AsyncSession

medias_router = APIRouter(prefix="/api/medias", tags=["Medias"])
app_logger = logger.bind(name="app")

uploads_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "uploads"
)


@medias_router.post("/", status_code=status.HTTP_201_CREATED)
async def download_media(
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db),
        api_key: str = Header(..., convert_underscores=False)):
    """Loading the media file and its publication on Yandex.Disk"""
    app_logger.info(f"POST /api/medias (api_key={api_key})")

    existing_user = await get_current_user_or_none(api_key, db)

    file_name = f"{uuid.uuid4()}_{file.filename}"
    user_folder = os.path.join(uploads_path, str(existing_user.id))
    file_path = os.path.join(user_folder, file_name)

    try:
        await create_folder(user_folder)

        async with aiofiles.open(file_path, "wb") as buffer:
            await buffer.write(await file.read())

        app_logger.info(f"The file is saved locally: {file_path}")

        uploaded = await upload_file_to_disk(user_folder, file_name, YANDEX_DISK_APP_FOLDER_PATH, YANDEX_DISK_TOKEN)
        if not uploaded:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Upload to Yandex.Disk failed")

        yandex_disk_file_path = f"{YANDEX_DISK_APP_FOLDER_PATH}/{file_name}"
        public_url = await get_file_shareable_link(yandex_disk_file_path, YANDEX_DISK_TOKEN)
        if not public_url:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get public link")

        direct_url = await get_direct_link(public_url)
        if not direct_url:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get direct link")

        try:
            new_media = models.Media(image_link=direct_url)
            db.add(new_media)
            await db.commit()
            await db.refresh(new_media)

            app_logger.info(f"The file is uploaded and saved in the database (media_id={new_media.id})")

            await delete_folder_recursive(user_folder)

            return {"result": True, "media_id": new_media.id}

        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create media")

    except HTTPException as http_ex:
        app_logger.error(f"Error HTTP: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        app_logger.exception(f"Error media uploads: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")
