"""
Configuration module for AI Mentor backend.
Loads environment variables and provides application settings.
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Configuration
    app_name: str = "AI Mentor API"
    app_version: str = "1.0.0"
    debug: bool = False

    # LLM Server Configuration
    llm_base_url: str = "http://localhost:8080/v1"
    llm_model_name: str = "mistral-7b-instruct-v0.2.q5_k_m.gguf"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 512

    # Embedding Configuration
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    # Milvus Lite Configuration (file-based, no Docker needed)
    milvus_uri: str = "./milvus_data/ai_mentor.db"  # Local SQLite-based storage
    milvus_collection_name: str = "course_materials"

    # RAG Configuration
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k_retrieval: int = 3
    similarity_threshold: float = 0.7

    # File paths
    course_materials_dir: str = "./course_materials"
    models_dir: str = "/workspace/models"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
