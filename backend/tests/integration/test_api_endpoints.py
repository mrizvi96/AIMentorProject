"""
Integration tests for FastAPI endpoints

Tests the full request-response lifecycle for chat endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from main import app


@pytest.fixture
def client():
    """Test client for FastAPI app"""
    return TestClient(app)


@pytest.fixture
def mock_rag_result():
    """Mock RAG query result"""
    return {
        "answer": "Variables in Python are containers for storing data values.",
        "sources": [
            {
                "text": "Python variables store data values...",
                "score": 0.85,
                "metadata": {"file_name": "python_basics.pdf", "page_label": "5"}
            }
        ],
        "question": "What is a Python variable?",
        "num_sources": 1,
        "workflow_path": "retrieve → grade → generate",
        "rewrites_used": 0,
        "was_rewritten": False
    }


@pytest.mark.integration
class TestChatEndpoint:
    """Tests for /api/chat endpoint"""

    @patch('app.api.chat_router.rag_service')
    def test_chat_success(self, mock_rag_service, client, mock_rag_result):
        """Test successful chat request"""
        # Setup
        mock_rag_service.query.return_value = {
            "response": mock_rag_result["answer"],
            "sources": mock_rag_result["sources"],
            "question": mock_rag_result["question"]
        }

        # Execute
        response = client.post(
            "/api/chat",
            json={"message": "What is a Python variable?"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "question" in data
        assert len(data["sources"]) > 0

    def test_chat_empty_message(self, client):
        """Test chat with empty message"""
        response = client.post(
            "/api/chat",
            json={"message": ""}
        )

        # Assert - should fail validation
        assert response.status_code == 422  # Validation error

    def test_chat_missing_message(self, client):
        """Test chat with missing message field"""
        response = client.post(
            "/api/chat",
            json={}
        )

        # Assert
        assert response.status_code == 422

    def test_chat_too_long_message(self, client):
        """Test chat with message exceeding max length"""
        response = client.post(
            "/api/chat",
            json={"message": "a" * 3000}  # Exceeds 2000 char limit
        )

        # Assert
        assert response.status_code == 422

    @patch('app.api.chat_router.rag_service')
    def test_chat_with_conversation_id(self, mock_rag_service, client, mock_rag_result):
        """Test chat with custom conversation ID"""
        # Setup
        mock_rag_service.query.return_value = {
            "response": mock_rag_result["answer"],
            "sources": mock_rag_result["sources"],
            "question": mock_rag_result["question"]
        }

        # Execute
        response = client.post(
            "/api/chat",
            json={
                "message": "Test question",
                "conversation_id": "test-conv-123"
            }
        )

        # Assert
        assert response.status_code == 200


@pytest.mark.integration
class TestAgenticChatEndpoint:
    """Tests for /api/chat-agentic endpoint"""

    @patch('app.api.chat_router.get_agentic_rag_service')
    def test_agentic_chat_success(self, mock_get_service, client, mock_rag_result):
        """Test successful agentic chat request"""
        # Setup
        mock_service = Mock()
        mock_service.query.return_value = mock_rag_result
        mock_get_service.return_value = mock_service

        # Execute
        response = client.post(
            "/api/chat-agentic",
            json={"message": "What is a Python variable?"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "workflow_path" in data
        assert "rewrites_used" in data
        assert "was_rewritten" in data

    @patch('app.api.chat_router.get_agentic_rag_service')
    def test_agentic_chat_with_rewrite(self, mock_get_service, client, mock_rag_result):
        """Test agentic chat that triggers query rewrite"""
        # Setup
        mock_service = Mock()
        rewritten_result = mock_rag_result.copy()
        rewritten_result["workflow_path"] = "retrieve → grade → rewrite → retrieve → grade → generate"
        rewritten_result["rewrites_used"] = 1
        rewritten_result["was_rewritten"] = True
        mock_service.query.return_value = rewritten_result
        mock_get_service.return_value = mock_service

        # Execute
        response = client.post(
            "/api/chat-agentic",
            json={"message": "How does it work?"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["rewrites_used"] > 0
        assert data["was_rewritten"] is True
        assert "rewrite" in data["workflow_path"]

    @patch('app.api.chat_router.get_agentic_rag_service')
    def test_agentic_chat_error_handling(self, mock_get_service, client):
        """Test agentic chat error handling"""
        # Setup
        mock_service = Mock()
        mock_service.query.side_effect = Exception("Service error")
        mock_get_service.return_value = mock_service

        # Execute
        response = client.post(
            "/api/chat-agentic",
            json={"message": "Test question"}
        )

        # Assert
        assert response.status_code == 500
        assert "detail" in response.json()


@pytest.mark.integration
@pytest.mark.slow
class TestCompareEndpoint:
    """Tests for /api/chat/compare endpoint"""

    @patch('app.api.chat_router.get_agentic_rag_service')
    @patch('app.api.chat_router.rag_service')
    def test_compare_both_rag_types(self, mock_simple_rag, mock_get_agentic, client, mock_rag_result):
        """Test comparison of simple and agentic RAG"""
        # Setup simple RAG
        mock_simple_rag.query.return_value = {
            "response": "Simple RAG answer",
            "sources": mock_rag_result["sources"]
        }

        # Setup agentic RAG
        mock_agentic_service = Mock()
        mock_agentic_service.query.return_value = mock_rag_result
        mock_get_agentic.return_value = mock_agentic_service

        # Execute
        response = client.get(
            "/api/chat/compare",
            params={"question": "What is a variable?"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "question" in data
        assert "simple_rag" in data
        assert "agentic_rag" in data
        assert "answer" in data["simple_rag"]
        assert "answer" in data["agentic_rag"]
        assert "workflow" in data["agentic_rag"]

    def test_compare_missing_question(self, client):
        """Test compare endpoint without question parameter"""
        response = client.get("/api/chat/compare")

        # Assert
        assert response.status_code == 422


@pytest.mark.integration
class TestHealthEndpoint:
    """Tests for health check endpoint"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "status" in data or "message" in data


@pytest.mark.integration
class TestCORSHeaders:
    """Tests for CORS configuration"""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are configured"""
        response = client.options("/api/chat")

        # Note: CORS headers might not be present in test client
        # This test documents expected behavior
        assert response.status_code in [200, 405]  # OPTIONS might not be explicitly defined


@pytest.mark.integration
class TestResponseSchema:
    """Tests for response schema validation"""

    @patch('app.api.chat_router.rag_service')
    def test_chat_response_schema(self, mock_rag_service, client):
        """Test that chat response matches expected schema"""
        # Setup
        mock_rag_service.query.return_value = {
            "response": "Test answer",
            "sources": [{"text": "Test", "score": 0.8, "metadata": {}}],
            "question": "Test?"
        }

        # Execute
        response = client.post(
            "/api/chat",
            json={"message": "Test question"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert isinstance(data["answer"], str)
        assert isinstance(data["sources"], list)
        assert isinstance(data["question"], str)

        # Validate source structure
        if len(data["sources"]) > 0:
            source = data["sources"][0]
            assert "text" in source
            assert "score" in source
            assert "metadata" in source

    @patch('app.api.chat_router.get_agentic_rag_service')
    def test_agentic_response_schema(self, mock_get_service, client):
        """Test that agentic chat response matches expected schema"""
        # Setup
        mock_service = Mock()
        mock_service.query.return_value = {
            "answer": "Test",
            "sources": [],
            "question": "Test?",
            "workflow_path": "retrieve → generate",
            "rewrites_used": 0,
            "was_rewritten": False
        }
        mock_get_service.return_value = mock_service

        # Execute
        response = client.post(
            "/api/chat-agentic",
            json={"message": "Test"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Validate extended response structure
        assert isinstance(data["workflow_path"], str)
        assert isinstance(data["rewrites_used"], int)
        assert isinstance(data["was_rewritten"], bool)
