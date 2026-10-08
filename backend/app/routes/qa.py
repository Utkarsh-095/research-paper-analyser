"""Routes for question answering and chat history."""

import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    Paper,
    ChatHistory,
    QuestionRequest,
    AnswerResponse,
    ChatHistoryResponse,
)
from ..rag_engine import rag_engine

router = APIRouter(prefix="/qa", tags=["Q&A"])


@router.post("/ask", response_model=AnswerResponse)
def ask_question(request: QuestionRequest, db: Session = Depends(get_db)):
    """Ask a question about a specific paper."""
    paper = db.query(Paper).filter(Paper.id == request.paper_id).first()
    if not paper:
        raise HTTPException(404, "Paper not found")
    if not paper.processed:
        raise HTTPException(400, "Paper is still being processed")

    result = rag_engine.answer_question(
        collection_name=paper.collection_name,
        question=request.question,
        paper_title=paper.title,
    )

    # Save to chat history
    chat = ChatHistory(
        paper_id=paper.id,
        question=request.question,
        answer=result["answer"],
        sources=json.dumps(result["sources"]),
        confidence=result["confidence"],
    )
    db.add(chat)
    db.commit()

    return AnswerResponse(
        answer=result["answer"],
        sources=result["sources"] if request.include_sources else [],
        confidence=result["confidence"],
        question=request.question,
        paper_title=paper.title,
    )


@router.get("/history/{paper_id}", response_model=List[ChatHistoryResponse])
def get_chat_history(paper_id: int, db: Session = Depends(get_db)):
    history = (
        db.query(ChatHistory)
        .filter(ChatHistory.paper_id == paper_id)
        .order_by(ChatHistory.timestamp.desc())
        .limit(50)
        .all()
    )
    return [ChatHistoryResponse.model_validate(h) for h in history]


@router.delete("/history/{paper_id}")
def clear_chat_history(paper_id: int, db: Session = Depends(get_db)):
    db.query(ChatHistory).filter(ChatHistory.paper_id == paper_id).delete()
    db.commit()
    return {"message": "Chat history cleared"}