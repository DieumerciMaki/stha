import json
import os
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path

root=Path(__file__).resolve().parents[1]
runtime=root/'runtime'
credentials=json.loads((runtime/'database-credentials.json').read_text())
backup=root/'backups'/datetime.now().strftime('%Y%m%d-%H%M%S')
backup.mkdir(parents=True,exist_ok=False)
env={**os.environ,'PGPASSWORD':credentials['app_password']}
subprocess.run([str(Path(credentials['pg_bin'])/'pg_dump.exe'),'-h','127.0.0.1','-p','5433','-U','waste_app','-d','waste_project','-Fc','-f',str(backup/'database.dump')],env=env,check=True)
with zipfile.ZipFile(backup/'files.zip','w',zipfile.ZIP_DEFLATED) as z:
    for folder in ('data','models','samples'):
        for file in (root/folder).rglob('*'):
            if file.is_file():z.write(file,file.relative_to(root))
print('Sauvegarde créée dans',backup)
