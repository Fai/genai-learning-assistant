# Architecture Documentation

## Overview

The GenAI Learning Assistant is built on a modular, production-ready architecture that leverages AWS Bedrock AgentCore and implements the Strand Agent pattern for complex, multi-step learning interactions.

## System Architecture

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        Client Layer                           │
│  (Web Browsers, Mobile Apps, CLI, API Clients)               │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            │ HTTPS/REST
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                      API Gateway/ALB                          │
│              (Load Balancing & SSL Termination)              │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                      FastAPI Application                      │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              API Layer (REST Endpoints)                │  │
│  │  - /ask, /review-code, /learning-path, /health        │  │
│  └─────────────────────┬──────────────────────────────────┘  │
│                        │                                      │
│  ┌─────────────────────▼──────────────────────────────────┐  │
│  │            Learning Agent (Strand Agent)              │  │
│  │  - State Management                                    │  │
│  │  - Context Tracking                                    │  │
│  │  - Goal Identification                                 │  │
│  │  - Progress Monitoring                                 │  │
│  └─────────────────────┬──────────────────────────────────┘  │
│                        │                                      │
│  ┌─────────────────────▼──────────────────────────────────┐  │
│  │         Bedrock Service (AWS Integration)             │  │
│  │  - Model Invocation                                    │  │
│  │  - Agent Runtime                                       │  │
│  │  - Knowledge Base Retrieval                            │  │
│  │  - Retry Logic & Error Handling                        │  │
│  └─────────────────────┬──────────────────────────────────┘  │
└────────────────────────┼──────────────────────────────────────┘
                         │
                         │ AWS SDK (Boto3)
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                     AWS Bedrock                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │           Bedrock Runtime                            │    │
│  │  - Claude 3 Sonnet Model                             │    │
│  │  - Claude 3 Haiku Model (optional)                   │    │
│  └──────────────────────────────────────────────────────┘    │
│  ┌──────────────────────────────────────────────────────┐    │
│  │        Bedrock Agent Runtime (optional)              │    │
│  │  - Agent Execution                                   │    │
│  │  - Action Groups                                     │    │
│  └──────────────────────────────────────────────────────┘    │
│  ┌──────────────────────────────────────────────────────┐    │
│  │       Knowledge Bases (optional)                     │    │
│  │  - Vector Search                                     │    │
│  │  - Document Retrieval                                │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. API Layer (`src/api/`)

**Purpose**: Expose learning agent functionality through RESTful endpoints.

**Key Files**:
- `routes.py`: API endpoint definitions
- `models.py`: Pydantic request/response models

**Responsibilities**:
- HTTP request handling
- Input validation
- Response formatting
- Error handling and HTTP status codes

### 2. Strand Agent Framework (`src/agents/strand_agent.py`)

**Purpose**: Provide a modular, stateful agent framework for multi-step interactions.

**Key Concepts**:
- **StrandContext**: Maintains conversation state, variables, and metadata
- **StrandState**: Tracks execution lifecycle (IDLE, RUNNING, COMPLETED, etc.)
- **StrandMessage**: Represents individual messages in the conversation
- **StrandAgent**: Abstract base class for implementing specialized agents

**Features**:
- Stateful conversation management
- Iteration tracking and limits
- Timeout handling
- Pause/resume capabilities
- Context serialization

### 3. Learning Agent (`src/agents/learning_agent.py`)

**Purpose**: Specialized agent for educational assistance.

**Learning Goals**:
- Concept Explanation
- Problem Solving
- Code Review
- Guided Practice
- Assessment
- Personalized Learning Paths

**Key Methods**:
- `ask_question()`: Handle single question with session continuity
- `review_code()`: Provide educational code review
- `create_learning_path()`: Generate personalized learning roadmap
- `get_learning_summary()`: Generate session summary

### 4. Bedrock Service (`src/services/bedrock_service.py`)

**Purpose**: Interface with AWS Bedrock Runtime and Agent Runtime APIs.

**Key Features**:
- Model invocation (synchronous and streaming)
- Agent invocation
- Knowledge base retrieval
- Automatic retry logic with exponential backoff
- Error handling and logging

**AWS Services Integration**:
- `bedrock-runtime`: For direct model invocation
- `bedrock-agent-runtime`: For agent execution
- CloudWatch: For logging and metrics (when deployed)

### 5. Configuration Management (`src/config/`)

**Purpose**: Centralized configuration with environment variable support.

**Key Features**:
- Pydantic-based settings with validation
- Environment-specific configuration
- Default values with overrides
- Type-safe configuration access

**Configuration Categories**:
- Application settings
- API settings
- AWS credentials and region
- Bedrock model configuration
- Agent parameters
- Retry and timeout settings

### 6. Utilities (`src/utils/`)

**Components**:
- **Logger** (`logger.py`): Structured logging with structlog
- **Exceptions** (`exceptions.py`): Custom exception hierarchy

## Data Flow

### Question-Answer Flow

1. **Client Request**: User sends question via `/api/v1/ask` endpoint
2. **API Layer**: Validates request, extracts parameters
3. **Learning Agent**:
   - Creates or retrieves StrandContext
   - Identifies learning goal
   - Builds context-aware prompt
4. **Bedrock Service**:
   - Prepares request for Bedrock API
   - Invokes Claude model
   - Handles retries on failures
5. **Response Processing**:
   - Extracts model response
   - Updates context with agent response
   - Tracks learning progress
6. **API Response**: Returns formatted response to client

### Code Review Flow

1. Client submits code for review
2. Learning Agent constructs educational review prompt
3. Bedrock Service invokes model with code context
4. Response includes:
   - What code does well
   - Areas for improvement
   - Best practices
   - Learning opportunities

## State Management

### StrandContext State Diagram

```
IDLE → RUNNING → COMPLETED
  ↓       ↓         ↑
  ↓    PAUSED ──────┘
  ↓       ↓
  └─→ FAILED
  └─→ TIMEOUT
```

**State Transitions**:
- `IDLE → RUNNING`: When execution starts
- `RUNNING → PAUSED`: When pause() is called
- `PAUSED → RUNNING`: When resume() is called
- `RUNNING → COMPLETED`: When should_continue() returns False
- `RUNNING → FAILED`: When an error occurs
- `RUNNING → TIMEOUT`: When execution exceeds timeout

## Scalability Considerations

### Horizontal Scaling

- Stateless API design allows multiple instances
- Session state managed via session_id (can be externalized to Redis/DynamoDB)
- Load balancer distributes traffic across instances

### Vertical Scaling

- Async/await pattern for I/O operations
- Thread pool for blocking AWS SDK calls
- Configurable timeouts and concurrency limits

### AWS Infrastructure

- **ECS Fargate**: Serverless container orchestration
- **Application Load Balancer**: Traffic distribution
- **CloudWatch**: Centralized logging and metrics
- **Secrets Manager**: Secure credential storage

## Security

### Authentication & Authorization

- API key authentication (to be implemented)
- AWS IAM roles for Bedrock access
- VPC security groups for network isolation

### Data Protection

- HTTPS/TLS for data in transit
- AWS KMS for encryption at rest (when using Knowledge Bases)
- No storage of sensitive user data

### Input Validation

- Pydantic models for request validation
- Input size limits
- SQL injection prevention (no database in current implementation)

## Monitoring & Observability

### Logging

- Structured JSON logging in production
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Context-aware logging with request IDs

### Metrics

- Health check endpoint
- Metrics endpoint (Prometheus-compatible)
- CloudWatch metrics (when deployed on AWS)

### Tracing

- Request/response logging
- Bedrock API call tracing
- Error tracking with stack traces

## Performance Optimization

### Caching Strategy

- Response caching (configurable)
- Session context caching
- TTL-based cache invalidation

### Rate Limiting

- Request rate limiting per client
- Configurable limits
- Token bucket algorithm

### Timeout Management

- Request-level timeouts
- Model invocation timeouts
- Graceful degradation on timeout

## Future Enhancements

1. **Multi-Model Support**: Support for multiple Bedrock models
2. **Session Persistence**: External session storage (Redis/DynamoDB)
3. **Real-time Features**: WebSocket support for streaming responses
4. **Advanced Analytics**: Learning progress analytics and reporting
5. **Multi-tenancy**: Support for multiple organizations
6. **Knowledge Base Integration**: Enhanced RAG capabilities
7. **Custom Action Groups**: Extend agent capabilities with custom actions
