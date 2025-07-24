"""
Celery worker configuration for background tasks
"""
from celery import Celery
from .core.config import settings

# Create Celery app
celery_app = Celery(
    'evaluator',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['src.services.evaluation']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    result_expires=3600,
    task_track_started=True,
    task_time_limit=settings.MAX_EVALUATION_TIME,
    task_soft_time_limit=settings.MAX_EVALUATION_TIME - 60,
)

# Export celery app for the worker command
app = celery_app

# Import tasks to register them
from . import tasks  # noqa