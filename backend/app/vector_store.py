"""ChromaDB Vector Store wrapper (Updated for ChromaDB 0.4+)."""

import chromadb
from typing import List, Dict
from .config import settings
from .embeddings import embedding_engine


class VectorStore:
    def __init__(self):
        # Uses modern ChromaDB PersistentClient
        self.client = chromadb.PersistentClient(path=settings.chroma_persist_dir)

    def create_collection(self, name: str):
        return self.client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"}
        )

    def delete_collection(self, name: str):
        try:
            self.client.delete_collection(name)
        except Exception:
            pass

    def add_documents(self, collection_name: str, chunks: List[Dict], paper_id: int):
        collection = self.create_collection(collection_name)
        texts = [chunk["text"] for chunk in chunks]
        ids = [f"paper_{paper_id}_chunk_{chunk['chunk_index']}" for chunk in chunks]
        metadatas = [
            {
                "paper_id": paper_id,
                "chunk_index": chunk["chunk_index"],
                "char_start": chunk.get("char_start", 0),
                "char_length": chunk.get("char_length", 0),
            }
            for chunk in chunks
        ]

        batch_size = 100
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            batch_ids = ids[i : i + batch_size]
            batch_meta = metadatas[i : i + batch_size]
            batch_embeddings = embedding_engine.embed_texts(batch_texts)

            collection.add(
                documents=batch_texts,
                embeddings=batch_embeddings,
                metadatas=batch_meta,
                ids=batch_ids
            )

    def query(self, collection_name: str, query_text: str, n_results: int = settings.top_k_results) -> List[Dict]:
        collection = self.create_collection(collection_name)
        query_embedding = embedding_engine.embed_query(query_text)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )

        formatted = []
        if results and results["documents"]:
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            ):
                formatted.append({
                    "text": doc,
                    "metadata": meta,
                    "similarity": max(0.0, 1.0 - dist)
                })

        return formatted


vector_store = VectorStore()