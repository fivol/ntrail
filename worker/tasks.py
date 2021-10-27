from celery import Celery
from time import sleep

app = Celery('tasks', broker='redis://localhost', backend='redis://localhost')


@app.task
def add(x, y):
    sleep(0.2)
    return x + y
