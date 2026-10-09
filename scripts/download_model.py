import hashlib
import json
import urllib.request
from pathlib import Path

root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'models/active.json').read_text(encoding='utf-8'))
path=root/manifest['weights']
if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=manifest['sha256']:
    temp=path.with_suffix('.download')
    urllib.request.urlretrieve(manifest['source']+'/resolve/'+manifest['revision']+'/best.pt',temp)
    if hashlib.sha256(temp.read_bytes()).hexdigest()!=manifest['sha256']:
        temp.unlink(missing_ok=True)
        raise SystemExit('Empreinte du téléchargement incorrecte.')
    temp.replace(path)
for i in range(3):
    sample=root/'samples'/f'example_{i}.jpg'
    if not sample.exists():
        urllib.request.urlretrieve(f'https://raw.githubusercontent.com/CatSatOK/litter-detection-yolov11/main/example_{i}.jpg',sample)
print('Modèle et exemples prêts.')
