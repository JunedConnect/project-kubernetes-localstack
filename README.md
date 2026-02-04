# <img src="https://raw.githubusercontent.com/JunedConnect/project-kubernetes-localstack/main/images/localstack-logo.png" alt="LocalStack Logo" width="40" height="40"> Local Cloud

A Flask REST API for user management with avatar uploads. Built with Kind (Kubernetes), LocalStack for AWS emulation, and a complete CI/CD pipeline. Users are stored in DynamoDB with avatars in S3, all running locally without AWS costs.

<br>

## How It Works

1. **LocalStack** emulates AWS services (S3 and DynamoDB) locally
2. **Terraform** provisions the S3 bucket and DynamoDB table through LocalStack
3. **Docker** containerises the Flask application
4. **Kind** creates a local Kubernetes cluster
5. **Helm** deploys the containerised app to the Kubernetes cluster
6. The App API connects to LocalStack to store user data in DynamoDB and avatars in S3
7. **GitHub Actions** automates testing, security scanning, and deployment validation

<br>

## Architecture Overview

```
                                                                        ┌─────────┐
┌────────────────────────────────────────────────────────────────┐      │  User   │
│                    Kind Kubernetes Cluster                     │      │         │
│                                                                │      └────┬────┘
│   ┌─────────────────┐        ┌──────────────────────────┐      │           │
│   │  Deployment     │ ────►  │  Service (NodePort 30080)│ ─────┼───────────┘
│   │  my-app         │        │                          │      │ http://localhost:30080
│   └────────┬────────┘        └──────────────────────────┘      │
│            │                                                   │
└────────────┼───────────────────────────────────────────────────┘
             │
             │ http://host.docker.internal:4566
             │ (or http://DockerbridgegatewayIP:4566)
             ▼
┌────────────────────────────────────────────────────────────────┐
│                    LocalStack (0.0.0.0:4566)                   │
│                                                                │
│   ┌─────────────────────┐      ┌────────────────────────┐      │
│   │  DynamoDB           │      │  S3                    │      │
│   │  my-app-table       │      │  my-app-bucket         │      │
│   └─────────────────────┘      └────────────────────────┘      │
└────────────────────────────────────────────────────────────────┘
```

<br>

## Directory Structure

```
./
├── .github/
│   └── workflows/
│       └── tests.yaml
├── app/
│   ├── my_app/
│   ├── tests/
│   ├── dockerfile
│   └── pyproject.toml
├── helm-chart
│   └── my-app/
├── terraform/
│   └── modules/
├── scripts/
│   ├── setup.sh
│   ├── teardown.sh
│   └── test-api.sh
├── .pre-commit-config.yaml
└── kind-config.yaml
```

<br>

## Design Decisions

### LocalStack for AWS Emulation

**Why LocalStack**: Provides a local AWS environment without cloud costs or account setup requirements. This enables:
- Zero-cost development and testing
- Faster iteration cycles (no network latency)
- Safe experimentation without affecting actual AWS infrastructure

**Critical Implementation**: LocalStack must bind to `0.0.0.0:4566` on Linux (GitHub Actions) because pods inside Kind cannot reach `localhost`. The solution extracts the Docker bridge gateway IP that Kind uses to reach the host:
```bash
HOST_IP=$(docker exec my-app-cluster-control-plane ip route show | grep default | awk '{print $3}')
```

<br>

### Dockerfile Design

**Multi-stage Build**
- First stage installs Poetry and dependencies
- Second stage copies only runtime files
- Result: Smaller final image, faster builds, reduced attack surface

**Non-root User**
- Prevents privilege escalation attacks

**SHA-based Base Images**
- Base images pinned with SHA256 digests (e.g., `python:3.10@sha256:...`)
- Ensures immutable, reproducible builds
- Guarantees same base image across all environments

<br>

### Helm Chart Features

**High Availability**
- 3 replicas ensure service continuity during node failures
- Pod disruption budgets maintain minimum 1 pod during updates
- Rolling updates with `maxSurge: 1, maxUnavailable: 0` for zero downtime

**Health Checks**
- Readiness probe - prevents traffic to unready pods
- Liveness probe - restarts unhealthy pods automatically

**Resource Management**
- Resource requests ensure guaranteed CPU and memory allocation per pod
- Resource limits prevent pods from consuming excessive resources
- HorizontalPodAutoscaler automatically scales between 3-10 replicas based on load

**Security**
- Non-root user prevents privilege escalation
- Read-only root filesystem limits attack surface
- All Linux capabilities dropped for minimal permissions

<br>

### CI/CD Pipeline Structure

**Quality Gates (Parallel Execution)**
1. **Code Linting**
2. **Unit Tests**
3. **Docker Build & Scan**
4. **Terraform Validation**
5. **Helm Validation**
6. **Repo Security**

**Why Parallel**: Quality checks run simultaneously, failing fast and saving CI time

<br>

**Integration Testing (Independent)**

7. **Integration Tests** - Full end-to-end deployment with LocalStack + Kind
   - Tests AWS integration (not mocked)
   - Validates Kubernetes deployment, networking, and health checks

<br>

**Reporting**

8. **Pipeline Summary** - Aggregates all job statuses for quick review

<br>

**App Code Testing Strategy Choices**
- Unit tests use mocked boto3 for speed and reliability
- Integration tests use LocalStack for accurate AWS behaviour validation
- Coverage threshold at 70% balances quality with pragmatism
- Trivy configured for HIGH/CRITICAL vulnerabilities only

<br>

## Setup

### Prerequisites

- Docker
- Kind
- kubectl
- Helm
- Terraform
- AWS CLI
- LocalStack CLI
- Python 3.8+

<br>

### Configuration

Update configuration if needed:
- **Helm values**: [helm-chart/my-app/values.yaml](helm-chart/my-app/values.yaml)
- **Terraform variables**: [terraform/terraform.tfvars](terraform/terraform.tfvars)

<br>

### Local Setup

**setup.sh**
- Starts LocalStack for AWS service emulation
- Provisions S3 bucket and DynamoDB table with Terraform
- Creates Kind Kubernetes cluster
- Builds Docker image and loads it into Kind
- Deploys application with Helm

```bash
./scripts/setup.sh
```

<br>

**test-api.sh**
- Tests GET /swagger/ UI endpoint
- Tests GET /users endpoint
- Tests POST /user with avatar upload

```bash
./scripts/test-api.sh
```

<br>

**teardown.sh**
- Removes Helm deployment
- Deletes Kind cluster
- Destroys Terraform infrastructure
- Stops LocalStack

```bash
./scripts/teardown.sh
```

<br>

## CI/CD Pipeline

The GitHub Actions pipeline runs 8 automated jobs on every push and pull request to the main branch:

**Quality & Security**

1. **Code Linting** - Ruff and mypy check Python code quality and types
2. **Unit Tests** - pytest with 70% coverage threshold
3. **Docker Build & Scan** - Builds image and runs Trivy vulnerability scan
4. **Terraform Validation** - Format check, validation, and Checkov security scan
5. **Helm Validation** - Helm lint and template rendering
6. **Repo Security** - Trivy filesystem scan and Gitleaks secret detection

**Integration Testing**

7. **Integration Tests** - Full end-to-end deployment testing
   - Starts LocalStack with AWS services (S3, DynamoDB)
   - Provisions infrastructure with Terraform
   - Creates Kind cluster and extracts Docker bridge IP
   - Builds and loads app image into Kind
   - Deploys with Helm using LocalStack endpoint
   - Tests API endpoints (/swagger/, GET /users, POST /user)

**Reporting**

8. **Pipeline Summary** - Aggregates all job statuses

<br>

All quality and security jobs must pass before merging to main. Integration test will run independently.

<br>

## API Usage

**Swagger UI**
```bash
curl http://localhost:30080/swagger/
```

**Get Users**
```bash
curl http://localhost:30080/users
```

**Create User**
```bash
# Create a test image
echo -n "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" | base64 -d > /tmp/test-avatar.png

# Create user with avatar
curl -X POST http://localhost:30080/user \
  -F "name=John Doe" \
  -F "email=john@example.com" \
  -F "avatar=@/tmp/test-avatar.png"

# Cleanup
rm /tmp/test-avatar.png
```

<br>

## Future Improvements

### EKS Deployment

- Deploy to production-grade EKS cluster
- Replace LocalStack with actual AWS services (DynamoDB, S3)
- Configure pod identity to assume IAM role for DynamoDB and S3 access

### Observability & Monitoring (Prometheus & Grafana Stack)

- Add `/metrics` endpoint to my-app for application-specific metrics (request counts, latency, error rates)
- Deploy Prometheus Operator on EKS to scrape metrics from my-app pods (user creation rates, S3 upload success/failures, DynamoDB response times)
- Set up custom Grafana dashboards for visualisation of my-app metrics
- Configure alerting (e.g. high error rates, latency, resource exhaustion)

### Security Enhancements

- Replace environment variables with Kubernetes Secrets
- Integrate External Secrets Operator with AWS Secrets Manager
- Implement Kubernetes Network Policies to restrict pod-to-pod communication

### Domain Management

- Deploy nginx-ingress controller on EKS to manage traffic to the Kubernetes cluster
- Integrate External-DNS for automatic Route53 DNS record management
- Enable certificate management with Cert-Manager

### CI/CD Enhancements

- Integrate FluxCD or ArgoCD for EKS deployment, and separate infrastructure and application into separate repositories
- Use ECR (Elastic Container Registry) for storing container images with immutable tags and lifecycle policies