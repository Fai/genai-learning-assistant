"""Application settings and configuration management."""

import os
from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Settings
    app_name: str = Field(default="GenAI Learning Assistant", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    environment: str = Field(default="development", description="Environment (development/staging/production)")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # API Settings
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_prefix: str = Field(default="/api/v1", description="API route prefix")
    cors_origins: str = Field(default="*", description="CORS allowed origins (comma-separated)")

    # AWS Settings
    aws_region: str = Field(default="us-east-1", description="AWS region")
    aws_access_key_id: Optional[str] = Field(default=None, description="AWS access key ID")
    aws_secret_access_key: Optional[str] = Field(default=None, description="AWS secret access key")
    aws_session_token: Optional[str] = Field(default=None, description="AWS session token")

    # AWS Bedrock Settings
    bedrock_model_id: str = Field(
        default="anthropic.claude-3-sonnet-20240229-v1:0",
        description="Bedrock model ID",
    )
    bedrock_runtime_region: str = Field(default="us-east-1", description="Bedrock runtime region")
    bedrock_agent_id: Optional[str] = Field(default=None, description="Bedrock Agent ID")
    bedrock_agent_alias_id: Optional[str] = Field(default=None, description="Bedrock Agent Alias ID")
    bedrock_knowledge_base_id: Optional[str] = Field(default=None, description="Bedrock Knowledge Base ID")

    # Agent Settings
    max_tokens: int = Field(default=4096, description="Maximum tokens for agent responses")
    temperature: float = Field(default=0.7, description="Agent temperature (0.0-1.0)")
    top_p: float = Field(default=0.9, description="Agent top_p sampling")
    max_iterations: int = Field(default=10, description="Maximum agent iterations")
    agent_timeout: int = Field(default=300, description="Agent timeout in seconds")

    # Retry Settings
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay: int = Field(default=1, description="Initial retry delay in seconds")
    retry_backoff: float = Field(default=2.0, description="Retry backoff multiplier")

    # Rate Limiting
    rate_limit_requests: int = Field(default=100, description="Rate limit requests per minute")
    rate_limit_window: int = Field(default=60, description="Rate limit window in seconds")

    # Cache Settings
    enable_cache: bool = Field(default=True, description="Enable response caching")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")

    # Monitoring Settings
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_port: int = Field(default=9090, description="Metrics port")

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is between 0.0 and 1.0."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Temperature must be between 0.0 and 1.0")
        return v

    @field_validator("top_p")
    @classmethod
    def validate_top_p(cls, v: float) -> float:
        """Validate top_p is between 0.0 and 1.0."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("top_p must be between 0.0 and 1.0")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
