"""
Simple RAG Service for AI Mentor
Handles document retrieval and response generation using LlamaIndex
"""
from typing import List, Dict, Optional
import logging
from llama_index.core import VectorStoreIndex, ServiceContext, Settings
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core.schema import Document, NodeWithScore
from pymilvus import connections

from ..core.config import settings

logger = logging.getLogger(__name__)


class RAGService:
    """
    Simple RAG service that retrieves relevant documents and generates responses.
    Phase 1 implementation - no agentic behavior yet.
    """

    def __init__(self):
        self.vector_store = None
        self.index = None
        self.query_engine = None
        self._initialized = False

    def initialize(self):
        """Initialize the RAG service with LLM, embeddings, and vector store"""
        if self._initialized:
            logger.info("RAG service already initialized")
            return

        try:
            logger.info("Initializing RAG service...")

            # Connect to Milvus
            logger.info(f"Connecting to Milvus at {settings.milvus_host}:{settings.milvus_port}")
            connections.connect(
                alias="default",
                host=settings.milvus_host,
                port=settings.milvus_port
            )

            # Initialize embedding model (HuggingFace sentence-transformers)
            logger.info(f"Loading embedding model: {settings.embedding_model_name}")
            embed_model = HuggingFaceEmbedding(
                model_name=settings.embedding_model_name
            )

            # Initialize LLM (OpenAI-compatible llama.cpp server)
            logger.info(f"Connecting to LLM server at {settings.llm_base_url}")
            llm = OpenAI(
                api_base=settings.llm_base_url,
                api_key="dummy",  # llama.cpp server doesn't need real key
                model=settings.llm_model_name,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
            )

            # Configure LlamaIndex Settings (global configuration)
            Settings.llm = llm
            Settings.embed_model = embed_model
            Settings.chunk_size = settings.chunk_size
            Settings.chunk_overlap = settings.chunk_overlap

            # Initialize Milvus vector store
            self.vector_store = MilvusVectorStore(
                host=settings.milvus_host,
                port=settings.milvus_port,
                collection_name=settings.milvus_collection_name,
                dim=settings.embedding_dimension,
                overwrite=False  # Don't delete existing data
            )

            # Create index from vector store
            logger.info("Creating vector store index...")
            self.index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store
            )

            # Create query engine with custom system prompt
            self.query_engine = self.index.as_query_engine(
                similarity_top_k=settings.top_k_retrieval,
                text_qa_template=self._get_qa_template()
            )

            self._initialized = True
            logger.info("✓ RAG service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            raise

    def _get_qa_template(self) -> str:
        """Get the system prompt template for QA"""
        return """You are an expert Computer Science mentor helping students understand complex topics.

Context information from course materials:
{context_str}

Based strictly on the context above, answer the following question. If the context doesn't contain enough information to answer the question, say so explicitly.

Question: {query_str}

Instructions:
1. Provide a clear, direct answer
2. Use simple language and analogies when helpful
3. Cite specific parts of the context you used
4. If unsure, acknowledge limitations

Answer: """

    async def query(self, question: str) -> Dict:
        """
        Query the RAG system with a question

        Args:
            question: User's question

        Returns:
            Dict with response text and source documents
        """
        if not self._initialized:
            raise RuntimeError("RAG service not initialized. Call initialize() first.")

        try:
            logger.info(f"Processing query: {question[:100]}...")

            # Query the index
            response = self.query_engine.query(question)

            # Extract source nodes (documents)
            sources = []
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes:
                    sources.append({
                        'text': node.node.text[:200] + "...",  # First 200 chars
                        'score': node.score,
                        'metadata': node.node.metadata
                    })

            result = {
                'response': str(response),
                'sources': sources,
                'question': question
            }

            logger.info(f"Generated response with {len(sources)} sources")
            return result

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            raise

    def get_stats(self) -> Dict:
        """Get statistics about the RAG service"""
        return {
            'initialized': self._initialized,
            'collection_name': settings.milvus_collection_name,
            'embedding_model': settings.embedding_model_name,
            'llm_endpoint': settings.llm_base_url,
        }


# Global RAG service instance
rag_service = RAGService()
