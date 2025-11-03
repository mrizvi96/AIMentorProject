# Backend Testing Guide

Comprehensive testing suite for the AI Mentor backend using pytest.

---

## Quick Start

```bash
# Install pytest (if not already installed)
pip install pytest pytest-asyncio pytest-mock

# Run all tests
cd backend
pytest

# Run with verbose output
pytest -v

# Run specific test categories
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests only
pytest -m "not slow"        # Exclude slow tests
```

---

## Test Structure

```
tests/
├── conftest.py                      # Shared fixtures and configuration
├── unit/                            # Unit tests (isolated components)
│   └── test_langgraph_nodes.py     # LangGraph node tests
├── integration/                     # Integration tests (full workflows)
│   └── test_api_endpoints.py       # API endpoint tests
└── README.md                        # This file
```

---

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
- Test individual components in isolation
- Use mocks for dependencies
- Fast execution
- No external services required

**Modules tested:**
- LangGraph nodes (retrieve, grade_documents, rewrite_query, generate)
- Routing logic
- Individual helper functions

### Integration Tests (`@pytest.mark.integration`)
- Test full request-response workflows
- Test API endpoints end-to-end
- May use mocks for expensive operations
- Tests component interactions

**Modules tested:**
- FastAPI endpoints (/api/chat, /api/chat-agentic, /api/chat/compare)
- Request validation
- Response schemas
- Error handling

---

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with coverage (if pytest-cov installed)
pytest --cov=app --cov-report=html

# Run specific file
pytest tests/unit/test_langgraph_nodes.py

# Run specific test class
pytest tests/unit/test_langgraph_nodes.py::TestRetrieveNode

# Run specific test method
pytest tests/unit/test_langgraph_nodes.py::TestRetrieveNode::test_retrieve_with_original_question

# Run tests matching pattern
pytest -k "retrieve"        # All tests with 'retrieve' in name
pytest -k "not slow"        # Exclude slow tests
```

### Filter by Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Exclude slow tests
pytest -m "not slow"

# Run tests requiring LLM server
pytest -m requires_llm

# Run tests requiring ChromaDB
pytest -m requires_db

# Combine markers
pytest -m "unit and not slow"
```

### Output Options

```bash
# Verbose output
pytest -v

# Show print statements
pytest -s

# Stop at first failure
pytest -x

# Show local variables on failure
pytest -l

# Show summary of all outcomes
pytest -ra

# Quiet mode (minimal output)
pytest -q
```

---

## Test Fixtures

### Available Fixtures

Located in `tests/conftest.py`:

**Mock Objects:**
- `mock_llm_response` - Mock LLM response object
- `mock_llm` - Mock MistralLLM instance
- `mock_query_engine` - Mock query engine with realistic responses
- `mock_chroma_client` - Mock ChromaDB client

**Agent State:**
- `initial_agent_state` - Clean initial state
- `agent_state_with_documents` - State with retrieved documents
- `agent_state_irrelevant_docs` - State with irrelevant documents

**Test Data:**
- `sample_questions` - List of sample questions
- `sample_documents` - List of sample documents with metadata
- `test_settings` - Test configuration settings

### Using Fixtures

```python
def test_example(mock_llm, initial_agent_state):
    """Fixtures are injected automatically by pytest"""
    # Use fixtures directly
    service = AgenticRAGService()
    service.llm = mock_llm
    result = service._retrieve(initial_agent_state)
    assert result["documents"] is not None
```

---

## Writing New Tests

### Unit Test Template

```python
import pytest
from unittest.mock import Mock, patch

@pytest.mark.unit
class TestMyComponent:
    """Tests for MyComponent"""

    def test_basic_functionality(self, mock_dependency):
        """Test basic functionality"""
        # Setup
        component = MyComponent()
        component.dependency = mock_dependency

        # Execute
        result = component.do_something()

        # Assert
        assert result is not None
        mock_dependency.method.assert_called_once()

    def test_error_handling(self, mock_dependency):
        """Test error handling"""
        # Setup
        mock_dependency.method.side_effect = Exception("Error")
        component = MyComponent()
        component.dependency = mock_dependency

        # Execute & Assert
        with pytest.raises(Exception):
            component.do_something()
```

### Integration Test Template

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

@pytest.mark.integration
class TestMyEndpoint:
    """Tests for /api/my-endpoint"""

    def test_success_case(self, client):
        """Test successful request"""
        response = client.post(
            "/api/my-endpoint",
            json={"param": "value"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "expected_field" in data
```

---

## Test Best Practices

### 1. Test Naming
- Use descriptive names: `test_retrieve_with_original_question`
- Follow pattern: `test_<what>_<condition>_<expected>`

### 2. Test Structure (AAA Pattern)
```python
def test_example():
    # Arrange - Setup test data and mocks
    mock = Mock()

    # Act - Execute the code being tested
    result = function_under_test(mock)

    # Assert - Verify expected outcomes
    assert result == expected_value
```

### 3. Isolation
- Each test should be independent
- Use fixtures for setup/teardown
- Don't rely on test execution order

### 4. Mocking
- Mock external dependencies (LLM, database)
- Don't mock the code you're testing
- Use `Mock` for simple mocks, `MagicMock` for complex objects

### 5. Coverage Goals
- Aim for >80% code coverage
- Focus on critical paths first
- Test edge cases and error conditions

---

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-mock pytest-cov
      - name: Run tests
        run: |
          cd backend
          pytest -v --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## Troubleshooting

### Common Issues

**Import Errors:**
```bash
# Ensure backend directory is in Python path
cd backend
pytest
```

**Fixture Not Found:**
- Check fixture is defined in `conftest.py` or test file
- Verify fixture name matches usage

**Mock Not Working:**
- Check patch path is correct (use full import path)
- Ensure mock is created before code execution

**Tests Hanging:**
- Check for infinite loops or missing timeouts
- Use `pytest-timeout` to set test timeouts

### Debugging Tests

```bash
# Run with debugger
pytest --pdb                     # Drop to debugger on failure
pytest --pdb-trace              # Drop to debugger at start of each test

# Show full diff on assertion failures
pytest -vv

# Show print statements
pytest -s

# Show local variables on failure
pytest -l --tb=long
```

---

## Test Metrics

### Current Coverage

Run to generate coverage report:
```bash
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

### Test Execution Time

```bash
# Show slowest 10 tests
pytest --durations=10

# Profile test execution
pytest --profile
```

---

## Next Steps

### Planned Test Additions

1. **Performance Tests**
   - Benchmark retrieval speed
   - Measure end-to-end latency
   - Test with large document sets

2. **Load Tests**
   - Concurrent request handling
   - Rate limiting behavior
   - Memory usage under load

3. **End-to-End Tests**
   - Full system tests with real LLM
   - Real database operations
   - Multi-step workflows

4. **Property-Based Tests**
   - Use `hypothesis` for property testing
   - Generate random inputs
   - Test invariants

---

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Mock Documentation](https://docs.python.org/3/library/unittest.mock.html)

---

**Last Updated:** 2025-11-03
**Test Framework Version:** pytest 7.x
**Coverage Target:** >80%
