# GenAI Learning Assistant

A production-ready GenAI Learning Assistant powered by AWS Bedrock AgentCore and Strand Agent framework.

[![CI/CD](https://github.com/yourusername/genai-learning-assistant/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/yourusername/genai-learning-assistant/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🚀 Features

- **Advanced AI Learning Agent**: Personalized educational assistance using AWS Bedrock and Anthropic Claude
- **Strand Agent Pattern**: Modular, stateful agent framework for complex multi-step learning interactions
- **Production-Ready**: Complete with logging, monitoring, error handling, and retry logic
- **RESTful API**: FastAPI-based API with OpenAPI documentation
- **Scalable Architecture**: Containerized deployment with Docker and AWS ECS support
- **Multiple Learning Modes**:
  - Concept Explanation
  - Problem Solving
  - Code Review
  - Guided Practice
  - Assessment
  - Personalized Learning Paths

## 📋 Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Monitoring](#monitoring)
- [Contributing](#contributing)
- [License](#license)

## 🏗️ Architecture

### High-Level Architecture

```
┌─────────────────┐
│   API Layer     │ FastAPI + Uvicorn
│   (REST API)    │
└────────┬────────┘
         │
┌────────▼────────┐
│ Learning Agent  │ Strand Agent Pattern
│   (AgentCore)   │
└────────┬────────┘
         │
┌────────▼────────┐
│ Bedrock Service │ AWS Bedrock Runtime
│   (AWS SDK)     │
└────────┬────────┘
         │
┌────────▼────────┐
│  AWS Bedrock    │ Claude 3 Sonnet
│  AgentCore      │
└─────────────────┘
```

### Key Components

1. **Strand Agent Framework**: Modular agent architecture for stateful, multi-step interactions
2. **AWS Bedrock Integration**: Direct integration with AWS Bedrock Runtime API
3. **Learning Agent**: Specialized agent for educational assistance
4. **Configuration Management**: Environment-based configuration with Pydantic
5. **Structured Logging**: JSON-based logging with structlog
6. **Error Handling**: Comprehensive error handling with retry logic

## 📦 Prerequisites

- Python 3.11 or higher
- AWS Account with Bedrock access
- AWS CLI configured (for deployment)
- Docker (optional, for containerized deployment)

### AWS Permissions Required

- `bedrock:InvokeModel`
- `bedrock:InvokeModelWithResponseStream`
- `bedrock-agent-runtime:InvokeAgent`
- `bedrock-agent-runtime:Retrieve`

## 🔧 Installation

### Local Development

1. **Clone the repository**:
```bash
git clone https://github.com/yourusername/genai-learning-assistant.git
cd genai-learning-assistant
```

2. **Create a virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
make install-dev
# Or manually:
pip install -r requirements.txt
```

4. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Run the application**:
```bash
make run-dev
# Or manually:
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Installation

```bash
# Build the image
make docker-build

# Run the container
make docker-run
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Application Settings
ENVIRONMENT=development
LOG_LEVEL=INFO

# AWS Settings
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Bedrock Settings
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_RUNTIME_REGION=us-east-1

# Optional: Agent Configuration
BEDROCK_AGENT_ID=your_agent_id
BEDROCK_AGENT_ALIAS_ID=your_agent_alias_id
BEDROCK_KNOWLEDGE_BASE_ID=your_knowledge_base_id
```

### Configuration Options

All configuration options are defined in `src/config/settings.py`:

- **Application Settings**: Environment, debug mode, logging
- **API Settings**: Host, port, CORS configuration
- **AWS Settings**: Region, credentials
- **Bedrock Settings**: Model ID, agent configuration
- **Agent Settings**: Max tokens, temperature, iterations
- **Retry Settings**: Max retries, backoff configuration

## 💻 Usage

### API Endpoints

Once running, access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`

### Example API Calls

#### Ask a Question

```bash
curl -X POST "http://localhost:8000/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Can you explain what recursion is in programming?"
  }'
```

#### Request Code Review

```bash
curl -X POST "http://localhost:8000/api/v1/review-code" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
    "language": "python",
    "context_description": "Recursive fibonacci implementation"
  }'
```

#### Create Learning Path

```bash
curl -X POST "http://localhost:8000/api/v1/learning-path" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Python Programming",
    "current_level": "beginner",
    "target_level": "intermediate",
    "time_commitment": "10 hours per week"
  }'
```

### Python Client Example

```python
import requests

# Ask a question
response = requests.post(
    "http://localhost:8000/api/v1/ask",
    json={"question": "What is machine learning?"}
)
print(response.json()["answer"])

# Continue conversation
session_id = response.json()["session_id"]
response = requests.post(
    "http://localhost:8000/api/v1/ask",
    json={
        "question": "Can you give me an example?",
        "session_id": session_id
    }
)
```

## 📚 API Documentation

### Endpoints

#### `GET /api/v1/health`
Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

#### `POST /api/v1/ask`
Ask a question to the learning agent.

**Request**:
```json
{
  "question": "What is recursion?",
  "session_id": "optional-session-id",
  "learner_level": "beginner"
}
```

**Response**:
```json
{
  "answer": "Recursion is...",
  "session_id": "abc-123",
  "strand_id": "xyz-789",
  "learning_goal": "concept_explanation",
  "iteration": 1,
  "complete": false
}
```

#### `POST /api/v1/review-code`
Get educational code review.

#### `POST /api/v1/learning-path`
Create a personalized learning path.

#### `GET /api/v1/metrics`
Get application metrics.

## 🛠️ Development

### Running Tests

```bash
# Run all tests with coverage
make test

# Run tests without coverage
make test-quick

# Run specific test file
pytest tests/test_agents.py -v
```

### Code Quality

```bash
# Run linting
make lint

# Format code
make format

# Run all checks
make check
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
make setup-pre-commit

# Run pre-commit on all files
pre-commit run --all-files
```

## 🧪 Testing

The project includes comprehensive unit and integration tests:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test API endpoints and service integration
- **Mocked AWS Services**: Uses mocked Bedrock services for testing

### Test Coverage

Run tests with coverage report:
```bash
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

## 🚢 Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
make docker-compose-up

# View logs
make docker-compose-logs

# Stop services
make docker-compose-down
```

### AWS ECS Deployment

1. **Build and push Docker image**:
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -f deployment/Dockerfile -t genai-learning-assistant:latest .
docker tag genai-learning-assistant:latest ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/genai-learning-assistant:latest
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/genai-learning-assistant:latest
```

2. **Deploy with CloudFormation**:
```bash
aws cloudformation deploy \
  --template-file deployment/cloudformation.yml \
  --stack-name genai-learning-assistant \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides ContainerImage=ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/genai-learning-assistant:latest
```

### Environment-Specific Deployments

- **Development**: Deployed automatically on push to `develop` branch
- **Production**: Deployed automatically on push to `main` branch

See `.github/workflows/ci-cd.yml` for CI/CD configuration.

## 📊 Monitoring

### Application Metrics

- Health checks: `/api/v1/health`
- Metrics endpoint: `/api/v1/metrics`
- CloudWatch integration (when deployed on AWS)

### Logging

- Structured JSON logging in production
- Human-readable logs in development
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

### Optional Monitoring Stack

Start Prometheus and Grafana:
```bash
docker-compose -f deployment/docker-compose.yml --profile monitoring up -d
```

- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000` (default credentials: admin/admin)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run tests: `make check`
5. Commit your changes: `git commit -am 'Add new feature'`
6. Push to the branch: `git push origin feature/my-feature`
7. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- AWS Bedrock for providing the foundation AI models
- Anthropic Claude for the underlying language model
- FastAPI for the excellent web framework
- The open-source community

## 📞 Support

For issues, questions, or contributions, please:
- Open an issue on GitHub
- Contact the maintainers
- Check the documentation in the `docs/` directory

---

**Made with ❤️ using AWS Bedrock AgentCore and Strand Agent**