from celery import shared_task
from dronesim.celery import app

@app.task
def add(x, y):
    print("######### Task beendet...")
    return x + y
