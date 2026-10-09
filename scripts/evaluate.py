import argparse
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path
from ultralytics import YOLO
from dataset_tools import check_dataset,split_digest

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description='Évaluer les masques sur la partition test indépendante.')
parser.add_argument('--data',type=Path,required=True)
parser.add_argument('--weights',type=Path,default=root/'models/waste-yolo11s-seg.pt')
parser.add_argument('--device',default='cpu')
args=parser.parse_args()
partitions=check_dataset(args.data)
model=YOLO(str(args.weights.resolve()))
if model.task!='segment':parser.error('Modèle de segmentation requis.')
metrics=model.val(data=str(args.data.resolve()),split='test',device=args.device,imgsz=960,project=str(root/'runs'),name='evaluation-test')
report={'mask_map50':float(metrics.seg.map50),'mask_map50_95':float(metrics.seg.map),
        'model_sha256':hashlib.sha256(args.weights.read_bytes()).hexdigest(),
        'dataset_sha256':split_digest(partitions['test']),'test_images':len(partitions['test']),
        'split':'test','evaluated_at':datetime.now(timezone.utc).isoformat(),'metrics':metrics.results_dict,
        'dataset_yaml':str(args.data.resolve())}
(Path(metrics.save_dir)/'evaluation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(root/'models/evaluation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('Évaluation enregistrée dans',metrics.save_dir)
