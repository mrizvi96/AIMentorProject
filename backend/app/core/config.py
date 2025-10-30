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
    embedding_model_name: str = "all-MiniLM-L6-v2"  # Fast, lightweight embedding model
    embedding_dimension: int = 384

    # ChromaDB Configuration (file-based, no server needed)
    chroma_db_path: str = "./chroma_db"  # Relative to backend directory
    chroma_collection_name: str = "course_materials" 
    # RAG Configuration
    chunk_size: int = 256
    chunk_overlap: int = 25
    top_k_retrieval: int = 1
    similarity_threshold: float = 0.7

    # File paths
    course_materials_dir: str = "../course_materials"
    models_dir: str = "/workspace/models"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
