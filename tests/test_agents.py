"""Tests for agent implementations."""

import pytest

from src.agents import LearningAgent, StrandAgent, StrandContext, StrandState
from src.utils import AgentExecutionError


class TestStrandAgent:
    """Tests for StrandAgent base class."""

    async def test_strand_context_creation(self) -> None:
        """Test strand context creation."""
        context = StrandContext()

        assert context.state == StrandState.IDLE
        assert context.iteration == 0
        assert len(context.messages) == 0
        assert context.strand_id is not None
        assert context.session_id is not None

    async def test_add_message_to_context(self) -> None:
        """Test adding messages to context."""
        context = StrandContext()
        context.add_message("user", "Hello", metadata={"test": "value"})

        assert len(context.messages) == 1
        assert context.messages[0].role == "user"
        assert context.messages[0].content == "Hello"
        assert context.messages[0].metadata["test"] == "value"

    async def test_context_to_dict(self) -> None:
        """Test context serialization."""
        context = StrandContext()
        context.add_message("user", "Test message")

        context_dict = context.to_dict()

        assert context_dict["strand_id"] == context.strand_id
        assert context_dict["session_id"] == context.session_id
        assert context_dict["state"] == StrandState.IDLE.value
        assert len(context_dict["messages"]) == 1


@pytest.mark.asyncio
class TestLearningAgent:
    """Tests for LearningAgent."""

    async def test_ask_question(self, learning_agent: LearningAgent, sample_question: str) -> None:
        """Test asking a question."""
        response = await learning_agent.ask_question(sample_question)

        assert "answer" in response
        assert "session_id" in response
        assert "strand_id" in response
        assert response["answer"] != ""

    async def test_identify_learning_goal(self, learning_agent: LearningAgent) -> None:
        """Test learning goal identification."""
        # Test concept explanation
        goal = await learning_agent._identify_learning_goal("Can you explain what recursion is?")
        assert goal == "concept_explanation"

        # Test problem solving
        goal = await learning_agent._identify_learning_goal("Help me solve this problem")
        assert goal == "problem_solving"

        # Test code review
        goal = await learning_agent._identify_learning_goal("Please review my code")
        assert goal == "code_review"

    async def test_code_review(self, learning_agent: LearningAgent, sample_code: dict[str, str]) -> None:
        """Test code review functionality."""
        review = await learning_agent.review_code(
            code=sample_code["code"],
            language=sample_code["language"],
            context_description="Fibonacci implementation",
        )

        assert isinstance(review, str)
        assert len(review) > 0

    async def test_create_learning_path(self, learning_agent: LearningAgent) -> None:
        """Test learning path creation."""
        learning_path = await learning_agent.create_learning_path(
            topic="Python Programming",
            current_level="beginner",
            target_level="intermediate",
            time_commitment="10 hours per week",
        )

        assert isinstance(learning_path, dict)
        assert "topic" in learning_path or "plan" in learning_path

    async def test_get_learning_summary(self, learning_agent: LearningAgent) -> None:
        """Test learning summary generation."""
        # Create a context with some data
        context = StrandContext()
        context.add_message("user", "Test question")
        context.add_message("assistant", "Test answer")
        context.variables["learning_goal"] = "concept_explanation"

        summary = await learning_agent.get_learning_summary(context)

        assert summary["session_id"] == context.session_id
        assert summary["strand_id"] == context.strand_id
        assert summary["learning_goal"] == "concept_explanation"
        assert summary["total_interactions"] > 0

    async def test_should_continue(self, learning_agent: LearningAgent) -> None:
        """Test should_continue logic."""
        context = StrandContext(max_iterations=5)

        # Should continue initially
        assert learning_agent.should_continue(context) is True

        # Should not continue when marked complete
        context.variables["learning_complete"] = True
        assert learning_agent.should_continue(context) is False

    async def test_session_continuity(self, learning_agent: LearningAgent) -> None:
        """Test that sessions maintain continuity."""
        # First question
        response1 = await learning_agent.ask_question("What is Python?")
        session_id = response1["session_id"]

        # Second question in same session
        response2 = await learning_agent.ask_question(
            "Can you give me an example?",
            session_id=session_id,
        )

        assert response2["session_id"] == session_id
        assert response2["iteration"] > 0
