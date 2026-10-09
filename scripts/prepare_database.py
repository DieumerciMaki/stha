"""Create/start a project-owned PostgreSQL cluster, never alter another cluster."""
import json
import os
import secrets
import subprocess
from pathlib import Path
import psycopg
from psycopg import sql

root = Path(__file__).resolve().parents[1]
runtime = root / 'runtime'
runtime.mkdir(exist_ok=True)
cluster = runtime / 'postgres'
credentials_path = runtime / 'database-credentials.json'
if credentials_path.exists():
    credentials = json.loads(credentials_path.read_text())
    pg = Path(credentials['pg_bin'])
else:
    candidates = list(Path('C:/Program Files/PostgreSQL').glob('*/bin/pg_ctl.exe'))
    if not candidates:
        raise SystemExit('Installez PostgreSQL pour utiliser le lancement Windows, ou utilisez Docker Compose. Consultez le guide.')
    pg = sorted(candidates, reverse=True)[0].parent
    credentials = {'admin_password':secrets.token_hex(24), 'app_password':secrets.token_hex(24), 'pg_bin':str(pg)}
    credentials_path.write_text(json.dumps(credentials), encoding='utf-8')
if not (cluster / 'PG_VERSION').exists():
    password_file = runtime / 'init-password.tmp'
    password_file.write_text(credentials['admin_password'])
    try:
        subprocess.run([str(pg / 'initdb.exe'), '-D', str(cluster), '--username=waste_admin', '--pwfile='+str(password_file),
                        '--auth=scram-sha-256', '--encoding=UTF8', '--locale=C'], check=True)
    finally:
        password_file.unlink(missing_ok=True)
status = subprocess.run([str(pg / 'pg_ctl.exe'), '-D', str(cluster), 'status'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
if status.returncode:
    with (runtime / 'pg-launch.log').open('a') as log:
        subprocess.run([str(pg / 'pg_ctl.exe'), '-D', str(cluster), '-l', str(runtime / 'postgres.log'),
                        '-o', '-p 5433 -h 127.0.0.1', '-w', 'start'], stdout=log, stderr=log, check=True)
with psycopg.connect(host='127.0.0.1', port=5433, user='waste_admin', password=credentials['admin_password'], dbname='postgres', autocommit=True) as db:
    if not db.execute("SELECT 1 FROM pg_roles WHERE rolname='waste_app'").fetchone():
        db.execute(sql.SQL('CREATE ROLE waste_app LOGIN PASSWORD {}').format(sql.Literal(credentials['app_password'])))
    if not db.execute("SELECT 1 FROM pg_database WHERE datname='waste_project'").fetchone():
        db.execute('CREATE DATABASE waste_project OWNER waste_app')
env_file = root / '.env'
if not env_file.exists():
    env_file.write_text('DATABASE_URL=postgresql+psycopg://waste_app:'+credentials['app_password']+'@127.0.0.1:5433/waste_project\nJOB_MODE=local\n', encoding='utf-8')
print('PostgreSQL du projet prêt sur le port 5433.')
