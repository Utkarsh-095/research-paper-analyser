"""Embedding generation using local models or OpenAI."""

from typing import List
import numpy as np
from .config import settings


class EmbeddingEngine:
    """Generates embeddings for text chunks."""

    def __init__(self):
        self.provider = settings.embedding_provider
        self.model_name = settings.embedding_model
        self._model = None

    def _load_model(self):
        if self._model is not None:
            return

        if self.provider == "local":
            from sentence_transformers import SentenceTransformer
            print(f"Loading local embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            print("Embedding model loaded successfully")
        elif self.provider == "openai":
            from openai import OpenAI
            self._model = OpenAI(api_key=settings.openai_api_key)
        else:
            raise ValueError(f"Unknown embedding provider: {self.provider}")

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Return a list of embedding vectors for *texts*."""
        self._load_model()

        if self.provider == "local":
            embeddings = self._model.encode(texts, show_progress_bar=True)
            return embeddings.tolist()

        elif self.provider == "openai":
            response = self._model.embeddings.create(
                input=texts,
                model=self.model_name,
            )
            return [item.embedding for item in response.data]

    def embed_query(self, query: str) -> List[float]:
        """Embed a single query string."""
        self._load_model()

        if self.provider == "local":
            embedding = self._model.encode([query])
            return embedding[0].tolist()
        elif self.provider == "openai":
            response = self._model.embeddings.create(
                input=[query],
                model=self.model_name,
            )
            return response.data[0].embedding

    @property
    def dimension(self) -> int:
        self._load_model()
        if self.provider == "local":
            return self._model.get_sentence_embedding_dimension()
        elif self.provider == "openai":
            return 1536  # text-embedding-ada-002
        return 384


# Singleton
embedding_engine = EmbeddingEngine()