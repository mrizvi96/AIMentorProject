"""
Agentic RAG Service with LangGraph
Self-correcting RAG workflow: retrieve → grade → rewrite → generate
"""
import logging
from typing import Dict, List

from llama_index.core import VectorStoreIndex, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from .mistral_llm import MistralLLM
import chromadb

from langgraph.graph import StateGraph, END
from .agent_state import AgentState
from ..core.config import settings

logger = logging.getLogger(__name__)

class AgenticRAGService:
    """Agentic RAG with self-correction capabilities"""

    def __init__(self):
        self.index = None
        self.query_engine = None
        self.llm = None
        self.graph = None
        self._initialize()

    def _initialize(self):
        """Initialize all components"""
        logger.info("Initializing Agentic RAG service...")

        # Configure embedding model (using sentence-transformers on GPU)
        logger.info("  Configuring embeddings via sentence-transformers...")
        import os
        # Disable hf_transfer to avoid dependency issues
        os.environ.pop('HF_HUB_ENABLE_HF_TRANSFER', None)

        embed_model = HuggingFaceEmbedding(
            model_name="all-MiniLM-L6-v2",  # Fast, lightweight embedding model
            device="cuda"  # Use GPU for fast embeddings
        )
        Settings.embed_model = embed_model

        # Configure LLM
        logger.info("  Connecting to LLM server...")
        self.llm = MistralLLM(
            server_url=settings.llm_base_url.replace("/v1", ""),
            temperature=settings.llm_temperature,
            num_output=settings.llm_max_tokens,
        )
        Settings.llm = self.llm

        # Connect to ChromaDB
        logger.info("  Connecting to ChromaDB...")
        chroma_client = chromadb.PersistentClient(path=settings.chroma_db_path)
        chroma_collection = chroma_client.get_or_create_collection(name=settings.chroma_collection_name)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

        self.index = VectorStoreIndex.from_vector_store(vector_store)
        self.query_engine = self.index.as_query_engine(
            similarity_top_k=settings.top_k_retrieval
        )

        # Build LangGraph workflow
        logger.info("  Building LangGraph workflow...")
        self._build_graph()

        logger.info("✓ Agentic RAG service initialized")

    def _build_graph(self):
        """Build the LangGraph state machine"""
        # Create graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("retrieve", self._retrieve)
        workflow.add_node("grade_documents", self._grade_documents)
        workflow.add_node("rewrite_query", self._rewrite_query)
        workflow.add_node("generate", self._generate)

        # Set entry point
        workflow.set_entry_point("retrieve")

        workflow.add_edge("retrieve", "grade_documents")

        # Add conditional edges
        workflow.add_conditional_edges(
            "grade_documents",
            self._decide_after_grading,
            {
                "generate": "generate",
                "rewrite": "rewrite_query"
            }
        )

        workflow.add_edge("rewrite_query", "retrieve")  # Loop back
        workflow.add_edge("generate", END)

        # Compile graph
        self.graph = workflow.compile()

        logger.info("  Graph compiled with nodes: retrieve -> grade_documents -> [rewrite_query] -> retrieve -> generate")

    # === NODE IMPLEMENTATIONS ===

    def _retrieve(self, state: AgentState) -> AgentState:
        """
        Retrieve Node: Query vector store for relevant documents
        """
        # Use rewritten question if available, otherwise original
        question = state.get("rewritten_question") or state["question"]

        logger.info(f"[RETRIEVE] Querying: {question[:100]}...")
        state["workflow_path"].append("retrieve")

        try:
            # Query the vector store
            response = self.query_engine.query(question)

            # Extract documents and scores
            documents = []
            scores = []

            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes:
                    documents.append(node.node.text)
                    scores.append(float(node.score) if node.score else 0.0)

            state["documents"] = documents
            state["document_scores"] = scores

            logger.info(f"  Retrieved {len(documents)} documents (avg score: {sum(scores)/len(scores):.2f})")

        except Exception as e:
            logger.error(f"  Retrieval failed: {e}")
            state["documents"] = []
            state["document_scores"] = []

        return state

    def _grade_documents(self, state: AgentState) -> AgentState:
        """
        Grade Documents Node: LLM evaluates relevance of retrieved context

        This is the critical self-reflection step that enables self-correction.
        """
        question = state.get("rewritten_question") or state["question"]
        documents = state["documents"]

        logger.info(f"[GRADE] Evaluating {len(documents)} documents for relevance...")
        state["workflow_path"].append("grade")

        if not documents:
            logger.warning("  No documents to grade")
            state["relevance_decision"] = "no"
            return state

        # Construct grading prompt
        docs_text = "\n\n".join([f"Document {i+1}:\n{doc[:300]}..."
                                  for i, doc in enumerate(documents)])

        grading_prompt = f"""You are a grading assistant. Your task is to determine if the retrieved documents are relevant to answer the user's question.

Question: {question}

Retrieved Documents:
{docs_text}

Are these documents relevant to answering the question? Respond with ONLY "yes" or "no".

If the documents contain information that could help answer the question, respond "yes".
If the documents are off-topic or unhelpful, respond "no".

Response:"""

        try:
            # Call LLM for grading (non-streaming)
            response = self.llm.complete(grading_prompt)
            decision = response.text.strip().lower()

            # Parse yes/no (handle variations)
            if "yes" in decision:
                state["relevance_decision"] = "yes"
                logger.info("  Decision: RELEVANT ✓")
            else:
                state["relevance_decision"] = "no"
                logger.info("  Decision: NOT RELEVANT ✗")

        except Exception as e:
            logger.error(f"  Grading failed: {e}, defaulting to 'yes'")
            state["relevance_decision"] = "yes"  # Fail safe

        return state

    def _rewrite_query(self, state: AgentState) -> AgentState:
        """
        Rewrite Query Node: Reformulate question for better retrieval
        """
        original_question = state["question"]
        current_question = state.get("rewritten_question") or original_question

        logger.info(f"[REWRITE] Attempt {state['retry_count'] + 1}/{state['max_retries']}")
        state["workflow_path"].append("rewrite")

        rewrite_prompt = f"""You are a query reformulation assistant. The original question did not retrieve relevant documents.

Original question: {original_question}

Your task: Rewrite this question to improve retrieval results. Make it more specific, add context, or rephrase for clarity.

Rewritten question:"""

        try:
            # Call LLM for query rewrite (non-streaming)
            response = self.llm.complete(rewrite_prompt)
            rewritten = response.text.strip()

            state["rewritten_question"] = rewritten
            state["retry_count"] += 1

            logger.info(f"  Original: {original_question[:80]}...")
            logger.info(f"  Rewritten: {rewritten[:80]}...")

        except Exception as e:
            logger.error(f"  Rewrite failed: {e}")
            # Keep current question

        return state

    def _generate(self, state: AgentState) -> AgentState:
        """
        Generate Node: Synthesize final answer from validated documents
        """
        question = state.get("rewritten_question") or state["question"]
        documents = state["documents"]

        logger.info(f"[GENERATE] Creating answer from {len(documents)} documents")
        state["workflow_path"].append("generate")

        # Construct context from documents
        context = "\n\n".join([f"Source {i+1}:\n{doc}"
                               for i, doc in enumerate(documents)])

        generation_prompt = f"""You are an expert Computer Science mentor helping students learn.

Context Documents:
{context}

Question: {question}

Instructions:
- Provide a clear, concise answer based STRICTLY on the context above
- If context is insufficient, acknowledge it honestly
- Cite sources by mentioning "Source 1", "Source 2", etc.
- Use analogies to make concepts accessible
- Be encouraging and supportive

Answer:"""

        try:
            # Call LLM for generation (non-streaming)
            response = self.llm.complete(generation_prompt)
            state["generation"] = response.text.strip()

            logger.info(f"  Generated {len(state['generation'])} character answer")

        except Exception as e:
            logger.error(f"  Generation failed: {e}")
            state["generation"] = f"I apologize, but I encountered an error generating the answer: {str(e)}"

        return state

    # === ROUTING FUNCTIONS ===

    def _decide_after_grading(self, state: AgentState) -> str:
        """
        Conditional routing after document grading.

        Returns:
            "generate" if documents are relevant OR max retries reached
            "rewrite" if documents are irrelevant AND retries available
        """
        decision = state.get("relevance_decision", "yes")
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", 2)

        # If relevant, proceed to generation
        if decision == "yes":
            logger.info(f"[ROUTE] → generate (documents are relevant)")
            return "generate"

        # If not relevant but retries exhausted, give up and generate anyway
        if retry_count >= max_retries:
            logger.info(f"[ROUTE] → generate (max retries {max_retries} reached)")
            return "generate"

        # Otherwise, rewrite query and try again
        logger.info(f"[ROUTE] → rewrite (retry {retry_count + 1}/{max_retries})")
        return "rewrite"

    # === PUBLIC API ===

    def query(self, question: str, max_retries: int = 2) -> Dict:
        """
        Query the agentic RAG system

        Args:
            question: User's question
            max_retries: Maximum query rewrites allowed (default: 2)

        Returns:
            Dict with answer, sources, metadata, workflow path
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"AGENTIC RAG QUERY: {question[:100]}...")
        logger.info(f"{'='*60}")

        # Initialize state
        initial_state: AgentState = {
            "question": question,
            "rewritten_question": None,
            "documents": [],
            "document_scores": [],
            "generation": "",
            "messages": [],
            "retry_count": 0,
            "max_retries": max_retries,
            "relevance_decision": None,
            "workflow_path": []
        }

        try:
            # Run the graph
            final_state = self.graph.invoke(initial_state)

            # Extract results
            result = {
                "answer": final_state["generation"],
                "sources": [
                    {
                        "text": doc[:200] + "..." if len(doc) > 200 else doc,
                        "score": score,
                        "metadata": {}
                    }
                    for doc, score in zip(final_state["documents"], final_state["document_scores"])
                ],
                "question": question,
                "num_sources": len(final_state["documents"]),
                "workflow_path": " → ".join(final_state["workflow_path"]),
                "rewrites_used": final_state["retry_count"],
                "was_rewritten": final_state["rewritten_question"] is not None
            }

            logger.info(f"\n{'='*60}")
            logger.info(f"WORKFLOW COMPLETE: {result['workflow_path']}")
            logger.info(f"Rewrites: {result['rewrites_used']}/{max_retries}")
            logger.info(f"{'='*60}\n")

            return result

        except Exception as e:
            logger.error(f"Agentic RAG failed: {e}")
            import traceback
            traceback.print_exc()
            raise

    # === STREAMING API ===
    # TODO: Implement streaming properly in Week 3
    # Current issue: Using stream_chat() inside nodes and consuming streams synchronously
    # breaks LangGraph's astream_events() because streams are exhausted before events can be emitted.
    #
    # Proper approach (Week 3):
    # 1. Keep nodes non-streaming (use complete())
    # 2. Use graph.astream() to stream state updates
    # 3. Stream only the final generation tokens to users
    # 4. Grade/rewrite nodes remain hidden from user (no need to stream those)

    async def query_stream(self, question: str, max_retries: int = 2):
        """
        Query with streaming support - yields tokens as they're generated

        NOTE: Currently not working due to architectural issues.
        This needs to be reimplemented following Week 3 approach.

        Yields:
            Dict with type ("token", "metadata", "workflow") and content
        """
        logger.warning("Streaming not yet properly implemented - using non-streaming query()")
        result = self.query(question, max_retries)

        # Yield the complete result at once for now
        yield {
            "type": "complete",
            "answer": result["answer"],
            "sources": result["sources"],
            "workflow_path": result["workflow_path"]
        }
        return

        # OLD BROKEN IMPLEMENTATION REMOVED
        # See STREAMING_FIX_10252025.md for details on why this didn't work

# Global singleton
_agentic_rag_service = None

def get_agentic_rag_service() -> AgenticRAGService:
    """Get or create the global agentic RAG service"""
    global _agentic_rag_service
    if _agentic_rag_service is None:
        _agentic_rag_service = AgenticRAGService()
    return _agentic_rag_service

async def get_agentic_rag_service_async() -> AgenticRAGService:
    """Get or create the global agentic RAG service (async version)"""
    global _agentic_rag_service
    if _agentic_rag_service is None:
        _agentic_rag_service = AgenticRAGService()
    return _agentic_rag_service