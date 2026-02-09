# Lab 3 Report: Continuous Integration and Delivery (CI/CD)

## Objective
To create an automated Continuous Integration and Delivery (CI/CD) pipeline for a Python Flask application using GitHub Actions, including automated testing, Docker image building, and publishing to Docker Hub.

## Initial State
- Python Flask application from Lab 1
- Docker containerization from Lab 2
- 14 unit tests created and passing locally

##  Project Structure After Lab 3
```
labs/
├── .github/
│   └── workflows/
│       └── python-ci.yml          # CI/CD pipeline configuration
└── app_python/
    ├── app.py                     # Main Flask application
    ├── Dockerfile                 # Docker configuration
    ├── requirements.txt           # Python dependencies
    ├── tests/                     # Unit tests (14 tests)
    │   ├── __init__.py
    │   ├── test_app.py
    │   └── test_health.py
    ├── docs/
    │   └── LAB03.md               # This documentation
    └── README.md                  # Updated with CI badge
```

## 🔧 Implemented Components

### 1. Unit Testing Framework (3 points)

**Framework Selection**: `pytest`

- Most popular Python testing framework
- Simple and readable syntax
- Rich ecosystem and plugins
- Strong community support

**Test Coverage**:
- 14 unit tests in total
- Endpoints tested: `/`, `/health`
- JSON structure validation
- Error handling (404)
- Helper function testing (`get_uptime()`)

**Test Execution**:
```bash
pytest -v
14 passed in 2.09s
```

**Dependencies Added**:
```txt
Flask==3.1.0
pytest==8.0.0
pytest-cov==4.1.0
flake8==7.0.0
```

---

### 2. GitHub Actions CI/CD Pipeline (4 points)

**Workflow File**: `.github/workflows/python-ci.yml`

**Pipeline Features**:
- Triggered on push and pull requests
- Path-based filtering for efficiency
- Separate jobs for testing and Docker build

**Jobs**:
1. **Lint and Test**
   - Setup Python
   - Install dependencies
   - Run flake8
   - Run pytest

2. **Docker Build & Push**
   - Runs only on push to `main`
   - Logs into Docker Hub
   - Builds image
   - Pushes with tags

**Versioning Strategy**:
- `latest` for main branch
- `sha-<commit>` for traceability

**Dockerfile**:
```dockerfile
FROM python:3.13-slim
RUN groupadd -r appuser && useradd --no-log-init -r -g appuser appuser
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=appuser:appuser . .
USER appuser
EXPOSE 8080
CMD ["python", "app.py"]
```

---

### 3. CI/CD Best Practices (3 points)

1. **Path-Based Triggers**
```yaml
paths:
  - 'app_python/**'
  - '.github/workflows/python-ci.yml'
```

2. **Dependency Caching**
```yaml
cache: 'pip'
cache-dependency-path: 'app_python/requirements.txt'
```

3. **Security**
- Non-root Docker user
- Slim base image
- Minimal attack surface

4. **CI Status Badge**
```markdown
![Python CI/CD](https://github.com/username/repo/actions/workflows/python-ci.yml/badge.svg)
```

---

##  Key Decisions and Rationale

### Testing Framework
`pytest` chosen over `unittest` due to readability, fixtures, and ecosystem.

### Versioning
Hybrid tagging (`latest` + commit SHA) for simplicity and reproducibility.

### Docker Security
- Non-root execution
- Reduced image size
- No unnecessary packages

---

##  Workflow Execution

```
lint-test
├── Checkout
├── Python setup
├── Install deps
├── flake8
└── pytest (14 passed)

docker-build
├── Docker login
├── Build image
└── Push to Docker Hub
```

---

## Performance Metrics

### Local
- Tests: ~2s
- Docker build: ~30s
- Image size: ~120MB

### CI
- Total time: 2–3 minutes
- Cached deps: ~10s
- Docker push: ~90s

---

##  Technical Details

### Secrets
- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`

### Test Design
- Fixtures
- Parameterized tests
- Clear assertions
- No mocks

---

##  Acceptance Criteria

### Unit Testing
- [x] pytest selected
- [x] Tests in correct directory
- [x] All endpoints covered
- [x] All tests pass

### CI/CD
- [x] GitHub Actions workflow
- [x] Lint + tests
- [x] Docker build and push
- [x] Proper tagging

### Best Practices
- [x] Status badge
- [x] Caching
- [x] Security measures

---

##  Challenges

### Timing Issues
Fixed flaky uptime test by increasing delay.

### Docker Permissions
Solved by logging to stdout.

### Slow Dependencies
Solved via pip caching.

---

##  Lessons Learned
- Path filtering saves CI time
- Docker caching is critical
- Non-root containers need planning
- pytest fixtures are powerful

---

##  Future Improvements
- Multi-arch Docker builds
- Vulnerability scanning
- Staging environment
- GitOps with ArgoCD

---

## Conclusion
A full CI/CD pipeline was successfully implemented using GitHub Actions.  
All tests pass, Docker images are built and published automatically, and best practices were applied.


