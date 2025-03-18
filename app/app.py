from contextlib import asynccontextmanager
from fastapi import FastAPI

from config.config import init_db, get_db


# from .routes.medias import router as medias_router
# from .routes.posts import router as posts_router
from .routes.users import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application life cycle
    start - initialization of the database
    off - closing the connection with the database
    """
    await init_db()
    yield
    await get_db().close()


def create_app() -> FastAPI:
    """Create FastAPI app function"""

    app = FastAPI(lifespan=lifespan)

    # app.include_router(medias_router)
    # app.include_router(posts_router)
    app.include_router(users_router)

    return app
