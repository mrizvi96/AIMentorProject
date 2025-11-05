"""
Simple RAG Service for AI Mentor
Handles document retrieval and response generation using LlamaIndex
"""
import os
# Disable hf_transfer before any HuggingFace imports
os.environ.pop('HF_HUB_ENABLE_HF_TRANSFER', None)

from typing import List, Dict, Optional
import logging
from llama_index.core import VectorStoreIndex, ServiceContext, Settings, PromptTemplate
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from .mistral_llm import MistralLLM
from llama_index.core.schema import Document, NodeWithScore
import chromadb

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

            # Initialize embedding model (HuggingFace sentence-transformers)
            logger.info(f"Loading embedding model: {settings.embedding_model_name}")
            embed_model = HuggingFaceEmbedding(
                model_name=settings.embedding_model_name,
                device="cuda"  # Use GPU for fast embeddings
            )

            # Initialize LLM (llama.cpp server)
            logger.info(f"Connecting to Mistral-7B via llama.cpp server at {settings.llm_base_url}")
            llm = MistralLLM(
                server_url=settings.llm_base_url.replace("/v1", ""),  # Remove /v1 suffix
                temperature=settings.llm_temperature,
                num_output=settings.llm_max_tokens,
            )

            # Configure LlamaIndex Settings (global configuration)
            Settings.llm = llm
            Settings.embed_model = embed_model
            Settings.chunk_size = settings.chunk_size
            Settings.chunk_overlap = settings.chunk_overlap

            # Initialize ChromaDB client and vector store
            logger.info(f"Connecting to ChromaDB at {settings.chroma_db_path}")
            chroma_client = chromadb.PersistentClient(path=settings.chroma_db_path)
            chroma_collection = chroma_client.get_or_create_collection(name=settings.chroma_collection_name)
            logger.info(f"ChromaDB collection '{settings.chroma_collection_name}' has {chroma_collection.count()} documents")
            self.vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

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

    def _get_qa_template(self) -> PromptTemplate:
        """Get the system prompt template for QA"""
        return PromptTemplate("""You are an expert Computer Science mentor helping introductory computer science students understand complex topics. Your goal is to provide pedagogical, accurate, and well-cited responses.

Context information from course materials:
{context_str}

IMPORTANT INSTRUCTIONS:

1. ANSWER SCOPE:
   - Base your answer ONLY on the provided context above
   - If the context does not contain sufficient information to fully answer the question, explicitly state: "The provided materials do not contain enough information about [specific topic]"
   - DO NOT add information from your general knowledge that is not supported by the context
   - If multiple sources support different aspects of your answer, cite each one specifically

2. PEDAGOGICAL APPROACH:
   - Tailor explanations for introductory computer science learners
   - Use simple language, analogies, and examples when helpful
   - For conceptual questions, consider providing pseudocode or Python examples if they help clarify the concept
   - Guide students toward understanding rather than just providing direct answers to problem-solving questions

3. CITATION REQUIREMENTS (CRITICAL):
   - After your answer, include a "Sources:" section
   - For each claim, cite the specific source that supports it
   - Use this format: [Source: filename, page X]
   - Example: "Python is a high-level programming language [Source: Introduction_to_Python_Programming.pdf, page 41]"
   - If referring to authors cited within a source, clarify this: "As cited in [Source: programming-fundamentals.pdf, page 15], Gaddis et al. describe..."
   - ALWAYS use "page X" format, never "page_label: X"
   - If page numbers are not available in metadata, use "Source: filename"

4. ANSWER COMPLETENESS:
   - Ensure your answer addresses ALL parts of the question
   - For "compare and contrast" questions, cover both similarities AND differences
   - For "when would you use X" questions, provide practical guidance on use cases
   - For "why" questions, explain the reasoning, not just the "what"

5. TECHNICAL ACCURACY:
   - Pay careful attention to technical distinctions in the source material
   - If sources make subtle distinctions (e.g., variables vs boxes, direct vs indirect recursion), honor these distinctions
   - Double-check that examples and explanations align with the source material

Question: {query_str}

Answer: """)

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
            'collection_name': settings.chroma_collection_name,
            'embedding_model': settings.embedding_model_name,
            'llm_endpoint': settings.llm_base_url,
        }


# Global RAG service instance
rag_service = RAGService()
