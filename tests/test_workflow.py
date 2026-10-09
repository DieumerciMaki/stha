import io
import time
import numpy as np
from PIL import Image
from app import segmentation

def image_bytes():
    buffer=io.BytesIO()
    Image.new('RGB',(32,32),(140,150,145)).save(buffer,'PNG')
    return buffer.getvalue()

def upload(client, **extra):
    return client.post('/api/observations', data={'title':'Observation test',**extra}, files={'image':('image.png',image_bytes(),'image/png')})

def test_authentication_and_protected_files(client):
    assert client.get('/api/workspace').status_code==401
    assert client.get('/api/status').json()=={'initialized':False}
    setup=client.post('/api/auth/setup',json={'name':'Test','login':'admin','password':'VeryLongPassword2026!'})
    assert setup.status_code==201
    assert 'HttpOnly' in setup.headers['set-cookie'] and 'SameSite=strict' in setup.headers['set-cookie']
    assert client.post('/api/auth/setup',json={'name':'Test','login':'other','password':'VeryLongPassword2026!'}).status_code==409
    row=upload(client).json()
    assert client.get(row['image_url']).status_code==200
    client.post('/api/auth/logout')
    assert client.get(row['image_url']).status_code==401
    assert client.post('/api/auth/login',json={'login':'admin','password':'WrongPassword2026!'}).status_code==401
    assert client.post('/api/auth/login',json={'login':'admin','password':'VeryLongPassword2026!'}).status_code==200

def test_input_validation_and_geojson(admin):
    assert upload(admin,latitude='-1.68').status_code==422
    assert admin.post('/api/observations',data={'title':'Bad'},files={'image':('bad.jpg',b'not an image','image/jpeg')}).status_code==422
    assert admin.post('/api/auth/logout',headers={'Origin':'https://unrelated.example'}).status_code==403
    row=upload(admin,latitude='-1.68',longitude='29.22',neighborhood='Quartier test').json()
    assert row['coordinate_source']=='manual'
    assert row['latitude']==-1.68
    geo=admin.get('/api/export/geojson').json()
    assert geo['features'][0]['geometry']['coordinates']==[29.22,-1.68]
    assert row['original_sha256']!=row['image_sha256']

def test_masks_keep_holes_and_do_not_double_count():
    a=np.zeros((10,10));a[1:9,1:9]=1;a[4:6,4:6]=0
    b=np.zeros((10,10));b[1:3,1:3]=1
    mask=segmentation.mask_union([a,b],10,10)
    assert np.count_nonzero(mask)==60
    assert mask[4,4]==0

def test_complete_workflow_and_roles(admin, monkeypatch):
    def fake(image_path,confidence,output_dir):
        output_dir.mkdir(parents=True,exist_ok=True)
        (output_dir/'mask.png').write_bytes(image_bytes())
        (output_dir/'overlay.jpg').write_bytes(image_bytes())
        (output_dir/'result.json').write_text('{}')
        return {'instances':[],'instance_count':0,'coverage_percent':0,'duration_seconds':.1}
    monkeypatch.setattr(segmentation,'predict',fake)
    row=upload(admin,title='=UnsafeCSVFormula').json()
    assert "'=UnsafeCSVFormula" in admin.get('/api/export/csv').text
    analysis=admin.post('/api/observations/'+row['id']+'/analyses',json={'confidence':.25}).json()
    for _ in range(50):
        result=admin.get('/api/analyses/'+analysis['id']).json()
        if result['status']=='completed':break
        time.sleep(.02)
    assert result['status']=='completed'
    assert admin.get(result['mask_url']).status_code==200
    for decision in ['uncertain','accepted','rejected']:
        assert admin.post('/api/analyses/'+analysis['id']+'/reviews',json={'decision':decision,'comment':'Examen test'}).status_code==201
    reviews=admin.get('/api/analyses/'+analysis['id']).json()['reviews']
    assert len(reviews)==3 and reviews[-1]['decision']=='rejected'
    assert reviews[-1]['reviewer']=='Gestionnaire test'
    exported=admin.get('/api/observations/'+row['id']+'/export').json()
    assert len(exported['analyses'][0]['reviews'])==3
    assert admin.post('/api/users',json={'name':'Agent test','login':'agent-test','password':'AgentPassword2026!','role':'agent'}).status_code==201
    admin.post('/api/auth/logout')
    assert admin.post('/api/auth/login',json={'login':'agent-test','password':'AgentPassword2026!'}).status_code==200
    assert admin.post('/api/analyses/'+analysis['id']+'/reviews',json={'decision':'accepted'}).status_code==403
    assert admin.put('/api/settings',json={'city':'Goma','project_name':'Test','default_confidence':.25}).status_code==403
