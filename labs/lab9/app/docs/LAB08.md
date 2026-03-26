# Lab 8 — Metrics & Monitoring with Prometheus

## Task 1 — Application Metrics

### Metrics I Implemented

#### 1. HTTP Metrics (RED Method):
- **`http_requests_total`** (Counter) — Total HTTP requests with labels:
  - `method` (GET, POST)
  - `endpoint` (/, /health, /metrics)
  - `status` (200, 404, 500)
  
- **`http_request_duration_seconds`** (Histogram) — Request duration
  - Helps track performance and latency
  - Buckets from 5ms to 10s for detailed analysis
  - Essential for SLOs/SLAs
  
- **`http_requests_in_progress`** (Gauge) — Current active requests
  - Shows real-time load on the service
  - Helps detect traffic spikes

#### 2. Business Metrics:
- **`devops_info_endpoint_calls`** (Counter) — Number of endpoint calls
  - Tracks which endpoints are most popular
  - Helps understand user behavior

- **`devops_info_system_collection_seconds`** (Histogram) — System info collection time
  - Monitors performance of system information gathering
  - Helps identify slow operations

- **`devops_info_active_clients`** (Gauge) — Active clients
  - Shows how many users are currently using the service
  - Useful for capacity planning

- **`devops_info_uptime_seconds`** (Gauge) — Service uptime
  - Tracks how long the service has been running
  - Important for availability monitoring

### Screenshot of /metrics Endpoint

![Metrics output](screenshots/metrics-endpoint.png)

*Screenshot shows all implemented metrics with their current values*

### Why I Chose These Metrics

1. **RED Method (Rate, Errors, Duration)** — Industry standard for web services:
   - **Rate** (`http_requests_total`) — How much traffic?
   - **Errors** (`http_requests_total{status=~"5.."}`) — How many failures?
   - **Duration** (`http_request_duration_seconds`) — How fast is the response?

2. **Business Metrics** — Show how the service is used:
   - Track feature adoption (`endpoint_calls`)
   - Monitor user engagement (`active_clients`)
   - Measure operational efficiency (`system_collection_seconds`)

3. **Uptime** — Basic availability monitoring:
   - Quick health check
   - Integration with alerting

### Code Implementation

```python
from prometheus_client import Counter, Histogram, Gauge

# HTTP Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests in progress'
)

# Business Metrics
endpoint_calls = Counter(
    'devops_info_endpoint_calls',
    'Number of calls to specific endpoints',
    ['endpoint', 'method']
)

system_info_duration = Histogram(
    'devops_info_system_collection_seconds',
    'Time taken to collect system information'
)

active_clients = Gauge(
    'devops_info_active_clients',
    'Number of active clients currently using the service'
)

service_uptime_seconds = Gauge(
    'devops_info_uptime_seconds',
    'Service uptime in seconds'
)
'''
###Testing Results

-After implementing the metrics, I tested the endpoint:
# Test the main endpoint
-curl http://localhost:8080/

# Test health check
-curl http://localhost:8080/health

# View all metrics
-curl http://localhost:8080/metrics
### Evidence

-✅ /metrics endpoint is accessible
-✅ All required metric types implemented (Counter, Gauge, Histogram)
-✅ Proper labels used (method, endpoint, status)
-✅ Business metrics added as required
-✅ Metrics show real values after making requests

## Task 3 — Grafana Dashboards

### Prometheus Data Source

I added Prometheus as a data source in Grafana:
- URL: http://prometheus:9090
- Status: ✅ Successfully connected

### Dashboard Panels

I created a custom dashboard with 7 panels:

1. **HTTP Requests per Second** - Shows request rate by endpoint
2. **5xx Error Rate** - Monitors server errors
3. **95th Percentile Request Duration** - Performance monitoring
4. **Concurrent Requests** - Real-time load
5. **HTTP Status Codes** - Distribution of responses
6. **Service Uptime** - Availability monitoring
7. **System Info Collection Time** - Business metric

### Dashboard Screenshot
![Grafana Dashboard](screenshots/grafana-dashboard.png)

### PromQL Queries Used

```promql
# Request Rate
sum(rate(http_requests_total[5m])) by (endpoint)

# Error Rate
sum(rate(http_requests_total{status=~"5.."}[5m]))

# 95th Percentile Duration
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))

# Active Requests
http_requests_in_progress

# Status Distribution
sum by (status) (rate(http_requests_total[5m]))

# Uptime
up{job="app"}

# Average System Info Time
rate(devops_info_system_collection_seconds_sum[5m]) / rate(devops_info_system_collection_seconds_count[5m])