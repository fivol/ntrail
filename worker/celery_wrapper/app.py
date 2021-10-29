from celery import Celery

# import celery_pool_asyncio # noqa
# celery_pool_asyncio.__package__ # noqa

app = Celery('tasks', broker='redis://localhost', backend='redis://localhost')
