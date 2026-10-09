from celery import Celery
from .config import REDIS_URL
from .jobs import run_analysis

celery = Celery('waste', broker=REDIS_URL)
celery.conf.update(task_acks_late=True, worker_prefetch_multiplier=1, task_reject_on_worker_lost=True,
                   broker_connection_retry_on_startup=True)

@celery.task(name='waste.analyze')
def analyze_task(key):
    run_analysis(key)
