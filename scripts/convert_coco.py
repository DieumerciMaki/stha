"""Convert a CVAT COCO polygon export into YOLO segmentation train/val/test."""
import argparse
import json
import random
import shutil
from pathlib import Path
import yaml

parser=argparse.ArgumentParser(description='Convertir les polygones COCO de CVAT vers YOLO segmentation.')
parser.add_argument('--annotations',type=Path,required=True)
parser.add_argument('--images',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--seed',type=int,default=42)
args=parser.parse_args()
if args.output.exists() and any(args.output.iterdir()):parser.error('Le dossier de sortie doit être vide pour conserver les partitions existantes.')
data=json.loads(args.annotations.read_text(encoding='utf-8'))
images=list(data['images']);random.Random(args.seed).shuffle(images)
if len(images)<10:parser.error('Au moins dix images sont nécessaires pour trois partitions non vides.')
categories={x['id']:i for i,x in enumerate(sorted(data['categories'],key=lambda x:x['id']))}
names=[x['name'] for x in sorted(data['categories'],key=lambda x:x['id'])]
annotations={}
for annotation in data['annotations']:
    if not isinstance(annotation.get('segmentation'),list):parser.error('Annotations polygonales requises ; les masques RLE ne sont pas pris en charge par ce convertisseur.')
    annotations.setdefault(annotation['image_id'],[]).append(annotation)
splits={'train':images[:int(len(images)*.7)],'val':images[int(len(images)*.7):int(len(images)*.85)],'test':images[int(len(images)*.85):]}
image_root=args.images.resolve()
for split,items in splits.items():
    for folder in ('images','labels'):(args.output/folder/split).mkdir(parents=True,exist_ok=True)
    for image in items:
        source=(image_root/image['file_name']).resolve()
        if not source.is_relative_to(image_root) or not source.is_file():parser.error('Image manquante ou chemin hors du dossier autorisé : '+image['file_name'])
        dest=args.output/'images'/split/(str(image['id'])+source.suffix.lower());shutil.copyfile(source,dest)
        lines=[]
        for annotation in annotations.get(image['id'],[]):
            for polygon in annotation['segmentation']:
                if len(polygon)<6:continue
                coordinates=[float(value)/(image['width'] if i%2==0 else image['height']) for i,value in enumerate(polygon)]
                lines.append(str(categories[annotation['category_id']])+' '+' '.join(f'{min(1,max(0,v)):.8f}' for v in coordinates))
        (args.output/'labels'/split/(str(image['id'])+'.txt')).write_text('\n'.join(lines),encoding='utf-8')
config={'path':str(args.output.resolve()),'train':'images/train','val':'images/val','test':'images/test','names':dict(enumerate(names))}
(args.output/'dataset.yaml').write_text(yaml.safe_dump(config,allow_unicode=True,sort_keys=False),encoding='utf-8')
print('Dataset converti. Contrôlez les polygones et séparez les images proches du même site avant l’entraînement.')
