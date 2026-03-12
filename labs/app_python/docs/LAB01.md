# Lab 1 Submission - DevOps Info Service

## Framework Selection

**Choice:** Flask

**Why Flask:**
1. **Simplicity** - Easy to learn and understand
2. **Lightweight** - Minimal dependencies
3. **Flexibility** - Can add only what we need
4. **Documentation** - Excellent official docs

**Comparison Table:**
| Framework | Pros | Cons | For our project |
|-----------|------|------|-----------------|
| Flask     | Simple, lightweight, flexible | Less built-in features | ✅ Perfect choice |
| FastAPI   | Async, auto-docs, validation | Steeper learning curve | Overkill |
| Django    | Full-featured, ORM, admin | Heavyweight, complex | Too much |

## Best Practices Applied

### 1. Clean Code Organization
```python
# Imports grouped by purpose
import os
import platform
import socket
from datetime import datetime, timezone
from flask import Flask, jsonify, request 
```
### Error Handling
- Implemented 404 and 500 error handlers.
### Configuration Management

```python
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
```
### API Documentation 
#### GET /
Returns comprehensive system information including:
- Service metadata (name, version, framework)
- System details (hostname, platform, CPU, Python version)
- Runtime information (uptime, current time)
- Request information (client IP, user agent)
- Available endpoints

#### GET /health
Returns health status for monitoring with:
- Status indicator ("healthy")
- Current timestamp in ISO format
- Uptime in seconds

### Testing Evidence

Service tested successfully on port 8080 with the following commands:
```bash
curl http://localhost:8080/ | jq .
curl http://localhost:8080/health | jq .
```

### Screenshots Attached

1. **Main endpoint**: Complete JSON response from `GET /`
2. **Health check**: JSON response from `GET /health`  
3. **Formatted output**: Pretty-printed output using `jq`

### Challenges Solved

1. **Port conflict**: Used `PORT=8080` instead of default `5000` to avoid conflicts with macOS AirPlay Receiver
2. **JSON validation**: Tested with `jq` tool to ensure proper JSON formatting and validate response structure
