import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / '.env')
DATA = Path(os.getenv('WASTE_DATA_DIR', str(ROOT / 'data'))).resolve()
DATABASE_URL = os.getenv('DATABASE_URL', f"sqlite:///{(DATA / 'test.db').as_posix()}")
MODEL_MANIFEST = ROOT / 'models' / 'active.json'
JOB_MODE = os.getenv('JOB_MODE', 'local')
REDIS_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')
MAX_BYTES = 15 * 1024 * 1024
MAX_PIXELS = 20_000_000
for path in (DATA, DATA / 'originals', DATA / 'results'):
    path.mkdir(parents=True, exist_ok=True)
