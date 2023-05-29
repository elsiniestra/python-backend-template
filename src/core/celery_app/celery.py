import celery

from src.core.config.config import RedisSettings

redis_url = RedisSettings().connection_url

app = celery.Celery("tasks", broker=redis_url, backend=redis_url, include=["celery_app.tasks"])


app.conf.update(worker_prefetch_multiplier=1, task_remote_tracebacks=True)

if __name__ == "__main__":
    app.start()
