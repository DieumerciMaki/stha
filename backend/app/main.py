import csv
import hashlib
import io
import json
import logging
import threading
import time
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import date
from urllib.parse import urlsplit
from PIL import Image, ImageOps, UnidentifiedImageError
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from .config import ROOT, DATA, MAX_BYTES, MAX_PIXELS, JOB_MODE
from .database import Session, User, LoginSession, Observation, Analysis, Review, Setting, engine, now
from .auth import current_user, public_user, require_role, hash_password, check_password, start_session, COOKIE
from . import segmentation, jobs

logger = logging.getLogger(__name__)
mutation_lock = threading.Lock()
attempts = defaultdict(list)

@asynccontextmanager
async def lifespan(app):
    # Schema is installed by Alembic before the server starts.
    with Session() as db:
        db.execute(select(Setting).limit(1))
    jobs.recover()
    yield

app = FastAPI(title='Déchets urbains', version='1.0.0', lifespan=lifespan)

@app.middleware('http')
async def browser_security(request, call_next):
    if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
        origin = request.headers.get('origin')
        if origin:
            parsed = urlsplit(origin)
            allowed = parsed.netloc == request.headers.get('host') or (parsed.hostname in ('127.0.0.1', 'localhost') and parsed.port == 5173 and request.url.hostname in ('127.0.0.1', 'localhost'))
            if not allowed:
                return JSONResponse({'detail': 'Origine de la demande non autorisée.'}, status_code=403)
        if request.headers.get('sec-fetch-site') == 'cross-site':
            return JSONResponse({'detail': 'Origine de la demande non autorisée.'}, status_code=403)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'same-origin'
    response.headers['X-Frame-Options'] = 'DENY'
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    return response

def require(db, kind, key):
    row = db.get(kind, key)
    if not row:
        raise HTTPException(404, 'Élément introuvable.')
    return row

def review_dict(db, row):
    reviewer = db.get(User, row.reviewed_by)
    return {'id': row.id, 'decision': row.decision, 'comment': row.comment, 'created_at': row.created_at,
            'reviewer': reviewer.name if reviewer else 'Compte indisponible'}

def analysis_dict(db, row, reviews=None):
    result = json.loads(row.result_json) if row.result_json else None
    if reviews is None:
        reviews = [review_dict(db, x) for x in db.scalars(select(Review).where(Review.analysis_id == row.id).order_by(Review.id))]
    return {'id': row.id, 'observation_id': row.observation_id, 'status': row.status, 'created_at': row.created_at,
            'finished_at': row.finished_at, 'confidence': row.confidence, 'error': row.error, 'result': result,
            'reviews': reviews, 'latest_review': reviews[-1] if reviews else None,
            'overlay_url': f'/api/analyses/{row.id}/files/overlay' if result else None,
            'mask_url': f'/api/analyses/{row.id}/files/mask' if result else None}

def observation_dict(db, row, analyses=None):
    if analyses is None:
        analyses = [analysis_dict(db, x) for x in db.scalars(select(Analysis).where(Analysis.observation_id == row.id).order_by(Analysis.created_at.desc()))]
    fields = ('id', 'title', 'neighborhood', 'location', 'notes', 'latitude', 'longitude', 'coordinate_source',
              'captured_at', 'created_at', 'width', 'height', 'image_sha256', 'original_sha256')
    return {**{key: getattr(row, key) for key in fields}, 'image_url': f'/api/observations/{row.id}/image',
            'latest_analysis': analyses[0] if analyses else None, 'analyses': analyses}

def settings_dict(db):
    values = {x.key: x.value for x in db.scalars(select(Setting))}
    return {'city': values.get('city', 'Goma'), 'project_name': values.get('project_name', 'Déchets urbains'),
            'default_confidence': float(values.get('default_confidence', '0.25'))}

@app.get('/api/status')
def status():
    with Session() as db:
        return {'initialized': db.scalars(select(User.id).limit(1)).first() is not None}

@app.get('/api/health')
def health():
    with Session() as db:
        db.execute(text('SELECT 1'))
    return {'status': 'ok', 'version': app.version, 'database': engine.dialect.name,
            'jobs': JOB_MODE, 'model': segmentation.model_status()}

class Credentials(BaseModel):
    login: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=10, max_length=200)

class SetupRequest(Credentials):
    name: str = Field(min_length=2, max_length=120)

@app.post('/api/auth/setup', status_code=201)
def setup(body: SetupRequest, response: Response, request: Request):
    if not body.name.strip() or not body.login.strip():
        raise HTTPException(422, 'Renseignez votre nom et votre identifiant.')
    with mutation_lock, Session.begin() as db:
        if engine.dialect.name == 'postgresql':
            db.execute(text('SELECT pg_advisory_xact_lock(67482011)'))
        if db.scalars(select(User.id).limit(1)).first():
            raise HTTPException(409, 'Le projet est déjà configuré. Connectez-vous.')
        user = User(id=str(uuid.uuid4()), name=body.name.strip(), login=body.login.strip().lower(),
                    password_hash=hash_password(body.password), role='admin')
        db.add(user)
    start_session(response, user, request.url.scheme == 'https')
    return public_user(user)

@app.post('/api/auth/login')
def login(body: Credentials, response: Response, request: Request):
    key = request.client.host if request.client else 'local'
    moment = time.monotonic()
    attempts[key] = [x for x in attempts[key] if moment - x < 300]
    if len(attempts[key]) >= 10:
        raise HTTPException(429, 'Trop de tentatives. Réessayez dans cinq minutes.')
    attempts[key].append(moment)
    with Session() as db:
        user = db.scalars(select(User).where(User.login == body.login.strip().lower())).first()
        if not user or not user.active or not check_password(body.password, user.password_hash):
            raise HTTPException(401, 'Identifiant ou mot de passe incorrect.')
    attempts[key] = []
    start_session(response, user, request.url.scheme == 'https')
    return public_user(user)

@app.get('/api/auth/me')
def me(user=Depends(current_user)):
    return public_user(user)

@app.post('/api/auth/logout')
def logout(request: Request, response: Response, user=Depends(current_user)):
    token = request.cookies.get(COOKIE, '')
    with Session.begin() as db:
        session = db.get(LoginSession, hashlib.sha256(token.encode()).hexdigest())
        if session:
            db.delete(session)
    response.delete_cookie(COOKIE)
    return {'saved': True}

@app.get('/api/workspace')
def workspace(user=Depends(current_user)):
    with Session() as db:
        reviews = defaultdict(list)
        people = {x.id: x.name for x in db.scalars(select(User))}
        for row in db.scalars(select(Review).order_by(Review.id)):
            reviews[row.analysis_id].append({'id': row.id, 'decision': row.decision, 'comment': row.comment,
                                             'created_at': row.created_at, 'reviewer': people.get(row.reviewed_by, '')})
        analyses = defaultdict(list)
        for row in db.scalars(select(Analysis).order_by(Analysis.created_at.desc())):
            analyses[row.observation_id].append(analysis_dict(db, row, reviews[row.id]))
        observations = [observation_dict(db, x, analyses[x.id]) for x in db.scalars(select(Observation).order_by(Observation.created_at.desc()))]
        return {'observations': observations, 'settings': settings_dict(db), 'model': segmentation.model_status()}

def exif_coordinates(source):
    try:
        gps = source.getexif().get_ifd(34853)
        def decimal(parts):
            return float(parts[0]) + float(parts[1]) / 60 + float(parts[2]) / 3600
        lat, lon = decimal(gps[2]), decimal(gps[4])
        if gps[1] == 'S': lat = -lat
        if gps[3] == 'W': lon = -lon
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return lat, lon
    except (KeyError, TypeError, ValueError, ZeroDivisionError, AttributeError):
        pass
    return None

@app.post('/api/observations', status_code=201)
async def create_observation(image: UploadFile = File(...), title: str = Form(..., min_length=1, max_length=120),
    neighborhood: str = Form('', max_length=120), location: str = Form('', max_length=160), notes: str = Form('', max_length=4000),
    latitude: float | None = Form(None, ge=-90, le=90), longitude: float | None = Form(None, ge=-180, le=180),
    captured_at: date | None = Form(None), user=Depends(current_user)):
    require_role(user, 'admin', 'agent')
    if not title.strip():
        raise HTTPException(422, 'Le titre est obligatoire.')
    if (latitude is None) != (longitude is None):
        raise HTTPException(422, 'Renseignez ensemble latitude et longitude.')
    raw = await image.read(MAX_BYTES + 1)
    await image.close()
    if len(raw) > MAX_BYTES:
        raise HTTPException(413, 'Image trop volumineuse : maximum 15 Mo.')
    coordinate_source = 'manual' if latitude is not None else None
    try:
        with Image.open(io.BytesIO(raw)) as source:
            if source.format not in ('JPEG', 'PNG', 'WEBP') or source.width * source.height > MAX_PIXELS:
                raise HTTPException(422, 'Utilisez une image JPEG, PNG ou WebP de moins de 20 millions de pixels.')
            if latitude is None:
                gps = exif_coordinates(source)
                if gps:
                    latitude, longitude = gps
                    coordinate_source = 'exif'
            normalized = ImageOps.exif_transpose(source).convert('RGB')
            normalized.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, ValueError):
        raise HTTPException(422, 'Le fichier ne contient pas une image valide.')
    key = str(uuid.uuid4())
    path = DATA / 'originals' / f'{key}.jpg'
    original = DATA / 'originals' / f'{key}.source'
    normalized.save(path, 'JPEG', quality=95)
    original.write_bytes(raw)
    row = Observation(id=key, title=title.strip(), neighborhood=neighborhood.strip(), location=location.strip(),
                      notes=notes.strip(), latitude=latitude, longitude=longitude, coordinate_source=coordinate_source,
                      captured_at=captured_at.isoformat() if captured_at else None, created_by=user.id,
                      width=normalized.width, height=normalized.height,
                      image_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), original_sha256=hashlib.sha256(raw).hexdigest())
    try:
        with Session.begin() as db:
            db.add(row)
            db.flush()
            value = observation_dict(db, row)
    except Exception:
        path.unlink(missing_ok=True)
        original.unlink(missing_ok=True)
        raise
    return value

@app.get('/api/observations/{key}')
def observation(key: str, user=Depends(current_user)):
    with Session() as db:
        return observation_dict(db, require(db, Observation, key))

@app.get('/api/observations/{key}/image')
def image_file(key: str, user=Depends(current_user)):
    with Session() as db:
        require(db, Observation, key)
    return FileResponse(DATA / 'originals' / f'{key}.jpg', media_type='image/jpeg')

class AnalysisRequest(BaseModel):
    confidence: float = Field(default=.25, ge=.05, le=.95)

@app.post('/api/observations/{key}/analyses', status_code=202)
def analyze(key: str, body: AnalysisRequest, user=Depends(current_user)):
    require_role(user, 'admin', 'agent')
    if not segmentation.model_status()['configured']:
        raise HTTPException(409, 'Le modèle est indisponible.')
    with mutation_lock, Session.begin() as db:
        require(db, Observation, key)
        if engine.dialect.name == 'postgresql':
            db.execute(text('SELECT pg_advisory_xact_lock(67482012)'))
        pending = list(db.scalars(select(Analysis).where(Analysis.status.in_(['queued', 'running']))))
        if any(x.observation_id == key for x in pending):
            raise HTTPException(409, 'Cette observation possède déjà une analyse en cours.')
        if len(pending) >= 20:
            raise HTTPException(409, 'La file contient vingt analyses. Attendez la fin des traitements.')
        row = Analysis(id=str(uuid.uuid4()), observation_id=key, confidence=body.confidence, created_by=user.id)
        db.add(row)
        db.flush()
        value = analysis_dict(db, row)
    try:
        jobs.submit(row.id)
    except Exception:
        with Session.begin() as db:
            failed = db.get(Analysis, row.id)
            failed.status, failed.error = 'failed', 'Le service de traitement est indisponible. Relancez l’analyse.'
        raise HTTPException(503, 'Le service de traitement est indisponible.')
    return value

@app.get('/api/analyses/{key}')
def analysis(key: str, user=Depends(current_user)):
    with Session() as db:
        return analysis_dict(db, require(db, Analysis, key))

@app.get('/api/analyses/{key}/files/{kind}')
def result_file(key: str, kind: str, user=Depends(current_user)):
    if kind not in ('mask', 'overlay', 'json'):
        raise HTTPException(404)
    with Session() as db:
        if require(db, Analysis, key).status != 'completed':
            raise HTTPException(409, 'Analyse non terminée.')
    name = {'mask': 'mask.png', 'overlay': 'overlay.jpg', 'json': 'result.json'}[kind]
    return FileResponse(DATA / 'results' / key / name, filename=f'{key}-{name}' if kind != 'overlay' else None)

class ReviewRequest(BaseModel):
    decision: str = Field(pattern='^(accepted|rejected|uncertain)$')
    comment: str = Field(default='', max_length=4000)

@app.post('/api/analyses/{key}/reviews', status_code=201)
def review(key: str, body: ReviewRequest, user=Depends(current_user)):
    require_role(user, 'admin', 'reviewer')
    with Session.begin() as db:
        if require(db, Analysis, key).status != 'completed':
            raise HTTPException(409, 'Analyse non terminée.')
        db.add(Review(analysis_id=key, decision=body.decision, comment=body.comment.strip(), reviewed_by=user.id))
    return {'saved': True}

@app.get('/api/observations/{key}/export')
def export_observation(key: str, user=Depends(current_user)):
    with Session() as db:
        value = observation_dict(db, require(db, Observation, key))
    return JSONResponse(value, headers={'Content-Disposition': f'attachment; filename="observation-{key}.json"'})

@app.get('/api/export/{kind}')
def export_all(kind: str, user=Depends(current_user)):
    with Session() as db:
        rows = [observation_dict(db, x) for x in db.scalars(select(Observation).order_by(Observation.created_at.desc()))]
    if kind == 'geojson':
        features = [{'type': 'Feature', 'id': x['id'], 'geometry': {'type': 'Point', 'coordinates': [x['longitude'], x['latitude']]},
                     'properties': {'title': x['title'], 'neighborhood': x['neighborhood'], 'coordinate_source': x['coordinate_source']}}
                    for x in rows if x['latitude'] is not None]
        return JSONResponse({'type': 'FeatureCollection', 'features': features}, headers={'Content-Disposition': 'attachment; filename="observations.geojson"'})
    if kind != 'csv':
        raise HTTPException(404)
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=';')
    writer.writerow(['Référence', 'Titre', 'Quartier', 'Lieu', 'Date ajout', 'Date capture', 'Latitude', 'Longitude', 'Analyse', 'Instances', 'Couverture pixels %', 'Vérification'])
    def safe(value):
        return "'" + value if isinstance(value, str) and value.startswith(('=', '+', '-', '@', '\t', '\r')) else value
    for row in rows:
        analysis = row['latest_analysis'] or {}
        result = analysis.get('result') or {}
        review = analysis.get('latest_review') or {}
        writer.writerow([safe(x) for x in [row['id'], row['title'], row['neighborhood'], row['location'], row['created_at'], row['captured_at'], row['latitude'], row['longitude'], analysis.get('status', ''), result.get('instance_count', ''), result.get('coverage_percent', ''), review.get('decision', '')]])
    return Response('\ufeff' + buffer.getvalue(), media_type='text/csv; charset=utf-8', headers={'Content-Disposition': 'attachment; filename="observations.csv"'})

@app.get('/api/settings')
def get_settings(user=Depends(current_user)):
    with Session() as db:
        return settings_dict(db)

class SettingsRequest(BaseModel):
    city: str = Field(min_length=2, max_length=120)
    project_name: str = Field(min_length=2, max_length=120)
    default_confidence: float = Field(ge=.05, le=.95)

@app.put('/api/settings')
def update_settings(body: SettingsRequest, user=Depends(current_user)):
    require_role(user, 'admin')
    if not body.city.strip() or not body.project_name.strip():
        raise HTTPException(422, 'Renseignez le nom du projet et la ville.')
    with Session.begin() as db:
        for key, value in body.model_dump().items():
            db.merge(Setting(key=key, value=str(value).strip()))
    return {'saved': True}

class PasswordRequest(BaseModel):
    current_password: str = Field(max_length=200)
    new_password: str = Field(min_length=10, max_length=200)

@app.put('/api/auth/password')
def password(body: PasswordRequest, request: Request, user=Depends(current_user)):
    if not check_password(body.current_password, user.password_hash):
        raise HTTPException(422, 'Le mot de passe actuel est incorrect.')
    token_hash = hashlib.sha256(request.cookies[COOKIE].encode()).hexdigest()
    with Session.begin() as db:
        row = require(db, User, user.id)
        row.password_hash = hash_password(body.new_password)
        for session in db.scalars(select(LoginSession).where(LoginSession.user_id == user.id, LoginSession.token_hash != token_hash)):
            db.delete(session)
    return {'saved': True}

@app.get('/api/users')
def users(user=Depends(current_user)):
    require_role(user, 'admin')
    with Session() as db:
        return [public_user(x) for x in db.scalars(select(User).order_by(User.created_at))]

class UserRequest(SetupRequest):
    role: str = Field(pattern='^(admin|agent|reviewer)$')

@app.post('/api/users', status_code=201)
def create_user(body: UserRequest, user=Depends(current_user)):
    require_role(user, 'admin')
    with mutation_lock, Session.begin() as db:
        if db.scalars(select(User).where(User.login == body.login.strip().lower())).first():
            raise HTTPException(409, 'Cet identifiant existe déjà.')
        if not body.name.strip() or not body.login.strip():
            raise HTTPException(422, 'Renseignez le nom et l’identifiant.')
        row = User(id=str(uuid.uuid4()), name=body.name.strip(), login=body.login.strip().lower(), password_hash=hash_password(body.password), role=body.role)
        db.add(row)
        db.flush()
        return public_user(row)

@app.get('/api/samples')
def samples(user=Depends(current_user)):
    manifest = ROOT / 'samples' / 'manifest.json'
    return json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else []

@app.get('/api/samples/{key}')
def sample_file(key: str, user=Depends(current_user)):
    if key not in ('example_0', 'example_1', 'example_2') or not (ROOT / 'samples' / f'{key}.jpg').is_file():
        raise HTTPException(404)
    return FileResponse(ROOT / 'samples' / f'{key}.jpg', media_type='image/jpeg', filename=f'{key}.jpg')

frontend = ROOT / 'frontend' / 'dist'
if frontend.exists():
    app.mount('/assets', StaticFiles(directory=frontend / 'assets'), name='assets')

@app.get('/{path:path}')
def spa(path: str):
    if path.startswith('api/'):
        raise HTTPException(404, 'Route introuvable.')
    return FileResponse(frontend / 'index.html')
