"""
AI Mentor FastAPI Application
Main entry point for the backend API server.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api.chat_router import router as chat_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Mentor API",
    description="Agentic RAG system for computer science education",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Svelte dev server
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router)

@app.get("/")
def health_check():
    """Root health check endpoint"""
    return {
        "status": "ok",
        "message": "AI Mentor API is running",
        "version": "1.0.0"
    }

@app.get("/api/health")
def detailed_health():
    """Detailed health check with service status"""
    health = {
        "status": "ok",
        "services": {
            "api": "running",
            "llm": "not_checked",
            "vector_db": "not_checked",
            "rag": "not_configured"
        }
    }

    # Check LLM server
    try:
        import requests
        resp = requests.get("http://localhost:8080/v1/models", timeout=5)
        health["services"]["llm"] = "running" if resp.ok else "error"
    except Exception as e:
        health["services"]["llm"] = f"down: {str(e)}"

    # Check Milvus Lite
    try:
        from pymilvus import connections, utility
        connections.connect(host="localhost", port="19530")
        health["services"]["vector_db"] = "running"
        connections.disconnect("default")
    except Exception as e:
        health["services"]["vector_db"] = f"down: {str(e)}"

    return health

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("🚀 AI Mentor API starting up...")
    logger.info("Listening on port 8000")
    logger.info("API docs available at http://localhost:8000/docs")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("👋 AI Mentor API shutting down...")
