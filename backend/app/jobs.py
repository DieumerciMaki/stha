import json
import logging
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import select
from .config import DATA, JOB_MODE, REDIS_URL
from .database import Session, Analysis, now
from . import segmentation

logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=1)

def run_analysis(key):
    with Session.begin() as db:
        row = db.get(Analysis, key)
        if not row or row.status != 'queued':
            return
        row.status = 'running'
        observation_id, confidence = row.observation_id, row.confidence
    try:
        result = segmentation.predict(DATA / 'originals' / f'{observation_id}.jpg', confidence, DATA / 'results' / key)
        with Session.begin() as db:
            row = db.get(Analysis, key)
            row.status, row.finished_at = 'completed', now()
            row.result_json = json.dumps(result, ensure_ascii=False)
    except Exception:
        logger.exception('Analysis failed %s', key)
        with Session.begin() as db:
            row = db.get(Analysis, key)
            row.status, row.finished_at = 'failed', now()
            row.error = 'Le traitement a échoué. Vous pouvez relancer cette analyse ; détails dans le journal du serveur.'

def submit(key):
    if JOB_MODE == 'celery':
        from .worker import analyze_task
        analyze_task.delay(key)
    else:
        executor.submit(run_analysis, key)

def recover():
    if JOB_MODE == 'local':
        with Session.begin() as db:
            for row in db.scalars(select(Analysis).where(Analysis.status == 'running')):
                row.status, row.error = 'failed', 'Analyse interrompue par un arrêt du logiciel. Relancez-la.'
            keys = list(db.scalars(select(Analysis.id).where(Analysis.status == 'queued').order_by(Analysis.created_at)))
        for key in keys:
            submit(key)
