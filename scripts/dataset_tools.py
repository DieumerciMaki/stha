import hashlib
from pathlib import Path
import yaml

def resolve_split(data_path, split):
    data_path=Path(data_path).resolve()
    config=yaml.safe_load(data_path.read_text(encoding='utf-8'))
    base=Path(config.get('path',data_path.parent))
    if not base.is_absolute():base=data_path.parent/base
    entry=config.get(split)
    if not isinstance(entry,str):raise ValueError('Chaque partition doit être un dossier d’images.')
    folder=Path(entry)
    if not folder.is_absolute():folder=base/folder
    return folder.resolve()

def check_dataset(data_path):
    seen={};files={}
    for split in ('train','val','test'):
        folder=resolve_split(data_path,split)
        images=sorted(x for x in folder.rglob('*') if x.suffix.lower() in ('.jpg','.jpeg','.png','.webp'))
        if not images:raise ValueError('Partition vide : '+split)
        for image in images:
            digest=hashlib.sha256(image.read_bytes()).hexdigest()
            if digest in seen:raise ValueError('Image identique dans plusieurs entrées ou partitions : '+str(image))
            seen[digest]=split
            parts=list(image.parts)
            if 'images' not in parts:raise ValueError('Dossiers images/labels requis.')
            parts[len(parts)-1-parts[::-1].index('images')]='labels'
            label=Path(*parts).with_suffix('.txt')
            if not label.exists():raise ValueError('Annotation manquante : '+str(label))
            for line in label.read_text().splitlines():
                values=line.split()
                if len(values)<7 or (len(values)-1)%2:raise ValueError('Polygone de segmentation invalide : '+str(label))
                if any(not 0<=float(x)<=1 for x in values[1:]):raise ValueError('Coordonnée non normalisée : '+str(label))
        files[split]=images
    return files

def split_digest(images):
    digest=hashlib.sha256()
    for image in images:
        parts=list(image.parts);parts[len(parts)-1-parts[::-1].index('images')]='labels'
        label=Path(*parts).with_suffix('.txt')
        digest.update(hashlib.sha256(image.read_bytes()).digest())
        digest.update(label.read_bytes())
    return digest.hexdigest()
