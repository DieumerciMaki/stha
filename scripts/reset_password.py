import argparse
import getpass
import sys
from pathlib import Path
from sqlalchemy import select, delete
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.database import Session,User,LoginSession
from app.auth import hash_password

parser=argparse.ArgumentParser(description='Réinitialiser un mot de passe avec accès au PC et à la base du projet.')
parser.add_argument('--login',required=True)
args=parser.parse_args()
password=getpass.getpass('Nouveau mot de passe (10 caractères minimum) : ')
if len(password)<10:raise SystemExit('Mot de passe trop court.')
if password!=getpass.getpass('Confirmez le nouveau mot de passe : '):raise SystemExit('Les mots de passe diffèrent.')
with Session.begin() as db:
    user=db.scalars(select(User).where(User.login==args.login.strip().lower())).first()
    if not user:raise SystemExit('Compte introuvable.')
    user.password_hash=hash_password(password)
    db.execute(delete(LoginSession).where(LoginSession.user_id==user.id))
print('Mot de passe réinitialisé et sessions invalidées.')
