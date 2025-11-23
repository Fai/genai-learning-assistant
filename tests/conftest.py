"""Pytest configuration and fixtures."""

import os
from typing import Any, AsyncIterator, Iterator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["AWS_REGION"] = "us-east-1"
os.environ["BEDROCK_MODEL_ID"] = "anthropic.claude-3-sonnet-20240229-v1:0"


@pytest.fixture
def mock_bedrock_client() -> MagicMock:
    """Create a mock Bedrock client."""
    client = MagicMock()

    # Mock invoke_model response
    client.invoke_model.return_value = {
        "body": MagicMock(
            read=lambda: b'{"content": [{"type": "text", "text": "This is a test response"}], "usage": {"input_tokens": 10, "output_tokens": 20}}'
        )
    }

    # Mock invoke_agent response
    client.invoke_agent.return_value = {
        "completion": [
            {"chunk": {"bytes": b"Test agent response"}},
        ],
    }

    return client


@pytest.fixture
def mock_bedrock_service(mock_bedrock_client: MagicMock) -> AsyncMock:
    """Create a mock BedrockService."""
    service = AsyncMock()

    # Mock methods
    service.invoke_model.return_value = {
        "content": [{"type": "text", "text": "This is a test response"}],
        "usage": {"input_tokens": 10, "output_tokens": 20},
    }

    service.invoke_agent.return_value = {
        "completion": "Test agent response",
        "traces": [],
        "session_id": "test-session-id",
    }

    service.retrieve_from_knowledge_base.return_value = [
        {
            "content": {"text": "Test document content"},
            "score": 0.95,
        }
    ]

    return service


@pytest.fixture
def test_client() -> Iterator[TestClient]:
    """Create a test client for the FastAPI application."""
    from src.main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture
async def learning_agent(mock_bedrock_service: AsyncMock) -> Any:
    """Create a learning agent with mocked Bedrock service."""
    from src.agents import LearningAgent

    agent = LearningAgent(bedrock_service=mock_bedrock_service)
    return agent


@pytest.fixture
def sample_question() -> str:
    """Sample question for testing."""
    return "Can you explain what recursion is in programming?"


@pytest.fixture
def sample_code() -> dict[str, str]:
    """Sample code for testing."""
    return {
        "code": """def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)""",
        "language": "python",
    }
