import argparse
from pathlib import Path
from ultralytics import YOLO
from dataset_tools import check_dataset

parser=argparse.ArgumentParser(description='Entraînement reproductible sur des images annotées de déchets.')
parser.add_argument('--data',type=Path,required=True)
parser.add_argument('--weights',default=str(Path(__file__).resolve().parents[1]/'models/waste-yolo11s-seg.pt'))
parser.add_argument('--epochs',type=int,default=50)
parser.add_argument('--device',default='cpu')
args=parser.parse_args()
check_dataset(args.data)
model=YOLO(args.weights)
if model.task!='segment':parser.error('Modèle de segmentation requis.')
model.train(data=str(args.data.resolve()),epochs=args.epochs,imgsz=960,batch=2,device=args.device,seed=42,deterministic=True,
            project=str(Path(__file__).resolve().parents[1]/'runs'),name='goma-segmentation')
