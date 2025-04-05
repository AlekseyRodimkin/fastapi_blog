from sqlalchemy import event
from app.models import Tweet
from config.logging_config import logger
from celery import group

app_logger = logger.bind(name="app")


# @event.listens_for(Tweet, "after_delete")
# def trigger(mapper, connection, target):
#     """Trigger for ... """
#     app_logger.debug(f"trigger()")
#
#     query = ...
#     result = connection.execute(query)
#
#     task_group = group(
#         task_name.s(...)
#         for ... in ...
#     )
#
#     result = task_group.apply_async()
#     app_logger.debug(f"Celery task group ID: {result.id}")
