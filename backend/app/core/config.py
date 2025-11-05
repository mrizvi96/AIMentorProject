"""
Configuration module for AI Mentor backend.
Loads environment variables and provides application settings.
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path


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
    llm_max_tokens: int = 768  # IMPROVEMENT: Increased from 512 for fuller citations

    # Embedding Configuration
    embedding_model_name: str = "all-MiniLM-L6-v2"  # Fast, lightweight embedding model
    embedding_dimension: int = 384

    # ChromaDB Configuration (file-based, no server needed)
    # Use absolute path to ensure it works from any directory (e.g., evaluation/)
    chroma_db_path: str = str(Path(__file__).parent.parent.parent / "chroma_db")
    chroma_collection_name: str = "course_materials" 
    # RAG Configuration
    chunk_size: int = 512  # IMPROVEMENT: Increased from 256 for better context preservation
    chunk_overlap: int = 50  # IMPROVEMENT: Increased from 25 to match chunk size increase
    top_k_retrieval: int = 3  # IMPROVEMENT: Increased from 1 for multi-source support
    similarity_threshold: float = 0.4  # IMPROVEMENT: Lowered from 0.7 for broader retrieval

    # File paths
    course_materials_dir: str = "../course_materials"
    models_dir: str = "/workspace/models"

    # GitHub OAuth Configuration
    github_client_id: str = ""
    github_client_secret: str = ""
    github_redirect_uri: str = "http://localhost:8000/api/auth/github/callback"

    # Session Management
    session_secret_key: str = "dev-secret-key-change-in-production"
    session_expiry_seconds: int = 3600  # 1 hour

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
