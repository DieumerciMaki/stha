import json
import os
import subprocess
import sys
from pathlib import Path
import pytest
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from dataset_tools import check_dataset

def test_initial_alembic_migration(tmp_path):
    project=Path(__file__).resolve().parents[1]
    database=tmp_path/'migration.db'
    subprocess.run([sys.executable,'-m','alembic','-c',str(project/'backend/alembic.ini'),'upgrade','head'],
                   env={**os.environ,'DATABASE_URL':'sqlite:///'+database.as_posix()},check=True,capture_output=True)
    import sqlite3
    with sqlite3.connect(database) as db:
        assert db.execute('SELECT version_num FROM alembic_version').fetchone()[0]=='0001'
        assert db.execute("SELECT name FROM sqlite_master WHERE name='reviews'").fetchone()

def test_cvat_polygon_conversion_and_duplicate_guard(tmp_path):
    images=tmp_path/'images';images.mkdir()
    records=[];annotations=[]
    for i in range(10):
        Image.new('RGB',(40,40),(10*i,100,150)).save(images/f'{i}.png')
        records.append({'id':i,'file_name':f'{i}.png','width':40,'height':40})
        annotations.append({'id':i,'image_id':i,'category_id':1,'segmentation':[[4,4,32,4,32,32,4,32]],'iscrowd':0})
    source=tmp_path/'annotations.json'
    source.write_text(json.dumps({'images':records,'annotations':annotations,'categories':[{'id':1,'name':'dechets'}]}))
    output=tmp_path/'dataset'
    command=[sys.executable,str(Path(__file__).resolve().parents[1]/'scripts/convert_coco.py'),'--annotations',str(source),'--images',str(images),'--output',str(output)]
    subprocess.run(command,check=True,capture_output=True)
    partitions=check_dataset(output/'dataset.yaml')
    assert {k:len(v) for k,v in partitions.items()}=={'train':7,'val':1,'test':2}
    assert (output/'labels/train/7.txt').exists()
    partitions['val'][0].write_bytes(partitions['train'][0].read_bytes())
    with pytest.raises(ValueError,match='identique'):
        check_dataset(output/'dataset.yaml')
