import celery

from src.core.config.config import RedisSettings

redis_url = RedisSettings().connection_url

celery_app = celery.Celery("tasks", broker=redis_url, backend=redis_url)


celery_app.conf.update(
    worker_prefetch_multiplier=1, task_remote_tracebacks=True, broker_connection_retry_on_startup=True
)

if __name__ == "__main__":
    celery_app.start()
