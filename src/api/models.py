"""Pydantic models for API requests and responses."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Current timestamp")


class ErrorResponse(BaseModel):
    """Error response."""

    error: str = Field(..., description="Error message")
    details: dict[str, Any] | None = Field(default=None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class AskQuestionRequest(BaseModel):
    """Request to ask a question to the learning agent."""

    question: str = Field(..., min_length=1, max_length=4000, description="User's question")
    session_id: str | None = Field(default=None, description="Session ID for conversation continuity")
    learner_level: str | None = Field(default=None, description="Learner's current level")
    learning_preferences: dict[str, Any] | None = Field(
        default=None,
        description="Learning preferences",
    )

    model_config = {"json_schema_extra": {"examples": [{"question": "Can you explain what recursion is?"}]}}


class AskQuestionResponse(BaseModel):
    """Response to a question."""

    answer: str = Field(..., description="Agent's answer")
    session_id: str = Field(..., description="Session ID")
    strand_id: str = Field(..., description="Strand ID")
    learning_goal: str | None = Field(default=None, description="Identified learning goal")
    iteration: int = Field(..., description="Current iteration")
    complete: bool = Field(..., description="Whether learning session is complete")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class CodeReviewRequest(BaseModel):
    """Request for code review."""

    code: str = Field(..., min_length=1, description="Code to review")
    language: str = Field(..., min_length=1, description="Programming language")
    context_description: str = Field(default="", description="Context about the code")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "code": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
                    "language": "python",
                    "context_description": "Recursive fibonacci implementation",
                }
            ]
        }
    }


class CodeReviewResponse(BaseModel):
    """Response for code review."""

    review: str = Field(..., description="Detailed code review")
    language: str = Field(..., description="Programming language")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class LearningPathRequest(BaseModel):
    """Request to create a learning path."""

    topic: str = Field(..., min_length=1, description="Learning topic")
    current_level: str = Field(..., description="Current skill level")
    target_level: str = Field(..., description="Target skill level")
    time_commitment: str = Field(..., description="Available time commitment")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "topic": "Python Programming",
                    "current_level": "beginner",
                    "target_level": "intermediate",
                    "time_commitment": "10 hours per week",
                }
            ]
        }
    }


class LearningPathResponse(BaseModel):
    """Response with learning path."""

    learning_path: dict[str, Any] = Field(..., description="Structured learning path")
    topic: str = Field(..., description="Learning topic")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class SessionSummaryResponse(BaseModel):
    """Learning session summary."""

    session_id: str = Field(..., description="Session ID")
    strand_id: str = Field(..., description="Strand ID")
    learning_goal: str = Field(..., description="Learning goal")
    total_interactions: int = Field(..., description="Total interactions")
    duration_seconds: float | None = Field(default=None, description="Session duration")
    progress: dict[str, Any] = Field(default_factory=dict, description="Learning progress")
    topics_covered: list[str] = Field(default_factory=list, description="Topics covered")
    learning_complete: bool = Field(..., description="Whether learning is complete")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
