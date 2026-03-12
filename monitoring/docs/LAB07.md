# Lab 7 — Observability & Logging with Loki Stack

## Student Information

- **Name:** Anastasia Kuchumova  
- **Date:** March 12, 2026  
- **Course:** DevOps Core Course  
- **GitHub Branch:** `lab07`

---

## 1. Architecture

- **Components:**
  - **Loki 3.0.0** — central log storage (TSDB on filesystem)
  - **Promtail 3.0.0** — log collector with Docker service discovery
  - **Grafana 12.3.1** — UI for querying and dashboards
  - **Application:** `devops-info-service` (Python + Flask, JSON logging)

- **High‑level flow:**
  - Containers write logs to stdout
  - Docker stores logs under `/var/lib/docker/containers`
  - Promtail discovers containers via Docker socket and reads log files
  - Promtail sends logs to Loki over HTTP (`/loki/api/v1/push`)
  - Grafana reads logs from Loki and visualizes them

- **Text diagram:**

  ```text
  [ devops-info-service container ]         [ loki container ]
                │                                   ▲
                ▼                                   │
  Docker JSON logs (/var/lib/docker/containers)    │
                │                                   │
                ▼                                   │
        [ promtail container ]  ───────────────►  HTTP push
                                                    │
                                                    ▼
                                           [ grafana container ]
  ```

---

## 2. Setup Guide

### 2.1 Prerequisites

- Docker Engine / Docker Desktop with **docker compose v2**
- Git Bash or WSL terminal
- Repository checked out to `DevOps-Core-Course`

### 2.2 Local stack deployment

1. Go to project root:
   ```bash
   cd DevOps-Core-Course/monitoring
   ```
2. Start Loki, Promtail, Grafana and app:
   ```bash
   docker compose up -d
   docker compose ps
   ```
3. Verify services:
   ```bash
   curl http://localhost:3100/ready         # Loki
   curl http://localhost:3000/api/health    # Grafana
   ```
4. Access Grafana in browser:
   ```text
   http://localhost:3000
   ```
   - **User:** `admin`
   - **Password:** `admin` (development only)

5. Add Loki data source in Grafana:
   - **Connections → Data sources → Add data source → Loki**
   - URL: `http://loki:3100`
   - Click **Save & test**.

---

## 3. Configuration

### 3.1 Loki (`monitoring/loki/config.yml`)

- **Server:**
  - HTTP port `3100`
  - `auth_enabled: false` for local testing
- **Storage:**
  - `common.storage.filesystem` with TSDB directories under `/var/loki`
  - Single instance (`replication_factor: 1`)
- **Schema:**
  - `schema: v13` with `store: tsdb`, `object_store: filesystem`
  - Daily index period (`period: 24h`)
- **Retention:**
  - `limits_config.retention_period: 168h` (7 days)
  - `compactor.retention_enabled: true` for cleanup

**Why this setup:**
- TSDB + filesystem is simple and fast for single-node labs
- 7‑day retention is enough for exercises without wasting disk
- No auth keeps configuration minimal for local environment

### 3.2 Promtail (`monitoring/promtail/config.yml`)

- **Server:** HTTP port `9080` for status endpoints
- **Clients:** send logs to `http://loki:3100/loki/api/v1/push`
- **Discovery:**
  - `docker_sd_configs` using `unix:///var/run/docker.sock`
  - Refresh interval: `5s`
- **Relabeling:**
  - Extract container name to label `container`
  - Copy container labels `app` and `logging`
- **Filtering and parsing:**
  - `pipeline_stages` parse only streams with `logging="promtail"`
  - `json` stage extracts fields like `level`, `message`, `event`, `method`, `path`, `status_code`, `client_ip`

**Why this setup:**
- Docker service discovery automatically tracks new/removed containers
- Labels (`app`, `logging`) allow clean LogQL selectors
- JSON parsing makes fields queryable in Grafana using `| json`

### 3.3 Docker Compose (`monitoring/docker-compose.yml`)

- **Network:** dedicated `logging` bridge for all services
- **Volumes:**
  - `loki-data` for logs and index
  - `grafana-data` for dashboards and data sources
- **Resource limits:** `deploy.resources` configured for:
  - Loki, Promtail, Grafana, and `app-python`
  - CPU and memory limits + reservations
- **Health checks:**
  - Loki: `curl -f http://localhost:3100/ready`
  - Grafana: `curl -f http://localhost:3000/api/health`

---

## 4. Application Logging (JSON)

- **Application:** `labs/app_python/app.py`
- **Logger configuration:**
  - Custom `JSONFormatter` based on `logging.Formatter`
  - Logger name: `"devops-info-service"`
  - Level controlled via env var `LOG_LEVEL` (default `INFO`)
  - Output to stdout (picked up by Docker and Promtail)

- **Logged events:**
  - **Startup:** host, port, debug mode
  - **Requests:** method, path, client IP, user agent
  - **Responses:** method, path, status code, client IP
  - **Health checks:** uptime seconds and client IP
  - **Errors:** 404 and 500 with path and client IP

- **Example JSON log (conceptual):**

  ```json
  {
    "timestamp": "2026-03-12T12:00:00+00:00",
    "level": "INFO",
    "message": "Request handled",
    "event": "response",
    "method": "GET",
    "path": "/health",
    "status_code": 200,
    "client_ip": "127.0.0.1"
  }
  ```

---

## 5. Dashboard

Grafana dashboard built with **Loki** data source and the following panels:

1. **Logs Table** (logs view)  
   - Query: `{app=~"devops-.*"}`
   - Shows recent logs from all devops applications.

2. **Request Rate** (time series)  
   - Query: `sum by (app) (rate({app=~"devops-.*"} [1m]))`  
   - Visualizes number of log lines per second per app (proxy for request rate).

3. **Error Logs** (logs view)  
   - Query: `{app=~"devops-.*"} | json | level="ERROR"`  
   - Filters only error-level entries from JSON logs.

4. **Log Level Distribution** (pie/stat)  
   - Query: `sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))`  
   - Shows count of logs by level (INFO, ERROR, etc.) over last 5 minutes.

---

## 6. Production Config

- **Resource limits:**
  - All services have CPU and memory limits and reservations
  - Protects host from runaway resource usage
- **Security:**
  - Anonymous Grafana access disabled: `GF_AUTH_ANONYMOUS_ENABLED=false`
  - Admin password set via `GF_SECURITY_ADMIN_PASSWORD` env var
  - For real deployments secrets should be moved to `.env` and not committed
- **Retention:**
  - Loki keeps logs for **7 days** (`168h`)
  - Compactor and table manager configured to delete old data

---

## 7. Testing

### 7.1 Stack verification

- Check running containers:
  ```bash
  cd DevOps-Core-Course/monitoring
  docker compose ps
  ```

- Health endpoints:
  ```bash
  curl http://localhost:3100/ready
  curl http://localhost:3000/api/health
  ```

### 7.2 Application traffic

- Generate log traffic:
  ```bash
  for i in {1..20}; do curl http://localhost:8000/; done
  for i in {1..20}; do curl http://localhost:8000/health; done
  ```

### 7.3 LogQL examples

- All logs from Python app:
  ```logql
  {app="devops-python"}
  ```

- Only errors:
  ```logql
  {app="devops-python"} |= "ERROR"
  ```

- JSON parsing and field filtering:
  ```logql
  {app="devops-python"} | json | method="GET"
  ```

---

## 8. Challenges

- **Loki configuration:**  
  Needed to carefully follow Loki 3.0 TSDB config (schema v13, common section).

- **Promtail relabeling:**  
  Correct extraction of container name and labels was required for clean selectors.

- **JSON logging design:**  
  Designing a simple custom formatter that stays readable but still structured.

---

## 9. Summary

- Loki, Promtail, Grafana, and the Python app run together via Docker Compose.  
- Application logs are structured JSON and fully queryable in Grafana using LogQL.  
- Dashboard provides visibility into log streams, request rate, errors and levels.  
- Stack is prepared for small‑scale production use with retention, limits and basic security.

