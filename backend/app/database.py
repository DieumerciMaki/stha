from datetime import datetime, timezone
from sqlalchemy import create_engine, event, String, Text, Float, Integer, ForeignKey, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from .config import DATABASE_URL

def now():
    return datetime.now(timezone.utc).isoformat()

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {})
if DATABASE_URL.startswith('sqlite'):
    @event.listens_for(engine, 'connect')
    def sqlite_foreign_keys(connection, _):
        connection.execute('PRAGMA foreign_keys=ON')
Session = sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    login: Mapped[str] = mapped_column(String(120), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(24), default='agent')
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[str] = mapped_column(String(40), default=now)

class LoginSession(Base):
    __tablename__ = 'login_sessions'
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    expires_at: Mapped[str] = mapped_column(String(40))

class Observation(Base):
    __tablename__ = 'observations'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    neighborhood: Mapped[str] = mapped_column(String(120), default='')
    location: Mapped[str] = mapped_column(String(160), default='')
    notes: Mapped[str] = mapped_column(Text, default='')
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    coordinate_source: Mapped[str | None] = mapped_column(String(24))
    captured_at: Mapped[str | None] = mapped_column(String(10))
    created_at: Mapped[str] = mapped_column(String(40), default=now, index=True)
    created_by: Mapped[str] = mapped_column(ForeignKey('users.id'))
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    image_sha256: Mapped[str] = mapped_column(String(64))
    original_sha256: Mapped[str] = mapped_column(String(64))

class Analysis(Base):
    __tablename__ = 'analyses'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    observation_id: Mapped[str] = mapped_column(ForeignKey('observations.id'), index=True)
    status: Mapped[str] = mapped_column(String(24), default='queued', index=True)
    created_at: Mapped[str] = mapped_column(String(40), default=now)
    finished_at: Mapped[str | None] = mapped_column(String(40))
    created_by: Mapped[str] = mapped_column(ForeignKey('users.id'))
    confidence: Mapped[float] = mapped_column(Float)
    result_json: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)

class Review(Base):
    __tablename__ = 'reviews'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[str] = mapped_column(ForeignKey('analyses.id'), index=True)
    decision: Mapped[str] = mapped_column(String(24))
    comment: Mapped[str] = mapped_column(Text)
    reviewed_by: Mapped[str] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[str] = mapped_column(String(40), default=now)

class Setting(Base):
    __tablename__ = 'settings'
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
