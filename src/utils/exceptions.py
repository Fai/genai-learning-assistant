"""Custom exceptions for GenAI Learning Assistant."""


class GenAIAssistantError(Exception):
    """Base exception for GenAI Learning Assistant."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        """Initialize exception with message and optional details."""
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(GenAIAssistantError):
    """Raised when there is a configuration error."""

    pass


class ValidationError(GenAIAssistantError):
    """Raised when validation fails."""

    pass


class BedrockError(GenAIAssistantError):
    """Raised when there is an AWS Bedrock error."""

    pass


class AgentError(GenAIAssistantError):
    """Base exception for agent-related errors."""

    pass


class AgentExecutionError(AgentError):
    """Raised when agent execution fails."""

    pass


class AgentTimeoutError(AgentError):
    """Raised when agent execution times out."""

    pass


class RateLimitError(GenAIAssistantError):
    """Raised when rate limit is exceeded."""

    pass


class CacheError(GenAIAssistantError):
    """Raised when there is a cache error."""

    pass
