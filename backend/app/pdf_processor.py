"""PDF text extraction and chunking."""

import fitz  # PyMuPDF
import re
from typing import List, Dict, Tuple
from .config import settings


class PDFProcessor:
    """Extracts text from PDFs and splits it into overlapping chunks."""

    def __init__(
        self,
        chunk_size: int = settings.chunk_size,
        chunk_overlap: int = settings.chunk_overlap,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    # ── extraction ──────────────────────────────────────────────────────

    def extract_text(self, filepath: str) -> Tuple[str, int, Dict]:
        """Return (full_text, num_pages, metadata) from a PDF file."""
        doc = fitz.open(filepath)
        pages: List[str] = []
        metadata = {
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
            "subject": doc.metadata.get("subject", ""),
            "pages": len(doc),
        }

        for page in doc:
            text = page.get_text("text")
            if text.strip():
                pages.append(text)

        doc.close()
        full_text = "\n\n".join(pages)
        full_text = self._clean_text(full_text)
        return full_text, len(pages), metadata

    # ── chunking ────────────────────────────────────────────────────────

    def chunk_text(self, text: str) -> List[Dict]:
        """Split *text* into overlapping chunks with metadata."""
        sentences = self._split_into_sentences(text)
        chunks: List[Dict] = []
        current_chunk: List[str] = []
        current_length = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            if current_length + sentence_length > self.chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append(
                    {
                        "text": chunk_text,
                        "chunk_index": chunk_index,
                        "char_start": sum(len(c["text"]) for c in chunks),
                        "char_length": len(chunk_text),
                    }
                )
                chunk_index += 1

                # keep overlap
                overlap_text = ""
                overlap_sentences: List[str] = []
                for s in reversed(current_chunk):
                    if len(overlap_text) + len(s) <= self.chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_text = " ".join(overlap_sentences)
                    else:
                        break
                current_chunk = overlap_sentences
                current_length = len(overlap_text)

            current_chunk.append(sentence)
            current_length += sentence_length

        # last chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(
                {
                    "text": chunk_text,
                    "chunk_index": chunk_index,
                    "char_start": sum(len(c["text"]) for c in chunks),
                    "char_length": len(chunk_text),
                }
            )

        return chunks

    def process_pdf(self, filepath: str) -> Dict:
        """High-level: extract → chunk → return everything."""
        full_text, num_pages, metadata = self.extract_text(filepath)
        chunks = self.chunk_text(full_text)
        return {
            "full_text": full_text,
            "num_pages": num_pages,
            "metadata": metadata,
            "chunks": chunks,
            "num_chunks": len(chunks),
        }

    # ── helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _clean_text(text: str) -> str:
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        text = re.sub(r"-\n", "", text)            # dehyphenate
        text = text.replace("\x00", "")
        return text.strip()

    @staticmethod
    def _split_into_sentences(text: str) -> List[str]:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]