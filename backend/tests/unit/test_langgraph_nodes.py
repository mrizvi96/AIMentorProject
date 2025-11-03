"""
Unit tests for LangGraph nodes in Agentic RAG workflow

Tests each node (retrieve, grade_documents, rewrite_query, generate) in isolation.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.agentic_rag import AgenticRAGService
from app.services.agent_state import AgentState


@pytest.mark.unit
class TestRetrieveNode:
    """Tests for the retrieve node"""

    def test_retrieve_with_original_question(self, mock_query_engine, initial_agent_state):
        """Test retrieval using original question"""
        # Setup
        service = AgenticRAGService.__new__(AgenticRAGService)
        service.query_engine = mock_query_engine

        # Execute
        result = service._retrieve(initial_agent_state)

        # Assert
        assert len(result["documents"]) == 2
        assert len(result["document_scores"]) == 2
        assert result["document_scores"][0] == 0.85
        assert result["document_scores"][1] == 0.78
        assert "retrieve" in result["workflow_path"]
        mock_query_engine.query.assert_called_once_with("What is a Python variable?")

    def test_retrieve_with_rewritten_question(self, mock_query_engine, initial_agent_state):
        """Test retrieval using rewritten question"""
        # Setup
        service = AgenticRAGService.__new__(AgenticRAGService)
        service.query_engine = mock_query_engine
        initial_agent_state["rewritten_question"] = "How do variables work in Python?"

        # Execute
        result = service._retrieve(initial_agent_state)

        # Assert
        mock_query_engine.query.assert_called_once_with("How do variables work in Python?")

    def test_retrieve_handles_empty_results(self, initial_agent_state):
        """Test retrieve node handles empty results gracefully"""
        # Setup
        service = AgenticRAGService.__new__(AgenticRAGService)
        mock_engine = MagicMock()
        mock_response = Mock()
        mock_response.source_nodes = []
        mock_engine.query.return_value = mock_response
        service.query_engine = mock_engine

        # Execute
        result = service._retrieve(initial_agent_state)

        # Assert
        assert result["documents"] == []
        assert result["document_scores"] == []
        assert "retrieve" in result["workflow_path"]

    def test_retrieve_handles_exceptions(self, mock_query_engine, initial_agent_state):
        """Test retrieve node handles query engine exceptions"""
        # Setup
        service = AgenticRAGService.__new__(AgenticRAGService)
        mock_query_engine.query.side_effect = Exception("Query failed")
        service.query_engine = mock_query_engine

        # Execute
        result = service._retrieve(initial_agent_state)

        # Assert
        assert result["documents"] == []
        assert result["document_scores"] == []


@pytest.mark.unit
class TestGradeDocumentsNode:
    """Tests for the grade_documents node"""

    def test_grade_relevant_documents(self, agent_state_with_documents, mock_llm):
        """Test grading relevant documents"""
        # Setup
        service = AgenticRAGService.__new__(AgenticRAGService)
        service.llm = mock_llm
        mock_llm.complete.return_value = Mock(text="yes")

        # Execute
        result = service._grade_documents(agent_state_with_documents)

        # Assert
        assert result["relevance_decision"] == "yes"
        assert "grade" in result["workflow_path"]
        mock_llm.complete.assert_called_once()

    def test_grade_irrelevant_documents(self, agent_state_with_documents, mock_llm):
        """Test grading irrelevant documents"""
        # Setup
        service = AgenticRAGService.__new__(AgenticRAGService)
        service.llm = mock_llm
        mock_llm.complete.return_value = Mock(text="no, these documents are not relevant")

        # Execute
        result = service._grade_documents(agent_state_with_documents)

        # Assert
        assert result["relevance_decision"] == "no"
        assert "grade" in result["workflow_path"]

    def test_grade_no_documents(self, initial_agent_state, mock_llm):
        """Test grading when no documents are present"""
        # Setup
        service = AgenticRAGService.__new__(AgenticRAGService)
        service.llm = mock_llm

        # Execute
        result = service._grade_documents(initial_agent_state)

        # Assert
        assert result["relevance_decision"] == "no"
        mock_llm.complete.assert_not_called()

    def test_grade_handles_llm_failure(self, agent_state_with_documents, mock_llm):
        """Test grading handles LLM failures gracefully"""
        # Setup
        service = AgenticRAGService.__new__(AgenticRAGService)
        service.llm = mock_llm
        mock_llm.complete.side_effect = Exception("LLM unavailable")

        # Execute
        result = service._grade_documents(agent_state_with_documents)

        # Assert - should fail safe to 'yes'
        assert result["relevance_decision"] == "yes"


@pytest.mark.unit
class TestRewriteQueryNode:
    """Tests for the rewrite_query node"""

    def test_rewrite_query_basic(self, agent_state_irrelevant_docs, mock_llm):
        """Test basic query rewriting"""
        # Setup
        service = AgenticRAGService.__new__(AgenticRAGService)
        service.llm = mock_llm
        mock_llm.complete.return_value = Mock(
            text="How do you store data values in Python programming?"
        )

        # Execute
        result = service._rewrite_query(agent_state_irrelevant_docs)

        # Assert
        assert result["rewritten_question"] is not None
        assert result["rewritten_question"] != result["question"]
        assert result["retry_count"] == 1
        assert "rewrite" in result["workflow_path"]
        mock_llm.complete.assert_called_once()

    def test_rewrite_increments_retry_count(self, agent_state_irrelevant_docs, mock_llm):
        """Test that rewrite increments retry counter"""
        # Setup
        service = AgenticRAGService.__new__(AgenticRAGService)
        service.llm = mock_llm
        mock_llm.complete.return_value = Mock(text="Rewritten question")
        agent_state_irrelevant_docs["retry_count"] = 1

        # Execute
        result = service._rewrite_query(agent_state_irrelevant_docs)

        # Assert
        assert result["retry_count"] == 2

    def test_rewrite_handles_llm_failure(self, agent_state_irrelevant_docs, mock_llm):
        """Test rewrite handles LLM failures"""
        # Setup
        service = AgenticRAGService.__new__(AgenticRAGService)
        service.llm = mock_llm
        mock_llm.complete.side_effect = Exception("LLM error")

        # Execute
        result = service._rewrite_query(agent_state_irrelevant_docs)

        # Assert - should keep original question
        assert result.get("rewritten_question") is None or \
               result["rewritten_question"] == result["question"]


@pytest.mark.unit
class TestGenerateNode:
    """Tests for the generate node"""

    def test_generate_with_documents(self, agent_state_with_documents, mock_llm):
        """Test generation with valid documents"""
        # Setup
        service = AgenticRAGService.__new__(AgenticRAGService)
        service.llm = mock_llm
        mock_llm.complete.return_value = Mock(
            text="Variables in Python are containers for storing data values."
        )

        # Execute
        result = service._generate(agent_state_with_documents)

        # Assert
        assert result["generation"] != ""
        assert len(result["generation"]) > 10
        assert "generate" in result["workflow_path"]
        mock_llm.complete.assert_called_once()

    def test_generate_prompt_includes_context(self, agent_state_with_documents, mock_llm):
        """Test that generation prompt includes document context"""
        # Setup
        service = AgenticRAGService.__new__(AgenticRAGService)
        service.llm = mock_llm
        mock_llm.complete.return_value = Mock(text="Test answer")

        # Execute
        service._generate(agent_state_with_documents)

        # Assert - check that prompt includes documents
        call_args = mock_llm.complete.call_args[0][0]
        assert "Python variables store data values" in call_args
        assert "Variables in Python do not need explicit declaration" in call_args

    def test_generate_handles_llm_failure(self, agent_state_with_documents, mock_llm):
        """Test generation handles LLM failures"""
        # Setup
        service = AgenticRAGService.__new__(AgenticRAGService)
        service.llm = mock_llm
        mock_llm.complete.side_effect = Exception("LLM connection failed")

        # Execute
        result = service._generate(agent_state_with_documents)

        # Assert - should have error message
        assert "error" in result["generation"].lower() or \
               "apologize" in result["generation"].lower()


@pytest.mark.unit
class TestRoutingLogic:
    """Tests for conditional routing decisions"""

    def test_route_to_generate_when_relevant(self, agent_state_with_documents):
        """Test routing to generate when documents are relevant"""
        # Setup
        service = AgenticRAGService.__new__(AgenticRAGService)
        agent_state_with_documents["relevance_decision"] = "yes"

        # Execute
        decision = service._decide_after_grading(agent_state_with_documents)

        # Assert
        assert decision == "generate"

    def test_route_to_rewrite_when_irrelevant(self, agent_state_irrelevant_docs):
        """Test routing to rewrite when documents are irrelevant"""
        # Setup
        service = AgenticRAGService.__new__(AgenticRAGService)
        agent_state_irrelevant_docs["relevance_decision"] = "no"
        agent_state_irrelevant_docs["retry_count"] = 0

        # Execute
        decision = service._decide_after_grading(agent_state_irrelevant_docs)

        # Assert
        assert decision == "rewrite"

    def test_route_to_generate_when_max_retries_reached(self, agent_state_irrelevant_docs):
        """Test routing to generate when max retries exhausted"""
        # Setup
        service = AgenticRAGService.__new__(AgenticRAGService)
        agent_state_irrelevant_docs["relevance_decision"] = "no"
        agent_state_irrelevant_docs["retry_count"] = 2
        agent_state_irrelevant_docs["max_retries"] = 2

        # Execute
        decision = service._decide_after_grading(agent_state_irrelevant_docs)

        # Assert
        assert decision == "generate"

    def test_route_respects_max_retries_parameter(self, agent_state_irrelevant_docs):
        """Test that routing respects custom max_retries setting"""
        # Setup
        service = AgenticRAGService.__new__(AgenticRAGService)
        agent_state_irrelevant_docs["relevance_decision"] = "no"
        agent_state_irrelevant_docs["retry_count"] = 3
        agent_state_irrelevant_docs["max_retries"] = 5

        # Execute
        decision = service._decide_after_grading(agent_state_irrelevant_docs)

        # Assert
        assert decision == "rewrite"  # Still has retries left
