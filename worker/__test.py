import asyncio
from celery import Celery

# celery_pool_asyncio importing is optional
# It imports when you run worker or beat if you define pool or scheduler
# but it does not imports when you open REPL or when you run web application.
# If you want to apply monkey patches anyway to make identical environment
# when you use REPL or run web application app it's good idea to import
# celery_pool_asyncio module
import celery_pool_asyncio  # noqa
# Sometimes noqa does not disable linter (Spyder IDE)
celery_pool_asyncio.__package__


app = Celery('__test__1', broker='redis://localhost', backend='redis://localhost')


@app.task(
    bind=True,
    soft_time_limit=42,  # raises celery.exceptions.SoftTimeLimitExceeded inside the coroutine
    time_limit=300,  # breaks coroutine execution
)
async def my_task(self, *args, **kwargs):
    await asyncio.sleep(5)
    return 2


@app.task
async def my_simple_task(*args, **kwargs):
    await asyncio.sleep(5)


async def main():
    promise = await my_task.delay()
    print(promise, type(promise))
    print(await promise.get())

if __name__ == '__main__':
    asyncio.run(main())
