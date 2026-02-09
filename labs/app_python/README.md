# DevOps Info Service

A lightweight web service that provides system information and health status, designed for DevOps monitoring and educational purposes.

---

## Features

- System information (OS, architecture, CPU, Python version)
- Health check endpoint for monitoring systems
- Self-documenting API output
- Configurable via environment variables
- Dockerized and published on Docker Hub

---

## Prerequisites

For local (non-Docker) usage:
- Python **3.11+**
- pip package manager

For containerized usage:
- Docker Engine / Docker Desktop

---

## Installation (Local Development)

1. Clone the repository:
```bash
git clone <repository-url>
cd app_python
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate      # macOS / Linux
venv\Scripts\activate       # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

---

## Running the Application (Local)

Default configuration:
```bash
python app.py
```

Application will start at:
```
http://localhost:5000
```

Custom configuration examples:
```bash
PORT=8080 python app.py
HOST=127.0.0.1 PORT=3000 python app.py
```

---

## API Endpoints

| Method | Endpoint | Description |
|------|--------|-------------|
| GET | `/` | Returns service and system information |
| GET | `/health` | Health check endpoint |

---

## Project Structure

```text
app_python/
├── app.py              # Main application
├── requirements.txt    # Python dependencies
├── README.md           # Project documentation
├── .gitignore          # Git ignore rules
├── .dockerignore       # Docker ignore rules
├── Dockerfile          # Docker configuration
├── docs/               # Lab documentation
│   ├── LAB01.md
│   ├── LAB02.md
│   └── screenshots/
│       ├── 01-main-endpoint.png
│       ├── 02-health-check.png
│       └── 03-formatted-output.png
└── tests/              # Unit tests
    └── __init__.py
```

---

## 🐳 Docker Containerization

This application is fully containerized and published to Docker Hub.

---

### Build Image Locally

```bash
docker build -t devops-info-service .
```

---

### Run Container Locally

```bash
docker run -d -p 8080:8080 devops-info-service
```

Application will be available at:
```
http://localhost:8080
```

---

## Using Docker Hub

### Pull Image

```bash
docker pull nayaya0/devops-info-service:1.0
```

### Run Image from Docker Hub

```bash
docker run -d -p 8080:8080 nayaya0/devops-info-service:1.0
```

---

## Docker Hub Repository

- **Repository:** https://hub.docker.com/r/nayaya0/devops-info-service
- **Available tags:** `1.0`, `latest`
- **Architecture:** `linux/arm64/v8` (Apple Silicon compatible)
- **Compressed size:** 46.01 MB

---

## Useful Docker Commands

```bash
docker ps                     # List running containers
docker logs <container-name>  # View container logs
docker stop <container-name>  # Stop container
docker rm <container-name>    # Remove container
docker rmi <image-name>       # Remove image
docker system prune -a        # Cleanup unused resources
```
# Trigger CI/CD
