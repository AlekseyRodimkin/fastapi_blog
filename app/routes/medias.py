import os
import uuid

import aiofiles
from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app import (
    YANDEX_DISK_APP_FOLDER_PATH,
    YANDEX_DISK_TOKEN,
    Media,
    create_folder,
    delete_folder_recursive,
    get_db,
    get_direct_link,
    get_file_shareable_link,
    logger,
    upload_file_to_disk,
    user_by_api_key,
)

medias_router = APIRouter(prefix="/api/medias", tags=["Medias"])
app_logger = logger.bind(name="app")

uploads_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "uploads",
)


@medias_router.post("/", status_code=201, response_model=dict)
async def download_media(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    api_key: str = Header(..., convert_underscores=False),
):
    """Media file download and publication on Yandex.Disk"""
    app_logger.info(f"POST /api/medias")

    try:
        existing_user = await user_by_api_key(api_key=api_key, db=db)

        file_name = f"{uuid.uuid4()}_{file.filename}"
        user_folder = os.path.join(uploads_path, str(existing_user.id))
        file_path = os.path.join(user_folder, file_name)

        await create_folder(user_folder)
        app_logger.debug(f"Created folder: {user_folder}")

        async with aiofiles.open(file_path, "wb") as buffer:
            await buffer.write(await file.read())
        app_logger.info(f"File saved locally: {file_path}")

        try:
            uploaded = await upload_file_to_disk(
                user_folder, file_name, YANDEX_DISK_APP_FOLDER_PATH, YANDEX_DISK_TOKEN
            )
            if not uploaded:
                app_logger.error("Yandex.Disk upload failed")
                raise Exception
        except Exception as e:
            app_logger.exception("Yandex.Disk upload error")
            raise

        yandex_disk_file_path = f"{YANDEX_DISK_APP_FOLDER_PATH}/{file_name}"
        public_url = await get_file_shareable_link(yandex_disk_file_path, YANDEX_DISK_TOKEN)
        direct_url = await get_direct_link(public_url) if public_url else None

        if not direct_url:
            app_logger.error("Failed to get direct link")
            raise Exception("Failed to get direct link")

        try:
            new_media = Media(image_link=direct_url, file_name=file_name)
            db.add(new_media)
            await db.commit()
            await db.refresh(new_media)
            app_logger.info(f"Media created (ID: {new_media.id})")
        except Exception as e:
            app_logger.exception("Database commit error")
            await db.rollback()
            raise Exception("Failed to create new Media")

        await delete_folder_recursive(user_folder)
        return {"result": True, "media_id": new_media.id}

    except HTTPException as http_ex:
        if http_ex.status_code == 500:
            app_logger.exception("Internal server error")
            raise HTTPException(status_code=500, detail={"result": False})
        raise http_ex

    except Exception as e:
        app_logger.exception(f"Critical error: {str(e)}")
        raise HTTPException(status_code=500, detail={"result": False})
