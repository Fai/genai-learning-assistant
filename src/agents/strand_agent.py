"""Strand Agent implementation - A modular agent framework for complex tasks."""

import asyncio
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from src.config import get_settings
from src.services import BedrockService
from src.utils import AgentExecutionError, AgentTimeoutError, get_logger

logger = get_logger(__name__)


class StrandState(str, Enum):
    """Strand execution states."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class StrandMessage:
    """Message in a strand conversation."""

    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class StrandContext:
    """Context for a strand execution."""

    strand_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: StrandState = StrandState.IDLE
    messages: list[StrandMessage] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)
    iteration: int = 0
    max_iterations: int = 10
    start_time: datetime | None = None
    end_time: datetime | None = None
    error: str | None = None

    def add_message(self, role: str, content: str, metadata: dict[str, Any] | None = None) -> None:
        """Add a message to the context."""
        message = StrandMessage(role=role, content=content, metadata=metadata or {})
        self.messages.append(message)

    def get_conversation_history(self) -> list[dict[str, str]]:
        """Get conversation history in API format."""
        return [{"role": msg.role, "content": msg.content} for msg in self.messages]

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "strand_id": self.strand_id,
            "session_id": self.session_id,
            "state": self.state.value,
            "messages": [msg.to_dict() for msg in self.messages],
            "variables": self.variables,
            "iteration": self.iteration,
            "max_iterations": self.max_iterations,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "error": self.error,
        }


class StrandAgent(ABC):
    """Base class for Strand Agents.

    Strand agents are modular, stateful agents that can execute complex multi-step tasks
    with full context awareness and error handling.
    """

    def __init__(self, bedrock_service: BedrockService | None = None) -> None:
        """Initialize strand agent.

        Args:
            bedrock_service: Optional BedrockService instance
        """
        self.settings = get_settings()
        self.bedrock_service = bedrock_service or BedrockService()
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def process_step(self, context: StrandContext) -> StrandContext:
        """Process a single step in the strand execution.

        Args:
            context: Current strand context

        Returns:
            Updated context

        Raises:
            AgentExecutionError: If step processing fails
        """
        pass

    @abstractmethod
    def should_continue(self, context: StrandContext) -> bool:
        """Determine if the strand should continue execution.

        Args:
            context: Current strand context

        Returns:
            True if should continue, False otherwise
        """
        pass

    async def execute(
        self,
        initial_input: str,
        context: StrandContext | None = None,
        timeout: int | None = None,
    ) -> StrandContext:
        """Execute the strand agent.

        Args:
            initial_input: Initial user input
            context: Optional existing context to continue
            timeout: Optional timeout in seconds

        Returns:
            Final context

        Raises:
            AgentExecutionError: If execution fails
            AgentTimeoutError: If execution times out
        """
        # Create or use existing context
        if context is None:
            context = StrandContext(max_iterations=self.settings.max_iterations)

        # Add initial input if this is a new context
        if not context.messages:
            context.add_message("user", initial_input)

        context.state = StrandState.RUNNING
        context.start_time = datetime.utcnow()

        self.logger.info(
            "Starting strand execution",
            strand_id=context.strand_id,
            session_id=context.session_id,
        )

        try:
            # Execute with timeout
            timeout_seconds = timeout or self.settings.agent_timeout
            result = await asyncio.wait_for(
                self._execute_loop(context),
                timeout=timeout_seconds,
            )

            result.state = StrandState.COMPLETED
            result.end_time = datetime.utcnow()

            self.logger.info(
                "Strand execution completed",
                strand_id=result.strand_id,
                iterations=result.iteration,
                duration=(result.end_time - result.start_time).total_seconds(),
            )

            return result

        except asyncio.TimeoutError:
            context.state = StrandState.TIMEOUT
            context.end_time = datetime.utcnow()
            context.error = f"Execution timed out after {timeout_seconds} seconds"

            self.logger.error(
                "Strand execution timed out",
                strand_id=context.strand_id,
                timeout=timeout_seconds,
            )

            raise AgentTimeoutError(
                f"Strand execution timed out after {timeout_seconds} seconds",
                details={"strand_id": context.strand_id, "timeout": timeout_seconds},
            )

        except Exception as e:
            context.state = StrandState.FAILED
            context.end_time = datetime.utcnow()
            context.error = str(e)

            self.logger.error(
                "Strand execution failed",
                strand_id=context.strand_id,
                error=str(e),
            )

            raise AgentExecutionError(
                f"Strand execution failed: {e}",
                details={"strand_id": context.strand_id, "error": str(e)},
            )

    async def _execute_loop(self, context: StrandContext) -> StrandContext:
        """Execute the main processing loop.

        Args:
            context: Strand context

        Returns:
            Updated context

        Raises:
            AgentExecutionError: If max iterations exceeded
        """
        while self.should_continue(context):
            if context.iteration >= context.max_iterations:
                raise AgentExecutionError(
                    f"Maximum iterations ({context.max_iterations}) exceeded",
                    details={"strand_id": context.strand_id, "iterations": context.iteration},
                )

            self.logger.debug(
                "Processing strand step",
                strand_id=context.strand_id,
                iteration=context.iteration,
            )

            # Process the next step
            context = await self.process_step(context)
            context.iteration += 1

        return context

    async def invoke_model(
        self,
        prompt: str,
        system_prompt: str | None = None,
        context: StrandContext | None = None,
    ) -> str:
        """Invoke the Bedrock model with the given prompt.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            context: Optional context for conversation history

        Returns:
            Model response text

        Raises:
            AgentExecutionError: If model invocation fails
        """
        try:
            response = await self.bedrock_service.invoke_model(
                prompt=prompt,
                system_prompt=system_prompt,
            )

            # Extract text from response based on model type
            if "content" in response:
                # Anthropic Claude format
                content_blocks = response["content"]
                text = "".join(block.get("text", "") for block in content_blocks if block.get("type") == "text")
                return text.strip()

            return ""

        except Exception as e:
            self.logger.error("Model invocation failed", error=str(e))
            raise AgentExecutionError(
                f"Model invocation failed: {e}",
                details={"error": str(e)},
            )

    async def pause(self, context: StrandContext) -> None:
        """Pause strand execution.

        Args:
            context: Strand context
        """
        context.state = StrandState.PAUSED
        self.logger.info("Strand execution paused", strand_id=context.strand_id)

    async def resume(self, context: StrandContext) -> StrandContext:
        """Resume paused strand execution.

        Args:
            context: Paused strand context

        Returns:
            Updated context

        Raises:
            AgentExecutionError: If context is not paused
        """
        if context.state != StrandState.PAUSED:
            raise AgentExecutionError(
                "Cannot resume strand that is not paused",
                details={"strand_id": context.strand_id, "state": context.state.value},
            )

        self.logger.info("Resuming strand execution", strand_id=context.strand_id)
        return await self.execute("", context=context)
