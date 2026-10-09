import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Request, Response
from sqlalchemy import select
from .database import Session, User, LoginSession, now

COOKIE = 'waste_session'

def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1).hex()
    return salt + ':' + digest

def check_password(password, stored):
    salt, digest = stored.split(':', 1)
    candidate = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1).hex()
    return hmac.compare_digest(candidate, digest)

def public_user(user):
    return {'id': user.id, 'name': user.name, 'login': user.login, 'role': user.role, 'active': user.active}

def current_user(request: Request):
    token = request.cookies.get(COOKIE, '')
    if not token:
        raise HTTPException(401, 'Connectez-vous pour accéder au projet.')
    with Session() as db:
        session = db.get(LoginSession, hashlib.sha256(token.encode()).hexdigest())
        if not session or session.expires_at < now():
            raise HTTPException(401, 'Votre session a expiré. Reconnectez-vous.')
        user = db.get(User, session.user_id)
        if not user or not user.active:
            raise HTTPException(401, 'Compte indisponible.')
        return user

def require_role(user, *roles):
    if user.role not in roles:
        raise HTTPException(403, 'Votre compte ne permet pas cette action.')

def start_session(response: Response, user, secure=False):
    token = secrets.token_urlsafe(48)
    with Session.begin() as db:
        db.add(LoginSession(token_hash=hashlib.sha256(token.encode()).hexdigest(), user_id=user.id,
                            expires_at=(datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()))
        for expired in db.scalars(select(LoginSession).where(LoginSession.expires_at < now())):
            db.delete(expired)
    response.set_cookie(COOKIE, token, httponly=True, samesite='strict', secure=secure, max_age=43200)
