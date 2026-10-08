"""SQLAlchemy models and Pydantic schemas."""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

Base = declarative_base()


# ──────────────────────────── SQLAlchemy Models ────────────────────────────

class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    filename = Column(String(500), nullable=False)
    filepath = Column(String(1000), nullable=False)
    file_size = Column(Integer, default=0)
    num_pages = Column(Integer, default=0)
    num_chunks = Column(Integer, default=0)
    summary = Column(Text, default="")
    key_findings = Column(Text, default="")
    upload_date = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)
    collection_name = Column(String(200), nullable=False)


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sources = Column(Text, default="")
    confidence = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)


# ──────────────────────────── Pydantic Schemas ─────────────────────────────

class PaperResponse(BaseModel):
    id: int
    title: str
    filename: str
    file_size: int
    num_pages: int
    num_chunks: int
    summary: str
    key_findings: str
    upload_date: datetime
    processed: bool

    class Config:
        from_attributes = True


class QuestionRequest(BaseModel):
    paper_id: int
    question: str
    include_sources: bool = True


class AnswerResponse(BaseModel):
    answer: str
    sources: List[dict]
    confidence: float
    question: str
    paper_title: str


class SummaryResponse(BaseModel):
    paper_id: int
    title: str
    summary: str
    key_findings: str
    num_pages: int
    num_chunks: int


class ChatHistoryResponse(BaseModel):
    id: int
    question: str
    answer: str
    sources: str
    confidence: float
    timestamp: datetime

    class Config:
        from_attributes = True