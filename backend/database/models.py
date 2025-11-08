# backend/database/models.py
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, UniqueConstraint
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aarii_chatlogs.db")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

class ChatLog(Base):
    __tablename__ = "chat_logs"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(128), index=True)
    role = Column(String(16), index=True)    # "user" / "assistant" / "system"
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True)
    session_id = Column(String(128), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class MemoryIndexMapping(Base):
    """
    Maps our memory row id (SQLite primary key) to FAISS insertion index.
    Keeps mapping robust if deletions occur.
    """
    __tablename__ = "memory_mapping"
    id = Column(Integer, primary_key=True, index=True)
    faiss_index = Column(Integer, index=True, unique=True)
    memory_row_id = Column(Integer, index=True, unique=True)
    session_id = Column(String(128), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("faiss_index", "memory_row_id", name="_faiss_mem_uc"),)

def init_db():
    Base.metadata.create_all(bind=engine)

# auto-init on import
init_db()
