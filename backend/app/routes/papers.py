"""Routes for paper upload, listing, and deletion."""

import os
import shutil
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import Paper, PaperResponse, SummaryResponse
from ..pdf_processor import PDFProcessor
from ..vector_store import vector_store
from ..summarizer import summarizer

router = APIRouter(prefix="/papers", tags=["Papers"])
pdf_processor = PDFProcessor()


@router.post("/upload", response_model=PaperResponse)
async def upload_paper(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a PDF, extract text, chunk, embed, summarize."""
    # Validate
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")

    content = await file.read()
    if len(content) > settings.max_file_size:
        raise HTTPException(400, f"File too large (max {settings.max_file_size // 1024 // 1024}MB)")

    # Save file
    unique_name = f"{uuid.uuid4().hex}_{file.filename}"
    filepath = os.path.join(settings.upload_dir, unique_name)
    with open(filepath, "wb") as f:
        f.write(content)

    try:
        # Process PDF
        result = pdf_processor.process_pdf(filepath)

        # Derive title
        title = result["metadata"].get("title") or file.filename.replace(".pdf", "")
        collection_name = f"paper_{uuid.uuid4().hex[:12]}"

        # Store embeddings
        vector_store.add_documents(collection_name, result["chunks"], paper_id=0)

        # Summarize
        summary_result = summarizer.summarize(result["full_text"], title)

        # Persist to DB
        paper = Paper(
            title=title,
            filename=file.filename,
            filepath=filepath,
            file_size=len(content),
            num_pages=result["num_pages"],
            num_chunks=result["num_chunks"],
            summary=summary_result["summary"],
            key_findings=summary_result["key_findings"],
            upload_date=datetime.utcnow(),
            processed=True,
            collection_name=collection_name,
        )
        db.add(paper)
        db.commit()
        db.refresh(paper)

        # Update vector store paper_id references
        return PaperResponse.model_validate(paper)

    except Exception as e:
        # Cleanup on failure
        if os.path.exists(filepath):
            os.remove(filepath)
        raise HTTPException(500, f"Error processing paper: {str(e)}")


@router.get("/", response_model=List[PaperResponse])
def list_papers(db: Session = Depends(get_db)):
    papers = db.query(Paper).order_by(Paper.upload_date.desc()).all()
    return [PaperResponse.model_validate(p) for p in papers]


@router.get("/{paper_id}", response_model=PaperResponse)
def get_paper(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(404, "Paper not found")
    return PaperResponse.model_validate(paper)


@router.get("/{paper_id}/summary", response_model=SummaryResponse)
def get_summary(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(404, "Paper not found")
    return SummaryResponse(
        paper_id=paper.id,
        title=paper.title,
        summary=paper.summary,
        key_findings=paper.key_findings,
        num_pages=paper.num_pages,
        num_chunks=paper.num_chunks,
    )


@router.delete("/{paper_id}")
def delete_paper(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(404, "Paper not found")

    # Remove vector collection
    vector_store.delete_collection(paper.collection_name)

    # Remove file
    if os.path.exists(paper.filepath):
        os.remove(paper.filepath)

    db.delete(paper)
    db.commit()
    return {"message": f"Paper '{paper.title}' deleted successfully"}