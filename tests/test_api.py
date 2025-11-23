"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, test_client: TestClient) -> None:
        """Test health check endpoint."""
        response = test_client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data


class TestAskEndpoint:
    """Tests for ask question endpoint."""

    def test_ask_question_success(self, test_client: TestClient) -> None:
        """Test successful question asking."""
        request_data = {
            "question": "What is recursion?",
        }

        response = test_client.post("/api/v1/ask", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "session_id" in data
        assert "strand_id" in data
        assert data["iteration"] >= 0

    def test_ask_question_with_session(self, test_client: TestClient) -> None:
        """Test asking question with session ID."""
        request_data = {
            "question": "What is Python?",
            "session_id": "test-session-123",
        }

        response = test_client.post("/api/v1/ask", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data

    def test_ask_question_empty(self, test_client: TestClient) -> None:
        """Test asking empty question."""
        request_data = {
            "question": "",
        }

        response = test_client.post("/api/v1/ask", json=request_data)

        # Should fail validation
        assert response.status_code == 422


class TestCodeReviewEndpoint:
    """Tests for code review endpoint."""

    def test_review_code_success(self, test_client: TestClient) -> None:
        """Test successful code review."""
        request_data = {
            "code": "def hello():\n    print('Hello')",
            "language": "python",
            "context_description": "Simple hello function",
        }

        response = test_client.post("/api/v1/review-code", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "review" in data
        assert data["language"] == "python"

    def test_review_code_missing_fields(self, test_client: TestClient) -> None:
        """Test code review with missing fields."""
        request_data = {
            "code": "def hello():\n    print('Hello')",
        }

        response = test_client.post("/api/v1/review-code", json=request_data)

        # Should fail validation
        assert response.status_code == 422


class TestLearningPathEndpoint:
    """Tests for learning path endpoint."""

    def test_create_learning_path_success(self, test_client: TestClient) -> None:
        """Test successful learning path creation."""
        request_data = {
            "topic": "Python Programming",
            "current_level": "beginner",
            "target_level": "intermediate",
            "time_commitment": "10 hours per week",
        }

        response = test_client.post("/api/v1/learning-path", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "learning_path" in data
        assert data["topic"] == "Python Programming"

    def test_create_learning_path_missing_fields(self, test_client: TestClient) -> None:
        """Test learning path creation with missing fields."""
        request_data = {
            "topic": "Python",
        }

        response = test_client.post("/api/v1/learning-path", json=request_data)

        # Should fail validation
        assert response.status_code == 422


class TestMetricsEndpoint:
    """Tests for metrics endpoint."""

    def test_get_metrics(self, test_client: TestClient) -> None:
        """Test metrics endpoint."""
        response = test_client.get("/api/v1/metrics")

        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "service" in data
        assert "version" in data


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_redirect(self, test_client: TestClient) -> None:
        """Test root endpoint redirects to docs."""
        response = test_client.get("/", follow_redirects=False)

        assert response.status_code == 307  # Temporary redirect
        assert "/api/v1/docs" in response.headers["location"]
