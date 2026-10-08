"""Application configuration."""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # =========================================================================
    # 👉 PASTE YOUR GROQ API KEY HERE (Starts with gsk_...)
    # =========================================================================
    openai_api_key: str = "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"

    # Groq Settings
    openai_base_url: str = "https://api.groq.com/openai/v1"
    openai_model: str = "openai/gpt-oss-120b"

    # Embedding Settings
    embedding_provider: str = "local"
    embedding_model: str = "all-MiniLM-L6-v2"

    # Storage Paths
    chroma_persist_dir: str = "./chroma_db"
    database_url: str = "sqlite:///./research_papers.db"
    upload_dir: str = "./uploads"
    max_file_size: int = 50 * 1024 * 1024  # 50MB

    # RAG Settings
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_results: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"


settings = Settings()

os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.chroma_persist_dir, exist_ok=True)