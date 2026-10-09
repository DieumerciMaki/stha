import argparse
import hashlib
import json
import shutil
from pathlib import Path
from ultralytics import YOLO

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description='Activer un modèle YOLO de segmentation entraîné pour le projet.')
parser.add_argument('--weights',type=Path,required=True)
parser.add_argument('--name',required=True)
parser.add_argument('--dataset',required=True)
args=parser.parse_args()
model=YOLO(str(args.weights.resolve()))
if model.task!='segment':parser.error('Modèle de segmentation requis.')
target=root/'models/goma-segmentation.pt'
if args.weights.resolve()!=target.resolve():shutil.copyfile(args.weights,target)
manifest={'name':args.name,'architecture':'YOLO segmentation personnalisée','weights':'models/goma-segmentation.pt',
          'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'revision':'entraînement personnalisé',
          'source':None,'dataset':args.dataset,'class_names':list(model.names.values()),'local_evaluation':None,
          'license_declared_by_author':'À documenter pour le jeu de données et les poids',
          'runtime_license':'Ultralytics AGPL-3.0 ou Enterprise',
          'limitations':'Performances à mesurer sur un jeu de test indépendant. Couverture en pixels uniquement.'}
(root/'models/active.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('Modèle enregistré. Redémarrez le serveur et évaluez la partition test.')
