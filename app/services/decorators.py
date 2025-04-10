import inspect
from functools import wraps

from fastapi import HTTPException

from config.logging_config import logger

app_logger = logger.bind(name="app")


def exception_handler():
    """Main route decorator"""

    def decorator(func):
        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except HTTPException as http_ex:
                    app_logger.error(f"Error HTTP: {http_ex.detail}")
                    raise http_ex
                except Exception as e:
                    app_logger.error(f"Unhandled error: {str(e)}")
                    db = kwargs.get("db") or next(
                        (arg for arg in args if hasattr(arg, "rollback")), None
                    )  # rollback
                    if db:
                        await db.rollback()
                    raise HTTPException(
                        status_code=500,
                        detail={
                            "result": False,
                            "error_type": 500,
                            "error_message": "Internal server error",
                        },
                    )

            return wrapper
        else:
            raise TypeError("This decorator only supports async functions")

    return decorator
