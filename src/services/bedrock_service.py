"""AWS Bedrock service implementation with retry logic and error handling."""

import asyncio
import json
from typing import Any, AsyncIterator

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config import get_settings
from src.utils import BedrockError, get_logger

logger = get_logger(__name__)


class BedrockService:
    """Service for interacting with AWS Bedrock Runtime."""

    def __init__(self) -> None:
        """Initialize Bedrock service with AWS credentials and configuration."""
        self.settings = get_settings()
        self._client: Any = None
        self._agent_runtime_client: Any = None
        self._initialize_clients()

    def _initialize_clients(self) -> None:
        """Initialize Bedrock runtime and agent runtime clients."""
        try:
            # Configure boto3 with retry and timeout settings
            config = Config(
                region_name=self.settings.bedrock_runtime_region,
                retries={"max_attempts": self.settings.max_retries, "mode": "adaptive"},
                connect_timeout=30,
                read_timeout=self.settings.agent_timeout,
            )

            # Create session with credentials if provided
            session_kwargs = {}
            if self.settings.aws_access_key_id:
                session_kwargs["aws_access_key_id"] = self.settings.aws_access_key_id
            if self.settings.aws_secret_access_key:
                session_kwargs["aws_secret_access_key"] = self.settings.aws_secret_access_key
            if self.settings.aws_session_token:
                session_kwargs["aws_session_token"] = self.settings.aws_session_token

            session = boto3.Session(**session_kwargs) if session_kwargs else boto3.Session()

            # Initialize Bedrock Runtime client
            self._client = session.client("bedrock-runtime", config=config)

            # Initialize Bedrock Agent Runtime client
            self._agent_runtime_client = session.client("bedrock-agent-runtime", config=config)

            logger.info(
                "Bedrock clients initialized",
                region=self.settings.bedrock_runtime_region,
                model_id=self.settings.bedrock_model_id,
            )

        except Exception as e:
            logger.error("Failed to initialize Bedrock clients", error=str(e))
            raise BedrockError(f"Failed to initialize Bedrock clients: {e}", details={"error": str(e)})

    @retry(
        retry=retry_if_exception_type((ClientError, ConnectionError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def invoke_model(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        stop_sequences: list[str] | None = None,
    ) -> dict[str, Any]:
        """Invoke Bedrock model with the given prompt.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stop_sequences: List of stop sequences

        Returns:
            Model response as dictionary

        Raises:
            BedrockError: If model invocation fails
        """
        try:
            # Prepare request body based on model type
            body = self._prepare_request_body(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens or self.settings.max_tokens,
                temperature=temperature or self.settings.temperature,
                stop_sequences=stop_sequences,
            )

            logger.debug(
                "Invoking Bedrock model",
                model_id=self.settings.bedrock_model_id,
                prompt_length=len(prompt),
            )

            # Invoke model in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._client.invoke_model(
                    modelId=self.settings.bedrock_model_id,
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps(body),
                ),
            )

            # Parse response
            response_body = json.loads(response["body"].read())

            logger.info(
                "Model invocation successful",
                model_id=self.settings.bedrock_model_id,
                input_tokens=response_body.get("usage", {}).get("input_tokens", 0),
                output_tokens=response_body.get("usage", {}).get("output_tokens", 0),
            )

            return response_body

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            logger.error(
                "Bedrock model invocation failed",
                error_code=error_code,
                error_message=error_message,
            )
            raise BedrockError(
                f"Bedrock model invocation failed: {error_message}",
                details={"error_code": error_code, "error_message": error_message},
            )
        except Exception as e:
            logger.error("Unexpected error during model invocation", error=str(e))
            raise BedrockError(f"Unexpected error: {e}", details={"error": str(e)})

    async def invoke_model_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> AsyncIterator[str]:
        """Invoke Bedrock model with streaming response.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Yields:
            Chunks of generated text

        Raises:
            BedrockError: If model invocation fails
        """
        try:
            body = self._prepare_request_body(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens or self.settings.max_tokens,
                temperature=temperature or self.settings.temperature,
            )

            logger.debug(
                "Invoking Bedrock model with streaming",
                model_id=self.settings.bedrock_model_id,
            )

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._client.invoke_model_with_response_stream(
                    modelId=self.settings.bedrock_model_id,
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps(body),
                ),
            )

            # Process streaming response
            stream = response.get("body")
            if stream:
                for event in stream:
                    chunk = event.get("chunk")
                    if chunk:
                        chunk_data = json.loads(chunk.get("bytes").decode())
                        if "delta" in chunk_data:
                            text = chunk_data["delta"].get("text", "")
                            if text:
                                yield text

        except Exception as e:
            logger.error("Streaming invocation failed", error=str(e))
            raise BedrockError(f"Streaming invocation failed: {e}", details={"error": str(e)})

    @retry(
        retry=retry_if_exception_type((ClientError, ConnectionError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def invoke_agent(
        self,
        input_text: str,
        session_id: str,
        enable_trace: bool = True,
        session_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Invoke Bedrock Agent with the given input.

        Args:
            input_text: User input text
            session_id: Session identifier
            enable_trace: Enable trace for debugging
            session_state: Optional session state

        Returns:
            Agent response

        Raises:
            BedrockError: If agent invocation fails
        """
        if not self.settings.bedrock_agent_id or not self.settings.bedrock_agent_alias_id:
            raise BedrockError(
                "Bedrock Agent ID and Alias ID must be configured",
                details={"agent_id": self.settings.bedrock_agent_id},
            )

        try:
            logger.debug(
                "Invoking Bedrock Agent",
                agent_id=self.settings.bedrock_agent_id,
                session_id=session_id,
            )

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._agent_runtime_client.invoke_agent(
                    agentId=self.settings.bedrock_agent_id,
                    agentAliasId=self.settings.bedrock_agent_alias_id,
                    sessionId=session_id,
                    inputText=input_text,
                    enableTrace=enable_trace,
                    sessionState=session_state or {},
                ),
            )

            # Process agent response
            completion = ""
            traces = []

            for event in response.get("completion", []):
                if "chunk" in event:
                    chunk = event["chunk"]
                    completion += chunk.get("bytes", b"").decode("utf-8")
                if "trace" in event and enable_trace:
                    traces.append(event["trace"])

            logger.info(
                "Agent invocation successful",
                agent_id=self.settings.bedrock_agent_id,
                session_id=session_id,
                response_length=len(completion),
            )

            return {"completion": completion, "traces": traces, "session_id": session_id}

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            logger.error(
                "Bedrock agent invocation failed",
                error_code=error_code,
                error_message=error_message,
            )
            raise BedrockError(
                f"Agent invocation failed: {error_message}",
                details={"error_code": error_code, "error_message": error_message},
            )

    def _prepare_request_body(
        self,
        prompt: str,
        system_prompt: str | None,
        max_tokens: int,
        temperature: float,
        stop_sequences: list[str] | None = None,
    ) -> dict[str, Any]:
        """Prepare request body based on model type.

        Args:
            prompt: User prompt
            system_prompt: System prompt
            max_tokens: Maximum tokens
            temperature: Temperature
            stop_sequences: Stop sequences

        Returns:
            Request body dictionary
        """
        # Prepare body for Anthropic Claude models
        messages = [{"role": "user", "content": prompt}]

        body: dict[str, Any] = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": self.settings.top_p,
        }

        if system_prompt:
            body["system"] = system_prompt

        if stop_sequences:
            body["stop_sequences"] = stop_sequences

        return body

    async def retrieve_from_knowledge_base(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[dict[str, Any]]:
        """Retrieve documents from Bedrock Knowledge Base.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of retrieved documents

        Raises:
            BedrockError: If retrieval fails
        """
        if not self.settings.bedrock_knowledge_base_id:
            raise BedrockError(
                "Knowledge Base ID must be configured",
                details={"knowledge_base_id": None},
            )

        try:
            logger.debug(
                "Retrieving from knowledge base",
                knowledge_base_id=self.settings.bedrock_knowledge_base_id,
                query=query,
            )

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._agent_runtime_client.retrieve(
                    knowledgeBaseId=self.settings.bedrock_knowledge_base_id,
                    retrievalQuery={"text": query},
                    retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": max_results}},
                ),
            )

            results = response.get("retrievalResults", [])

            logger.info(
                "Knowledge base retrieval successful",
                knowledge_base_id=self.settings.bedrock_knowledge_base_id,
                results_count=len(results),
            )

            return results

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            logger.error(
                "Knowledge base retrieval failed",
                error_code=error_code,
                error_message=error_message,
            )
            raise BedrockError(
                f"Knowledge base retrieval failed: {error_message}",
                details={"error_code": error_code, "error_message": error_message},
            )
