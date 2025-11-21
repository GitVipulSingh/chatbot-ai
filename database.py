# database.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Index
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

# SQLite DB (file sits next to project)
DATABASE_URL = "sqlite:///./chat_history.db"

# connect_args required for SQLite + SQLAlchemy in single-threaded dev apps
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ChatMessage(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False, default="global")  # <-- session id for per-user chats
    role = Column(String, nullable=False)  # 'user' or 'bot' (or 'system')
    content = Column(String, nullable=False) # message text
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # helpful index (session_id + timestamp) created below

# create tables (no-op if already exist)
Base.metadata.create_all(bind=engine)

# Add compound index programmatically (SQLAlchemy won't add it twice)
try:
    Index('ix_messages_session_timestamp', ChatMessage.session_id, ChatMessage.timestamp).create(bind=engine)
except Exception:
    # Index may already exist; fail silently
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
