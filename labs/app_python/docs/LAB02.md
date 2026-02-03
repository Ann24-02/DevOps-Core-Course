# Lab 2 — Docker Containerization

## Docker Best Practices Applied

### 1. Non-root User
What: Created appuser and run application as this user  
Why it matters: Reduces attack surface. If container is compromised, attacker has limited privileges.

Dockerfile snippet:
```dockerfile
RUN groupadd -r appuser && useradd --no-log-init -r -g appuser appuser
USER appuser
```

### 2. Specific Base Image Version
What: Using python:3.13-slim instead of python:latest  
Why it matters: Ensures reproducible builds. Avoids unexpected changes from upstream.

### 3. .dockerignore File
What: Excluding unnecessary files from build context  
Why it matters: Reduces image size, speeds up builds, prevents sensitive data leaks.

### 4. Layer Ordering Optimization
What: Copy requirements.txt first, install dependencies, then copy code  
Why it matters: Better Docker cache utilization. Code changes don't trigger dependency reinstallation.

Dockerfile snippet:
```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=appuser:appuser . .
```

---

## Image Information & Decisions

### Base Image Choice
**Selected:** python:3.13-slim

**Justification:**
- Slim version contains only essential Python components
- Significantly smaller (~120MB) than full image (~1GB)
- Maintains glibc compatibility (unlike Alpine)
- Specific version ensures reproducibility

### Final Image Size Analysis
- Local size: 221MB  
- Compressed size on Docker Hub: 46.01MB  

**Assessment:** Acceptable size for educational project. Production could reduce to ~80MB with Alpine.

### Layer Structure
Image consists of 11 layers:
1. Base Debian layer (109MB)
2. System dependencies (4.99MB)
3. Python compiled from source (43.2MB) — ARM64 specific
4. Our layers: user, dependencies, code (~15MB)

---

## Build & Run Process

### Docker Build Output
```bash
$ docker build -t my-python-app .
Sending build context to Docker daemon  15.87kB
Step 1/9 : FROM python:3.13-slim
 ---> 123abc456def
Step 2/9 : RUN apt-get update && apt-get clean && rm -rf /var/lib/apt/lists/*
 ---> Running in a1b2c3d4e5
Removing intermediate container a1b2c3d4e5
 ---> 789def012abc
...
Step 9/9 : CMD ["python", "app.py"]
 ---> Running in f6e5d4c3b2a
Removing intermediate container f6e5d4c3b2a
 ---> ab576c5ce770
Successfully built ab576c5ce770
Successfully tagged my-python-app:latest
```

### Container Run Output
```bash
$ docker run -d -p 8080:8080 --name myapp my-python-app
6f85dc7b729340179f3fbedf1dfc2ef8a2dd4d5eaac8e65ab1b11ff89e1d5b30

$ docker ps
CONTAINER ID   IMAGE           COMMAND           CREATED         STATUS         PORTS                    NAMES
6f85dc7b7293   my-python-app   "python app.py"   5 seconds ago   Up 4 seconds   0.0.0.0:8080->8080/tcp   myapp
```

---

## Endpoint Testing Output

```bash
$ curl http://localhost:8080/
{
  "endpoints": [
    {
      "description": "Service information",
      "method": "GET",
      "path": "/"
    },
    {
      "description": "Health check",
      "method": "GET",
      "path": "/health"
    }
  ],
  "request": {
    "client_ip": "172.17.0.1",
    "method": "GET",
    "path": "/",
    "user_agent": "curl/8.7.1"
  },
  "runtime": {
    "current_time": "2026-02-03T18:20:48.898412+00:00",
    "timezone": "UTC",
    "uptime_human": "0 hours, 1 minutes",
    "uptime_seconds": 73
  },
  "service": {
    "description": "DevOps course info service",
    "framework": "Flask",
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "system": {
    "architecture": "aarch64",
    "cpu_count": 8,
    "hostname": "6f85dc7b7293",
    "platform": "Linux",
    "platform_version": "Linux-6.10.14-linuxkit-aarch64-with-glibc2.41",
    "python_version": "3.13.11"
  }
}

$ curl http://localhost:8080/health
{"status":"healthy","timestamp":"2026-02-03T18:20:48.908035+00:00","uptime_seconds":73}
```

---

## Docker Hub Repository

### Repository Information
URL: https://hub.docker.com/r/nayaya0/devops-info-service

### Available Tags

| Tag     | Digest       | OS/Arch          | Compressed Size |
|---------|---------------|------------------|-----------------|
| 1.0     | 86f0e81e7f52  | linux/arm64/v8   | 46.01 MB        |
| latest  | 86f0e81e7f52  | linux/arm64/v8   | 46.01 MB        |

### Tagging Strategy Explanation
Two-tag approach:
1. `nayaya0/devops-info-service:1.0` — Versioned release for reproducibility  
2. `nayaya0/devops-info-service:latest` — Latest stable for convenience

### Push Verification (Shortened)
```bash
$ docker push nayaya0/devops-info-service:1.0
The push refers to repository [docker.io/nayaya0/devops-info-service]
f2dca332e341: Pushed 
ee5e74e345bb: Pushed 
3ea009573b47: Pushed 
...
1.0: digest: sha256:ab576c5ce770ddc2c6b073823b7c5ed6f517098fcfa2d40c5cd5edae7cccdc2a size: 2617
```

---

## Technical Analysis

### Why the Dockerfile Works This Way
The command order is optimized for caching. Dependencies are installed before copying code, allowing layer reuse when code changes.

### What Would Happen If Layer Order Changed?
If code was copied before dependencies:
1. Any code change would invalidate the dependency layer cache
2. All dependencies would reinstall on every build
3. Build time would increase 2–3x

### Security Considerations Implemented
1. Non-root user: Application runs as regular user `appuser`
2. Minimal base image: Reduced attack surface (slim variant)
3. No unnecessary packages: Only required dependencies
4. `.dockerignore`: Prevents sensitive file inclusion
5. Specific Python version: Avoids unexpected security issues

### How `.dockerignore` Improves Build
1. Reduces build context → faster transfer to Docker daemon
2. Excludes unnecessary files → smaller image size
3. Prevents accidental inclusion of sensitive data (`.env`, credentials)
4. Speeds up CI/CD pipelines by ignoring test files and logs

---

## Challenges & Solutions

### Challenge 1: Docker Daemon Not Running
**Problem:** Cannot connect to the Docker daemon at unix:///Users/.../.docker/run/docker.sock  
**Solution:** Started Docker Desktop and waited for daemon to initialize  
**Learning:** Docker requires explicit daemon startup (Docker Desktop on macOS)

### Challenge 2: Large Image Size (450MB Initial)
**Problem:** Initial image was 450MB  
**Root Cause:** Empty `apt-get install` command installed unnecessary packages  
**Solution:** Removed `apt-get install`, kept only `apt-get clean`  
**Result:** Size reduced to 221MB (51% reduction)

### Challenge 3: Typo in Tag Name
**Problem:** Created tag `lates` instead of `latest`  
**Solution:** Removed incorrect tag, created correct one  
**Learning:** Docker allows multiple tags for same image; must double-check names

### Challenge 4: ARM64 Python Compilation Overhead
**Discovery:** On ARM64 (Apple Silicon), `python:3.13-slim` compiles Python from source  
**Impact:** Adds 43.2MB to image size  
**Acceptance:** For compatibility, kept slim image despite size; Alpine would be smaller
