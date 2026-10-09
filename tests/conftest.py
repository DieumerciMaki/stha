import os
import sys
import tempfile
from pathlib import Path
import pytest

scratch = tempfile.TemporaryDirectory(prefix='waste-project-tests-')
os.environ['DATABASE_URL'] = 'sqlite:///' + (Path(scratch.name) / 'tests.db').as_posix()
os.environ['WASTE_DATA_DIR'] = scratch.name
os.environ['JOB_MODE'] = 'local'
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from app.database import Base, engine
from app.main import app
from fastapi.testclient import TestClient

def pytest_sessionfinish(session, exitstatus):
    from app.jobs import executor
    executor.shutdown(wait=True)
    engine.dispose()
    scratch.cleanup()

@pytest.fixture
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with TestClient(app) as client:
        yield client

@pytest.fixture
def admin(client):
    response = client.post('/api/auth/setup', json={'name':'Gestionnaire test','login':'admin-test','password':'PasswordTest2026!'})
    assert response.status_code == 201
    return client
