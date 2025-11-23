# Deployment Guide

This guide covers deploying the GenAI Learning Assistant to various environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Deployment](#local-deployment)
- [Docker Deployment](#docker-deployment)
- [AWS ECS Deployment](#aws-ecs-deployment)
- [Environment Variables](#environment-variables)
- [CI/CD Pipeline](#cicd-pipeline)
- [Monitoring & Logging](#monitoring--logging)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required

- Python 3.11+
- AWS Account with Bedrock access
- AWS CLI configured
- Docker (for containerized deployment)

### AWS Permissions

Your AWS credentials need the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agent-runtime:InvokeAgent",
        "bedrock-agent-runtime:Retrieve"
      ],
      "Resource": "*"
    }
  ]
}
```

## Local Deployment

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/genai-learning-assistant.git
cd genai-learning-assistant
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Run Application

```bash
# Development mode with auto-reload
make run-dev

# Production mode
make run
```

Access the application at `http://localhost:8000`

## Docker Deployment

### Single Container

```bash
# Build image
make docker-build

# Run container
make docker-run
```

### Docker Compose (Recommended)

```bash
# Start all services
make docker-compose-up

# View logs
make docker-compose-logs

# Stop services
make docker-compose-down
```

#### With Monitoring Stack

```bash
docker-compose -f deployment/docker-compose.yml --profile monitoring up -d
```

This starts:
- GenAI Learning Assistant
- Prometheus (http://localhost:9090)
- Grafana (http://localhost:3000)

## AWS ECS Deployment

### Option 1: CloudFormation (Recommended)

#### 1. Prepare ECR Repository

```bash
# Create ECR repository
aws ecr create-repository --repository-name genai-learning-assistant

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
```

#### 2. Build and Push Image

```bash
# Build image
docker build -f deployment/Dockerfile -t genai-learning-assistant:latest .

# Tag for ECR
docker tag genai-learning-assistant:latest \
  ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/genai-learning-assistant:latest

# Push to ECR
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/genai-learning-assistant:latest
```

#### 3. Deploy with CloudFormation

```bash
aws cloudformation deploy \
  --template-file deployment/cloudformation.yml \
  --stack-name genai-learning-assistant \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    ContainerImage=ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/genai-learning-assistant:latest \
    Environment=production \
    BedrockModelId=anthropic.claude-3-sonnet-20240229-v1:0
```

#### 4. Get Load Balancer URL

```bash
aws cloudformation describe-stacks \
  --stack-name genai-learning-assistant \
  --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerURL`].OutputValue' \
  --output text
```

### Option 2: Manual ECS Setup

#### 1. Create ECS Cluster

```bash
aws ecs create-cluster --cluster-name genai-learning-assistant
```

#### 2. Register Task Definition

Edit `deployment/aws-ecs-task-definition.json` with your account details, then:

```bash
aws ecs register-task-definition \
  --cli-input-json file://deployment/aws-ecs-task-definition.json
```

#### 3. Create ECS Service

```bash
aws ecs create-service \
  --cluster genai-learning-assistant \
  --service-name genai-learning-assistant-service \
  --task-definition genai-learning-assistant \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

## Environment Variables

### Required Variables

```bash
# AWS Configuration
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Application Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Optional Variables

```bash
# Bedrock Agent (if using agents)
BEDROCK_AGENT_ID=your_agent_id
BEDROCK_AGENT_ALIAS_ID=your_agent_alias_id

# Knowledge Base (if using KB)
BEDROCK_KNOWLEDGE_BASE_ID=your_kb_id

# AWS Credentials (use IAM roles in production)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Agent Configuration
MAX_TOKENS=4096
TEMPERATURE=0.7
MAX_ITERATIONS=10
AGENT_TIMEOUT=300

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=*
```

### Using AWS Secrets Manager

For production deployments, store sensitive values in AWS Secrets Manager:

```bash
# Create secret
aws secretsmanager create-secret \
  --name genai-assistant/bedrock-agent-id \
  --secret-string "your-agent-id"

# Update ECS task definition to reference secrets
# See deployment/aws-ecs-task-definition.json for examples
```

## CI/CD Pipeline

### GitHub Actions

The repository includes a complete CI/CD pipeline in `.github/workflows/ci-cd.yml`.

#### Setup

1. Configure GitHub Secrets:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`

2. Push to trigger:
   - `develop` branch → Deploys to development
   - `main` branch → Deploys to production

#### Pipeline Stages

1. **Test**: Runs linting and tests
2. **Build**: Builds Docker image
3. **Deploy**: Pushes to ECR and updates ECS service

### Manual Deployment

```bash
# Build and tag
docker build -f deployment/Dockerfile -t genai-learning-assistant:v1.0.0 .

# Push to ECR
docker tag genai-learning-assistant:v1.0.0 \
  ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/genai-learning-assistant:v1.0.0
docker push ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/genai-learning-assistant:v1.0.0

# Update ECS service
aws ecs update-service \
  --cluster genai-learning-assistant \
  --service genai-learning-assistant-service \
  --force-new-deployment
```

## Monitoring & Logging

### CloudWatch Logs

When deployed on AWS, logs are automatically sent to CloudWatch:

```bash
# View logs
aws logs tail /ecs/genai-learning-assistant --follow
```

### Health Checks

```bash
# Check application health
curl http://your-alb-url/api/v1/health
```

### Metrics

```bash
# Get metrics
curl http://your-alb-url/api/v1/metrics
```

### CloudWatch Alarms

Create alarms for critical metrics:

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name genai-assistant-high-error-rate \
  --alarm-description "Alert on high error rate" \
  --metric-name Errors \
  --namespace AWS/ApplicationELB \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 10
```

## Troubleshooting

### Common Issues

#### 1. Bedrock Access Denied

**Error**: `AccessDeniedException: User is not authorized to perform: bedrock:InvokeModel`

**Solution**: Ensure your IAM role/user has the required Bedrock permissions.

```bash
# Test Bedrock access
aws bedrock list-foundation-models --region us-east-1
```

#### 2. Container Fails to Start

**Check logs**:
```bash
docker logs <container-id>
```

**Common causes**:
- Missing environment variables
- Invalid AWS credentials
- Port already in use

#### 3. High Latency

**Causes**:
- Cold start (first request)
- Large prompts
- Network latency to Bedrock

**Solutions**:
- Implement warming (health check calls)
- Use streaming for long responses
- Choose nearest AWS region

#### 4. Rate Limiting

**Error**: `ThrottlingException: Rate exceeded`

**Solutions**:
- Implement exponential backoff (already included)
- Request rate limit increase from AWS
- Implement request queuing

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
make run-dev
```

### Testing Deployment

```bash
# Test health endpoint
curl http://localhost:8000/api/v1/health

# Test ask endpoint
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Test question"}'
```

## Production Checklist

- [ ] Environment variables configured
- [ ] AWS credentials set up (IAM roles preferred)
- [ ] Bedrock model access enabled
- [ ] Docker image built and pushed to ECR
- [ ] ECS cluster and service created
- [ ] Load balancer configured
- [ ] Health checks passing
- [ ] CloudWatch logging enabled
- [ ] Monitoring and alarms set up
- [ ] SSL/TLS certificate configured (for HTTPS)
- [ ] CORS configured appropriately
- [ ] Rate limiting configured
- [ ] Backup and disaster recovery plan
- [ ] Security audit completed

## Rollback Procedure

If deployment fails:

```bash
# Rollback to previous task definition
aws ecs update-service \
  --cluster genai-learning-assistant \
  --service genai-learning-assistant-service \
  --task-definition genai-learning-assistant:PREVIOUS_REVISION
```

## Support

For deployment issues:
- Check CloudWatch logs
- Review ECS service events
- Open a GitHub issue
- Contact AWS support for Bedrock-specific issues
