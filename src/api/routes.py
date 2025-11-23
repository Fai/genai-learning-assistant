"""API routes for GenAI Learning Assistant."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from src import __version__
from src.agents import LearningAgent
from src.services import BedrockService
from src.utils import AgentError, BedrockError, get_logger

from .models import (
    AskQuestionRequest,
    AskQuestionResponse,
    CodeReviewRequest,
    CodeReviewResponse,
    ErrorResponse,
    HealthResponse,
    LearningPathRequest,
    LearningPathResponse,
)

logger = get_logger(__name__)

# Create router
router = APIRouter()

# Initialize services (will be dependency injected in production)
bedrock_service = BedrockService()
learning_agent = LearningAgent(bedrock_service=bedrock_service)


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns:
        Health status
    """
    return HealthResponse(status="healthy", version=__version__)


@router.post(
    "/ask",
    response_model=AskQuestionResponse,
    status_code=status.HTTP_200_OK,
    tags=["Learning"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
async def ask_question(request: AskQuestionRequest) -> AskQuestionResponse:
    """Ask a question to the learning agent.

    Args:
        request: Question request

    Returns:
        Agent's response

    Raises:
        HTTPException: If question processing fails
    """
    try:
        logger.info(
            "Processing question",
            session_id=request.session_id,
            question_length=len(request.question),
        )

        # Ask question
        response = await learning_agent.ask_question(
            question=request.question,
            session_id=request.session_id,
        )

        logger.info(
            "Question processed successfully",
            session_id=response["session_id"],
            strand_id=response["strand_id"],
        )

        return AskQuestionResponse(
            answer=response["answer"],
            session_id=response["session_id"],
            strand_id=response["strand_id"],
            learning_goal=response.get("learning_goal"),
            iteration=response["iteration"],
            complete=response["complete"],
        )

    except AgentError as e:
        logger.error("Agent error processing question", error=str(e), details=e.details)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": e.message, "details": e.details},
        )
    except BedrockError as e:
        logger.error("Bedrock error processing question", error=str(e), details=e.details)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": e.message, "details": e.details},
        )
    except Exception as e:
        logger.error("Unexpected error processing question", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "details": {"message": str(e)}},
        )


@router.post(
    "/review-code",
    response_model=CodeReviewResponse,
    status_code=status.HTTP_200_OK,
    tags=["Learning"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
async def review_code(request: CodeReviewRequest) -> CodeReviewResponse:
    """Review code and provide educational feedback.

    Args:
        request: Code review request

    Returns:
        Code review response

    Raises:
        HTTPException: If code review fails
    """
    try:
        logger.info(
            "Processing code review",
            language=request.language,
            code_length=len(request.code),
        )

        review = await learning_agent.review_code(
            code=request.code,
            language=request.language,
            context_description=request.context_description,
        )

        logger.info("Code review completed successfully", language=request.language)

        return CodeReviewResponse(review=review, language=request.language)

    except Exception as e:
        logger.error("Error processing code review", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to review code", "details": {"message": str(e)}},
        )


@router.post(
    "/learning-path",
    response_model=LearningPathResponse,
    status_code=status.HTTP_200_OK,
    tags=["Learning"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
async def create_learning_path(request: LearningPathRequest) -> LearningPathResponse:
    """Create a personalized learning path.

    Args:
        request: Learning path request

    Returns:
        Learning path response

    Raises:
        HTTPException: If learning path creation fails
    """
    try:
        logger.info(
            "Creating learning path",
            topic=request.topic,
            current_level=request.current_level,
            target_level=request.target_level,
        )

        learning_path = await learning_agent.create_learning_path(
            topic=request.topic,
            current_level=request.current_level,
            target_level=request.target_level,
            time_commitment=request.time_commitment,
        )

        logger.info("Learning path created successfully", topic=request.topic)

        return LearningPathResponse(learning_path=learning_path, topic=request.topic)

    except Exception as e:
        logger.error("Error creating learning path", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to create learning path", "details": {"message": str(e)}},
        )


@router.get("/metrics", tags=["Monitoring"])
async def get_metrics() -> dict[str, Any]:
    """Get application metrics.

    Returns:
        Metrics dictionary
    """
    # Placeholder for metrics - integrate with Prometheus or CloudWatch in production
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "service": "genai-learning-assistant",
        "version": __version__,
        "metrics": {
            "total_requests": "N/A",
            "active_sessions": "N/A",
            "avg_response_time": "N/A",
        },
    }


# Exception handlers
@router.exception_handler(HTTPException)
async def http_exception_handler(request: Any, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions.

    Args:
        request: Request object
        exc: HTTP exception

    Returns:
        JSON error response
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=str(exc.detail),
            details={"status_code": exc.status_code},
        ).model_dump(),
    )
