"""
Pytest configuration and shared fixtures

This file provides fixtures and configuration that are available to all tests.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock
from typing import Dict, List

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.services.agent_state import AgentState


# ========== Mock Fixtures ==========

@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing"""
    mock = Mock()
    mock.text = "This is a test response from the LLM."
    mock.raw = {"choices": [{"text": "This is a test response from the LLM."}]}
    return mock


@pytest.fixture
def mock_llm():
    """Mock MistralLLM instance"""
    mock = MagicMock()
    mock.complete.return_value = Mock(
        text="Test LLM response",
        raw={"choices": [{"text": "Test LLM response"}]}
    )
    mock.stream_complete.return_value = iter([
        Mock(text="Test ", raw={}),
        Mock(text="stream ", raw={}),
        Mock(text="response", raw={})
    ])
    return mock


@pytest.fixture
def mock_query_engine():
    """Mock query engine with realistic response"""
    mock = MagicMock()

    # Create mock source nodes
    mock_node1 = Mock()
    mock_node1.node.text = "Python variables store data values. A variable is created when you assign a value to it."
    mock_node1.score = 0.85

    mock_node2 = Mock()
    mock_node2.node.text = "Variables in Python do not need explicit declaration. The declaration happens automatically."
    mock_node2.score = 0.78

    # Configure query response
    mock_response = Mock()
    mock_response.source_nodes = [mock_node1, mock_node2]
    mock_response.response = "Test response"

    mock.query.return_value = mock_response
    return mock


@pytest.fixture
def mock_chroma_client():
    """Mock ChromaDB client"""
    mock = MagicMock()
    mock_collection = MagicMock()
    mock_collection.name = settings.chroma_collection_name
    mock.get_or_create_collection.return_value = mock_collection
    return mock


# ========== Agent State Fixtures ==========

@pytest.fixture
def initial_agent_state() -> AgentState:
    """Initial agent state for testing"""
    return {
        "question": "What is a Python variable?",
        "rewritten_question": None,
        "documents": [],
        "document_scores": [],
        "generation": "",
        "messages": [],
        "retry_count": 0,
        "max_retries": 2,
        "relevance_decision": None,
        "workflow_path": []
    }


@pytest.fixture
def agent_state_with_documents() -> AgentState:
    """Agent state with retrieved documents"""
    return {
        "question": "What is a Python variable?",
        "rewritten_question": None,
        "documents": [
            "Python variables store data values. A variable is created when you assign a value to it.",
            "Variables in Python do not need explicit declaration."
        ],
        "document_scores": [0.85, 0.78],
        "generation": "",
        "messages": [],
        "retry_count": 0,
        "max_retries": 2,
        "relevance_decision": None,
        "workflow_path": ["retrieve"]
    }


@pytest.fixture
def agent_state_irrelevant_docs() -> AgentState:
    """Agent state with irrelevant documents"""
    return {
        "question": "What is a Python variable?",
        "rewritten_question": None,
        "documents": [
            "The weather is sunny today.",
            "Coffee is a popular beverage."
        ],
        "document_scores": [0.12, 0.08],
        "generation": "",
        "messages": [],
        "retry_count": 0,
        "max_retries": 2,
        "relevance_decision": "no",
        "workflow_path": ["retrieve", "grade"]
    }


# ========== Test Data Fixtures ==========

@pytest.fixture
def sample_questions() -> List[str]:
    """Sample questions for testing"""
    return [
        "What is a Python variable?",
        "How do you define a function in Python?",
        "What is the difference between a list and a tuple?",
        "How does error handling work in Python?",
    ]


@pytest.fixture
def sample_documents() -> List[Dict[str, any]]:
    """Sample documents for testing"""
    return [
        {
            "text": "Variables in Python are used to store data values. "
                   "Python has no command for declaring a variable. "
                   "A variable is created the moment you first assign a value to it.",
            "score": 0.85,
            "metadata": {
                "file_name": "python_basics.pdf",
                "page_label": "5",
                "file_size": 1024000
            }
        },
        {
            "text": "Python functions are defined using the def keyword. "
                   "Functions can take parameters and return values.",
            "score": 0.72,
            "metadata": {
                "file_name": "python_functions.pdf",
                "page_label": "12",
                "file_size": 2048000
            }
        }
    ]


# ========== Environment Fixtures ==========

@pytest.fixture
def test_settings():
    """Test configuration settings"""
    return {
        "llm_base_url": "http://localhost:8080/v1",
        "llm_model_name": "test-model",
        "llm_temperature": 0.7,
        "llm_max_tokens": 512,
        "embedding_model_name": "all-MiniLM-L6-v2",
        "chroma_db_path": "./test_chroma_db",
        "chroma_collection_name": "test_collection",
        "chunk_size": 256,
        "chunk_overlap": 25,
        "top_k_retrieval": 3,
        "similarity_threshold": 0.7
    }


# ========== Pytest Hooks ==========

def pytest_configure(config):
    """Pytest configuration hook"""
    # Add custom markers
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow-running tests")
    config.addinivalue_line("markers", "requires_llm: Requires LLM server")
    config.addinivalue_line("markers", "requires_db: Requires ChromaDB")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically"""
    for item in items:
        # Auto-mark tests based on location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
